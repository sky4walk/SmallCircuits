#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tvmedia.py - Einzeldatei-Medienserver fuer den Browser eines Smart-TV.

Nur Python-Standardbibliothek. Keine Installation, keine Datenbank, kein Scan-Lauf.

    python3 tvmedia.py /pfad/zur/musik
    python3 tvmedia.py /mnt/medien --port 8080

Danach am Fernseher http://<server-ip>:8000 aufrufen.

Eigenschaften:
  * HTTP Range-Requests  -> Spulen funktioniert, grosse Dateien brechen nicht ab
  * ein einziges <audio>-Element -> Autoplay-Freigabe bleibt ueber Tracks erhalten
  * Fernbedienungs-Navigation (Pfeile / OK / Zurueck), inkl. Tizen- und WebOS-Keycodes
  * SRT wird beim Abruf nach WebVTT konvertiert
  * ES5-JavaScript, damit auch Browser ab ca. 2015 mitspielen

Kein Transkodieren: Video laeuft nur, wenn der TV Container und Codec nativ kann.
Faustregel MP4 mit H.264 + AAC. MKV vorher remuxen:
    ffmpeg -i film.mkv -c copy -movflags +faststart film.mp4
"""

import argparse
import json
import os
import re
import socket
import sys

try:
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
except ImportError:  # Python 3.6
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn

    class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

from urllib.parse import unquote, urlparse, parse_qs

# ---------------------------------------------------------------- Konfiguration

AUDIO_EXT = {'.mp3', '.m4a', '.aac', '.ogg', '.oga', '.opus', '.flac', '.wav', '.wma'}
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
VIDEO_EXT = {'.mp4', '.m4v', '.webm', '.mkv', '.mov', '.avi', '.ts', '.m2ts', '.mpg', '.mpeg'}
SUB_EXT = ['.vtt', '.srt']

MIME = {
    '.mp3': 'audio/mpeg', '.m4a': 'audio/mp4', '.aac': 'audio/aac',
    '.ogg': 'audio/ogg', '.oga': 'audio/ogg', '.opus': 'audio/ogg',
    '.flac': 'audio/flac', '.wav': 'audio/wav', '.wma': 'audio/x-ms-wma',
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
    '.gif': 'image/gif', '.webp': 'image/webp', '.bmp': 'image/bmp',
    '.mp4': 'video/mp4', '.m4v': 'video/mp4', '.webm': 'video/webm',
    '.mkv': 'video/x-matroska', '.mov': 'video/quicktime',
    '.avi': 'video/x-msvideo', '.ts': 'video/mp2t', '.m2ts': 'video/mp2t',
    '.mpg': 'video/mpeg', '.mpeg': 'video/mpeg',
}

ROOT = os.path.abspath('.')
CHUNK = 64 * 1024


def kind_of(name):
    ext = os.path.splitext(name)[1].lower()
    if ext in AUDIO_EXT:
        return 'audio'
    if ext in IMAGE_EXT:
        return 'image'
    if ext in VIDEO_EXT:
        return 'video'
    return None


def safe_join(rel):
    """Relativen Pfad auf ROOT abbilden und Ausbrueche verhindern."""
    rel = rel.replace('\\', '/').lstrip('/')
    full = os.path.realpath(os.path.join(ROOT, rel))
    root = os.path.realpath(ROOT)
    if full != root and not full.startswith(root + os.sep):
        return None
    return full


def srt_to_vtt(raw):
    for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode('latin-1', 'replace')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'(\d\d:\d\d:\d\d),(\d\d\d)', r'\1.\2', text)
    return ('WEBVTT\n\n' + text).encode('utf-8')


def find_subtitle(video_full):
    """Untertitel neben der Videodatei suchen: film.srt, film.de.srt, ..."""
    base = os.path.splitext(video_full)[0]
    folder = os.path.dirname(video_full)
    stem = os.path.basename(base).lower()
    for ext in SUB_EXT:
        cand = base + ext
        if os.path.isfile(cand):
            return cand
    try:
        for entry in sorted(os.listdir(folder)):
            low = entry.lower()
            if low.startswith(stem + '.') and os.path.splitext(low)[1] in SUB_EXT:
                return os.path.join(folder, entry)
    except OSError:
        pass
    return None


def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()


# ---------------------------------------------------------------- HTTP-Handler

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'tvmedia'

    def log_message(self, fmt, *args):
        sys.stderr.write('%s  %s\n' % (self.address_string(), fmt % args))

    # -- Routen

    def do_HEAD(self):
        self.route()

    def do_GET(self):
        self.route()

    def route(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query = parse_qs(parsed.query)

        if path == '/' or path == '/index.html':
            return self.send_bytes(PAGE.encode('utf-8'), 'text/html; charset=utf-8')
        if path == '/api/list':
            return self.api_list(query.get('path', [''])[0])
        if path.startswith('/media/'):
            return self.send_media(path[len('/media/'):])
        if path.startswith('/sub/'):
            return self.send_subtitle(path[len('/sub/'):])
        self.send_error(404, 'Nicht gefunden')

    # -- Verzeichnis auflisten (bei Bedarf, kein Vollscan)

    def api_list(self, rel):
        full = safe_join(rel)
        if not full or not os.path.isdir(full):
            return self.send_error(404, 'Ordner nicht gefunden')

        dirs, files = [], []
        try:
            entries = sorted(os.listdir(full), key=lambda s: s.lower())
        except OSError as exc:
            return self.send_error(403, 'Ordner nicht lesbar: %s' % exc)

        for name in entries:
            if name.startswith('.'):
                continue
            child = os.path.join(full, name)
            if os.path.isdir(child):
                dirs.append(name)
                continue
            kind = kind_of(name)
            if not kind:
                continue
            try:
                size = os.path.getsize(child)
            except OSError:
                size = 0
            item = {'name': name, 'kind': kind, 'size': size}
            if kind == 'video' and find_subtitle(child):
                item['sub'] = True
            files.append(item)

        rel_clean = rel.replace('\\', '/').strip('/')
        parent = None
        if rel_clean:
            parent = rel_clean.rsplit('/', 1)[0] if '/' in rel_clean else ''

        self.send_json({'path': rel_clean, 'parent': parent,
                        'dirs': dirs, 'files': files})

    # -- Mediendatei mit Range-Unterstuetzung

    def send_media(self, rel):
        full = safe_join(rel)
        if not full or not os.path.isfile(full):
            return self.send_error(404, 'Datei nicht gefunden')

        ext = os.path.splitext(full)[1].lower()
        ctype = MIME.get(ext, 'application/octet-stream')
        try:
            size = os.path.getsize(full)
        except OSError:
            return self.send_error(404, 'Datei nicht lesbar')

        start, end, status = 0, size - 1, 200
        header = self.headers.get('Range')
        if header:
            match = re.match(r'bytes=(\d*)-(\d*)\s*$', header.strip())
            if match:
                first, last = match.group(1), match.group(2)
                if first == '':
                    if last == '':
                        return self.send_error(400, 'Ungueltiger Range-Header')
                    start = max(0, size - int(last))
                else:
                    start = int(first)
                    end = int(last) if last else size - 1
                if start >= size:
                    self.send_response(416)
                    self.send_header('Content-Range', 'bytes */%d' % size)
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                end = min(end, size - 1)
                status = 206

        length = end - start + 1
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(length))
        if status == 206:
            self.send_header('Content-Range',
                             'bytes %d-%d/%d' % (start, end, size))
        self.end_headers()

        if self.command == 'HEAD':
            return
        try:
            with open(full, 'rb') as handle:
                handle.seek(start)
                left = length
                while left > 0:
                    block = handle.read(min(CHUNK, left))
                    if not block:
                        break
                    self.wfile.write(block)
                    left -= len(block)
        except (BrokenPipeError, ConnectionResetError):
            pass  # TV hat weitergeschaltet, das ist normal

    # -- Untertitel: SRT wird zu WebVTT

    def send_subtitle(self, rel):
        full = safe_join(rel)
        if not full or not os.path.isfile(full):
            return self.send_error(404, 'Video nicht gefunden')
        sub = find_subtitle(full)
        if not sub:
            return self.send_error(404, 'Kein Untertitel vorhanden')
        with open(sub, 'rb') as handle:
            raw = handle.read()
        if sub.lower().endswith('.srt'):
            raw = srt_to_vtt(raw)
        self.send_bytes(raw, 'text/vtt; charset=utf-8')

    # -- Hilfen

    def send_json(self, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_bytes(body, 'application/json; charset=utf-8')

    def send_bytes(self, body, ctype):
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)


# ---------------------------------------------------------------- Oberflaeche

PAGE = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Medien</title>
<style>
  /* Entworfen fuer 3 Meter Abstand und eine Fernbedienung:
     dunkler Grund, grosse Typo, und ein Fokusrahmen, der nicht zu uebersehen ist. */
  :root{
    --bg:#14161c; --panel:#1d212b; --line:#2c3140;
    --fg:#e9ecf3; --dim:#8991a6; --accent:#ffb02e;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);
    font-family:Arial,Helvetica,sans-serif;overflow:hidden;}
  #app{display:flex;flex-direction:column;height:100%;}

  header{padding:22px 44px 14px;border-bottom:2px solid var(--line);flex:none;}
  #crumb{font-size:15px;letter-spacing:.22em;text-transform:uppercase;
    color:var(--dim);margin-bottom:14px;white-space:nowrap;overflow:hidden;
    text-overflow:ellipsis;}
  #crumb b{color:var(--accent);font-weight:normal;}
  #tabs{display:flex;gap:12px;}
  .tab{padding:9px 22px;font-size:19px;color:var(--dim);border:3px solid transparent;
    border-radius:6px;background:var(--panel);cursor:pointer;}
  .tab.on{color:var(--bg);background:var(--accent);font-weight:bold;}

  #list{flex:1;overflow-y:auto;padding:14px 30px 20px;}
  .row{display:flex;align-items:center;gap:20px;padding:15px 20px;
    border-left:7px solid transparent;border-radius:6px;font-size:25px;}
  .row .tag{flex:none;width:2.3em;font-size:15px;letter-spacing:.14em;
    text-transform:uppercase;color:var(--dim);}
  .row .name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
  .row .meta{flex:none;font-size:16px;color:var(--dim);}
  .row.dir .name{color:var(--accent);}
  /* Auf einer Fernbedienung ist der Fokus der Mauszeiger. Deshalb bekommt er
     als einziges Element den vollen Kontrast. */
  .row.sel{background:var(--panel);border-left-color:var(--accent);
    outline:3px solid var(--accent);}
  .row.sel .tag,.row.sel .meta{color:var(--fg);}
  .row.playing .name:after{content:" \25B6";color:var(--accent);}
  #empty{padding:60px 24px;font-size:22px;color:var(--dim);}

  #bar{flex:none;display:none;align-items:center;gap:20px;padding:14px 44px;
    background:var(--panel);border-top:2px solid var(--line);}
  #bar.on{display:flex;}
  #viz{flex:none;width:64px;height:34px;}
  #np{flex:1;overflow:hidden;}
  #np .t{font-size:22px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
  #np .s{font-size:15px;color:var(--dim);margin-top:3px;}
  #track{height:5px;background:var(--line);border-radius:3px;margin-top:9px;}
  #fill{height:100%;width:0;background:var(--accent);border-radius:3px;}

  #over{position:fixed;inset:0;top:0;left:0;right:0;bottom:0;background:#000;
    display:none;align-items:center;justify-content:center;}
  #over.on{display:flex;}
  #over img,#over video{max-width:100%;max-height:100%;}
  #cap{position:absolute;left:0;right:0;bottom:0;padding:18px 44px;font-size:20px;
    background:rgba(0,0,0,.75);color:var(--fg);}
  #msg{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);
    background:var(--panel);border:3px solid var(--accent);border-radius:8px;
    padding:26px 34px;font-size:22px;max-width:74%;display:none;z-index:9;}
</style>
</head>
<body>
<div id="app">
  <header>
    <div id="crumb"></div>
    <div id="tabs"></div>
  </header>
  <div id="list"></div>
  <div id="bar">
    <canvas id="viz" width="64" height="34"></canvas>
    <div id="np"><div class="t"></div><div class="s"></div>
      <div id="track"><div id="fill"></div></div></div>
  </div>
</div>
<div id="over"><div id="cap"></div></div>
<div id="msg"></div>
<audio id="au"></audio>

<script>
/* ES5 - keine Pfeilfunktionen, kein fetch, keine Template-Strings.
   Aeltere Tizen- und WebOS-Browser brechen daran ab. */
var FILTERS = [
  {id:'all',   label:'Alles'},
  {id:'audio', label:'Musik'},
  {id:'image', label:'Bilder'},
  {id:'video', label:'Videos'}
];

var path = '', parent = null, rows = [], sel = 0, filter = 'all';
var queue = [], qi = -1, playingKey = null;
var overKind = null, overList = [], overIdx = 0, resumeAudio = false;

var $list = document.getElementById('list');
var $crumb = document.getElementById('crumb');
var $tabs = document.getElementById('tabs');
var $bar = document.getElementById('bar');
var $over = document.getElementById('over');
var $cap = document.getElementById('cap');
var $msg = document.getElementById('msg');
var au = document.getElementById('au');

function enc(p){
  return p.split('/').map(function(s){ return encodeURIComponent(s); }).join('/');
}
function join(a,b){ return a ? a + '/' + b : b; }
function mb(n){
  if(!n) return '';
  if(n < 1048576) return Math.round(n/1024) + ' KB';
  return (n/1048576).toFixed(1) + ' MB';
}
function clock(s){
  if(!s || s !== s) return '0:00';
  var m = Math.floor(s/60), r = Math.floor(s%60);
  return m + ':' + (r < 10 ? '0' : '') + r;
}
function note(text){
  $msg.textContent = text;
  $msg.style.display = 'block';
  window.clearTimeout(note.t);
  note.t = window.setTimeout(function(){ $msg.style.display = 'none'; }, 4000);
}

/* ---- Daten laden ---- */

function load(rel, keepSel){
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/list?path=' + encodeURIComponent(rel), true);
  xhr.onreadystatechange = function(){
    if(xhr.readyState !== 4) return;
    if(xhr.status !== 200){ note('Ordner nicht lesbar.'); return; }
    var data = JSON.parse(xhr.responseText);
    path = data.path; parent = data.parent;
    rows = [];
    if(parent !== null) rows.push({type:'up', name:'..'});
    for(var i=0;i<data.dirs.length;i++)
      rows.push({type:'dir', name:data.dirs[i]});
    for(var j=0;j<data.files.length;j++){
      var f = data.files[j];
      if(filter === 'all' || f.kind === filter)
        rows.push({type:'file', name:f.name, kind:f.kind, size:f.size, sub:f.sub});
    }
    if(!keepSel) sel = 0;
    if(sel >= rows.length) sel = rows.length - 1;
    if(sel < 0) sel = 0;
    render();
  };
  xhr.send();
}

/* ---- Anzeige ---- */

function render(){
  $crumb.innerHTML = '';
  var parts = path ? path.split('/') : [];
  var b = document.createElement('b');
  b.textContent = 'Medien';
  $crumb.appendChild(b);
  for(var i=0;i<parts.length;i++)
    $crumb.appendChild(document.createTextNode('  \u203A  ' + parts[i]));

  $tabs.innerHTML = '';
  for(var t=0;t<FILTERS.length;t++){
    var d = document.createElement('div');
    d.className = 'tab' + (FILTERS[t].id === filter ? ' on' : '');
    d.textContent = FILTERS[t].label;
    (function(id, el){
      el.onclick = function(){
        if(id === filter) return;
        filter = id;
        load(path);
      };
    })(FILTERS[t].id, d);
    $tabs.appendChild(d);
  }

  $list.innerHTML = '';
  if(!rows.length){
    var e = document.createElement('div');
    e.id = 'empty';
    e.textContent = 'Hier liegt nichts, was der Filter zeigt. '
                  + 'Mit Links/Rechts den Filter wechseln.';
    $list.appendChild(e);
    return;
  }
  for(var r=0;r<rows.length;r++){
    var row = rows[r], el = document.createElement('div');
    el.className = 'row' + (r === sel ? ' sel' : '')
                 + (row.type === 'dir' || row.type === 'up' ? ' dir' : '');
    if(row.type === 'file' && join(path,row.name) === playingKey)
      el.className += ' playing';

    var tag = document.createElement('span');
    tag.className = 'tag';
    tag.textContent = row.type === 'up' ? '\u2191'
                    : row.type === 'dir' ? '\u25A0'
                    : row.kind === 'audio' ? 'mp3'
                    : row.kind === 'image' ? 'img' : 'vid';
    var nm = document.createElement('span');
    nm.className = 'name';
    nm.textContent = row.type === 'up' ? 'Eine Ebene hoeher' : row.name;
    var mt = document.createElement('span');
    mt.className = 'meta';
    mt.textContent = row.type === 'file'
      ? mb(row.size) + (row.sub ? '  \u00B7 UT' : '') : '';

    el.appendChild(tag); el.appendChild(nm); el.appendChild(mt);
    (function(idx){
      el.onclick = function(){ sel = idx; render(); activate(); };
    })(r);
    $list.appendChild(el);
  }
  var cur = $list.children[sel];
  if(cur && cur.scrollIntoView) cur.scrollIntoView({block:'nearest'});
}

/* ---- Aktion auf der markierten Zeile ---- */

function activate(){
  var row = rows[sel];
  if(!row) return;
  if(row.type === 'up'){ load(parent); return; }
  if(row.type === 'dir'){ load(join(path, row.name)); return; }
  if(row.kind === 'audio') return playAudioFrom(row.name);
  if(row.kind === 'image') return openOverlay('image', row.name);
  if(row.kind === 'video') return openOverlay('video', row.name);
}

function siblings(kind){
  var out = [];
  for(var i=0;i<rows.length;i++)
    if(rows[i].type === 'file' && rows[i].kind === kind) out.push(rows[i].name);
  return out;
}

/* ---- Audio: ein Element, das nie ersetzt wird ---- */

function playAudioFrom(name){
  queue = siblings('audio');
  qi = queue.indexOf(name);
  playCurrent();
}
function playCurrent(){
  if(qi < 0 || qi >= queue.length) return;
  var name = queue[qi];
  playingKey = join(path, name);
  au.src = '/media/' + enc(playingKey);
  var p = au.play();
  if(p && p['catch']) p['catch'](function(){ note('Wiedergabe blockiert. Nochmal OK druecken.'); });
  document.querySelector('#np .t').textContent = name;
  $bar.className = 'on';
  render();
}
function step(delta){
  if(!queue.length) return;
  qi = (qi + delta + queue.length) % queue.length;
  playCurrent();
}
au.onended = function(){ step(1); };
au.onerror = function(){ note('Dieses Format spielt der Fernseher nicht ab.'); };
au.ontimeupdate = function(){
  document.querySelector('#np .s').textContent =
    clock(au.currentTime) + ' / ' + clock(au.duration);
  document.getElementById('fill').style.width =
    (au.duration ? (au.currentTime/au.duration*100) : 0) + '%';
};

/* Viele Fernseher dunkeln bei reinem Ton nach Minuten ab. Eine laufende
   Canvas-Zeichnung haelt manche Geraete wach - nicht alle. */
var ctx = document.getElementById('viz').getContext('2d');
var tick = 0;
function draw(){
  ctx.clearRect(0,0,64,34);
  if(!au.paused){
    ctx.fillStyle = '#ffb02e';
    for(var i=0;i<5;i++){
      var h = 6 + 13 * Math.abs(Math.sin(tick/17 + i));
      ctx.fillRect(i*13, 34-h, 8, h);
    }
    tick++;
  }
  (window.requestAnimationFrame || function(f){ window.setTimeout(f,60); })(draw);
}
draw();

/* ---- Overlay fuer Bild und Video ---- */

function openOverlay(kind, name){
  overKind = kind;
  overList = siblings(kind);
  overIdx = overList.indexOf(name);
  if(kind === 'video'){
    resumeAudio = !au.paused;
    au.pause();
  }
  showOverlay();
}
function showOverlay(){
  var old = $over.querySelector('img,video');
  if(old){ if(old.pause) old.pause(); $over.removeChild(old); }

  var name = overList[overIdx], rel = join(path, name), el;
  if(overKind === 'image'){
    el = document.createElement('img');
    el.src = '/media/' + enc(rel);
    el.onerror = function(){ note('Bild laesst sich nicht anzeigen.'); };
  } else {
    el = document.createElement('video');
    el.src = '/media/' + enc(rel);
    el.controls = true;
    el.autoplay = true;
    for(var i=0;i<rows.length;i++){
      if(rows[i].name === name && rows[i].sub){
        var tr = document.createElement('track');
        tr.kind = 'subtitles'; tr.srclang = 'de'; tr.label = 'Untertitel';
        tr.src = '/sub/' + enc(rel); tr['default'] = true;
        el.appendChild(tr);
      }
    }
    el.onerror = function(){
      note('Codec oder Container passt nicht. Mit '
         + '"ffmpeg -i datei -c copy -movflags +faststart datei.mp4" umpacken.');
    };
    el.onended = function(){ closeOverlay(); };
  }
  $over.insertBefore(el, $cap);
  $cap.textContent = name + '   (' + (overIdx+1) + ' von ' + overList.length + ')';
  $over.className = 'on';
}
function overStep(d){
  if(!overList.length) return;
  overIdx = (overIdx + d + overList.length) % overList.length;
  showOverlay();
}
function closeOverlay(){
  var el = $over.querySelector('img,video');
  if(el){ if(el.pause) el.pause(); $over.removeChild(el); }
  $over.className = '';
  if(overKind === 'video' && resumeAudio) au.play();
  overKind = null;
  render();
}

/* ---- Fernbedienung ---- */

var BACK = [8, 27, 461, 10009, 166];   // Browser, Escape, WebOS, Tizen, sonstige
document.addEventListener('keydown', function(ev){
  var k = ev.keyCode;

  if($over.className === 'on'){
    if(BACK.indexOf(k) >= 0){ closeOverlay(); ev.preventDefault(); return; }
    var vid = $over.querySelector('video');
    if(overKind === 'image'){
      if(k === 39){ overStep(1);  ev.preventDefault(); }
      if(k === 37){ overStep(-1); ev.preventDefault(); }
    } else if(vid){
      if(k === 39){ vid.currentTime += 10; ev.preventDefault(); }
      if(k === 37){ vid.currentTime -= 10; ev.preventDefault(); }
      if(k === 13 || k === 32 || k === 179){
        if(vid.paused) vid.play(); else vid.pause();
        ev.preventDefault();
      }
    }
    return;
  }

  if(k === 40){ sel = Math.min(sel+1, rows.length-1); render(); ev.preventDefault(); }
  else if(k === 38){ sel = Math.max(sel-1, 0); render(); ev.preventDefault(); }
  else if(k === 13){ activate(); ev.preventDefault(); }
  else if(k === 37 || k === 39){
    var i = 0;
    for(var f=0;f<FILTERS.length;f++) if(FILTERS[f].id === filter) i = f;
    i = (i + (k === 39 ? 1 : -1) + FILTERS.length) % FILTERS.length;
    filter = FILTERS[i].id;
    load(path);
    ev.preventDefault();
  }
  else if(BACK.indexOf(k) >= 0){
    if(parent !== null) load(parent);
    ev.preventDefault();
  }
  else if(k === 32 || k === 179){
    if(au.src){ if(au.paused) au.play(); else au.pause(); }
    ev.preventDefault();
  }
  else if(k === 176) step(1);
  else if(k === 177) step(-1);
  else if(k === 178){ au.pause(); }
});

load('');
</script>
</body>
</html>
"""


# ---------------------------------------------------------------- Start

def main():
    global ROOT
    ap = argparse.ArgumentParser(description='Medienserver fuer den TV-Browser')
    ap.add_argument('dir', nargs='?', default='.', help='Wurzelverzeichnis der Medien')
    ap.add_argument('--port', type=int, default=8000, help='Port (Vorgabe 8000)')
    ap.add_argument('--bind', default='0.0.0.0', help='Adresse (Vorgabe 0.0.0.0)')
    args = ap.parse_args()

    ROOT = os.path.abspath(args.dir)
    if not os.path.isdir(ROOT):
        sys.exit('Kein Verzeichnis: %s' % ROOT)

    srv = ThreadingHTTPServer((args.bind, args.port), Handler)
    srv.daemon_threads = True
    print('Medien aus : %s' % ROOT)
    print('Am TV oeffnen: http://%s:%d' % (local_ip(), args.port))
    print('Beenden mit Strg-C')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\nGestoppt.')
        srv.server_close()


if __name__ == '__main__':
    main()
