/* ===== GitHub-native Editor Links ===== */
/* Editing stays on github.com, so authentication is handled by GitHub itself. */

var Editor = (function () {
  'use strict';

  var OWNER = 'NBStarry';
  var REPO = 'StarryBei-ai-config';
  var EDIT_BRANCH = 'dev';
  var viewBranch = EDIT_BRANCH;
  var DEFAULT_REPOSITORY = OWNER + '/' + REPO;

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

  function getTarget(repository, branch) {
    return {
      webBase: 'https://github.com/' + (repository || DEFAULT_REPOSITORY),
      branch: branch || EDIT_BRANCH
    };
  }

  function edit(filePath) {
    var target = getTarget();
    window.location.assign(target.webBase + '/edit/' + target.branch + '/' + encodePath(filePath));
  }

  function remove(filePath) {
    var target = getTarget();
    window.location.assign(target.webBase + '/delete/' + target.branch + '/' + encodePath(filePath));
  }

  function create(directory, template, defaultName, repository, branch) {
    var name = window.prompt('New file path under ' + directory + '/', defaultName || '');
    if (!name || !name.trim()) return;
    var params = new URLSearchParams();
    params.set('filename', name.trim());
    if (template) params.set('value', template);
    var target = getTarget(repository, branch);
    window.location.assign(target.webBase + '/new/' + target.branch + '/' + encodePath(directory) + '?' + params.toString());
  }

  function createEditBtn(filePath, repository, branch) {
    var target = getTarget(repository, branch);
    var btn = document.createElement('a');
    btn.className = 'btn-edit';
    btn.href = target.webBase + '/edit/' + target.branch + '/' + encodePath(filePath);
    btn.target = '_blank';
    btn.rel = 'noopener noreferrer';
    btn.textContent = 'GitHub Edit';
    btn.title = 'Edit with your GitHub login';
    btn.addEventListener('click', function (event) {
      event.stopPropagation();
    });
    return btn;
  }

  function createDeleteBtn(filePath, repository, branch) {
    var target = getTarget(repository, branch);
    var btn = document.createElement('a');
    btn.className = 'btn-delete';
    btn.href = target.webBase + '/delete/' + target.branch + '/' + encodePath(filePath);
    btn.target = '_blank';
    btn.rel = 'noopener noreferrer';
    btn.textContent = 'GitHub Delete';
    btn.title = 'Delete with your GitHub login';
    btn.addEventListener('click', function (event) {
      event.stopPropagation();
    });
    return btn;
  }

  function createCreateBtn(directory, template, defaultName, repository, branch) {
    var btn = document.createElement('button');
    btn.className = 'btn-create';
    btn.type = 'button';
    btn.textContent = '+';
    btn.title = 'Create on GitHub with your GitHub login';
    btn.addEventListener('click', function (event) {
      event.stopPropagation();
      create(directory, template, defaultName, repository, branch);
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
