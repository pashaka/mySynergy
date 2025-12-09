# Synergy-like Tool (Minimal)

This repository contains two minimal implementations of a Synergy-like master/slave setup:

- A Node.js prototype (in the project root) that uses `robotjs` / `iohook` (native modules).
- A Python alternative (under `python/`) that uses `pynput` and `websockets` and avoids native Node builds.

Important: controlling the mouse/keyboard programmatically requires OS permissions (Accessibility on macOS). Grant access to the Terminal/Python process in System Settings -> Privacy & Security.

Node.js quick start

1. Install dependencies:

```bash
cd /Users/pashaka/Public/mySynergy
npm install
```

2. Start the slave on the machine to be controlled:

```bash
npm run start:slave -- 8080
# or: node src/slave.js 8080
```

3. Start the master on the controlling machine:

```bash
npm run start:master -- <slave-ip> 8080
# or: node src/master.js <slave-ip> 8080
```

If you encounter native module install errors (e.g. `robotjs` / `iohook`) on macOS, try:

```bash
xcode-select --install
npm install --build-from-source robotjs
npm explore iohook -- npm run build
```

I also added guidance in the repo for using `cliclick` as a non-native fallback if you prefer.

Python alternative
------------------

If building native Node modules is troublesome, use the Python implementation in `python/`. It uses `pynput` for input control and `websockets` for networking.

1. Create and activate a virtual environment (recommended):

```bash
cd /Users/pashaka/Public/mySynergy
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r python/requirements.txt
```

3. Start the slave on the machine to be controlled:

```bash
python3 python/slave.py 8080
```

4. Start the master on the controlling machine:

```bash
python3 python/master.py <slave-ip> 8080
```

Notes and caveats
- Grant Accessibility permissions to the Terminal/Python in System Settings -> Privacy & Security to allow `pynput` to control the mouse/keyboard.
- The implementations are minimal prototypes and assume screens are arranged horizontally: moving the mouse to the right edge of the master triggers a `grab`; moving to the left edge of the slave triggers a `release` back to the master.
- Keyboard forwarding is best-effort; mapping platform-specific keycodes to consistent key names can be improved.

Next steps I can help with
- Add automatic discovery (mDNS) so master finds slaves by name.
- Add multi-monitor mapping and configurable edge thickness.
- Add a small UI or tray app for easier connect/manage.
- Add a `cliclick` fallback for macOS to avoid building native modules entirely.

If you'd like me to proceed with any of the above, tell me which one and I'll implement it next.
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

If you encounter "Cannot find module 'robotjs'" or installation/build errors on macOS:

1. Install Xcode Command Line Tools (if not installed):

```bash
xcode-select --install
```

2. Ensure you have a compatible `node` and `npm` (Node 14+ recommended) and that `node-gyp` prerequisites are installed. You may need Python and other build tools; installing the Xcode CLI above covers most requirements.

3. From the project directory try rebuilding/installing `robotjs` from source:

```bash
# from project root
npm install --build-from-source robotjs
```

4. If you prefer not to build native modules, an alternative approach is to install `cliclick` (a small CLI tool for macOS that can move/click the mouse) and I can update the project to use it as a fallback:

```bash
# using Homebrew
brew install cliclick
```

If you want, I can adapt the code to support `cliclick` as an optional fallback so you won't need to build `robotjs`.

If you want, I can:
- Add automatic discovery (mDNS) so master finds slaves by name.
- Add multi-monitor mapping and configurable edge thickness.
- Add a small UI to connect/manage slaves.
