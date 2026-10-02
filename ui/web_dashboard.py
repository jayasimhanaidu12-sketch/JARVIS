"""
Web-based Dashboard Server for J.A.R.V.I.S. Arc Reactor Interface.
Serves the animated HTML/CSS/JS Arc Reactor dashboard and handles
WebSocket communication for real-time command/response exchange.
"""

import asyncio
import json
import os
import re
import threading
import webbrowser
from pathlib import Path
from typing import Optional, Set

try:
    from aiohttp import web
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

from config.settings import ROOT_DIR, settings
from core.agent import jarvis_agent
from core.permissions import permission_manager
from voice.speech_to_text import stt
from voice.text_to_speech import tts
from logging_system.logger import jarvis_logger, JarvisActionRecord


# ─────────────────────────────────────────────────────────────────
# Name Greeting Detection
# ─────────────────────────────────────────────────────────────────
# Patterns: "my name is X", "i am X", "call me X", "i'm X", "this is X"
NAME_PATTERNS = [
    re.compile(r"\bmy\s+name\s+is\s+(.+)", re.IGNORECASE),
    re.compile(r"\bi(?:'|\u2019)?m\s+(.+)", re.IGNORECASE),
    re.compile(r"\bcall\s+me\s+(.+)", re.IGNORECASE),
    re.compile(r"\bthis\s+is\s+(.+?)(?:\s+speaking)?\.?$", re.IGNORECASE),
    re.compile(r"\bi\s+am\s+(.+)", re.IGNORECASE),
]

# Words that should NOT be treated as names (filter out sentences like "I'm hungry")
NAME_STOPWORDS = {
    "hungry", "tired", "bored", "happy", "sad", "fine", "good", "great",
    "okay", "ok", "busy", "here", "back", "ready", "done", "sorry",
    "lost", "confused", "looking", "trying", "going", "coming", "leaving",
    "not", "just", "doing", "feeling", "getting", "having", "making",
    "working", "waiting", "watching", "listening", "thinking", "wondering",
    "sure", "so", "very", "really", "actually", "about", "at", "in", "on",
    "a", "an", "the", "your", "his", "her", "their", "my",
}


def detect_name_introduction(text: str) -> Optional[str]:
    """
    Detects if the user is introducing themselves by name.
    Returns the extracted name (title-cased) if detected, else None.
    
    Examples:
        "my name is Jayasimha" → "Jayasimha"
        "I'm Tony Stark"       → "Tony Stark"
        "call me Peter"        → "Peter"
    """
    clean = text.strip()
    if not clean:
        return None

    for pattern in NAME_PATTERNS:
        match = pattern.search(clean)
        if match:
            raw_name = match.group(1).strip().rstrip(".!?,;:")
            # Remove trailing filler like "and I need help"
            raw_name = re.split(r"\b(?:and|but|so|can|could|would|please|help|i need|what|how)\b",
                                raw_name, flags=re.IGNORECASE)[0].strip()
            if not raw_name:
                continue
            # Check if first word is a stopword (i.e. not a real name)
            first_word = raw_name.split()[0].lower()
            if first_word in NAME_STOPWORDS:
                continue
            # Reasonable name length check (1-5 words, max 50 chars)
            if len(raw_name.split()) > 5 or len(raw_name) > 50:
                continue
            return raw_name.title()
    return None


HOW_ARE_YOU_PATTERNS = [
    re.compile(r"^(?:hi|hello|hey|yo)?\s*(?:jarvis)?\s*,?\s*(?:how\s+are\s+you|how\s+r\s+u|how're\s+you|how\s+are\s+you\s+doing|how's\s+it\s+going)(?:\s+jarvis)?(?:\s+today)?[\s\.\?!]*$", re.IGNORECASE),
    re.compile(r"^(?:how\s+are\s+you|how\s+are\s+you\s+doing)\s*(?:jarvis)?[\s\.\?!]*$", re.IGNORECASE),
]


def is_how_are_you_greeting(text: str) -> bool:
    clean = text.strip()
    if not clean:
        return False
    for pattern in HOW_ARE_YOU_PATTERNS:
        if pattern.search(clean):
            return True
    return False


def build_greeting(name: str) -> str:
    """Constructs the JARVIS greeting message for detected name."""
    return f"Hello {name} my name is jarvis how can i assist you today."


class WebDashboardServer:
    """Async web server for the JARVIS Arc Reactor HTML dashboard."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5050):
        self.host = host
        self.port = port
        self.template_dir = ROOT_DIR / "ui" / "templates"
        self.ws_clients: Set[web.WebSocketResponse] = set()
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None

    async def _create_app(self) -> web.Application:
        app = web.Application()
        app.router.add_get("/", self._handle_index)
        app.router.add_get("/ws", self._handle_websocket)
        app.router.add_post("/api/command", self._handle_command_api)
        app.router.add_post("/api/voice", self._handle_voice_api)
        # Static assets (favicon etc.)
        assets_dir = ROOT_DIR / "assets"
        if assets_dir.exists():
            app.router.add_static("/assets", str(assets_dir))
        return app

    # ─── HTTP Routes ─────────────────────────────────────────────

    async def _handle_index(self, request: web.Request) -> web.Response:
        """Serves the Arc Reactor HTML dashboard."""
        html_path = self.template_dir / "dashboard.html"
        if not html_path.exists():
            return web.Response(text="Dashboard HTML not found.", status=404)
        return web.FileResponse(html_path)

    async def _handle_command_api(self, request: web.Request) -> web.Response:
        """HTTP POST fallback for sending commands."""
        try:
            data = await request.json()
            cmd = data.get("command", "").strip()
            if not cmd:
                return web.json_response({"response": ""})

            # Check for name introduction first
            detected_name = detect_name_introduction(cmd)
            if detected_name:
                greeting = build_greeting(detected_name)
                tts.speak(greeting)
                return web.json_response({"response": greeting})

            # Normal command processing
            response = await asyncio.to_thread(jarvis_agent.process_command, cmd)
            return web.json_response({"response": response or ""})
        except Exception as e:
            return web.json_response({"response": f"Error: {str(e)}"}, status=500)

    async def _handle_voice_api(self, request: web.Request) -> web.Response:
        """HTTP POST fallback for voice trigger."""
        try:
            heard = await asyncio.to_thread(stt.listen_from_mic, 4.0)
            if heard:
                return web.json_response({"heard": heard})
            return web.json_response({"heard": ""})
        except Exception as e:
            return web.json_response({"heard": "", "error": str(e)})

    # ─── WebSocket Handler ───────────────────────────────────────

    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Full-duplex WebSocket connection for real-time dashboard updates."""
        ws_resp = web.WebSocketResponse()
        await ws_resp.prepare(request)
        self.ws_clients.add(ws_resp)
        print(f"[Dashboard WS] Client connected. Total: {len(self.ws_clients)}")

        try:
            async for msg in ws_resp:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._process_ws_message(ws_resp, data)
                    except json.JSONDecodeError:
                        pass
                elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
                    break
        finally:
            self.ws_clients.discard(ws_resp)
            print(f"[Dashboard WS] Client disconnected. Total: {len(self.ws_clients)}")

        return ws_resp

    async def _process_ws_message(self, ws: web.WebSocketResponse, data: dict):
        """Routes incoming WebSocket messages."""
        msg_type = data.get("type", "")

        if msg_type == "command":
            cmd_text = data.get("text", "").strip()
            if not cmd_text:
                return

            # Check for "how are you" greeting first
            if is_how_are_you_greeting(cmd_text):
                greeting = "Hello  i'm jarvis How may i assist you today ."
                threading.Thread(target=tts.speak, args=(greeting,), daemon=True).start()
                await self._broadcast({
                    "type": "greeting",
                    "text": greeting,
                })
                await self._broadcast({
                    "type": "status",
                    "state": "IDLE",
                    "caption": "SYSTEM ONLINE",
                })
                return

            # Check for name introduction
            detected_name = detect_name_introduction(cmd_text)
            if detected_name:
                greeting = build_greeting(detected_name)
                # Speak the greeting
                threading.Thread(target=tts.speak, args=(greeting,), daemon=True).start()
                # Send greeting response back to the dashboard
                await self._broadcast({
                    "type": "greeting",
                    "text": greeting,
                })
                await self._broadcast({
                    "type": "status",
                    "state": "IDLE",
                    "caption": "SYSTEM ONLINE",
                })
                return

            # Broadcast processing state
            await self._broadcast({
                "type": "status",
                "state": "PROCESSING",
                "caption": "PROCESSING DIRECTIVE",
            })

            # Execute command in background thread
            def worker():
                try:
                    resp = jarvis_agent.process_command(cmd_text)
                    asyncio.run_coroutine_threadsafe(
                        self._broadcast({"type": "response", "text": resp or ""}),
                        self._loop,
                    )
                except Exception as e:
                    asyncio.run_coroutine_threadsafe(
                        self._broadcast({"type": "response", "text": f"Notice: {str(e)}"}),
                        self._loop,
                    )

            threading.Thread(target=worker, daemon=True).start()

        elif msg_type == "voice_trigger":
            # Send listening state
            await self._broadcast({
                "type": "status",
                "state": "LISTENING",
                "caption": "LISTENING . . .",
            })

            def voice_worker():
                try:
                    heard = stt.listen_from_mic(duration_seconds=4.0)
                    if heard:
                        # Check for "how are you" greeting in voice input
                        if is_how_are_you_greeting(heard):
                            greeting = "Hello  i'm jarvis How may i assist you today ."
                            tts.speak(greeting)
                            asyncio.run_coroutine_threadsafe(
                                self._broadcast({"type": "greeting", "text": greeting}),
                                self._loop,
                            )
                            asyncio.run_coroutine_threadsafe(
                                self._broadcast({
                                    "type": "status",
                                    "state": "IDLE",
                                    "caption": "SYSTEM ONLINE",
                                }),
                                self._loop,
                            )
                            return

                        # Check for name introduction in voice input
                        detected_name = detect_name_introduction(heard)
                        if detected_name:
                            greeting = build_greeting(detected_name)
                            tts.speak(greeting)
                            asyncio.run_coroutine_threadsafe(
                                self._broadcast({"type": "greeting", "text": greeting}),
                                self._loop,
                            )
                            asyncio.run_coroutine_threadsafe(
                                self._broadcast({
                                    "type": "status",
                                    "state": "IDLE",
                                    "caption": "SYSTEM ONLINE",
                                }),
                                self._loop,
                            )
                            return

                        asyncio.run_coroutine_threadsafe(
                            self._broadcast({
                                "type": "status",
                                "state": "PROCESSING",
                                "caption": "PROCESSING DIRECTIVE",
                            }),
                            self._loop,
                        )
                        resp = jarvis_agent.process_command(heard)
                        asyncio.run_coroutine_threadsafe(
                            self._broadcast({"type": "response", "text": resp or ""}),
                            self._loop,
                        )
                    else:
                        asyncio.run_coroutine_threadsafe(
                            self._broadcast({
                                "type": "status",
                                "state": "IDLE",
                                "caption": "SYSTEM ONLINE",
                            }),
                            self._loop,
                        )
                except Exception:
                    asyncio.run_coroutine_threadsafe(
                        self._broadcast({
                            "type": "status",
                            "state": "IDLE",
                            "caption": "SYSTEM ONLINE",
                        }),
                        self._loop,
                    )

            threading.Thread(target=voice_worker, daemon=True).start()

        elif msg_type == "emergency_stop":
            jarvis_agent.handle_emergency_stop()
            await self._broadcast({
                "type": "status",
                "state": "HALTED",
                "caption": "EMERGENCY HALT",
            })

    async def _broadcast(self, data: dict):
        """Broadcasts a message to all connected WebSocket clients."""
        dead = set()
        for ws in self.ws_clients:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        self.ws_clients -= dead

    # ─── Server Lifecycle ────────────────────────────────────────

    async def _start_server(self):
        """Starts the async web server."""
        self._app = await self._create_app()
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.host, self.port)
        await site.start()
        self._loop = asyncio.get_event_loop()
        print(f"\n{'=' * 60}")
        print(f"  J.A.R.V.I.S. Arc Reactor Dashboard")
        print(f"  🌐 http://{self.host}:{self.port}")
        print(f"{'=' * 60}\n")

    def run(self, open_browser: bool = True):
        """Runs the dashboard server (blocking)."""
        if not HAS_AIOHTTP:
            print("[Dashboard] aiohttp not installed. Run: pip install aiohttp")
            print("[Dashboard] Falling back to tkinter dashboard...")
            from ui.dashboard import launch_dashboard as launch_tk
            launch_tk()
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self._start_server())

            # Register backend callbacks
            jarvis_logger.register_ui_callback(self._on_action_logged)

            if open_browser:
                webbrowser.open(f"http://{self.host}:{self.port}")

            loop.run_forever()
        except KeyboardInterrupt:
            print("\n[Dashboard] Shutting down...")
        finally:
            if self._runner:
                loop.run_until_complete(self._runner.cleanup())
            loop.close()

    def _on_action_logged(self, record: JarvisActionRecord):
        """Pushes tool execution updates to the dashboard."""
        if record.tool and hasattr(self, '_loop') and self._loop.is_running():
            tool_name = record.tool.replace("_", " ").upper()
            asyncio.run_coroutine_threadsafe(
                self._broadcast({
                    "type": "status",
                    "state": "PROCESSING",
                    "caption": f"EXECUTING // {tool_name}",
                }),
                self._loop,
            )


# Module-level instance
web_dashboard = WebDashboardServer()


def launch_web_dashboard(host: str = "127.0.0.1", port: int = 5050, open_browser: bool = True):
    """Convenience launcher for the web-based Arc Reactor dashboard."""
    server = WebDashboardServer(host=host, port=port)
    server.run(open_browser=open_browser)
