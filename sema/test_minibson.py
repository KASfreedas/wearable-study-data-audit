"""Minimal fixture for the hand-written BSON reader.

The reader is upstream of the study clock, so it needs a test that does not
depend on the real file. Synthetic documents with known values, asserted
exactly; then shape assertions against the real export.
Not a BSON library — just enough to prove the reader is not subtly wrong.
"""
import struct, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import minibson

def _cstr(s): return s.encode() + b"\x00"

def _doc(pairs):
    """Build a BSON document from (type_byte, name, encoded_value) triples."""
    body = b"".join(bytes([t]) + _cstr(n) + v for t, n, v in pairs) + b"\x00"
    return struct.pack("<i", len(body) + 4) + body

def _str(s):
    b = s.encode() + b"\x00"
    return struct.pack("<i", len(b)) + b

def test_reader_round_trips_known_values(tmp_path):
    inner = _doc([
        (0x02, "SCHEDULED_TS", _str("2021-12-15T15:16:00")),
        (0x0A, "EXPIRED_TS",   b""),                       # null
        (0x10, "STUDY_VERSION", struct.pack("<i", 5)),
        (0x01, "TOTAL_RT",      struct.pack("<d", 10.5)),
        (0x08, "FLAG",          b"\x01"),                  # true
    ])
    doc = _doc([
        (0x07, "_id",     bytes(range(12))),
        (0x02, "user_id", _str("621e2f1b67b776a240b3d87c")),
        (0x03, "data",    inner),
    ])
    f = tmp_path / "t.bson"; f.write_bytes(doc + doc)      # two records
    out = minibson.read(f)

    assert len(out) == 2, "document boundary handling is wrong"
    d = out[0]
    assert d["user_id"] == "621e2f1b67b776a240b3d87c"
    assert d["_id"] == bytes(range(12)).hex()
    assert d["data"]["SCHEDULED_TS"] == "2021-12-15T15:16:00"
    assert d["data"]["EXPIRED_TS"] is None, "null must survive as None, not vanish"
    assert d["data"]["STUDY_VERSION"] == 5
    assert d["data"]["TOTAL_RT"] == 10.5
    assert d["data"]["FLAG"] is True
    assert out[1] == out[0], "second document must parse identically"

def test_limit_stops_early(tmp_path):
    doc = _doc([(0x02, "user_id", _str("x"))])
    f = tmp_path / "t.bson"; f.write_bytes(doc * 5)
    assert len(minibson.read(f, limit=3)) == 3

def test_type_census_sees_every_type_at_every_depth(tmp_path):
    """type_census is what lets the suite assert that only covered reader
    branches are exercised, so it must itself find nested types."""
    inner = _doc([(0x02, "s", _str("x")), (0x0A, "n", b""), (0x10, "i", struct.pack("<i", 1))])
    doc = _doc([(0x07, "_id", bytes(range(12))), (0x03, "data", inner),
                (0x01, "d", struct.pack("<d", 1.0))])
    f = tmp_path / "c.bson"; f.write_bytes(doc)
    assert minibson.type_census(f) == {0x07, 0x03, 0x01, 0x02, 0x0A, 0x10}, \
        "nested subdocument types must be counted, not skipped"


REAL = Path(__file__).resolve().parent.parent / "data" / "sema.bson"

def test_real_sema_export_shape():
    if not REAL.exists():
        import pytest; pytest.skip("sema.bson not staged")
    docs = minibson.read(REAL)
    assert len(docs) == 15380
    assert len({d["user_id"] for d in docs}) == 63
    for k in ("SCHEDULED_TS", "COMPLETED_TS", "EXPIRED_TS"):
        assert k in docs[0]["data"]
