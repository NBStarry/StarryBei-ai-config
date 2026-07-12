/* ===== GitHub-native Editor Links ===== */
/* Editing stays on github.com, so authentication is handled by GitHub itself. */

var Editor = (function () {
  'use strict';

  var OWNER = 'NBStarry';
  var REPO = 'StarryBei-ai-config';
  var EDIT_BRANCH = 'dev';
  var viewBranch = EDIT_BRANCH;
  var WEB_BASE = 'https://github.com/' + OWNER + '/' + REPO;

  function setViewBranch(branch) {
    viewBranch = branch || EDIT_BRANCH;
  }

  function canEdit() {
    return viewBranch === EDIT_BRANCH;
  }

  function encodePath(filePath) {
    return String(filePath || '')
      .split('/')
      .filter(Boolean)
      .map(encodeURIComponent)
      .join('/');
  }

  function openGitHub(url) {
    window.open(url, '_blank', 'noopener,noreferrer');
  }

  function edit(filePath) {
    openGitHub(WEB_BASE + '/edit/' + EDIT_BRANCH + '/' + encodePath(filePath));
  }

  function remove(filePath) {
    openGitHub(WEB_BASE + '/delete/' + EDIT_BRANCH + '/' + encodePath(filePath));
  }

  function create(directory, template, defaultName) {
    var name = window.prompt('New file path under ' + directory + '/', defaultName || '');
    if (!name || !name.trim()) return;
    var params = new URLSearchParams();
    params.set('filename', name.trim());
    if (template) params.set('value', template);
    openGitHub(WEB_BASE + '/new/' + EDIT_BRANCH + '/' + encodePath(directory) + '?' + params.toString());
  }

  function createEditBtn(filePath) {
    var btn = document.createElement('button');
    btn.className = 'btn-edit';
    btn.type = 'button';
    btn.textContent = 'GitHub Edit';
    btn.title = 'Edit with your GitHub login';
    btn.addEventListener('click', function (event) {
      event.stopPropagation();
      edit(filePath);
    });
    return btn;
  }

  function createDeleteBtn(filePath) {
    var btn = document.createElement('button');
    btn.className = 'btn-delete';
    btn.type = 'button';
    btn.textContent = 'GitHub Delete';
    btn.title = 'Delete with your GitHub login';
    btn.addEventListener('click', function (event) {
      event.stopPropagation();
      remove(filePath);
    });
    return btn;
  }

  function createCreateBtn(directory, template, defaultName) {
    var btn = document.createElement('button');
    btn.className = 'btn-create';
    btn.type = 'button';
    btn.textContent = '+';
    btn.title = 'Create on GitHub with your GitHub login';
    btn.addEventListener('click', function (event) {
      event.stopPropagation();
      create(directory, template, defaultName);
    });
    return btn;
  }

  return {
    setViewBranch: setViewBranch,
    canEdit: canEdit,
    edit: edit,
    create: create,
    remove: remove,
    createEditBtn: createEditBtn,
    createDeleteBtn: createDeleteBtn,
    createCreateBtn: createCreateBtn
  };
})();
