import collections, struct, zlib, os
from pathlib import Path


def read_png(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    offset = 8
    compressed = bytearray()
    while offset < len(data):
        size = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4 : offset + 8]
        chunk = data[offset + 8 : offset + 8 + size]
        offset += 12 + size
        if kind == b"IHDR":
            w, h, depth, typ, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
        if kind == b"IDAT":
            compressed.extend(chunk)
    assert depth == 8 and typ in (2, 6) and interlace == 0
    bpp = 3 if typ == 2 else 4
    stride = w * bpp
    raw = zlib.decompress(compressed)
    previous = bytearray(stride)
    rows = []
    for y in range(h):
        start = y * (stride + 1)
        f = raw[start]
        row = bytearray(raw[start + 1 : start + 1 + stride])
        for i in range(stride):
            a = row[i - bpp] if i >= bpp else 0
            b = previous[i]
            c = previous[i - bpp] if i >= bpp else 0
            if f == 1:
                delta = a
            elif f == 2:
                delta = b
            elif f == 3:
                delta = (a + b) // 2
            elif f == 4:
                p = a + b - c
                pa = abs(p - a)
                pb = abs(p - b)
                pc = abs(p - c)
                delta = a if pa <= pb and pa <= pc else b if pb <= pc else c
            else:
                assert f == 0
                delta = 0
            row[i] = (row[i] + delta) & 255
        rows.append(row)
        previous = row
    return w, h, bpp, rows


boxes = []
for phase in range(4):
    w, h, bpp, rows = read_png(
        Path(os.environ.get("CURSOR_PROBE_OUTPUT", ".")) / f"headless-phase{phase}.png"
    )
    count = collections.Counter(
        bytes(row[i : i + 3]) for row in rows for i in range(0, len(row), bpp)
    )
    base = count.most_common(1)[0][0]
    points = [
        (x, y)
        for y, row in enumerate(rows)
        for x in range(w)
        if sum(abs(row[x * bpp + i] - base[i]) for i in range(3)) > 90
    ]
    box = (
        (
            min(x for x, y in points),
            min(y for x, y in points),
            max(x for x, y in points),
            max(y for x, y in points),
        )
        if points
        else None
    )
    print("phase", phase, "cursor bounding box:", box)
    if phase == 1:
        assert box is None, "Hidden cursor must not be drawn"
    else:
        assert box is not None, "Visible cursor missing"
        boxes.append(box)
assert boxes[0][0] < boxes[1][0] < boxes[2][0], "Cursor must move to the right"
assert boxes[0][1] < boxes[1][1] < boxes[2][1], "Cursor must move down"
print(
    "PASS: visible cursor moves, hidden cursor is absent, shape switch remains visible"
)
