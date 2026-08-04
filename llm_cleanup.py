"""Optional post-process pass: raw Whisper output -> local Ollama -> cleaned
text. Fixes filler words/punctuation and corrects known terms Whisper tends
to mangle (e.g. "cloud code" -> "Claude Code" — see bench/ findings,
2026-08-04: all three model sizes shared this blind spot, it's a vocabulary
gap, not something a bigger Whisper model fixes).

Best-effort by design: any failure (Ollama not running, timeout, a reply
that looks off) falls back to the original transcript rather than blocking
dictation. This is an enhancement, never a dependency.
"""
import requests

from config import LLMCleanupConfig

SYSTEM_PROMPT_TEMPLATE = (
    "You clean up raw speech-to-text output. Fix filler words (um, uh), "
    "punctuation, and obvious transcription errors. Correct these known "
    "terms if you see a near-miss/phonetic mistake for one of them: "
    "{known_terms}. Keep the meaning and wording otherwise unchanged - do "
    "not paraphrase, summarize, or add anything. Output ONLY the corrected "
    "text, nothing else, no preamble, no quotes around it."
)


def clean_up(text: str, cfg: LLMCleanupConfig) -> str:
    if not text.strip():
        return text

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        known_terms=", ".join(cfg.known_terms) if cfg.known_terms else "(none specified)")

    try:
        resp = requests.post(
            f"{cfg.ollama_host}/v1/chat/completions",
            json={
                "model": cfg.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                "temperature": 0.1,
                "stream": False,
            },
            timeout=cfg.timeout_seconds,
        )
        resp.raise_for_status()
        cleaned = resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[flowtype] LLM cleanup skipped ({e}), using raw transcript")
        return text

    # Sanity guard: a wildly different length means the model probably went
    # off-script (refused, added commentary, repeated itself) - small local
    # models do this. Don't trust it, fall back to the raw transcript.
    if not cleaned or len(cleaned) > len(text) * 3 or len(cleaned) < len(text) * 0.3:
        print("[flowtype] LLM cleanup output looked unreliable, using raw transcript")
        return text

    return cleaned
