'use strict';
globalThis.InventoryModel = Object.freeze({
  query(filters) {
    const query = new URLSearchParams();
    for (const key of ['plant', 'warehouse', 'search']) {
      const value = String(filters[key] || '').trim();
      if (value) query.set(key, value);
    }
    return query.toString();
  },
  view(rows, key, direction, requestedPage) {
    const sorted = [...rows].sort((a, b) => {
      const left = a[key], right = b[key];
      const comparison = typeof left === 'number' || typeof left === 'boolean'
        ? Number(left) - Number(right) : String(left).localeCompare(String(right), 'zh-CN', {numeric:true});
      return direction === 'desc' ? -comparison : comparison;
    });
    const pages = Math.max(1, Math.ceil(rows.length / 8));
    const page = Math.min(pages, Math.max(1, requestedPage));
    return {rows:sorted.slice((page - 1) * 8, page * 8), page, pages, total:rows.length};
  }
});
