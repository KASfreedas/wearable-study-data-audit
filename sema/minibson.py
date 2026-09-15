"""Minimal BSON reader — enough to enumerate fields and sample values.
No pymongo available in this container, so the format is parsed directly.
Spec: https://bsonspec.org/spec.html"""
import struct, datetime

def _cstr(b, i):
    j = b.index(b'\x00', i)
    return b[i:j].decode('utf-8', 'replace'), j+1

def _val(b, i, t):
    if t == 0x01: return struct.unpack_from('<d', b, i)[0], i+8
    if t == 0x02:
        n = struct.unpack_from('<i', b, i)[0]; i += 4
        return b[i:i+n-1].decode('utf-8','replace'), i+n
    if t in (0x03, 0x04):
        n = struct.unpack_from('<i', b, i)[0]
        return _doc(b, i)[0], i+n
    if t == 0x05:
        n = struct.unpack_from('<i', b, i)[0]
        return f'<binary {n}B>', i+5+n
    if t == 0x07: return b[i:i+12].hex(), i+12
    if t == 0x08: return bool(b[i]), i+1
    if t == 0x09:
        ms = struct.unpack_from('<q', b, i)[0]
        try: v = datetime.datetime.utcfromtimestamp(ms/1000)
        except Exception: v = f'<dt {ms}>'
        return v, i+8
    if t == 0x0A: return None, i
    if t == 0x10: return struct.unpack_from('<i', b, i)[0], i+4
    if t in (0x11, 0x12): return struct.unpack_from('<q', b, i)[0], i+8
    if t == 0x13: return '<decimal128>', i+16
    if t == 0x06 or t == 0xFF or t == 0x7F: return None, i
    raise ValueError(f'unhandled bson type 0x{t:02x} at {i}')

def _doc(b, start):
    n = struct.unpack_from('<i', b, start)[0]
    i = start + 4; out = {}
    while b[i] != 0x00:
        t = b[i]; i += 1
        k, i = _cstr(b, i)
        v, i = _val(b, i, t)
        out[k] = v
    return out, start + n

def read(path, limit=None):
    b = open(path, 'rb').read()
    i, docs = 0, []
    while i < len(b):
        d, i = _doc(b, i)
        docs.append(d)
        if limit and len(docs) >= limit: break
    return docs


def type_census(path):
    """Every BSON type byte actually present in the file, at any depth.

    Lets a caller assert that only reader paths covered by the fixture are
    exercised, instead of trusting that the file contains what it did last time.
    """
    b = open(path, 'rb').read()
    seen = set()

    def walk(b, start):
        n = struct.unpack_from('<i', b, start)[0]
        i = start + 4
        while b[i] != 0x00:
            t = b[i]; i += 1
            _, i = _cstr(b, i)
            seen.add(t)
            if t in (0x03, 0x04):
                walk(b, i)
            _, i = _val(b, i, t)
        return start + n

    i = 0
    while i < len(b):
        i = walk(b, i)
    return seen
