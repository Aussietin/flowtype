"""The version shown in flowtype.exe's Properties (build/version_info.txt)
must match the installer's AppVersion (installer.iss). Bump both together."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _iss_version() -> str:
    text = (ROOT / "installer.iss").read_text(encoding="utf-8")
    return re.search(r'#define AppVersion "([^"]+)"', text).group(1)


def _version_info() -> str:
    return (ROOT / "build" / "version_info.txt").read_text(encoding="utf-8")


def _as_four_part(v: str) -> tuple:
    parts = [int(p) for p in v.split(".")]
    return tuple(parts + [0] * (4 - len(parts)))


def test_version_resource_matches_installer():
    want = _as_four_part(_iss_version())
    info = _version_info()
    dotted = ".".join(map(str, want))
    for field in ("filevers", "prodvers"):
        got = re.search(field + r"=\(([^)]*)\)", info).group(1)
        assert tuple(int(x) for x in got.split(",")) == want, field
    assert f"StringStruct('FileVersion', '{dotted}')" in info
    assert f"StringStruct('ProductVersion', '{dotted}')" in info


def test_spec_uses_version_resource_and_no_upx():
    spec = (ROOT / "flowtype.spec").read_text(encoding="utf-8")
    assert "version_info.txt" in spec
    assert "upx=True" not in spec
    assert spec.count("upx=False") >= 2  # EXE and COLLECT
