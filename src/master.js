#!/usr/bin/env node
const WebSocket = require('ws');
let robot;
try {
  robot = require('robotjs');
} catch (e) {
  console.error('\n[master] Error: `robotjs` is not installed or failed to load.');
  console.error('[master] robotjs is required on the master to read the local mouse position.');
  console.error('[master] On macOS you may need Xcode Command Line Tools and to build native modules.');
  console.error('[master] Suggested steps:');
  console.error('  1) Install Xcode CLI: `xcode-select --install`');
  console.error('  2) Install node-gyp prerequisites (Python, etc.) and ensure `node` and `npm` are up-to-date.');
  console.error('  3) From the project directory run: `npm install --build-from-source robotjs`');
  process.exit(1);
}

let iohook;
try {
  iohook = require('iohook');
} catch (e) {
  iohook = null;
}

const args = process.argv.slice(2);
const host = args[0] || 'localhost';
const port = args[1] || 8080;
const ws = new WebSocket(`ws://${host}:${port}`);

const screenSize = robot.getScreenSize();
const EDGE_THRESHOLD = 1; // pixels from right edge on master

let controlling = false;
let lastPos = robot.getMousePos();

ws.on('open', () => {
  console.log(`[master] connected to ${host}:${port}`);
  setInterval(pollMouse, 16);

  if (iohook) {
    console.log('[master] iohook available: forwarding clicks and basic keys');
    iohook.on('mousedown', e => {
      ws.send(JSON.stringify({ type: 'mouseclick', button: e.button, down: true }));
    });
    iohook.on('mouseup', e => {
      ws.send(JSON.stringify({ type: 'mouseclick', button: e.button, down: false }));
    });
    iohook.on('keydown', e => {
      // For now forward the raw keycode; slave may not map it perfectly.
      ws.send(JSON.stringify({ type: 'keydown', keycode: e.rawcode || e.keycode }));
    });
    iohook.on('keyup', e => {
      ws.send(JSON.stringify({ type: 'keyup', keycode: e.rawcode || e.keycode }));
    });
    iohook.start();
  } else {
    console.log('[master] iohook not installed: keyboard events will not be forwarded (mouse still works)');
  }
});

ws.on('message', data => {
  try {
    const msg = JSON.parse(data);
    if (msg.type === 'release') {
      controlling = false;
      console.log('[master] control returned from slave');
    }
  } catch (e) {
    // ignore
  }
});

function pollMouse() {
  const pos = robot.getMousePos();
  const dx = pos.x - lastPos.x;
  const dy = pos.y - lastPos.y;
  lastPos = pos;

  if (!controlling && pos.x >= screenSize.width - EDGE_THRESHOLD) {
    controlling = true;
    console.log('[master] entering slave control mode');
    ws.send(JSON.stringify({ type: 'grab' }));
    return;
  }

  if (controlling) {
    // Send deltas; slave will apply relative motion starting at its left edge
    ws.send(JSON.stringify({ type: 'mousemove', dx, dy }));
  }
}

process.on('SIGINT', () => {
  if (iohook) iohook.stop();
  ws.close();
  process.exit();
});
