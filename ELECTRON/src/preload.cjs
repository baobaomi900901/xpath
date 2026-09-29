'use strict';
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('electronRange', {
  getState: () => ipcRenderer.invoke('range:get-state'),
  select: index => { if (Number.isInteger(index) && index >= 0 && index < 3) ipcRenderer.send('range:select', index); },
  refresh: () => ipcRenderer.send('range:refresh'),
  onState: callback => {
    if (typeof callback !== 'function') return () => {};
    const listener = (_event, state) => callback(state);
    ipcRenderer.on('range:state', listener);
    return () => ipcRenderer.removeListener('range:state', listener);
  },
});
