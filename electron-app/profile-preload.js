// Ghost Panel - Profile Browser Preload
// Anti-detect stealth script injected synchronously into the main page world
// before any website JavaScript can detect webdriver, canvas, or WebGL

const { contextBridge, ipcRenderer, webFrame } = require('electron');

try {
    const stealthCode = ipcRenderer.sendSync('get-profile-stealth-script');
    if (stealthCode) {
        webFrame.executeJavaScript(stealthCode);
    }
} catch (e) {
    console.error('[GHOST] Preload stealth inject error:', e);
}

// Expose safe flag
contextBridge.exposeInMainWorld('__ghost_profile', {
    isGhostBrowser: true,
});
