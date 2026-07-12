#!/usr/bin/env node

import fs from 'node:fs';
import fsp from 'node:fs/promises';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(SCRIPT_DIR, '..');
const SITE_ROOT = path.join(REPO_ROOT, 'site');
const HOME = os.homedir();

const args = process.argv.slice(2);
const options = { port: 4173, open: false, check: false };
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--port') options.port = Number(args[++i]);
  else if (args[i] === '--open') options.open = true;
  else if (args[i] === '--check') options.check = true;
  else throw new Error(`Unknown option: ${args[i]}`);
}
if (!Number.isInteger(options.port) || options.port < 1024 || options.port > 65535) {
  throw new Error('--port must be an integer between 1024 and 65535');
}

function homePath(...parts) {
  return path.join(HOME, ...parts);
}

function friendlyPath(filePath) {
  const absolute = path.resolve(filePath);
  const homePrefix = path.resolve(HOME) + path.sep;
  const value = absolute.toLowerCase().startsWith(homePrefix.toLowerCase())
    ? `~${path.sep}${absolute.slice(homePrefix.length)}`
    : absolute;
  return value.split(path.sep).join('/');
}

function parseFrontmatter(raw, fallbackName) {
  const normalized = raw.replace(/^\uFEFF/, '');
  const match = normalized.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
  const frontmatter = match ? match[1] : '';
  const body = match ? match[2] : normalized;
  const lines = frontmatter.split(/\r?\n/);

  function field(name) {
    for (let i = 0; i < lines.length; i++) {
      const found = lines[i].match(new RegExp(`^${name}:\\s*(.*)$`));
      if (!found) continue;
      let value = found[1].trim();
      if (/^[>|][+-]?$/.test(value)) {
        const continuation = [];
        for (i++; i < lines.length && (/^\s/.test(lines[i]) || lines[i] === ''); i++) {
          continuation.push(lines[i].trim());
        }
        value = continuation.filter(Boolean).join(' ');
      }
      return value.replace(/^['"]|['"]$/g, '');
    }
    return '';
  }

  return {
    name: field('name') || fallbackName,
    description: field('description'),
    version: field('version'),
    content: body
  };
}

async function findNamedFiles(root, fileName) {
  if (!fs.existsSync(root)) return [];
  const files = [];
  const visited = new Set();

  async function visit(directory) {
    let realDirectory;
    try {
      realDirectory = await fsp.realpath(directory);
    } catch {
      return;
    }
    const key = process.platform === 'win32' ? realDirectory.toLowerCase() : realDirectory;
    if (visited.has(key)) return;
    visited.add(key);

    let entries;
    try {
      entries = await fsp.readdir(directory, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const fullPath = path.join(directory, entry.name);
      if (entry.name === fileName && entry.isFile()) {
        files.push(fullPath);
        continue;
      }
      if (entry.isDirectory()) {
        await visit(fullPath);
      } else if (entry.isSymbolicLink()) {
        try {
          if ((await fsp.stat(fullPath)).isDirectory()) await visit(fullPath);
        } catch { /* dangling local link */ }
      }
    }
  }

  await visit(root);
  return files;
}

function redactObject(value, key = '') {
  if (/(token|secret|password|passphrase|api[_-]?key|authorization|cookie|credential)/i.test(key)) {
    return '[REDACTED]';
  }
  if (Array.isArray(value)) return value.map(item => redactObject(item));
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([name, item]) => [name, redactObject(item, name)]));
  }
  return value;
}

function redactText(content) {
  return content
    .replace(/\b(ghp_|github_pat_|sk-)[A-Za-z0-9_-]{12,}/g, '[REDACTED]')
    .replace(/^(\s*[^#\r\n]*(?:token|secret|password|passphrase|api[_-]?key|authorization|cookie|credential)[^=]*=\s*).+$/gim, '$1"[REDACTED]"');
}

async function readLocalConfig(filePath) {
  if (!fs.existsSync(filePath)) return null;
  const raw = await fsp.readFile(filePath, 'utf8');
  const extension = path.extname(filePath).toLowerCase();
  let content = redactText(raw);
  let meta = { keys: 0, has_hooks: false, has_plugins: false, model: null, plugin_count: 0, hook_event_count: 0 };
  if (extension === '.json') {
    try {
      const parsed = redactObject(JSON.parse(raw));
      content = JSON.stringify(parsed, null, 2);
      meta = {
        keys: Object.keys(parsed).length,
        has_hooks: Boolean(parsed.hooks),
        has_plugins: Boolean(parsed.enabledPlugins),
        model: parsed.model || null,
        plugin_count: parsed.enabledPlugins ? Object.keys(parsed.enabledPlugins).length : 0,
        hook_event_count: parsed.hooks ? Object.keys(parsed.hooks).length : 0
      };
    } catch { /* retain redacted raw content */ }
  }
  return {
    name: `local: ${path.basename(filePath)}`,
    file: friendlyPath(filePath),
    meta,
    content
  };
}

async function readManagedSourceContent(source) {
  if (!source) return { content: '', contentFile: '' };
  let contentFile = source;
  let stat;
  try { stat = await fsp.stat(source); } catch { return { content: '', contentFile: '' }; }
  if (stat.isDirectory()) {
    contentFile = ['SKILL.md.example', 'SKILL.md', 'README.md', path.join('.claude-plugin', 'marketplace.json')]
      .map(name => path.join(source, name))
      .find(candidate => fs.existsSync(candidate)) || '';
  }
  if (!contentFile) return { content: '', contentFile: '' };

  const raw = await fsp.readFile(contentFile, 'utf8');
  let content = redactText(raw);
  if (path.extname(contentFile).toLowerCase() === '.json') {
    try { content = JSON.stringify(redactObject(JSON.parse(raw)), null, 2); } catch { /* keep redacted text */ }
  }
  return { content, contentFile: friendlyPath(contentFile) };
}

function latestInstallation(installations) {
  return [...installations].sort((a, b) =>
    String(b.lastUpdated || b.installedAt || '').localeCompare(String(a.lastUpdated || a.installedAt || ''))
  )[0];
}

async function getLocalInventory() {
  const manifest = JSON.parse(await fsp.readFile(path.join(REPO_ROOT, 'config', 'manifest.json'), 'utf8'));
  const platform = process.platform === 'win32' ? 'windows' : process.platform === 'darwin' ? 'macos' : 'linux';
  const resources = [];

  for (const resource of manifest.resources) {
    const candidates = resource.sourceCandidates || (resource.source ? [resource.source] : []);
    const source = candidates
      .map(candidate => path.isAbsolute(candidate) ? candidate : path.join(REPO_ROOT, candidate))
      .find(candidate => fs.existsSync(candidate)) || null;
    const target = path.resolve(resource.target.replace('${home}', HOME).split('/').join(path.sep));
    const supported = resource.platforms.includes(platform);
    let item = null;
    try { item = await fsp.lstat(target); } catch { /* missing or dangling target */ }

    let status = 'missing';
    let detail = 'Target does not exist.';
    if (!supported) {
      status = 'unsupported';
      detail = `Not managed on ${platform}.`;
    } else if (!source) {
      status = 'missing-source';
      detail = 'No source candidate exists in this checkout.';
    } else if (resource.method === 'seed' && item) {
      status = 'installed';
      detail = 'Seed target exists and is intentionally not overwritten.';
    } else if (item) {
      let matches = false;
      if (item.isSymbolicLink()) {
        const linkTarget = await fsp.readlink(target);
        const actual = path.resolve(path.dirname(target), linkTarget).toLowerCase();
        matches = actual === path.resolve(source).toLowerCase();
      }
      if (matches) {
        status = 'installed';
        detail = 'Target points to the selected repository source.';
      } else {
        status = 'drifted';
        detail = 'Target exists but does not point to the selected repository source.';
      }
    }
    const display = await readManagedSourceContent(source);
    resources.push({
      ...resource,
      source,
      target,
      status,
      action: status === 'missing' ? 'install' : status === 'drifted' ? 'replace' : 'none',
      detail,
      content: display.content,
      contentFile: display.contentFile
    });
  }
  return {
    mode: 'actual',
    version: manifest.version,
    resources
  };
}

async function buildLocalData() {
  const base = JSON.parse(await fsp.readFile(path.join(SITE_ROOT, 'data.json'), 'utf8'));
  const data = JSON.parse(JSON.stringify(base));
  data.mode = 'local';
  data.git = { branch: 'local', commit: 'working-tree' };
  data.generated_at = new Date().toISOString();
  data.local = {
    hostname: os.hostname(),
    secrets_redacted: true,
    persisted: false,
    sources: []
  };
  data.inventory = await getLocalInventory();

  const skillKeys = new Set(data.skills.map(skill => `${skill.source}\u0000${skill.name}`.toLowerCase()));
  async function addSkills(root, source) {
    const files = await findNamedFiles(root, 'SKILL.md');
    if (files.length) data.local.sources.push({ source, root: friendlyPath(root), files: files.length });
    for (const filePath of files) {
      const raw = await fsp.readFile(filePath, 'utf8');
      const parsed = parseFrontmatter(raw, path.basename(path.dirname(filePath)));
      const key = `${source}\u0000${parsed.name}`.toLowerCase();
      if (skillKeys.has(key)) continue;
      skillKeys.add(key);
      data.skills.push({
        name: parsed.name,
        description: parsed.description,
        version: parsed.version,
        source,
        file: friendlyPath(filePath),
        content: parsed.content
      });
    }
  }

  const registryPath = homePath('.claude', 'plugins', 'installed_plugins.json');
  const installedPlugins = [];
  if (fs.existsSync(registryPath)) {
    const registry = JSON.parse(await fsp.readFile(registryPath, 'utf8'));
    const recommended = new Map(data.plugins.map(plugin => [`${plugin.name}@${plugin.marketplace}`, plugin]));
    for (const [pluginId, installations] of Object.entries(registry.plugins || {})) {
      const splitAt = pluginId.lastIndexOf('@');
      const name = splitAt > 0 ? pluginId.slice(0, splitAt) : pluginId;
      const marketplace = splitAt > 0 ? pluginId.slice(splitAt + 1) : 'local';
      const installation = latestInstallation(installations) || {};
      const known = recommended.get(pluginId) || {};
      installedPlugins.push({
        ...known,
        name,
        marketplace,
        installed: true,
        version: installation.version || '',
        scope: installation.scope || '',
        installed_at: installation.installedAt || '',
        last_updated: installation.lastUpdated || ''
      });
      if (installation.installPath && fs.existsSync(installation.installPath)) {
        await addSkills(installation.installPath, marketplace);
      }
    }
    data.local.sources.push({ source: 'claude-plugins', root: friendlyPath(registryPath), files: installedPlugins.length });
  }

  await addSkills(homePath('.claude', 'skills'), 'claude-local');
  await addSkills(homePath('.codex', 'skills'), 'codex-local');
  await addSkills(homePath('.agents', 'skills'), 'agents-local');

  const localConfigPaths = [
    homePath('.claude', 'settings.json'),
    homePath('.claude', 'CLAUDE.md'),
    homePath('.claude', 'plugins', 'installed_plugins.json'),
    homePath('.claude', 'plugins', 'known_marketplaces.json'),
    homePath('.codex', 'config.toml'),
    homePath('.codex', 'AGENTS.md')
  ];
  for (const configPath of localConfigPaths) {
    const config = await readLocalConfig(configPath);
    if (config) data.configs.push(config);
  }

  if (installedPlugins.length) data.plugins = installedPlugins;
  data.stats.total_skills = data.skills.length;
  data.stats.total_configs = data.configs.length;
  data.stats.total_plugins = data.plugins.length;
  data.stats.total_resources = data.inventory.resources.length;
  return data;
}

function contentType(filePath) {
  return ({
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.ico': 'image/x-icon'
  })[path.extname(filePath).toLowerCase()] || 'application/octet-stream';
}

function openBrowser(url) {
  const command = process.platform === 'win32' ? 'cmd.exe' : process.platform === 'darwin' ? 'open' : 'xdg-open';
  const commandArgs = process.platform === 'win32' ? ['/c', 'start', '', url] : [url];
  const child = spawn(command, commandArgs, { detached: true, stdio: 'ignore', windowsHide: true });
  child.unref();
}

const localData = await buildLocalData();
if (options.check) {
  const contentResources = localData.inventory.resources.filter(resource => resource.content).length;
  console.log(`Local Dashboard data: skills=${localData.stats.total_skills} configs=${localData.stats.total_configs} plugins=${localData.stats.total_plugins} resources=${localData.stats.total_resources} contents=${contentResources}`);
  process.exit(0);
}

const localJson = JSON.stringify(localData);
const server = http.createServer(async (request, response) => {
  try {
    const requestUrl = new URL(request.url, `http://${request.headers.host || '127.0.0.1'}`);
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      response.writeHead(405, { Allow: 'GET, HEAD' });
      response.end();
      return;
    }
    if (requestUrl.pathname === '/data.json') {
      response.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
      response.end(request.method === 'HEAD' ? undefined : localJson);
      return;
    }

    const relativePath = requestUrl.pathname === '/' ? 'index.html' : decodeURIComponent(requestUrl.pathname.slice(1));
    const filePath = path.resolve(SITE_ROOT, relativePath);
    const sitePrefix = path.resolve(SITE_ROOT) + path.sep;
    if (filePath !== path.join(SITE_ROOT, 'index.html') && !filePath.startsWith(sitePrefix)) {
      response.writeHead(403);
      response.end('Forbidden');
      return;
    }
    const body = await fsp.readFile(filePath);
    response.writeHead(200, { 'Content-Type': contentType(filePath), 'Cache-Control': 'no-store' });
    response.end(request.method === 'HEAD' ? undefined : body);
  } catch (error) {
    response.writeHead(error.code === 'ENOENT' ? 404 : 500, { 'Content-Type': 'text/plain; charset=utf-8' });
    response.end(error.code === 'ENOENT' ? 'Not found' : 'Local Dashboard error');
  }
});

server.listen(options.port, '127.0.0.1', () => {
  const url = `http://127.0.0.1:${options.port}/?branch=local#dashboard`;
  console.log(`Local Dashboard: ${url}`);
  console.log('Data stays in memory; auth files are excluded and sensitive config values are redacted.');
  console.log('Press Ctrl+C to stop.');
  if (options.open) openBrowser(url);
});
