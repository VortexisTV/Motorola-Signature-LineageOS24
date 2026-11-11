#!/usr/bin/env python3
"""Static checks for microG in the built image (microg/README.md).

    validate-microg.py --product-out <out/target/product/...> --tree <source tree> --reports <dir>
        [--fwb-manifest <frameworks/base/core/res/AndroidManifest.xml>]

Checks:
  microg.apks          both APKs are in the image and are the pinned release files (or at least
                       still carry microG's signature)
  microg.signer        the APKs' signing certificate is one LineageOS's framework accepts for
                       signature spoofing (read from the tree's frameworks/base)
  microg.debuggable    the spoofing is compiled in: MicrogUtils.isDebuggable() returns true in the
                       image (a compile-time flag of userdebug/eng builds, not ro.debuggable)
  microg.fake_signature  both manifests declare the fake-signature metadata
  microg.privapp       every privileged permission the APKs request is allowlisted, nothing more
  microg.sysconfig     the power/location exemptions are installed

Static evidence only: nothing here shows that apps accept microG on the phone.
"""
import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from motofw import apk, axml  # noqa: E402
from motofw.report import Report  # noqa: E402

AREA = "microg"
APPS = {
    "com.google.android.gms": "/system/product/priv-app/GmsCore/GmsCore.apk",
    "com.android.vending": "/system/product/priv-app/MicrogCompanion/MicrogCompanion.apk",
}
PINNED = {  # scripts/fetch-microg.sh
    "com.google.android.gms": "e5e6cba078bdec812b5450599350e5c1a12c8b7438da5bf77123af170f8c1a35",
    "com.android.vending": "9b8616011cc8f026bcbbe094df850794abb9d6d9f23214d7a8f8c4d1033ea012",
}
ALLOWLIST = "/system/product/etc/permissions/privapp-permissions-vantage-microg.xml"
SYSCONFIG = "/system/product/etc/sysconfig/sysconfig-vantage-microg.xml"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def manifest(path):
    with zipfile.ZipFile(path) as z:
        return axml.parse(z.read("AndroidManifest.xml"))


def lineage_microg_certs(tree: Path):
    """SHA-256 digests of the certificates LineageOS's microG check accepts, from the source."""
    fwb = tree / "frameworks" / "base"
    sources = [p for p in fwb.rglob("*.java") if "microg" in p.name.lower()] if fwb.is_dir() else []
    if not sources:
        sources = [p for p in (fwb / "services").rglob("*.java")
                   if "microg" in p.read_text(errors="ignore").lower()] if fwb.is_dir() else []
    digests, used = set(), []
    for src in sources:
        text = src.read_text(errors="ignore")
        # MicrogUtils.REAL_SIGNATURE is microG's release certificate (exact match required);
        # FAKE_SIGNATURE is Google's, the one microG may claim. Only the former may sign the APKs.
        m = re.search(r'REAL_SIGNATURE\s*=\s*new Signature\("([0-9a-fA-F]+)"\)', text)
        if m:
            digests.add(hashlib.sha256(bytes.fromhex(m.group(1))).hexdigest())
            used.append(f"{src.relative_to(tree)} (REAL_SIGNATURE)")
    return digests, used


def unstripped(out: Path, tree: Path, rel: str, module_dir: str):
    """Unstripped copy of an image binary: symbols/ if the build wrote it, else Soong's intermediates."""
    cand = [out / "symbols" / rel]
    base = tree / "out/soong/.intermediates" / module_dir
    if base.is_dir():
        cand += sorted(base.glob("android_arm64_*/unstripped/" + Path(rel).name))
    return next((c for c in cand if c.is_file()), None)


def debuggable_in_binary(out: Path, tree: Path):
    """(status, summary, details): does android::isDebuggable() of MicrogUtils return true?"""
    import subprocess
    tools = sorted(tree.glob("prebuilts/clang/host/linux-x86/clang-r*/bin"))
    image = out / "system/lib64/libandroid_runtime.so"
    syms = unstripped(out, tree, "system/lib64/libandroid_runtime.so", "frameworks/base/core/jni/libandroid_runtime")
    if not tools or not image.is_file() or syms is None:
        return "UNKNOWN", "libandroid_runtime.so, its unstripped copy or the LLVM tools not found", []
    bin_ = tools[-1]
    run = lambda *c: subprocess.run([str(x) for x in c], capture_output=True, text=True).stdout
    bid = lambda p: (re.search(r"Build ID: ([0-9a-f]+)", run(bin_ / "llvm-readelf", "-n", p)) or [None, None])[1]
    if bid(image) is None or bid(image) != bid(syms):
        return "UNKNOWN", "the unstripped libandroid_runtime.so is not the image's (Build ID differs)", [str(syms)]
    # The JNI function of MicrogUtils: android::isDebuggable(JNIEnv*, jclass), file-local.
    names = [l.split()[2] for l in run(bin_ / "llvm-nm", "--defined-only", syms).splitlines()
             if len(l.split()) == 3 and l.split()[2].startswith("_ZN7androidL12isDebuggableEP7_JNIEnvP7_jclass")]
    if len(names) != 1:
        return "UNKNOWN", "android::isDebuggable(JNIEnv*, jclass) not found exactly once", names
    dis = run(bin_ / "llvm-objdump", "-d", "--no-show-raw-insn", "--disassemble-symbols=" + names[0], syms)
    body = [" ".join(l.split(":", 1)[1].split("//")[0].split()) for l in dis.splitlines()
            if re.match(r"^\s+[0-9a-f]+:", l)]
    details = [f"libandroid_runtime.so Build ID {bid(image)}; {names[0]}: {'; '.join(body)}"]
    if body[:2] == ["mov w0, #0x1", "ret"]:
        return "PASS", ("LineageOS's microG check is compiled in: MicrogUtils.isDebuggable() in the image's "
                        "libandroid_runtime.so returns the constant true"), details
    if body[:2] in (["mov w0, wzr", "ret"], ["mov w0, #0x0", "ret"]):
        return "FAIL", "MicrogUtils.isDebuggable() returns false: microG's signature spoofing is compiled out", details
    return "UNKNOWN", "MicrogUtils.isDebuggable() is not a constant", details


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--product-out", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--reports", required=True)
    ap.add_argument("--fwb-manifest")
    a = ap.parse_args()
    out, tree = Path(a.product_out), Path(a.tree)
    r = Report("microG")

    host = {pkg: out / rel.lstrip("/") for pkg, rel in APPS.items()}
    missing = [rel for pkg, rel in APPS.items() if not host[pkg].exists()]
    if missing:
        r.fail("microg.apks", "microG APKs missing from the image", missing, AREA)
        r.write(a.reports, "microg")
        r.print_summary()
        return 1
    certs, notes = {}, []
    for pkg, path in host.items():
        certs[pkg] = apk.signing_info(path).get("cert_sha256")
        same = sha256(path) == PINNED[pkg]
        notes.append(f"{pkg}: {'identical to the pinned release file' if same else 'differs from the pinned file'}; "
                     f"signer {certs[pkg]}")
    if len(set(certs.values())) == 1 and None not in certs.values():
        r.passed("microg.apks", "both microG APKs are in /product/priv-app and signed by the same key", notes, AREA)
    else:
        r.fail("microg.apks", "microG APKs are unsigned or signed by different keys", notes, AREA)

    accepted, srcs = lineage_microg_certs(tree)
    if not accepted:
        r.unknown("microg.signer", "no microG certificate found in the tree's frameworks/base", srcs, AREA)
    elif set(certs.values()) <= accepted:
        r.passed("microg.signer", "the APKs are signed with a certificate LineageOS accepts for microG",
                 [f"source: {', '.join(srcs)}"], AREA)
    else:
        r.fail("microg.signer", "the APKs' certificate is not the one LineageOS accepts: apps would not "
               "recognise microG", [f"APK {c}" for c in set(certs.values())] + [f"source: {', '.join(srcs)}"], AREA)

    props = {}
    for bp in ("system/build.prop", "system/product/etc/build.prop", "system/system_ext/etc/build.prop"):
        p = out / bp
        if p.exists():
            for line in p.read_text(errors="replace").splitlines():
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    props.setdefault(k.strip(), v.strip())
    # MicrogUtils.isDebuggable() is native (core/jni/com_android_internal_content_MicrogUtils.cpp):
    # it returns the compile-time flag ANDROID_DEBUGGABLE, which Soong sets for userdebug and eng
    # builds. The run-time property ro.debuggable does not enter: LineageOS's userdebug builds set
    # it to 0 (PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG). So look at the compiled function itself.
    status, text, details = debuggable_in_binary(out, tree)
    details.append(f"ro.build.type={props.get('ro.build.type')}, ro.debuggable={props.get('ro.debuggable')} "
                   "(run-time property; 0 means no adb root, it does not affect microG)")
    if status == "PASS" and props.get("ro.build.type") in ("userdebug", "eng"):
        r.passed("microg.debuggable", text, details, AREA)
    elif status == "FAIL" or props.get("ro.build.type") == "user":
        r.fail("microg.debuggable", text if status == "FAIL" else "user build: LineageOS compiles microG's "
               "signature spoofing out", details, AREA)
    else:
        r.unknown("microg.debuggable", text, details, AREA)

    fake = []
    for pkg, path in host.items():
        root = manifest(path)
        names = {m.get("name") for m in root.iter("meta-data")}
        fake.append(f"{pkg}: {'fake-signature' in names}")
    if all(x.endswith("True") for x in fake):
        r.passed("microg.fake_signature", "both manifests declare fake-signature metadata", fake, AREA)
    else:
        r.fail("microg.fake_signature", "fake-signature metadata missing", fake, AREA)

    allow_path = out / ALLOWLIST.lstrip("/")
    fwb = Path(a.fwb_manifest) if a.fwb_manifest else tree / "frameworks/base/core/res/AndroidManifest.xml"
    if not allow_path.exists() or not fwb.exists():
        r.fail("microg.privapp", "allowlist or framework manifest missing", [str(allow_path), str(fwb)], AREA)
    else:
        levels = {}
        for m in re.finditer(r"<permission\b(.*?)/?>", fwb.read_text(errors="replace"), re.S):
            n = re.search(r'android:name="([^"]+)"', m.group(1))
            lv = re.search(r'android:protectionLevel="([^"]+)"', m.group(1))
            if n:
                levels[n.group(1)] = lv.group(1) if lv else "normal"
        allow = {}
        for block in re.finditer(r'<privapp-permissions package="([^"]+)">(.*?)</privapp-permissions>',
                                 allow_path.read_text(), re.S):
            allow[block.group(1)] = set(re.findall(r'permission name="([^"]+)"', block.group(2)))
        problems, details = [], []
        for pkg, path in host.items():
            req = {u.get("name") for u in manifest(path).iter("uses-permission")}
            priv = {p for p in req if "privileged" in levels.get(p, "")}
            lacking, extra = sorted(priv - allow.get(pkg, set())), sorted(allow.get(pkg, set()) - priv)
            details.append(f"{pkg}: {len(priv)} privileged requested, {len(allow.get(pkg, set()))} allowlisted")
            problems += [f"{pkg}: not allowlisted {p}" for p in lacking] + [f"{pkg}: allowlisted, not needed {p}" for p in extra]
        if problems:
            r.fail("microg.privapp", "privileged-permission allowlist does not match what microG requests "
                   "(a missing entry stops the boot under enforce)", problems, AREA)
        else:
            r.passed("microg.privapp", "allowlist equals the privileged permissions microG requests", details, AREA)

    if (out / SYSCONFIG.lstrip("/")).exists():
        r.passed("microg.sysconfig", "Doze/Data Saver/location exemptions installed", [SYSCONFIG], AREA)
    else:
        r.fail("microg.sysconfig", "sysconfig exemptions missing", [SYSCONFIG], AREA)

    r.write(a.reports, "microg")
    r.print_summary()
    return 1 if any(x["status"] == "FAIL" for x in r.results) else 0


if __name__ == "__main__":
    sys.exit(main())
