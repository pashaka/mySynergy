#!/usr/bin/env node
const WebSocket = require('ws');
let robot;
try {
  robot = require('robotjs');
} catch (e) {
  console.error('\n[slave] Error: `robotjs` is not installed or failed to load.');
  console.error('[slave] On macOS you may need Xcode Command Line Tools and to build native modules.');
  console.error('[slave] Suggested steps:');
  console.error('  1) Install Xcode CLI: `xcode-select --install`');
  console.error('  2) Install node-gyp prerequisites (Python, etc.) and ensure `node` and `npm` are up-to-date.');
  console.error('  3) From the project directory run: `npm install --build-from-source robotjs`');
  console.error('If you prefer avoiding native modules, I can adapt this project to use `cliclick` (brew install cliclick) as a fallback.');
  process.exit(1);
}

const args = process.argv.slice(2);
const port = parseInt(args[0], 10) || 8080;

const wss = new WebSocket.Server({ port });
let masterSocket = null;
let controlling = false;

console.log(`[slave] starting WebSocket server on port ${port}`);

wss.on('connection', socket => {
  console.log('[slave] master connected');
  masterSocket = socket;
  socket.on('message', onMessage);
  socket.on('close', () => {
    console.log('[slave] master disconnected');
    masterSocket = null;
    controlling = false;
  });
});

function onMessage(raw) {
  let msg;
  try {
    msg = JSON.parse(raw);
  } catch (e) {
    return;
  }

  switch (msg.type) {
    case 'grab':
      controlling = true;
      console.log('[slave] master grabbed control');
      break;
    case 'mousemove':
      if (!controlling) return;
      const pos = robot.getMousePos();
      robot.moveMouse(pos.x + (msg.dx || 0), pos.y + (msg.dy || 0));
      break;
    case 'mouseclick':
      if (!controlling) return;
      const btn = mapButton(msg.button);
      if (msg.down) robot.mouseToggle('down', btn); else robot.mouseToggle('up', btn);
      break;
    case 'keydown':
      if (!controlling) return;
      // raw forwarding: best-effort; mapping may be required per-OS
      // If you need reliable keyboard forwarding, we can send characters instead of raw codes.
      if (typeof msg.keycode !== 'undefined') {
        try { robot.keyToggle(String(msg.keycode), 'down'); } catch (e) { }
      }
      break;
    case 'keyup':
      if (!controlling) return;
      if (typeof msg.keycode !== 'undefined') {
        try { robot.keyToggle(String(msg.keycode), 'up'); } catch (e) { }
      }
      break;
    default:
      break;
  }
}

function mapButton(b) {
  // iohook uses 1=left, 2=right, 3=middle sometimes; robotjs expects 'left'/'right'/'middle'
  if (b === 2) return 'right';
  if (b === 3) return 'middle';
  return 'left';
}

// Poll to detect left-screen edge on slave to return control
setInterval(() => {
  if (!controlling || !masterSocket || masterSocket.readyState !== WebSocket.OPEN) return;
  const pos = robot.getMousePos();
  if (pos.x <= 0) {
    // return control
    try {
      masterSocket.send(JSON.stringify({ type: 'release' }));
      controlling = false;
      console.log('[slave] released control back to master');
    } catch (e) {
      // ignore
    }
  }
}, 50);
