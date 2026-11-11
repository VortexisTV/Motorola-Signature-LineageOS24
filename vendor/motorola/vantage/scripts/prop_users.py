#!/usr/bin/env python3
"""Which properties set by the stock system side does the stock vendor side read?

Static successor of the Android 16 port's work/propusers.py, which needed a running guest.

Usage:
    python3 -I prop_users.py --fw <extracted stock firmware> --out <json>
        [--ours <build.prop or getprop dump> ...] [--tmp <dir>]

For every property set in the stock /system, /system_ext and /product build.prop files it
records the value(s), and every file of the stock /vendor and /odm trees whose bytes contain the
property name (a reader candidate: init scripts, binaries, libraries, the RIL database). With
--ours (build.prop files of a built image, or an `adb shell getprop` dump) it also records what
the image sets, so that the result lists what the vendor may read and the image lacks.
A name occurring in a vendor file is evidence of a possible reader, not proof: names can be
composed at run time, and a string may be dead code.
"""
import argparse
import collections
import json
import re
import subprocess
import tempfile
from pathlib import Path

SYSTEM_SIDE = (("system", "system/system/build.prop"), ("system_ext", "system_ext/etc/build.prop"),
               ("product", "product/etc/build.prop"))


def read_props(path: Path):
    text = path.read_text(errors="replace")
    if text.lstrip().startswith("["):
        return dict(re.findall(r"^\[([^\]]+)\]: \[(.*)\]\s*$", text, re.M))
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("import") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip().split("?")[0]] = v.strip()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fw", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ours", action="append", default=[])
    ap.add_argument("--tmp")
    a = ap.parse_args()
    fw = Path(a.fw) / "root"
    stock = collections.OrderedDict()
    for part, rel in SYSTEM_SIDE:
        p = fw / rel
        if not p.exists():
            continue
        for k, v in read_props(p).items():
            stock.setdefault(k, []).append([part, v])
    ours = {}
    for f in a.ours:
        ours.update(read_props(Path(f)))

    tmp = Path(a.tmp or tempfile.mkdtemp())
    tmp.mkdir(parents=True, exist_ok=True)
    pat = tmp / "prop-patterns.txt"
    pat.write_text("\n".join(sorted(stock)) + "\n")
    readers = collections.defaultdict(set)
    cmd = ["grep", "-raoF", "-f", str(pat), str(fw / "vendor"), str(fw / "odm")]
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    for line in res.stdout.splitlines():
        f, _, name = line.rpartition(":")
        if f.endswith("build.prop"):
            continue
        readers[name].add(str(Path(f).relative_to(fw)))

    rows = []
    for k, vals in stock.items():
        rows.append({
            "name": k,
            "stock": vals,
            "ours": ours.get(k) if a.ours else None,
            "vendor_readers": sorted(readers.get(k, ()))[:20],
            "vendor_reader_count": len(readers.get(k, ())),
        })
    Path(a.out).write_text(json.dumps(rows, indent=1))
    read = [r for r in rows if r["vendor_reader_count"]]
    print(f"{len(rows)} stock system-side properties; {len(read)} named in stock vendor/odm files")
    if a.ours:
        miss = [r for r in read if r["ours"] is None]
        diff = [r for r in read if r["ours"] is not None and r["ours"] != r["stock"][-1][1]]
        print(f"of those, missing in ours: {len(miss)}; different value in ours: {len(diff)}")


if __name__ == "__main__":
    main()
