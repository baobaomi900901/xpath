'use strict';
const menu = document.querySelector('#menu');
const buttons = [...menu.querySelectorAll('[data-index]')];
const api = window.electronRange;
let selected = 0;
let revision = -1;
function render(state) {
  if (state.revision < revision) return;
  revision = state.revision;
  selected = state.selected;
  for (const [index, button] of buttons.entries()) button.setAttribute('aria-selected', String(index === selected));
  menu.setAttribute('aria-activedescendant', `menu-${selected}`);
  document.querySelector('#address').value = state.address;
  document.querySelector('#status').textContent = state.status;
  document.querySelector('#status').dataset.error = String(Boolean(state.error));
  document.querySelector('#range-title').textContent = `Electron ${state.runtime.major} 靶场`;
  document.querySelector('#view-mode').textContent = `Electron ${state.runtime.electron} · Chromium ${state.runtime.chromium} · Node ${state.runtime.node} · ${state.mode}`;
  const info = document.querySelector('#runtime-info');
  info.replaceChildren();
  for (const [label, value] of [['Electron', state.runtime.electron], ['Chromium', state.runtime.chromium], ['Node', state.runtime.node], ['嵌入方式', state.mode]]) {
    const dt = document.createElement('dt'), dd = document.createElement('dd');
    dt.textContent = label;
    dd.textContent = value;
    info.append(dt, dd);
  }
}
menu.addEventListener('click', event => {
  const button = event.target.closest('[data-index]');
  if (!button) return;
  menu.focus();
  api.select(Number(button.dataset.index));
});
menu.addEventListener('keydown', event => {
  if (!['ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)) return;
  event.preventDefault();
  const index = event.key === 'Home' ? 0 : event.key === 'End' ? 2 : Math.max(0, Math.min(2, selected + (event.key === 'ArrowDown' ? 1 : -1)));
  if (index !== selected) api.select(index);
});
document.querySelector('#refresh').addEventListener('click', () => api.refresh());
api.onState(render);
api.getState().then(render).catch(error => { document.querySelector('#status').textContent = `初始化失败：${error.message}`; });
