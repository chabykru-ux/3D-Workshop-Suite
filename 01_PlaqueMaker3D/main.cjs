const { app, BrowserWindow, Menu } = require('electron');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const entry = path.join(__dirname, 'app', 'index.html');
app.setAppUserModelId('com.azimuth171.plaquemaker3d');
function createWindow() {
  const win = new BrowserWindow({
    width: 1350, height: 900, minWidth: 800, minHeight: 530,
    backgroundColor: '#0d1422', title: 'PlaqueMaker 3D',
    icon: path.join(__dirname, 'app', 'icon.ico'),
    webPreferences: { nodeIntegration: false, contextIsolation: true, sandbox: true }
  });
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  win.webContents.on('will-navigate', (event, url) => {
    if (url !== pathToFileURL(entry).href) event.preventDefault();
  });
  win.loadFile(entry);
}
app.whenReady().then(() => {
  Menu.setApplicationMenu(null);
  createWindow();
  app.on('activate', () => { if (!BrowserWindow.getAllWindows().length) createWindow(); });
});
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
