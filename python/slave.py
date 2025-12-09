#!/usr/bin/env python3
"""Slave WebSocket server: applies received mouse/keyboard events locally.

Usage: python3 python/slave.py [port]
"""
import asyncio
import json
import argparse
import sys
import traceback

try:
    from pynput import mouse, keyboard
except Exception:
    print("[slave] Error: `pynput` is required. Install with: pip install pynput pyautogui websockets")
    raise

try:
    import pyautogui
except Exception:
    pyautogui = None

import websockets


class SlaveServer:
    def __init__(self, port):
        self.port = port
        self.mouse_ctrl = mouse.Controller()
        self.keyboard_ctrl = keyboard.Controller()
        self.controlling = False
        self.ws = None

    async def handler(self, websocket, path):
        print(f"[slave] master connected")
        self.ws = websocket
        try:
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue

                try:
                    t = msg.get('type')
                    if t == 'grab':
                        self.controlling = True
                        print('[slave] control acquired from master')
                    elif t == 'mousemove' and self.controlling:
                        dx = msg.get('dx', 0) or 0
                        dy = msg.get('dy', 0) or 0
                        x, y = self.mouse_ctrl.position
                        try:
                            self.mouse_ctrl.position = (int(x + dx), int(y + dy))
                        except Exception:
                            pass
                    elif t == 'mouseclick' and self.controlling:
                        btn = msg.get('button', 'left')
                        down = msg.get('down', True)
                        # map string to Button
                        btn_map = {
                            'Button.left': mouse.Button.left,
                            'Button.right': mouse.Button.right,
                            'Button.middle': mouse.Button.middle,
                            'left': mouse.Button.left,
                            'right': mouse.Button.right,
                            'middle': mouse.Button.middle
                        }
                        b = btn_map.get(btn, mouse.Button.left)
                        if down:
                            self.mouse_ctrl.press(b)
                        else:
                            self.mouse_ctrl.release(b)
                    elif t == 'keydown' and self.controlling:
                        k = msg.get('key')
                        self._press_key(k, down=True)
                    elif t == 'keyup' and self.controlling:
                        k = msg.get('key')
                        self._press_key(k, down=False)
                except Exception:
                    print('[slave] Exception while handling message:')
                    traceback.print_exc()
                    # don't re-raise; send error info back to client optionally
                    try:
                        await websocket.send(json.dumps({"type": "error", "message": "internal server error"}))
                    except Exception:
                        pass

        except websockets.ConnectionClosed:
            print('[slave] master disconnected')
        finally:
            self.ws = None
            self.controlling = False

    def _press_key(self, keystr, down=True):
        if keystr is None:
            return
        try:
            if keystr.startswith('Key.'):
                name = keystr.split('.', 1)[1]
                k = getattr(keyboard.Key, name)
                if down:
                    self.keyboard_ctrl.press(k)
                else:
                    self.keyboard_ctrl.release(k)
            else:
                # single character
                if down:
                    self.keyboard_ctrl.press(keystr)
                else:
                    self.keyboard_ctrl.release(keystr)
        except Exception:
            pass

    async def edge_watcher(self):
        # watch local mouse; if at left edge while controlling, release back to master
        while True:
            await asyncio.sleep(0.05)
            if not self.controlling or self.ws is None or self.ws.closed:
                continue
            x, y = self.mouse_ctrl.position
            if x <= 0:
                try:
                    await self.ws.send(json.dumps({"type": "release"}))
                    self.controlling = False
                    print('[slave] released control back to master')
                except Exception:
                    pass

    async def run(self):
        server = await websockets.serve(self.handler, '0.0.0.0', self.port)
        print(f"[slave] WebSocket server listening on :{self.port}")
        await self.edge_watcher()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', nargs='?', default=8080, type=int)
    args = parser.parse_args()
    srv = SlaveServer(args.port)
    try:
        asyncio.run(srv.run())
    except KeyboardInterrupt:
        print('[slave] exiting')


if __name__ == '__main__':
    main()
