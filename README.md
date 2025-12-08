# Synergy-like Node Tool (Minimal)

This project provides a minimal Synergy-like master/slave setup using Node.js. The master connects to a slave over WebSocket and forwards mouse movements + clicks. Keyboard forwarding is partially supported if `iohook` is available.

Important: controlling the mouse/keyboard programmatically requires native modules (`robotjs`, `iohook`) that need build tools and OS permissions. On macOS you must grant accessibility permissions to the Terminal/Node.

Quick start

1. Install dependencies:

```bash
cd /Users/pashaka/Public/mySynergy
npm install
```

2. On the PC you want to control (slave):

```bash
npm run start:slave -- 8080
# or: node src/slave.js 8080
```

3. On the master PC (your primary machine):

```bash
npm run start:master -- <slave-ip> 8080
# or: node src/master.js <slave-ip> 8080
```

How it works (overview)
- The slave runs a WebSocket server and awaits a master connection.
- The master polls its local mouse position. When the mouse reaches the right edge of the master's screen, the master sends a `grab` message and starts forwarding mouse deltas to the slave.
- The slave receives mouse deltas and moves its own cursor accordingly. If the slave's cursor reaches the left edge, it sends a `release` message to the master to return control.

Notes & caveats
- This is a minimal prototype — it assumes displays are arranged horizontally and does not implement advanced mapping or multi-monitor layouts.
- `robotjs` and `iohook` may need Xcode command-line tools and native builds; on Apple Silicon they may require workarounds or prebuilt binaries.
- Keyboard forwarding is limited because converting raw keycodes to characters across platforms is non-trivial. The code includes a simple pathway for key events but may need enhancement.

If you want, I can:
- Add automatic discovery (mDNS) so master finds slaves by name.
- Add multi-monitor mapping and configurable edge thickness.
- Add a small UI to connect/manage slaves.
