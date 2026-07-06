#!/usr/bin/env python3
"""Split an mbox file into individual .eml files.

mbox format (mboxrd variant, used by Thunderbird):
- Messages are concatenated in a single text file
- Each message starts with a separator line: "From <sender> <timestamp>\n"
  e.g. "From user@example.com Thu Jul 06 10:00:00 2026"
- This "From " line is NOT part of the email (it's the envelope marker)
- After the separator: standard RFC 2822 headers, blank line, then body
- In the body, lines starting with "From " are escaped to ">From "
  (mboxrd adds one ">" per nesting level, so ">From " -> ">>From " etc.)
- Messages are separated by a single blank line before the next "From " line
- Thunderbird also creates .msf (index) files alongside, which we ignore

Each extracted .eml contains the raw RFC 2822 message (headers + body),
with the mboxrd ">From " escaping reversed.
"""

import sys
import os
import re

# mbox "From " separator: "From " at line start, followed by an email-ish
# address and a date. We keep it simple — the key marker is "From " at col 0
# after a blank line (or at file start).
FROM_LINE = re.compile(rb'^From \S+.*\d{4}')


def extract_subject(raw_headers: bytes) -> str:
    """Extract Subject from raw header bytes for filename generation."""
    for line in raw_headers.split(b'\n'):
        if line.lower().startswith(b'subject:'):
            # Handle encoded subjects minimally — just grab the text
            subj = line.split(b':', 1)[1].strip()
            try:
                return subj.decode('utf-8', errors='replace')
            except Exception:
                return subj.decode('ascii', errors='replace')
    return "no_subject"


def unescape_mboxrd(line: bytes) -> bytes:
    """Reverse mboxrd escaping: strip one leading '>' from '>From ' lines.

    mboxrd rule: any line in the body matching /^>*From / had one '>'
    prepended when stored. So we strip exactly one leading '>'.
    Example: ">From " -> "From ", ">>From " -> ">From "
    """
    if line.startswith(b'>From ') or line.startswith(b'>>From '):
        return line[1:]
    return line


def sanitize_filename(name: str, max_len: int = 80) -> str:
    safe = "".join(c if c.isalnum() or c in " -_." else "_" for c in name)
    return safe[:max_len].strip() or "no_subject"


def mbox2eml(mbox_path: str, out_dir: str = None):
    if not os.path.isfile(mbox_path):
        print(f"Fehler: {mbox_path} nicht gefunden")
        sys.exit(1)

    if out_dir is None:
        out_dir = os.path.splitext(mbox_path)[0] + "_eml"
    os.makedirs(out_dir, exist_ok=True)

    file_size = os.path.getsize(mbox_path)
    print(f"Lese {mbox_path} ({file_size / 1024 / 1024:.1f} MB)...")

    count = 0
    msg_lines: list[bytes] = []      # accumulated lines of current message
    in_message = False

    def write_message():
        """Write accumulated msg_lines as .eml file."""
        nonlocal count
        if not msg_lines:
            return

        count += 1

        # Remove trailing blank lines
        while msg_lines and msg_lines[-1].strip() == b'':
            msg_lines.pop()

        # Unescape mboxrd ">From " in body (after first blank line = end of headers)
        header_done = False
        out_lines = []
        for line in msg_lines:
            if not header_done:
                if line.strip() == b'':
                    header_done = True
                out_lines.append(line)
            else:
                out_lines.append(unescape_mboxrd(line))

        raw = b''.join(out_lines)

        # Extract subject for filename
        header_end = raw.find(b'\r\n\r\n')
        if header_end == -1:
            header_end = raw.find(b'\n\n')
        headers = raw[:header_end] if header_end > 0 else raw[:200]
        subj = extract_subject(headers)

        fname = f"{count:06d}_{sanitize_filename(subj)}.eml"
        with open(os.path.join(out_dir, fname), "wb") as f:
            f.write(raw)

        if count % 500 == 0:
            print(f"  {count} Nachrichten verarbeitet...")

    with open(mbox_path, "rb") as f:
        for line in f:
            # Check for "From " separator line
            if line.startswith(b'From ') and FROM_LINE.match(line):
                # Save previous message
                write_message()
                msg_lines = []
                in_message = True
                # The "From " envelope line itself is NOT part of the .eml
                continue

            if in_message:
                msg_lines.append(line)

    # Don't forget the last message
    write_message()

    print(f"Fertig: {count} .eml Dateien in {out_dir}/")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <mbox-datei> [ausgabe-ordner]")
        sys.exit(1)
    mbox2eml(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
