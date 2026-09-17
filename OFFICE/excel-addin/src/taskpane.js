(function () {
  'use strict';

  var EXPECTED_USERNAME = 'admin';
  var EXPECTED_PASSWORD = '1';
  var OFFICE_WAIT_LIMIT_MS = 3000;
  var OFFICE_POLL_MS = 200;

  var state = { loggedIn: false, dialogOpen: false, menuOpen: false, error: false };
  var refs = {};

  [
    'login-trigger', 'login-dialog', 'login-form', 'username-input', 'password-input',
    'login-submit', 'login-cancel', 'login-error', 'login-status',
    'user-menu', 'user-menu-trigger', 'user-menu-name', 'logout-item'
  ].forEach(function (id) {
    refs[id] = document.getElementById(id);
  });

  function render() {
    refs['login-dialog'].hidden = !state.dialogOpen;
    refs['login-trigger'].hidden = state.loggedIn;
    refs['login-status'].hidden = !state.loggedIn;
    refs['user-menu-trigger'].hidden = !state.loggedIn;
    refs['user-menu'].hidden = !(state.loggedIn && state.menuOpen);
    refs['user-menu-trigger'].setAttribute('aria-expanded', state.loggedIn && state.menuOpen ? 'true' : 'false');
    refs['login-error'].hidden = !state.error;
  }

  function openDialog() {
    state.dialogOpen = true;
    state.error = false;
    refs['username-input'].value = '';
    refs['password-input'].value = '';
    render();
    refs['username-input'].focus();
  }

  function closeDialog() {
    state.dialogOpen = false;
    state.error = false;
    render();
  }

  function submitLogin() {
    var name = refs['username-input'].value.trim();
    var password = refs['password-input'].value;
    if (name !== EXPECTED_USERNAME || password !== EXPECTED_PASSWORD) {
      state.error = true;
      render();
      return;
    }
    state.loggedIn = true;
    state.dialogOpen = false;
    state.menuOpen = false;
    state.error = false;
    refs['user-menu-name'].textContent = EXPECTED_USERNAME;
    render();
  }

  function toggleMenu() {
    if (!state.loggedIn) return;
    state.menuOpen = !state.menuOpen;
    render();
  }

  function logout() {
    state.loggedIn = false;
    state.dialogOpen = false;
    state.menuOpen = false;
    state.error = false;
    render();
  }

  refs['login-trigger'].addEventListener('click', openDialog);
  refs['login-cancel'].addEventListener('click', closeDialog);
  // 点击时阻止原生提交, 避免 click 与 submit 双触发; 回车仍走 form 的 submit。
  refs['login-submit'].addEventListener('click', function (event) {
    event.preventDefault();
    submitLogin();
  });
  refs['login-form'].addEventListener('submit', function (event) {
    event.preventDefault();
    submitLogin();
  });
  refs['user-menu-trigger'].addEventListener('click', function (event) {
    event.stopPropagation();
    toggleMenu();
  });
  refs['logout-item'].addEventListener('click', function (event) {
    event.stopPropagation();
    logout();
  });
  document.addEventListener('click', function () {
    if (state.menuOpen) {
      state.menuOpen = false;
      render();
    }
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && state.dialogOpen) closeDialog();
  });

  window.__xpathRange = {
    getState: function () {
      return {
        loggedIn: state.loggedIn,
        dialogOpen: state.dialogOpen,
        menuOpen: state.menuOpen,
        error: state.error
      };
    }
  };

  render();

  // office.js 用 async 加载: 在浏览器里直接打开(无 Office 宿主)或离线时静默降级, 不影响靶场交互。
  var waited = 0;
  function waitForOffice() {
    if (typeof Office !== 'undefined' && Office.onReady) {
      Office.onReady(function () {});
      return;
    }
    if (waited >= OFFICE_WAIT_LIMIT_MS) return;
    waited += OFFICE_POLL_MS;
    window.setTimeout(waitForOffice, OFFICE_POLL_MS);
  }
  waitForOffice();
})();
