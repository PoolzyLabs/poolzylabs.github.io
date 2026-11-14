"""
Build fh6/data.js for the FH6 Test Bench from the "FH6 Track Times" Google Sheet.

Input: a JSON file with two keys, copied straight from the Sheets API values:
  "benchmarks": rows of 'Video Benchmarks'!A5:BA  (one list per car)
  "tracker":    rows of 'Launch Tracker'!A15:I    (for locked episode tags)

Usage:
  python3 tools/build_data.py input.json            -> writes fh6/data.js
  python3 tools/build_data.py input.json --inline   -> also prints the inline <script> for the Claude artifact

Never publishes the internal Heaven best lap (column Q).
"""
import json, sys, datetime, pathlib

# Public notes shown in lab reports, keyed by (make, model)
NOTES = {
    ("Gordon Murray Automotive", "T.50"): "Ships on semi-slicks, so the tire swap changes nothing.",
}

def num(s):
    s = str(s if s is not None else "").replace(",", "").replace("%", "").strip()
    if not s:
        return None
    try:
        f = float(s)
        return int(f) if f.is_integer() else f
    except ValueError:
        return None

def build(benchmarks, tracker):
    episodes = []
    for r in tracker:
        r = list(r) + [""] * 9
        if r[8].endswith("(locked)"):
            episodes.append((r[0], r[1], r[2], r[8].replace("(locked)", "").strip()))
    cars = []
    for r in benchmarks:
        r = list(r) + [""] * 53
        if not r[1] or not r[2]:
            continue
        o = {"y": num(r[0]) or r[0], "mk": r[1], "md": r[2]}
        for key, i in (("co", 3), ("ty", 4), ("dt", 5), ("sc", 7), ("body", 8), ("sf", 9),
                       ("hok", 11), ("lc", 14), ("li7", 15), ("tire", 20)):
            if str(r[i]).strip():
                o[key] = str(r[i]).strip()
        for key, i in (("sp", 6), ("lp", 13), ("hp", 21), ("tq", 22), ("wt", 23), ("fw", 24),
                       ("cc", 26), ("z60", 27), ("z100", 28), ("top", 29)):
            v = num(r[i])
            if v is not None:
                o[key] = v
        rs = [num(x) for x in r[34:40]]
        if all(v is not None for v in rs):
            o["rS"] = rs
        rt = [num(x) for x in r[47:53]]
        if all(v is not None for v in rt):
            o["rT"] = rt
        for y, mk, md, ep in episodes:
            if mk == r[1] and md == r[2] and (not y or str(y) == str(r[0])):
                o["ep"] = ep
        if (r[1], r[2]) in NOTES:
            o["note"] = NOTES[(r[1], r[2])]
        cars.append(o)
    return cars

def to_js(cars, updated):
    lines = ",\n".join(" " + json.dumps(c, ensure_ascii=False, separators=(",", ":")) for c in cars)
    return f'window.FH6_UPDATED = "{updated}";\nwindow.FH6_RAW = [\n{lines}\n];\n'

if __name__ == "__main__":
    src = json.load(open(sys.argv[1], encoding="utf-8"))
    cars = build(src["benchmarks"], src.get("tracker", []))
    js = to_js(cars, datetime.date.today().isoformat())
    out = pathlib.Path(__file__).resolve().parent.parent / "fh6" / "data.js"
    out.write_text(js, encoding="utf-8")
    print(f"Wrote {out} with {len(cars)} cars")
    if "--inline" in sys.argv:
        pathlib.Path(out.parent / "data.inline.html").write_text(f'<script id="fh6-data">\n{js}</script>\n', encoding="utf-8")
        print("Wrote fh6/data.inline.html (paste-in block for the Claude artifact; do not commit)")
