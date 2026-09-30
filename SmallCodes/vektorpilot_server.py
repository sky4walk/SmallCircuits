#!/usr/bin/env python3
"""
vektorpilot_server.py – Relay-Server für Netzspiele von Vektorpilot

Start:
    python3 vektorpilot_server.py                  # Port 8765, alle Schnittstellen
    python3 vektorpilot_server.py --port 9000

Keine Fremdbibliotheken: Der Server braucht nur Python 3.8 oder neuer.
HTTP und das WebSocket-Protokoll (RFC 6455) sind direkt auf asyncio
umgesetzt – nichts zu installieren, nichts zu aktualisieren.

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

Verschlüsselung (wss://) macht der Server nicht selbst. Dafür stellt man einen
Reverse Proxy wie Caddy davor (Let's Encrypt, DynDNS); WebSockets reicht Caddy
von selbst durch:
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
import base64
import collections
import hashlib
import json
import logging
import pathlib
import secrets
import struct

HTML_FILE = pathlib.Path(__file__).resolve().with_name("vektorpilot.html")
MAX_MSG = 256 * 1024        # größte angenommene Nachricht (Spielzustand, Karte)
MAX_PLAYERS = 16            # Menschen pro Raum
MAX_BACKLOG = 400           # Steuernachrichten, die für einen Client auflaufen dürfen
CHAT_HISTORY = 20           # so viele Chatzeilen bekommt ein Neuankömmling nachgeliefert
IDLE_TIMEOUT = 60           # Sekunden ohne jede Nachricht → Verbindung gilt als tot
HEAD_TIMEOUT = 15           # Sekunden, die ein Browser für die HTTP-Anfrage hat
WS_GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"   # fest vorgegeben in RFC 6455

log = logging.getLogger("vektorpilot")


# =====================================================================
# WebSocket-Rahmen (RFC 6455)
# =====================================================================
#   Byte 0:  FIN | RSV1-3 | Opcode (1 Text, 2 Binär, 0 Fortsetzung,
#                                   8 Schließen, 9 Ping, 10 Pong)
#   Byte 1:  MASK | Länge 0–125, 126 (+2 Byte Länge), 127 (+8 Byte Länge)
#   dann ggf. 4 Byte Maske (Browser → Server immer maskiert), dann Nutzdaten

OP_CONT, OP_TEXT, OP_BIN, OP_CLOSE, OP_PING, OP_PONG = 0, 1, 2, 8, 9, 10


class ProtocolError(Exception):
    pass


def frame(op, payload=b""):
    """Fertigen, unmaskierten Rahmen (Server → Browser) bauen."""
    n = len(payload)
    if n < 126:
        head = struct.pack("!BB", 0x80 | op, n)
    elif n < 65536:
        head = struct.pack("!BBH", 0x80 | op, 126, n)
    else:
        head = struct.pack("!BBQ", 0x80 | op, 127, n)
    return head + payload


def text_frame(obj):
    return frame(OP_TEXT, dumps(obj).encode("utf-8"))


def unmask(data, mask):
    if not data:
        return data
    n = len(data)
    key = (mask * (n // 4 + 1))[:n]
    return (int.from_bytes(data, "big") ^ int.from_bytes(key, "big")).to_bytes(n, "big")


async def read_frame(reader):
    b0, b1 = await reader.readexactly(2)
    if b0 & 0x70:
        raise ProtocolError("RSV-Bits gesetzt")
    fin, op, masked, n = b0 & 0x80, b0 & 0x0F, b1 & 0x80, b1 & 0x7F
    if n == 126:
        n = struct.unpack("!H", await reader.readexactly(2))[0]
    elif n == 127:
        n = struct.unpack("!Q", await reader.readexactly(8))[0]
    if not masked:
        raise ProtocolError("unmaskierter Rahmen vom Browser")
    if n > MAX_MSG:
        raise ProtocolError("Nachricht zu groß")
    if op >= 8 and (n > 125 or not fin):
        raise ProtocolError("ungültiger Steuerrahmen")
    mask = await reader.readexactly(4)
    return bool(fin), op, unmask(await reader.readexactly(n), mask)


# =====================================================================
# Räume und Spieler
# =====================================================================
class Client:
    def __init__(self, writer):
        self.id = "p" + secrets.token_hex(4)
        self.name = ""
        self.room = None
        self.writer = writer
        self.ctrl = collections.deque()   # Steuernachrichten: alle, in Reihenfolge (fertige Rahmen)
        self.state = None                 # Spielzustand: nur der neueste (fertiger Rahmen)
        self.wake = asyncio.Event()
        self.closed = False

    def push(self, fr):
        if len(self.ctrl) >= MAX_BACKLOG:
            self.ctrl.popleft()
        self.ctrl.append(fr)
        self.wake.set()

    def push_state(self, fr):
        self.state = fr
        self.wake.set()


class Room:
    def __init__(self, name):
        self.name = name
        self.clients = {}   # id -> Client, in Eintrittsreihenfolge
        self.host = None
        self.chat = collections.deque(maxlen=CHAT_HISTORY)   # [name, text]
        self.map_frame = None   # eigene Karte des Hosts (fertiger Rahmen)


rooms = {}


def clean(value, limit):
    s = str(value or "")
    s = "".join(ch for ch in s if ch.isprintable())
    return s.strip()[:limit]


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def broadcast(room, obj, skip=None):
    fr = text_frame(obj)          # einmal kodieren, an alle verteilen
    for c in room.clients.values():
        if c is not skip:
            c.push(fr)


def join(c, m):
    name = clean(m.get("name"), 16) or "Pilot"
    room_name = clean(m.get("room"), 24) or "lobby"
    room = rooms.get(room_name)
    if room is None:
        room = rooms[room_name] = Room(room_name)
    if len(room.clients) >= MAX_PLAYERS:
        c.push(text_frame({"t": "error", "x": f"Raum „{room_name}“ ist voll ({MAX_PLAYERS} Spieler)."}))
        if not room.clients:
            rooms.pop(room_name, None)
        return
    c.name, c.room = name, room
    room.clients[c.id] = c
    if room.host is None:
        room.host = c
    c.push(text_frame({"t": "welcome", "id": c.id, "host": room.host.id, "room": room.name,
                       "roster": [[o.id, o.name] for o in room.clients.values()],
                       "chat": list(room.chat)}))
    if room.map_frame and room.host is not c:
        c.push(room.map_frame)
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
        room.map_frame = None   # der neue Host schickt seine Karte selbst
        broadcast(room, {"t": "host", "id": room.host.id})
        log.info("Raum %s: neuer Host %s", room.name, room.host.name)


def handle(c, data):
    """Eine Textnachricht (UTF-8-Bytes) eines Browsers verarbeiten."""
    try:
        m = json.loads(data)
    except ValueError:            # auch ungültiges UTF-8 landet hier
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
        # Spielzustand vom Host: Rahmen einmal bauen, unverändert an alle anderen
        if room.host is c:
            fr = frame(OP_TEXT, data)
            for o in room.clients.values():
                if o is not c:
                    o.push_state(fr)
    elif t == "in":
        if room.host is not None and room.host is not c:
            try:
                k = int(m.get("k", 0)) & 31
            except (TypeError, ValueError):
                return
            room.host.push(text_frame({"t": "in", "f": c.id, "k": k}))
    elif t == "map":
        # eigene Karte vom Host: merken (für Neuankömmlinge) und an alle anderen
        if room.host is c:
            room.map_frame = frame(OP_TEXT, data)
            for o in room.clients.values():
                if o is not c:
                    o.push(room.map_frame)
    elif t == "chat":
        x = clean(m.get("x"), 200)
        if x:
            room.chat.append([c.name, x])
            broadcast(room, {"t": "chat", "f": c.name, "i": c.id, "x": x})
    elif t == "ping":
        c.push(text_frame({"t": "pong", "c": m.get("c")}))


# =====================================================================
# Verbindungen
# =====================================================================
async def ws_writer(c):
    """Schreibt für einen Spieler: erst alle Steuernachrichten, dann den neuesten Zustand."""
    w = c.writer
    try:
        while not c.closed:
            await c.wake.wait()
            c.wake.clear()
            while c.ctrl:
                w.write(c.ctrl.popleft())
            if c.state is not None:
                fr, c.state = c.state, None
                w.write(fr)
            await w.drain()
    except (ConnectionError, OSError, asyncio.CancelledError):
        pass


async def ws_session(reader, writer):
    c = Client(writer)
    task = asyncio.ensure_future(ws_writer(c))
    parts, part_op, close_code = [], None, 1000
    try:
        while True:
            fin, op, data = await asyncio.wait_for(read_frame(reader), IDLE_TIMEOUT)
            if op == OP_PING:
                c.push(frame(OP_PONG, data))
            elif op == OP_PONG:
                pass
            elif op == OP_CLOSE:
                break
            elif op in (OP_TEXT, OP_BIN, OP_CONT):
                if op == OP_CONT:
                    if part_op is None:
                        raise ProtocolError("Fortsetzung ohne Anfang")
                elif part_op is not None:
                    raise ProtocolError("neue Nachricht mitten in einer geteilten")
                else:
                    part_op = op
                parts.append(data)
                if sum(len(p) for p in parts) > MAX_MSG:
                    raise ProtocolError("Nachricht zu groß")
                if fin:
                    msg, is_text = b"".join(parts), part_op == OP_TEXT
                    parts, part_op = [], None
                    if is_text and msg:
                        handle(c, msg)
            else:
                raise ProtocolError(f"unbekannter Opcode {op}")
    except ProtocolError as e:
        log.info("Protokollfehler (%s): %s", c.name or c.id, e)
        close_code = 1002
    except (asyncio.IncompleteReadError, asyncio.TimeoutError, ConnectionError, OSError):
        close_code = 1001
    finally:
        leave(c)
        c.closed = True
        task.cancel()
        try:
            writer.write(frame(OP_CLOSE, struct.pack("!H", close_code)))
            await asyncio.wait_for(writer.drain(), 2)
        except Exception:
            pass
        writer.close()


async def read_head(reader):
    raw = await reader.readuntil(b"\r\n\r\n")
    lines = raw.decode("latin-1").split("\r\n")
    parts = lines[0].split(" ")
    if len(parts) != 3:
        raise ValueError("kaputte Anfragezeile")
    method, target, _ = parts
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return method, target.split("?", 1)[0], headers


async def http_reply(writer, status, reason, body, ctype, head_only=False, extra=""):
    hdr = (f"HTTP/1.1 {status} {reason}\r\n"
           f"Content-Type: {ctype}\r\n"
           f"Content-Length: {len(body)}\r\n"
           f"Cache-Control: no-cache\r\n"
           f"Connection: close\r\n{extra}\r\n")
    writer.write(hdr.encode("latin-1") + (b"" if head_only else body))
    await writer.drain()


async def connection(reader, writer):
    try:
        try:
            method, path, h = await asyncio.wait_for(read_head(reader), HEAD_TIMEOUT)
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, asyncio.LimitOverrunError, ValueError, OSError):
            return

        upgrade = h.get("upgrade", "").lower() == "websocket" and "upgrade" in h.get("connection", "").lower()
        if upgrade:
            key = h.get("sec-websocket-key", "")
            if method != "GET" or not path.endswith("/ws") or not key or h.get("sec-websocket-version") != "13":
                await http_reply(writer, 400, "Bad Request", b"Ungueltige WebSocket-Anfrage", "text/plain; charset=utf-8",
                                 extra="Sec-WebSocket-Version: 13\r\n")
                return
            accept = base64.b64encode(hashlib.sha1(key.encode("latin-1") + WS_GUID).digest()).decode()
            writer.write((
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n").encode("latin-1"))
            await writer.drain()
            await ws_session(reader, writer)
            return

        head_only = method == "HEAD"
        if method not in ("GET", "HEAD"):
            await http_reply(writer, 405, "Method Not Allowed", "Methode nicht erlaubt".encode(), "text/plain; charset=utf-8")
        elif path.endswith("/") or path.endswith("/vektorpilot.html") or path.endswith("/index.html"):
            try:
                body = HTML_FILE.read_bytes()
                await http_reply(writer, 200, "OK", body, "text/html; charset=utf-8", head_only)
            except OSError:
                await http_reply(writer, 500, "Internal Server Error",
                                 f"{HTML_FILE.name} fehlt neben dem Server".encode(), "text/plain; charset=utf-8", head_only)
        elif path.endswith("/status"):
            info = {name: [c.name for c in r.clients.values()] for name, r in rooms.items()}
            await http_reply(writer, 200, "OK", dumps(info).encode(), "application/json; charset=utf-8", head_only)
        else:
            await http_reply(writer, 404, "Not Found", "Nicht gefunden".encode(), "text/plain; charset=utf-8", head_only)
    except (ConnectionError, OSError):
        pass
    finally:
        if not writer.is_closing():
            writer.close()


async def serve(host, port):
    server = await asyncio.start_server(connection, host, port, limit=64 * 1024)
    log.info("Vektorpilot-Server auf http://%s:%d/  (WebSocket: /ws)", host, port)
    async with server:
        await server.serve_forever()


def main():
    ap = argparse.ArgumentParser(description="Relay-Server für Vektorpilot")
    ap.add_argument("--host", default="0.0.0.0", help="Adresse (Standard: alle Schnittstellen; '::' für IPv4+IPv6)")
    ap.add_argument("--port", type=int, default=8765, help="Port (Standard: 8765)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    if not HTML_FILE.exists():
        log.warning("Achtung: %s nicht gefunden – nur WebSocket-Betrieb", HTML_FILE)
    try:
        asyncio.run(serve(a.host, a.port))
    except KeyboardInterrupt:
        log.info("Server beendet")


if __name__ == "__main__":
    main()
