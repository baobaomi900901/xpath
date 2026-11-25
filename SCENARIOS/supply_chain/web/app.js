'use strict';
(() => {
  const $ = globalThis.InventoryObstacles.bind(document, document.documentElement.dataset.obstacles === 'true');
  const model = globalThis.InventoryModel;
  const state = {rows:[], key:'material_id', direction:'asc', page:1, query:'', ready:false, loading:false, exporting:false};
  const fields = ['material_id','name','unit','plant','warehouse','current','safety','target','enabled'];
  let request = 0;
  function setBusy(busy) {
    state.loading = busy;
    $('inventory').setAttribute('aria-busy', String(busy));
    $('query').disabled = busy;
    $('export').disabled = busy || state.exporting || !state.ready;
    $('previous').disabled = busy || state.page <= 1;
    $('next').disabled = busy || state.page >= Math.max(1, Math.ceil(state.rows.length / 8));
  }
  function render() {
    const view = model.view(state.rows, state.key, state.direction, state.page);
    state.page = view.page;
    $('rows').replaceChildren();
    for (const row of view.rows) {
      const tr = document.createElement('tr');
      for (const field of fields) {
        const td = document.createElement('td');
        td.textContent = field === 'enabled' ? (row[field] ? '启用' : '停用') : row[field];
        if (['current','safety','target'].includes(field)) td.className = 'number';
        if (field === 'enabled') td.className = row[field] ? 'enabled' : 'disabled';
        tr.append(td);
      }
      $('rows').append(tr);
    }
    if (!view.total) {
      const tr = document.createElement('tr'), td = document.createElement('td');
      td.colSpan = fields.length; td.className = 'empty'; td.textContent = '没有符合条件的库存记录，请调整查询条件。'; tr.append(td); $('rows').append(tr);
    }
    $('count').textContent = `共 ${view.total} 条 · 每页 8 条`;
    $('page').textContent = `第 ${view.page} / ${view.pages} 页`;
    for (const button of document.querySelectorAll('[data-sort]')) {
      button.parentElement.removeAttribute('aria-sort');
      if (button.dataset.sort === state.key) button.parentElement.setAttribute('aria-sort', state.direction === 'asc' ? 'ascending' : 'descending');
    }
    setBusy(state.loading);
  }
  async function json(url) {
    const response = await fetch(url, {cache:'no-store'});
    if (!response.ok) throw new Error(await response.text() || `请求失败（${response.status}）`);
    return response.json();
  }
  async function load() {
    const current = ++request;
    const query = model.query({plant:$('plant').value, warehouse:$('warehouse').value, search:$('search').value});
    setBusy(true); $('error').hidden = true; $('status').textContent = '正在查询库存…';
    try {
      const data = await json('/api/inventory?' + query);
      if (current !== request) return;
      state.rows = data.rows; state.query = query; state.page = 1; state.ready = true;
      const params = new URLSearchParams(query);
      $('scope').textContent = [params.get('plant') || '全部工厂', params.get('warehouse') || '全部仓库', params.get('search') ? `关键字：${params.get('search')}` : '全部物料'].join(' / ');
      $('status').textContent = `查询完成，共 ${data.rows.length} 条记录。导出包含全部查询结果。`;
      render();
    } catch (error) {
      if (current !== request) return;
      state.ready = false;
      $('error').textContent = `库存查询失败：${error.message}。请重新查询。`;
      $('error').hidden = false; $('status').textContent = '查询未完成，表格保留上次查询结果。';
    } finally { if (current === request) setBusy(false); }
  }
  $('filters').addEventListener('submit', event => {event.preventDefault(); load();});
  $('filters').addEventListener('reset', event => {
    event.preventDefault();
    for (const id of ['plant', 'warehouse', 'search']) $(id).value = '';
    load();
  });
  for (const button of document.querySelectorAll('[data-sort]')) button.addEventListener('click', () => {
    state.direction = state.key === button.dataset.sort && state.direction === 'asc' ? 'desc' : 'asc';
    state.key = button.dataset.sort; state.page = 1; render();
  });
  $('previous').addEventListener('click', () => {state.page--; render();});
  $('next').addEventListener('click', () => {state.page++; render();});
  $('export').addEventListener('click', async () => {
    state.exporting = true; $('export').disabled = true; $('error').hidden = true; $('status').textContent = '正在导出全部查询结果…';
    try {
      const response = await fetch('/api/export/inventory?' + state.query, {cache:'no-store'});
      if (!response.ok) throw new Error(await response.text() || `请求失败（${response.status}）`);
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement('a'); link.href = url; link.download = '库存明细.xlsx'; document.body.append(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
      $('status').textContent = '库存明细已导出，请在浏览器下载记录中查看。';
    } catch (error) {
      $('error').textContent = `导出失败：${error.message}。请重试。`; $('error').hidden = false; $('status').textContent = '导出未完成。';
    } finally {state.exporting = false; setBusy(state.loading);}
  });
  (async () => {
    setBusy(true);
    try {
      const context = await json('/api/context');
      $('batch').textContent = context.batch_id; $('today').textContent = context.today; $('deadline').textContent = context.deadline;
      $('plant').value = context.plant; $('warehouse').value = context.warehouse;
      for (const [id, value] of [['plants', context.plant], ['warehouses', context.warehouse]]) {
        const option = document.createElement('option'); option.value = value; $(id).append(option);
      }
      await load();
    } catch (error) {
      $('error').textContent = `任务信息读取失败：${error.message}。请刷新页面重试。`; $('error').hidden = false;
      $('status').textContent = '任务信息未加载。'; setBusy(false);
    }
  })();
})();
