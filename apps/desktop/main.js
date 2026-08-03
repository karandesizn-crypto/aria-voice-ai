const { app, BrowserWindow } = require("electron");
const { resolveAppUrl } = require("./app-url");

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    title: "Aria",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  win.loadURL(resolveAppUrl());
}

if (require.main === module) {
  app.whenReady().then(createWindow);
  app.on("window-all-closed", () => {
    if (process.platform !== "darwin") app.quit();
  });
}

module.exports = { resolveAppUrl, createWindow };
