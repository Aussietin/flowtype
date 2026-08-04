"""
Compares tiny.en / base.en / small.en on identical synthetic audio (Windows
SAPI TTS reading bench/ground_truth.txt) and scores each against the known
transcript via word error rate. Isolates the model-size question from
voice/mic variability — run bench/generate_test_audio.ps1 first.

Usage:
    venv\\Scripts\\python.exe bench\\benchmark_models.py
"""
import re
import time
from pathlib import Path

from faster_whisper import WhisperModel

BENCH_DIR = Path(__file__).resolve().parent
AUDIO_PATH = BENCH_DIR / "test_audio.wav"
GROUND_TRUTH_PATH = BENCH_DIR / "ground_truth.txt"
MODEL_SIZES = ["tiny.en", "base.en", "small.en"]


def normalize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text.split()


def word_error_rate(reference: list[str], hypothesis: list[str]) -> float:
    """Classic Levenshtein-based WER: (substitutions + deletions + insertions) / len(reference)."""
    r, h = len(reference), len(hypothesis)
    d = [[0] * (h + 1) for _ in range(r + 1)]
    for i in range(r + 1):
        d[i][0] = i
    for j in range(h + 1):
        d[0][j] = j
    for i in range(1, r + 1):
        for j in range(1, h + 1):
            cost = 0 if reference[i - 1] == hypothesis[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1,      # deletion
                d[i][j - 1] + 1,      # insertion
                d[i - 1][j - 1] + cost,  # substitution
            )
    return d[r][h] / max(len(reference), 1)


def main():
    if not AUDIO_PATH.exists():
        raise SystemExit(f"missing {AUDIO_PATH} — run generate_test_audio.ps1 first")

    ground_truth = GROUND_TRUTH_PATH.read_text(encoding="utf-8").strip()
    reference = normalize(ground_truth)

    print(f"Ground truth ({len(reference)} words):\n  {ground_truth}\n")
    print(f"{'model':<10} {'WER':>7} {'load+run (s)':>13}  transcript")
    print("-" * 100)

    for size in MODEL_SIZES:
        t0 = time.time()
        model = WhisperModel(size, device="cpu", compute_type="int8")
        segments, _info = model.transcribe(str(AUDIO_PATH), language="en", vad_filter=True)
        text = "".join(s.text for s in segments).strip()
        elapsed = time.time() - t0

        wer = word_error_rate(reference, normalize(text))
        print(f"{size:<10} {wer:>6.1%} {elapsed:>13.1f}  {text}")


if __name__ == "__main__":
    main()
