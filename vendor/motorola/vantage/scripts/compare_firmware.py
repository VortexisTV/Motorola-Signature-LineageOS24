#!/usr/bin/env python3
"""Compare two analysed stock firmware builds (inventory JSON + extracted trees).

Read-only. Written for the move from W2WVS36.55-95-5-1 (Android 16) to A171WVH.21-16-16
(Android 17), usable for any two builds analysed by analyze_firmware.py.

Usage:
    python3 -I compare_firmware.py --old-inv <dir> --old-fw <dir> --new-inv <dir> --new-fw <dir>
        --pinned <proprietary-files.txt> --props <properties.mk> --out <report.md> [--json <out.json>]

<inv> is a reports/inventory directory (props.json, vintf.json, packages.json, files.json,
permissions.json); <fw> is the extract-firmware output (root/<partition>/...).

Never prints APK meta-data values (stock apps carry API keys there).
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

PARTS = ["system", "system_ext", "product", "vendor", "odm", "vendor_dlkm", "system_dlkm"]
HAL_FOCUS = re.compile(r"radio|ims|camera|audio|qcril|bluetooth|gnss|nfc|biometrics|fingerprint|"
                       r"secure_element|wifi|power|health|graphics\.composer|media\.c2|dsp|cne|data")
APPS_FOCUS = ["com.motorola.camera5", "com.motorola.motosignature.app", "org.codeaurora.ims",
              "com.qualcomm.qti.telephonyservice", "com.qti.phone", "com.android.phone",
              "com.motorola.camera3", "com.motorola.cameraservice"]


def load(d: Path, name: str):
    p = d / name
    return json.loads(p.read_text()) if p.exists() else None


def part_root(fw: Path, part: str) -> Path:
    return fw / "root" / part / ("system" if part == "system" else "")


def read_text(p: Path):
    try:
        return p.read_text(errors="replace").strip()
    except OSError:
        return None


def sha256(p: Path):
    try:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()
    except OSError:
        return None


def prop(props, key):
    for part in PARTS:
        v = (props.get(part) or {}).get(key)
        if v is not None:
            return part, v
    return None, None


def identity(props):
    rows = {}
    for part in PARTS:
        p = props.get(part) or {}
        pre = {"system": "ro.system", "vendor": "ro.vendor", "odm": "ro.odm"}.get(part, f"ro.{part}")
        rows[part] = {
            "fingerprint": p.get(f"{pre}.build.fingerprint") or p.get(f"ro.{part}.build.fingerprint"),
            "id": p.get(f"{pre}.build.id"),
            "sdk": p.get(f"{pre}.build.version.sdk_full") or p.get(f"{pre}.build.version.sdk"),
            "release": p.get(f"{pre}.build.version.release"),
            "spl": p.get("ro.build.version.security_patch") or p.get(f"{pre}.build.security_patch"),
        }
    return rows


def selinux(fw: Path):
    v = part_root(fw, "vendor") / "etc" / "selinux"
    s = part_root(fw, "system") / "etc" / "selinux"
    mapping = sorted(x.name for x in (s / "mapping").glob("*.cil")) if (s / "mapping").is_dir() else []
    vcil = v / "vendor_sepolicy.cil"
    text = read_text(vcil) or ""
    versioned = sorted(set(re.findall(r"\b([a-z0-9_]+)_(20\d{4}|\d{2}\.0)\b", text)))
    return {
        "vendor_plat_sepolicy_vers": read_text(v / "plat_sepolicy_vers.txt"),
        "vendor_genfs_labels_version": read_text(v / "genfs_labels_version.txt"),
        "vendor_sepolicy_cil_sha256": sha256(vcil),
        "vendor_versioned_attributes": len(versioned),
        "vendor_refs_vendor_qtelephony": bool(re.search(r"\bvendor_qtelephony_\d", text)),
        "vendor_refs_moto_camera_app": bool(re.search(r"\bmoto_camera_app_\d", text)),
        "system_mapping_files": mapping,
        "system_plat_sepolicy_genfs": sorted(x.name for x in s.glob("plat_sepolicy_genfs_*.cil")),
    }


def hals(vintf, parts=("vendor", "odm")):
    out = {}
    for part in parts:
        for e in (vintf or {}).get(part, []):
            if e.get("kind") != "manifest":
                continue
            for h in e.get("hals", []):
                key = f"{h['name']} ({h.get('format') or 'hidl'})"
                ent = out.setdefault(key, {"versions": set(), "instances": set(), "files": set()})
                ent["versions"].update(h.get("versions") or [])
                ent["instances"].update(h.get("fqnames") or [])
                ent["files"].add(f"{part}:{e['file']}")
    return {k: {kk: sorted(vv) for kk, vv in v.items()} for k, v in out.items()}


def manifest_levels(vintf):
    out = {}
    for part in ("vendor", "odm", "system"):
        for e in (vintf or {}).get(part, []):
            if e.get("target_level") or e.get("level"):
                out.setdefault(part, []).append(
                    {"file": e["file"], "kind": e["kind"], "target_level": e.get("target_level"),
                     "level": e.get("level"), "sepolicy": e.get("sepolicy")})
    return out


def app_summary(pkgs, name):
    for x in pkgs or []:
        if x.get("package") == name:
            return {
                "path": x.get("path"), "versionName": x.get("versionName"),
                "versionCode": x.get("versionCode"), "minSdk": x.get("minSdkVersion"),
                "targetSdk": x.get("targetSdkVersion"), "sharedUserId": x.get("sharedUserId"),
                "cert": (x.get("signing") or {}).get("cert_sha256"), "sha256": x.get("sha256"),
                "uses_libraries": [(u["name"], u.get("required")) for u in x.get("uses_libraries") or []],
                "uses_permissions": len(x.get("uses_permissions") or []),
                "native_libs": len(x.get("native_libs") or []),
                "size": x.get("size"),
            }
    return None


def libraries(perms):
    out = {}
    for part in PARTS:
        for lib in ((perms or {}).get(part) or {}).get("libraries", []):
            out[lib["name"]] = f"{part}:{lib.get('file')}"
    return out


def pinned(pinned_file: Path, new_files):
    by_path = {f["path"]: f for f in new_files["files"]}
    links = {l["path"]: l["target"] for l in new_files["symlinks"]}
    rows = []
    for line in pinned_file.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        spec, _, sha = line.partition("|")
        rel = spec.split(";")[0]
        flags = spec.split(";")[1:]
        path = "/" + rel
        if path.startswith("/system/"):
            cands = [path, "/system/system/" + rel[len("system/"):]]
        else:
            cands = [path]
        hit = next((by_path[c] for c in cands if c in by_path), None)
        if any(f.startswith("SYMLINK=") for f in flags):
            tgt = next((links[c] for c in cands if c in links), None)
            want = next(f[len("SYMLINK="):] for f in flags if f.startswith("SYMLINK="))
            rows.append({"path": rel, "status": "symlink same" if tgt == want else
                         ("symlink missing" if tgt is None else f"symlink now -> {tgt}")})
            continue
        if hit is None:
            rows.append({"path": rel, "status": "MISSING", "old": sha})
        elif hit.get("sha256") == sha:
            rows.append({"path": rel, "status": "same", "old": sha, "new": hit["sha256"]})
        else:
            rows.append({"path": rel, "status": "changed", "old": sha, "new": hit.get("sha256")})
    return rows


def mk_props(props_mk: Path):
    keys = []
    for line in props_mk.read_text().splitlines():
        m = re.match(r"\s*([a-z][\w.\-]+)=(\S*)", line.strip().rstrip("\\").strip())
        if m:
            keys.append((m.group(1), m.group(2)))
    return keys


def main():
    ap = argparse.ArgumentParser()
    for k in ("old-inv", "old-fw", "new-inv", "new-fw", "pinned", "props", "out"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    oi, ni, ofw, nfw = map(Path, (a.old_inv, a.new_inv, a.old_fw, a.new_fw))
    O = {n: load(oi, n) for n in ("props.json", "vintf.json", "packages.json", "permissions.json", "summary.json")}
    N = {n: load(ni, n) for n in ("props.json", "vintf.json", "packages.json", "permissions.json", "summary.json")}
    new_files = load(ni, "files.json")

    res = {
        "identity": {"old": identity(O["props.json"]), "new": identity(N["props.json"])},
        "api": {},
        "selinux": {"old": selinux(ofw), "new": selinux(nfw)},
        "levels": {"old": manifest_levels(O["vintf.json"]), "new": manifest_levels(N["vintf.json"])},
        "apps": {n: {"old": app_summary(O["packages.json"], n), "new": app_summary(N["packages.json"], n)} for n in APPS_FOCUS},
        "pinned": pinned(Path(a.pinned), new_files),
        "props": [],
    }
    for k in ("ro.board.api_level", "ro.board.first_api_level", "ro.vendor.api_level",
              "ro.product.first_api_level", "ro.vendor.build.version.sdk", "ro.vndk.version",
              "ro.build.version.sdk_full", "ro.build.version.security_patch",
              "ro.vendor.build.security_patch", "ro.media.xml_variant.codecs"):
        res["api"][k] = {"old": prop(O["props.json"], k), "new": prop(N["props.json"], k)}
    ho, hn = hals(O["vintf.json"]), hals(N["vintf.json"])
    res["hals"] = {k: {"old": ho.get(k), "new": hn.get(k)} for k in sorted(set(ho) | set(hn))}
    lo, ln = libraries(O["permissions.json"]), libraries(N["permissions.json"])
    res["libraries"] = {"added": sorted(set(ln) - set(lo)), "removed": sorted(set(lo) - set(ln))}
    for key, mkval in mk_props(Path(a.props)):
        res["props"].append({"key": key, "layer": mkval, "old": prop(O["props.json"], key),
                             "new": prop(N["props.json"], key)})

    L = []
    w = L.append
    w("# Stock firmware comparison\n")
    w("Generated by `scripts/compare_firmware.py` from the two firmware inventories. Static data only.\n")
    w("## Build identity\n")
    w("| Partition | Old build | New build | New SDK | New SPL |")
    w("|---|---|---|---|---|")
    for part in PARTS:
        o, n = res["identity"]["old"][part], res["identity"]["new"][part]
        w(f"| {part} | `{o['fingerprint']}` | `{n['fingerprint']}` | {n['sdk']} | {n['spl'] or ''} |")
    w("\n## API levels and key properties\n")
    w("| Property | Old | New |")
    w("|---|---|---|")
    for k, v in res["api"].items():
        f = lambda t: f"`{t[1]}` ({t[0]})" if t[1] is not None else "unset"
        w(f"| `{k}` | {f(v['old'])} | {f(v['new'])} |")
    w("\n## Manifest / matrix levels\n")
    for side in ("old", "new"):
        for part, ents in res["levels"][side].items():
            for e in ents:
                w(f"- {side} {part} `{e['file']}` {e['kind']}: target-level={e['target_level']} level={e['level']} sepolicy={e['sepolicy']}")
    w("\n## SELinux\n")
    w("| Item | Old | New |")
    w("|---|---|---|")
    for k in res["selinux"]["old"]:
        o, n = res["selinux"]["old"][k], res["selinux"]["new"][k]
        if isinstance(o, list):
            o, n = ", ".join(o) or "none", ", ".join(n) or "none"
        w(f"| {k} | {o} | {n} |")
    w("\n## Vendor/odm HALs (radio, IMS, camera, audio and other hardware families)\n")
    w("| HAL | Old versions | New versions | Instances changed |")
    w("|---|---|---|---|")
    changed = 0
    for k, v in res["hals"].items():
        if not HAL_FOCUS.search(k):
            continue
        o, n = v["old"], v["new"]
        ov = ",".join(o["versions"]) if o else "absent"
        nv = ",".join(n["versions"]) if n else "absent"
        inst = "" if (o and n and o["instances"] == n["instances"]) else "yes"
        if ov != nv or inst:
            changed += 1
        w(f"| `{k}` | {ov or '-'} | {nv or '-'} | {inst} |")
    w(f"\nHAL entries in these families whose version or instances differ: {changed}.\n")
    w("## Apps the port uses or replaces\n")
    for n, v in res["apps"].items():
        o, nn = v["old"], v["new"]
        if not o and not nn:
            continue
        w(f"### `{n}`\n")
        w("| Field | Old | New |")
        w("|---|---|---|")
        for f in ("path", "versionName", "versionCode", "minSdk", "targetSdk", "sharedUserId", "cert", "sha256", "size", "uses_permissions", "native_libs"):
            w(f"| {f} | {(o or {}).get(f, 'absent') if o else 'absent'} | {(nn or {}).get(f, 'absent') if nn else 'absent'} |")
        ol = set(map(tuple, (o or {}).get("uses_libraries", []))) if o else set()
        nl = set(map(tuple, (nn or {}).get("uses_libraries", []))) if nn else set()
        w(f"\nuses-library (new): {', '.join(f'{x[0]}{'' if x[1] else ' (optional)'}' for x in sorted(nl)) or 'none'}")
        if ol != nl:
            w(f"\nuses-library added: {sorted(nl - ol)}; removed: {sorted(ol - nl)}")
        w("")
    w("## Shared libraries declared by the stock system side\n")
    w(f"Added: {', '.join(res['libraries']['added']) or 'none'}\n")
    w(f"Removed: {', '.join(res['libraries']['removed']) or 'none'}\n")
    w("## Files pinned by the Android 16 port (`proprietary-files.txt`)\n")
    w("| File | Status |")
    w("|---|---|")
    for r in res["pinned"]:
        w(f"| `{r['path']}` | {r['status']} |")
    cnt = {}
    for r in res["pinned"]:
        cnt[r["status"]] = cnt.get(r["status"], 0) + 1
    w(f"\nCounts: {cnt}\n")
    w("## Properties set by the Android 16 layer (`properties.mk`) against both stock builds\n")
    w("| Property | Layer value | Old stock | New stock |")
    w("|---|---|---|---|")
    for r in res["props"]:
        f = lambda t: f"`{t[1]}` ({t[0]})" if t[1] is not None else "unset"
        w(f"| `{r['key']}` | `{r['layer']}` | {f(r['old'])} | {f(r['new'])} |")
    Path(a.out).write_text("\n".join(L) + "\n")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1, default=list))
    print(f"written {a.out}: {len(res['pinned'])} pinned files {cnt}, {changed} HAL entries differ")


if __name__ == "__main__":
    main()
