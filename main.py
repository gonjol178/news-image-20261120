#!/usr/bin/env python3
"""Entry program for the World Ledger's 20 November 2026 front page.

The grader runs this file with the repository read-only beside it.  It
proves the bundled ``entry.png`` is a whole, well-formed PNG inside the
competition's limits — every chunk present, every checksum right, no
trailing junk — and only then copies it to the output directory.
Standard library only; no network.
"""

import hashlib
import json
import os
import struct
import sys
import zlib

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1_048_576         # 1 MiB, the competition's ceiling
MAX_SIDE = 1024               # no side of the image may exceed this


class BadImage(Exception):
    """The bundled PNG failed one of the structural checks."""


def walk_chunks(blob):
    """Yield (kind, body) for each PNG chunk, verifying every CRC."""
    if not blob.startswith(PNG_MAGIC):
        raise BadImage("missing PNG signature")
    pos = len(PNG_MAGIC)
    while pos < len(blob):
        if pos + 12 > len(blob):
            raise BadImage("chunk header runs past the end of the file")
        (length,) = struct.unpack(">I", blob[pos:pos + 4])
        kind = blob[pos + 4:pos + 8]
        body = blob[pos + 8:pos + 8 + length]
        if len(body) != length:
            raise BadImage("chunk %r is truncated" % kind)
        (stored_crc,) = struct.unpack(
            ">I", blob[pos + 8 + length:pos + 12 + length])
        if zlib.crc32(kind + body) & 0xFFFFFFFF != stored_crc:
            raise BadImage("checksum mismatch in chunk %r" % kind)
        yield kind, body
        pos += 12 + length
        if kind == b"IEND":
            if pos != len(blob):
                raise BadImage("bytes found after the IEND chunk")
            return
    raise BadImage("no IEND chunk: the image is not whole")


def inspect(path):
    """Return (width, height, size) for a PNG that passes every check."""
    with open(path, "rb") as fh:
        blob = fh.read()
    if len(blob) > MAX_BYTES:
        raise BadImage("image is %d bytes, over the 1 MiB limit" % len(blob))
    kinds = []
    width = height = None
    for kind, body in walk_chunks(blob):
        kinds.append(kind)
        if kind == b"IHDR":
            width, height = struct.unpack(">II", body[:8])
    if kinds[0] != b"IHDR":
        raise BadImage("the first chunk is not IHDR")
    if width > MAX_SIDE or height > MAX_SIDE:
        raise BadImage("image is %dx%d, over the 1024 limit"
                       % (width, height))
    return width, height, len(blob), hashlib.sha256(blob).hexdigest()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    try:
        width, height, size, digest = inspect(source)
    except (OSError, BadImage) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    with open(source, "rb") as fh, open(target, "wb") as out:
        out.write(fh.read())
    print(json.dumps({
        "ok": True,
        "file": target,
        "width": width,
        "height": height,
        "bytes": size,
        "sha256": digest,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
