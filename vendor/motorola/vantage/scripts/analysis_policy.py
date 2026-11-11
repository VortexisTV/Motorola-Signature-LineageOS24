#!/usr/bin/env python3
"""Compile a binary SELinux policy that the host's setools can open, from the inputs init uses.

    analysis_policy.py --secilc SECILC --out POLICY [--exact-out POLICY] [--compare PRECOMPILED]
                       --root /system=DIR --root /system_ext=DIR --root /product=DIR
                       --root /vendor=DIR --root /odm=DIR

Why: Android 17's platform policy has extended-permission rules for netlink messages
(allowx ... (nlmsg ...)) and may name policy capabilities that Ubuntu 24.04's libsepol 3.5 does
not know; setools on that libsepol refuses the whole binary ("Invalid avtab"). Those statements
only narrow permissions inside rules that stay in place (or switch kernel behaviour), so plain
allow and type_transition rules, which is all sepolicy_diff.py reads, are the same with and
without them. The file list and the secilc options are preflight.py's (= init's).

--exact-out also writes the unfiltered policy; --compare checks that one against a precompiled
policy (for stock: odm/etc/selinux/precompiled_sepolicy), to show the inputs are the right ones.
"""
import argparse
import ctypes
import ctypes.util
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from preflight import policy_inputs  # noqa: E402

XPERM = re.compile(r"^\s*\((allowx|auditallowx|dontauditx|neverallowx)\b.*\(nlmsg\b")
POLICYCAP = re.compile(r"^\s*\(policycap\s+([A-Za-z0-9_]+)\s*\)")


def host_knows_policycap():
    lib = ctypes.util.find_library("sepol")
    if not lib:
        return lambda name: True
    sepol = ctypes.CDLL(lib)
    sepol.sepol_polcap_getnum.argtypes = [ctypes.c_char_p]
    return lambda name: sepol.sepol_polcap_getnum(name.encode()) >= 0


def secilc(tool, files, out):
    cmd = [tool, "-m", "-M", "true", "-G", "-N", "-c", "30", "-o", str(out), "-f", "/dev/null"]
    p = subprocess.run(cmd + [str(f) for f in files], capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("secilc failed:\n" + "\n".join((p.stderr or p.stdout).strip().splitlines()[-15:]))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--secilc", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--exact-out")
    ap.add_argument("--compare")
    ap.add_argument("--root", action="append", default=[], metavar="/PREFIX=DIR")
    a = ap.parse_args()
    roots = dict(r.split("=", 1) for r in a.root)

    def one(prefix, rel):
        p = Path(roots[prefix]) / rel if prefix in roots else None
        return p if p is not None and p.exists() else None

    ver, files, missing = policy_inputs(one)
    if missing:
        sys.exit("missing policy inputs: " + ", ".join(missing))
    knows = host_knows_policycap()
    dropped = {"nlmsg extended-permission rules": 0}
    with tempfile.TemporaryDirectory() as tmp:
        if a.exact_out or a.compare:
            exact = Path(a.exact_out) if a.exact_out else Path(tmp) / "exact"
            secilc(a.secilc, files, exact)
            if a.compare:
                same = sha(exact) == sha(a.compare)
                print(f"  unfiltered compile {'equals' if same else 'DIFFERS FROM'} {a.compare} "
                      f"(sha256 {sha(exact)[:16]} vs {sha(a.compare)[:16]})")
        filtered = []
        for i, f in enumerate(files):
            lines = []
            for line in f.read_text(errors="replace").splitlines(keepends=True):
                if XPERM.match(line):
                    dropped["nlmsg extended-permission rules"] += 1
                    continue
                m = POLICYCAP.match(line)
                if m and not knows(m.group(1)):
                    key = f"policycap {m.group(1)}"
                    dropped[key] = dropped.get(key, 0) + 1
                    continue
                lines.append(line)
            g = Path(tmp) / f"{i:02d}-{f.name}"
            g.write_text("".join(lines))
            filtered.append(g)
        secilc(a.secilc, filtered, a.out)
    print(f"  analysis policy for vendor version {ver}: {len(files)} CIL files, removed for the host's libsepol: "
          + ", ".join(f"{k} x{v}" for k, v in dropped.items()))


if __name__ == "__main__":
    main()
