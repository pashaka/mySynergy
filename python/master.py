#!/usr/bin/env python3
"""Master: polls local mouse and forwards events to the slave over WebSocket.

Usage: python3 python/master.py <slave-host> [port]
"""
import asyncio
import json
import sys
import time
import argparse

try:
    from pynput import mouse, keyboard
except Exception as e:
    print("[master] Error: `pynput` is required. Install with: pip install pynput pyautogui websockets")
    raise

try:
    import pyautogui
except Exception:
    pyautogui = None

import websockets


async def run_master(host, port, edge_threshold=2, poll_interval=0.016):
    uri = f"ws://{host}:{port}"
    print(f"[master] connecting to {uri}")
    async with websockets.connect(uri) as ws:
        print("[master] connected")

        screen_width = None
        if pyautogui:
            try:
                screen_width = pyautogui.size().width
            except Exception:
                screen_width = None

        mouse_ctrl = mouse.Controller()
        kb_listener = None

        controlling = False
        last_pos = mouse_ctrl.position

        # keyboard listener: forward key events
        def on_press(key):
            try:
                k = key.char
            except AttributeError:
                k = str(key)  # e.g. 'Key.space'
            msg = {"type": "keydown", "key": k}
            asyncio.get_event_loop().create_task(ws.send(json.dumps(msg)))

        def on_release(key):
            try:
                k = key.char
            except AttributeError:
                k = str(key)
            msg = {"type": "keyup", "key": k}
            asyncio.get_event_loop().create_task(ws.send(json.dumps(msg)))

        # mouse click listener
        def on_click(x, y, button, pressed):
            btn = button.name if hasattr(button, 'name') else str(button)
            msg = {"type": "mouseclick", "button": btn, "down": pressed}
            asyncio.get_event_loop().create_task(ws.send(json.dumps(msg)))

        # Use a queue for outgoing events so listener threads can safely enqueue
        out_q = asyncio.Queue()

        def enqueue(msg):
            try:
                loop = asyncio.get_running_loop()
                # if called from event loop thread
                loop.create_task(ws.send(json.dumps(msg)))
            except RuntimeError:
                # called from a listener thread: use call_soon_threadsafe
                asyncio.get_event_loop().call_soon_threadsafe(out_q.put_nowait, msg)

        kb_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        kb_listener.start()
        mouse_listener = mouse.Listener(on_click=on_click)
        mouse_listener.start()

        async def send_outgoing():
            while True:
                msg = await out_q.get()
                try:
                    await ws.send(json.dumps(msg))
                except Exception:
                    pass

        send_task = asyncio.create_task(send_outgoing())

        try:
            while True:
                pos = mouse_ctrl.position
                dx = pos[0] - last_pos[0]
                dy = pos[1] - last_pos[1]
                last_pos = pos

                # determine screen width if unknown
                if screen_width is None and pyautogui:
                    try:
                        screen_width = pyautogui.size().width
                    except Exception:
                        screen_width = None

                if not controlling:
                    if screen_width is not None:
                        if pos[0] >= screen_width - edge_threshold:
                            controlling = True
                            print('[master] entering slave control mode')
                            await ws.send(json.dumps({"type": "grab"}))
                    else:
                        # If we can't determine screen width, allow user to press Ctrl+Shift+G to toggle (not implemented)
                        pass
                else:
                    # send mouse delta to slave
                    msg = {"type": "mousemove", "dx": dx, "dy": dy}
                    await ws.send(json.dumps(msg))

                # check for incoming release messages using a short timeout
                try:
                    data = await asyncio.wait_for(ws.recv(), timeout=0.01)
                    if data is not None:
                        try:
                            m = json.loads(data)
                            if m.get('type') == 'release':
                                controlling = False
                                print('[master] control returned from slave')
                        except Exception:
                            pass
                except asyncio.TimeoutError:
                    pass
                except websockets.ConnectionClosed as e:
                    # log close code and reason to help diagnose
                    try:
                        code = e.code
                        reason = e.reason
                    except Exception:
                        code = None
                        reason = None
                    print(f"[master] connection closed by slave (code={code}, reason={reason})")
                    break

                await asyncio.sleep(poll_interval)
        except KeyboardInterrupt:
            print('[master] exiting')
        finally:
            if kb_listener:
                kb_listener.stop()
            mouse_listener.stop()
            send_task.cancel()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='slave host IP or hostname')
    parser.add_argument('port', nargs='?', default=8080, type=int)
    args = parser.parse_args()
    asyncio.run(run_master(args.host, args.port))


if __name__ == '__main__':
    main()
