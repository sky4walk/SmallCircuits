#!/usr/bin/env python3
"""
vektorpilot_server.py – Relay-Server für Netzspiele von Vektorpilot

Start:
    python3 vektorpilot_server.py                  # Port 8765, alle Schnittstellen
    python3 vektorpilot_server.py --port 9000

Einzige Fremdbibliothek ist uvicorn mit WebSocket-Unterstützung:
    pip install "uvicorn[standard]"
    (Debian/Raspberry Pi OS: apt install python3-uvicorn python3-websockets)

Die Datei vektorpilot.html muss im selben Ordner liegen. Der Server liefert sie
unter http://<rechner>:8765/ aus und nimmt unter .../ws die WebSocket-
Verbindungen an. Die Seite kann auch lokal (file://) geöffnet werden, dann
trägt man die Serveradresse (ws://<rechner>:8765/ws) im Menü ein.

Arbeitsweise
------------
Der Server rechnet selbst nichts. Wer einen Raum als Erster betritt, ist Host:
Sein Browser rechnet das Spiel samt Computergegnern. Der Server reicht nur
weiter – Tastendrücke der Mitspieler an den Host, den Spielzustand vom Host an
alle anderen. Beim Spielzustand wird immer nur der neueste Stand zugestellt;
ein langsamer Mitspieler bekommt also keine veralteten Stände nachgeliefert.
Verlässt der Host den Raum, wird der dienstälteste Mitspieler Host und
rechnet mit dem letzten Stand weiter.

Außerdem merkt sich der Server je Raum die letzten 20 Chatzeilen (für
Neuankömmlinge) und die eigene Karte des Hosts, falls dieser eine aus dem
Karteneditor spielt – so bekommt jeder Mitspieler die Karte automatisch.

Hinter Caddy (Let's Encrypt, DynDNS) – WebSockets reicht Caddy von selbst durch:
    meinname.dyndns.org {
        redir /vektorpilot /vektorpilot/
        handle_path /vektorpilot/* {
            reverse_proxy 127.0.0.1:8765
        }
    }
    → Spiel unter https://meinname.dyndns.org/vektorpilot/
"""
import argparse
import asyncio
import collections
import json
import logging
import pathlib
import secrets

import uvicorn

HTML_FILE = pathlib.Path(__file__).resolve().with_name("vektorpilot.html")
MAX_MSG = 256 * 1024        # größte angenommene Nachricht (Spielzustand)
MAX_PLAYERS = 16            # Menschen pro Raum
MAX_BACKLOG = 400           # Steuernachrichten, die für einen Client auflaufen dürfen
CHAT_HISTORY = 20           # so viele Chatzeilen bekommt ein Neuankömmling nachgeliefert

log = logging.getLogger("vektorpilot")


class Client:
    def __init__(self):
        self.id = "p" + secrets.token_hex(4)
        self.name = ""
        self.room = None
        self.ctrl = collections.deque()   # Steuernachrichten: alle, in Reihenfolge
        self.state = None                 # Spielzustand: nur der neueste
        self.wake = asyncio.Event()
        self.closed = False

    def push(self, text):
        if len(self.ctrl) >= MAX_BACKLOG:
            self.ctrl.popleft()
        self.ctrl.append(text)
        self.wake.set()

    def push_state(self, text):
        self.state = text
        self.wake.set()


class Room:
    def __init__(self, name):
        self.name = name
        self.clients = {}   # id -> Client, in Eintrittsreihenfolge
        self.host = None
        self.chat = collections.deque(maxlen=CHAT_HISTORY)   # [name, text]
        self.map_msg = None  # eigene Karte des Hosts (unverändert weitergereicht)


rooms = {}


def clean(value, limit):
    s = str(value or "")
    s = "".join(ch for ch in s if ch.isprintable())
    return s.strip()[:limit]


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def broadcast(room, obj, skip=None):
    text = dumps(obj)
    for c in room.clients.values():
        if c is not skip:
            c.push(text)


def join(c, m):
    name = clean(m.get("name"), 16) or "Pilot"
    room_name = clean(m.get("room"), 24) or "lobby"
    room = rooms.get(room_name)
    if room is None:
        room = rooms[room_name] = Room(room_name)
    if len(room.clients) >= MAX_PLAYERS:
        c.push(dumps({"t": "error", "x": f"Raum „{room_name}“ ist voll ({MAX_PLAYERS} Spieler)."}))
        if not room.clients:
            rooms.pop(room_name, None)
        return
    c.name, c.room = name, room
    room.clients[c.id] = c
    if room.host is None:
        room.host = c
    c.push(dumps({"t": "welcome", "id": c.id, "host": room.host.id, "room": room.name,
                  "roster": [[o.id, o.name] for o in room.clients.values()],
                  "chat": list(room.chat)}))
    if room.map_msg and room.host is not c:
        c.push(room.map_msg)
    broadcast(room, {"t": "join", "id": c.id, "name": c.name}, skip=c)
    log.info("%s betritt Raum %s (%d Spieler)%s", name, room_name, len(room.clients),
             " als Host" if room.host is c else "")


def leave(c):
    room = c.room
    if room is None:
        return
    room.clients.pop(c.id, None)
    c.room = None
    log.info("%s verlässt Raum %s (%d übrig)", c.name, room.name, len(room.clients))
    if not room.clients:
        rooms.pop(room.name, None)
        return
    broadcast(room, {"t": "leave", "id": c.id, "name": c.name})
    if room.host is c:
        room.host = next(iter(room.clients.values()))
        room.map_msg = None   # der neue Host schickt seine Karte selbst
        broadcast(room, {"t": "host", "id": room.host.id})
        log.info("Raum %s: neuer Host %s", room.name, room.host.name)


def handle(c, raw):
    if len(raw) > MAX_MSG:
        return
    try:
        m = json.loads(raw)
    except ValueError:
        return
    if not isinstance(m, dict):
        return
    t = m.get("t")
    room = c.room
    if room is None:
        if t == "hello":
            join(c, m)
        return
    if t == "st":
        # Spielzustand vom Host: unverändert an alle anderen
        if room.host is c:
            for o in room.clients.values():
                if o is not c:
                    o.push_state(raw)
    elif t == "in":
        if room.host is not None and room.host is not c:
            try:
                k = int(m.get("k", 0)) & 31
            except (TypeError, ValueError):
                return
            room.host.push(dumps({"t": "in", "f": c.id, "k": k}))
    elif t == "map":
        # eigene Karte vom Host: merken (für Neuankömmlinge) und an alle anderen
        if room.host is c:
            room.map_msg = raw
            for o in room.clients.values():
                if o is not c:
                    o.push(raw)
    elif t == "chat":
        x = clean(m.get("x"), 200)
        if x:
            room.chat.append([c.name, x])
            broadcast(room, {"t": "chat", "f": c.name, "i": c.id, "x": x})
    elif t == "ping":
        c.push(dumps({"t": "pong", "c": m.get("c")}))


async def writer(c, send):
    try:
        while not c.closed:
            await c.wake.wait()
            c.wake.clear()
            while c.ctrl:
                await send({"type": "websocket.send", "text": c.ctrl.popleft()})
            if c.state is not None:
                text, c.state = c.state, None
                await send({"type": "websocket.send", "text": text})
    except Exception:   # Verbindung weg – der Leser räumt auf
        pass


async def websocket(scope, receive, send):
    first = await receive()
    if first["type"] != "websocket.connect":
        return
    if not scope["path"].rstrip("/").endswith("/ws") and scope["path"] != "/ws":
        await send({"type": "websocket.close", "code": 1008})
        return
    await send({"type": "websocket.accept"})
    c = Client()
    task = asyncio.create_task(writer(c, send))
    try:
        while True:
            msg = await receive()
            if msg["type"] == "websocket.disconnect":
                break
            if msg["type"] == "websocket.receive":
                raw = msg.get("text")
                if raw is None and msg.get("bytes"):
                    raw = msg["bytes"].decode("utf-8", "replace")
                if raw:
                    handle(c, raw)
    finally:
        leave(c)
        c.closed = True
        c.wake.set()
        task.cancel()


async def http(scope, receive, send):
    path, method = scope["path"], scope["method"]
    headers = [(b"content-type", b"text/plain; charset=utf-8")]
    if method not in ("GET", "HEAD"):
        status, body = 405, b"Methode nicht erlaubt"
    elif path.endswith("/") or path.endswith("/vektorpilot.html") or path.endswith("/index.html"):
        try:
            body, status = HTML_FILE.read_bytes(), 200
            headers = [(b"content-type", b"text/html; charset=utf-8"), (b"cache-control", b"no-cache")]
        except OSError:
            status, body = 500, f"{HTML_FILE.name} fehlt neben dem Server".encode()
    elif path.endswith("/status"):
        info = {name: [c.name for c in r.clients.values()] for name, r in rooms.items()}
        status, body = 200, dumps(info).encode()
        headers = [(b"content-type", b"application/json; charset=utf-8")]
    else:
        status, body = 404, b"Nicht gefunden"
    headers.append((b"content-length", str(len(body)).encode()))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": b"" if method == "HEAD" else body})


async def app(scope, receive, send):
    kind = scope["type"]
    if kind == "http":
        await http(scope, receive, send)
    elif kind == "websocket":
        await websocket(scope, receive, send)
    elif kind == "lifespan":
        while True:
            msg = await receive()
            if msg["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif msg["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return


def main():
    ap = argparse.ArgumentParser(description="Relay-Server für Vektorpilot")
    ap.add_argument("--host", default="0.0.0.0", help="Adresse (Standard: alle Schnittstellen)")
    ap.add_argument("--port", type=int, default=8765, help="Port (Standard: 8765)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    if not HTML_FILE.exists():
        log.warning("Achtung: %s nicht gefunden – nur WebSocket-Betrieb", HTML_FILE)
    log.info("Vektorpilot-Server auf http://%s:%d/  (WebSocket: /ws)", a.host, a.port)
    uvicorn.run(app, host=a.host, port=a.port, lifespan="off", log_level="warning",
                ws_max_size=MAX_MSG, ws_ping_interval=20, ws_ping_timeout=20, proxy_headers=True)


if __name__ == "__main__":
    main()
