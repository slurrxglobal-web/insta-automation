// Ghost Panel - Preload Script (Dashboard)
// Exposes safe IPC bridge to renderer

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('ghost', {
    // Window controls
    minimize: () => ipcRenderer.invoke('window-minimize'),
    maximize: () => ipcRenderer.invoke('window-maximize'),
    close: () => ipcRenderer.invoke('window-close'),

    // Accounts
    getAccounts: () => ipcRenderer.invoke('get-accounts'),
    addAccount: (data) => ipcRenderer.invoke('add-account', data),
    deleteAccount: (data) => ipcRenderer.invoke('delete-account', data),

    // Browser
    launchBrowser: (data) => ipcRenderer.invoke('launch-browser', data),
    closeBrowser: (data) => ipcRenderer.invoke('close-browser', data),
    getOpenBrowsers: () => ipcRenderer.invoke('get-open-browsers'),

    // Flask
    getFlaskUrl: () => ipcRenderer.invoke('get-flask-url'),

    // Events from main process
    onProfileOpened: (cb) => ipcRenderer.on('profile-opened', (_, data) => cb(data)),
    onProfileClosed: (cb) => ipcRenderer.on('profile-closed', (_, data) => cb(data)),
});
