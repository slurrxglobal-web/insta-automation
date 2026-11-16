// Ghost Panel - Electron Main Process
// AdsPower-style Anti-Detect Browser with embedded profile management

const { app, BrowserWindow, ipcMain, session, Menu, nativeTheme } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');
const crypto = require('crypto');

// ──────────────────────────────────────────────
// GLOBALS
// ──────────────────────────────────────────────
let mainWindow = null;
let flaskProcess = null;
const profileWindows = {};   // { profileId: BrowserWindow }
const FLASK_PORT = 5050;
const AUTO_POSTER_DIR = path.join(__dirname, '..', 'auto_poster');
const PROFILES_DIR = path.join(AUTO_POSTER_DIR, 'profiles');
const ACCOUNTS_FILE = path.join(AUTO_POSTER_DIR, 'accounts.json');

// Anti-Detect Fingerprint Pool
const GPU_RENDERERS = [
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (AMD, AMD Radeon RX 7900 XTX Direct3D11 vs_5_0 ps_5_0, D3D11)',
    'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Super Direct3D11 vs_5_0 ps_5_0, D3D11)',
];

const USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
];

const PLATFORM_URLS = {
    instagram:  'https://www.instagram.com/',
    facebook:   'https://www.facebook.com/',
    twitter:    'https://x.com/login',
    tiktok:     'https://www.tiktok.com/login',
    snapchat:   'https://my.snapchat.com/',
    pinterest:  'https://www.pinterest.com/login/',
    youtube:    'https://studio.youtube.com/',
};

// ──────────────────────────────────────────────
// FINGERPRINT ENGINE
// ──────────────────────────────────────────────
function getFingerprint(profileId) {
    const hash = parseInt(crypto.createHash('sha256').update(profileId).digest('hex').slice(0, 12), 16);
    return {
        userAgent:  USER_AGENTS[hash % USER_AGENTS.length],
        gpu:        GPU_RENDERERS[hash % GPU_RENDERERS.length],
        cores:      [4, 8, 12, 16][hash % 4],
        memory:     [4, 8, 16, 32][hash % 4],
        canvasSalt: ((hash % 100) + 1) * 0.000013,
        screenW:    1920,
        screenH:    1080,
        languages:  ['en-US', 'en'],
        platform:   'Win32',
        timezone:   'Asia/Kolkata',
    };
}

// ──────────────────────────────────────────────
// FLASK BACKEND MANAGEMENT
// ──────────────────────────────────────────────
function checkFlaskRunning() {
    return new Promise((resolve) => {
        const req = http.get(`http://127.0.0.1:${FLASK_PORT}/api/status`, (res) => {
            if (res.statusCode === 200) resolve(true);
            else resolve(false);
        });
        req.on('error', () => resolve(false));
        req.setTimeout(1500, () => {
            req.destroy();
            resolve(false);
        });
    });
}

async function startFlaskBackend() {
    const isAlreadyRunning = await checkFlaskRunning();
    if (isAlreadyRunning) {
        console.log('[GHOST] Flask automation backend already active on port', FLASK_PORT);
        return;
    }

    return new Promise((resolve) => {
        const pythonExe = 'python';
        const scriptPath = path.join(AUTO_POSTER_DIR, 'web_poster.py');

        if (!fs.existsSync(scriptPath)) {
            console.error('[GHOST] web_poster.py not found at', scriptPath);
            resolve();
            return;
        }

        flaskProcess = spawn(pythonExe, [scriptPath], {
            cwd: path.join(__dirname, '..'),
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
            windowsHide: true,    // NO black terminal window
        });

        flaskProcess.stdout.on('data', (data) => {
            const msg = data.toString().trim();
            if (msg) console.log('[FLASK]', msg);
            if (msg.includes('Running on')) resolve();
        });

        flaskProcess.stderr.on('data', (data) => {
            const msg = data.toString().trim();
            if (msg && !msg.includes('WARNING')) console.error('[FLASK-ERR]', msg);
            if (msg.includes('Running on')) resolve();
        });

        flaskProcess.on('error', (err) => {
            console.error('[FLASK] Failed to start:', err);
            resolve();
        });

        flaskProcess.on('close', (code) => {
            console.log('[FLASK] Process exited with code', code);
            flaskProcess = null;
        });

        setTimeout(resolve, 6000);
    });
}

function stopFlaskBackend() {
    if (flaskProcess) {
        try {
            flaskProcess.kill('SIGTERM');
        } catch (e) {
            try { process.kill(flaskProcess.pid); } catch (_) {}
        }
        flaskProcess = null;
    }
}

// ──────────────────────────────────────────────
// ANTI-DETECT INJECTION SCRIPT
// ──────────────────────────────────────────────
function getStealthScript(fp) {
    return `
    // ═══════ GHOST ANTI-DETECT ENGINE ═══════

    // 1. Remove automation markers
    try {
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        delete navigator.__proto__.webdriver;
    } catch(e) {}

    // Chrome runtime mock
    window.chrome = {
        runtime: { onMessage: { addListener: function(){} }, sendMessage: function(){} },
        loadTimes: function() { return {}; },
        csi: function() { return {}; },
        app: { isInstalled: false }
    };

    // 2. Hardware fingerprint
    try {
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => ${fp.cores} });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => ${fp.memory} });
        Object.defineProperty(navigator, 'languages', { get: () => ${JSON.stringify(fp.languages)} });
        Object.defineProperty(navigator, 'platform', { get: () => '${fp.platform}' });
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 0 });
    } catch(e) {}

    // 3. Screen dimensions lock
    try {
        Object.defineProperty(screen, 'width', { get: () => ${fp.screenW} });
        Object.defineProperty(screen, 'height', { get: () => ${fp.screenH} });
        Object.defineProperty(screen, 'availWidth', { get: () => ${fp.screenW} });
        Object.defineProperty(screen, 'availHeight', { get: () => ${fp.screenH - 40} });
    } catch(e) {}

    // 4. WebGL GPU Masking
    try {
        const wglGetParam = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(p) {
            if (p === 37445) return 'Google Inc. (NVIDIA)';
            if (p === 37446) return '${fp.gpu}';
            return wglGetParam.apply(this, arguments);
        };
        if (typeof WebGL2RenderingContext !== 'undefined') {
            const wgl2GetParam = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(p) {
                if (p === 37445) return 'Google Inc. (NVIDIA)';
                if (p === 37446) return '${fp.gpu}';
                return wgl2GetParam.apply(this, arguments);
            };
        }
    } catch(e) {}

    // 5. Canvas Noise Injection
    try {
        const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            const ctx = this.getContext('2d');
            if (ctx) {
                try {
                    const img = ctx.getImageData(0, 0, Math.min(16, this.width), Math.min(16, this.height));
                    for (let i = 0; i < img.data.length; i += 4) {
                        img.data[i] = (img.data[i] + ${Math.round(fp.canvasSalt * 100000) % 3}) % 256;
                    }
                    ctx.putImageData(img, 0, 0);
                } catch(e) {}
            }
            return origToDataURL.apply(this, arguments);
        };
    } catch(e) {}

    // 6. Plugins & MimeTypes spoof
    try {
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                { name: 'Native Client', filename: 'internal-nacl-plugin' }
            ]
        });
    } catch(e) {}

    console.log('[GHOST] Anti-Detect fingerprint active.');
    `;
}

// ──────────────────────────────────────────────
// MAIN DASHBOARD WINDOW
// ──────────────────────────────────────────────
function createMainWindow() {
    nativeTheme.themeSource = 'dark';

    const iconPath = path.join(__dirname, 'assets', 'icon.png');

    mainWindow = new BrowserWindow({
        width: 1440,
        height: 900,
        minWidth: 1100,
        minHeight: 700,
        title: 'Ghost Panel v3.0',
        backgroundColor: '#030508',
        icon: fs.existsSync(iconPath) ? iconPath : undefined,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
            webviewTag: true,
        },
        frame: false,       // Custom tactical title bar
        titleBarStyle: 'hidden',
        show: false,
    });

    mainWindow.loadFile(path.join(__dirname, 'dashboard.html'));

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        mainWindow.focus();
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
        Object.keys(profileWindows).forEach(id => {
            try { profileWindows[id].close(); } catch (_) {}
        });
    });

    Menu.setApplicationMenu(null);
}

// ──────────────────────────────────────────────
// PROFILE BROWSER WINDOW (AdsPower-style)
// ──────────────────────────────────────────────
function openProfileBrowser(profileId, platform, profileName) {
    if (profileWindows[profileId] && !profileWindows[profileId].isDestroyed()) {
        profileWindows[profileId].focus();
        return { success: true, message: 'Window focused' };
    }

    const fp = getFingerprint(profileId);
    const targetUrl = PLATFORM_URLS[platform] || 'https://www.google.com/';
    
    // Dedicated isolated session partition for this profile
    const partitionName = `persist:ghost_${profileId}`;
    const profileSession = session.fromPartition(partitionName);

    profileSession.setUserAgent(fp.userAgent);

    const iconPath = path.join(__dirname, 'assets', 'icon.png');

    const profileWin = new BrowserWindow({
        width: 1300,
        height: 850,
        minWidth: 900,
        minHeight: 600,
        title: `[GHOST] ${profileName || profileId} // ${platform.toUpperCase()}`,
        backgroundColor: '#0A0E17',
        icon: fs.existsSync(iconPath) ? iconPath : undefined,
        webPreferences: {
            partition: partitionName,
            contextIsolation: true,
            nodeIntegration: false,
            sandbox: false,
            preload: path.join(__dirname, 'profile-preload.js'),
        },
        autoHideMenuBar: true,
        show: false,
    });

    profileWin.webContents.on('dom-ready', () => {
        profileWin.webContents.executeJavaScript(getStealthScript(fp)).catch(() => {});
    });

    profileSession.webRequest.onBeforeSendHeaders((details, callback) => {
        details.requestHeaders['User-Agent'] = fp.userAgent;
        details.requestHeaders['Accept-Language'] = 'en-US,en;q=0.9';
        callback({ requestHeaders: details.requestHeaders });
    });

    profileWin.loadURL(targetUrl);

    profileWin.once('ready-to-show', () => {
        profileWin.show();
        profileWin.focus();
    });

    profileWin.on('closed', () => {
        delete profileWindows[profileId];
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('profile-closed', { profileId });
        }
    });

    profileWin.webContents.on('page-title-updated', (e, title) => {
        profileWin.setTitle(`[GHOST] ${profileName || profileId} // ${title}`);
    });

    profileWindows[profileId] = profileWin;

    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('profile-opened', { profileId, platform });
    }

    return { success: true, message: 'Browser launched' };
}

function closeProfileBrowser(profileId) {
    if (profileWindows[profileId] && !profileWindows[profileId].isDestroyed()) {
        profileWindows[profileId].close();
        delete profileWindows[profileId];
        return { success: true };
    }
    return { success: false, message: 'No active browser for this profile' };
}

// ──────────────────────────────────────────────
// ACCOUNTS MANAGEMENT
// ──────────────────────────────────────────────
function loadAccounts() {
    try {
        if (fs.existsSync(ACCOUNTS_FILE)) {
            return JSON.parse(fs.readFileSync(ACCOUNTS_FILE, 'utf-8'));
        }
    } catch (e) {
        console.error('[GHOST] Error loading accounts:', e);
    }
    return [];
}

function saveAccounts(accounts) {
    fs.writeFileSync(ACCOUNTS_FILE, JSON.stringify(accounts, null, 2), 'utf-8');
}

function addAccount(id, name, platform) {
    const accounts = loadAccounts();
    if (accounts.find(a => a.id === id)) {
        return { success: false, message: 'Profile ID already exists' };
    }

    const profileDir = path.join(PROFILES_DIR, id);
    if (!fs.existsSync(profileDir)) {
        fs.mkdirSync(profileDir, { recursive: true });
    }

    accounts.push({
        id,
        name: name || id,
        platform: platform || 'instagram',
        profile_dir: `profiles/${id}`,
        proxy: null,
        enabled: true,
    });
    saveAccounts(accounts);
    return { success: true };
}

function deleteAccount(id) {
    let accounts = loadAccounts();
    accounts = accounts.filter(a => a.id !== id);
    saveAccounts(accounts);
    closeProfileBrowser(id);
    return { success: true };
}

// ──────────────────────────────────────────────
// IPC HANDLERS
// ──────────────────────────────────────────────
function setupIPC() {
    ipcMain.handle('window-minimize', () => mainWindow?.minimize());
    ipcMain.handle('window-maximize', () => {
        if (mainWindow?.isMaximized()) mainWindow.unmaximize();
        else mainWindow?.maximize();
    });
    ipcMain.handle('window-close', () => mainWindow?.close());

    ipcMain.handle('get-accounts', () => {
        const accounts = loadAccounts();
        return accounts.map(acc => ({
            ...acc,
            fingerprint: getFingerprint(acc.id),
            isLoggedIn: checkProfileLogin(acc.id),
            isBrowserOpen: !!(profileWindows[acc.id] && !profileWindows[acc.id].isDestroyed()),
        }));
    });

    ipcMain.handle('add-account', (_, { id, name, platform }) => addAccount(id, name, platform));
    ipcMain.handle('delete-account', (_, { id }) => deleteAccount(id));

    ipcMain.handle('launch-browser', (_, { profileId, platform, profileName }) => {
        return openProfileBrowser(profileId, platform, profileName);
    });

    ipcMain.handle('close-browser', (_, { profileId }) => {
        return closeProfileBrowser(profileId);
    });

    ipcMain.handle('get-open-browsers', () => {
        return Object.keys(profileWindows).filter(id => 
            profileWindows[id] && !profileWindows[id].isDestroyed()
        );
    });

    ipcMain.handle('get-flask-url', () => `http://127.0.0.1:${FLASK_PORT}`);

    // Synchronous stealth script provider for preloads
    ipcMain.on('get-profile-stealth-script', (event) => {
        const senderWebContents = event.sender;
        let matchedId = null;
        for (const [id, win] of Object.entries(profileWindows)) {
            if (win && !win.isDestroyed() && win.webContents.id === senderWebContents.id) {
                matchedId = id;
                break;
            }
        }
        if (matchedId) {
            const fp = getFingerprint(matchedId);
            event.returnValue = getStealthScript(fp);
        } else {
            event.returnValue = '';
        }
    });
}

function checkProfileLogin(profileId) {
    const profileDir = path.join(PROFILES_DIR, profileId);
    const partitionDir = path.join(app.getPath('userData'), `Partitions`, `ghost_${profileId}`);
    const playwrightCookies = path.join(profileDir, 'Default', 'Network', 'Cookies');
    const playwrightStorage = path.join(profileDir, 'Default', 'Local Storage');
    
    return fs.existsSync(partitionDir) || fs.existsSync(playwrightCookies) || fs.existsSync(playwrightStorage);
}

// ──────────────────────────────────────────────
// APP LIFECYCLE
// ──────────────────────────────────────────────
app.whenReady().then(async () => {
    console.log('[GHOST] Ghost Panel v3.0 initializing...');

    if (!fs.existsSync(PROFILES_DIR)) {
        fs.mkdirSync(PROFILES_DIR, { recursive: true });
    }

    setupIPC();

    await startFlaskBackend();

    createMainWindow();
});

app.on('window-all-closed', () => {
    stopFlaskBackend();
    app.quit();
});

app.on('before-quit', () => {
    stopFlaskBackend();
    Object.keys(profileWindows).forEach(id => {
        try { profileWindows[id].close(); } catch (_) {}
    });
});

app.on('activate', () => {
    if (!mainWindow) createMainWindow();
});
