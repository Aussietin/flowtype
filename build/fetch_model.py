"""Download the faster-whisper base.en CT2 model into build/model/base.en/ so
the installer can bundle it. Run once before building the freeze:

    venv\\Scripts\\python.exe build\\fetch_model.py

The model dir is ~145 MB and is gitignored — it's a build input, not source.
"""
from pathlib import Path

from huggingface_hub import snapshot_download

DEST = Path(__file__).resolve().parent / "model" / "base.en"
REPO = "Systran/faster-whisper-base.en"


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=REPO,
        local_dir=DEST,
        allow_patterns=["*.bin", "*.json", "*.txt"],
    )
    model_bin = DEST / "model.bin"
    if not model_bin.exists():
        raise SystemExit(f"model.bin missing after download at {DEST}")
    size_mb = model_bin.stat().st_size / 1e6
    print(f"OK — {DEST} ({size_mb:.0f} MB model.bin)")


if __name__ == "__main__":
    main()
