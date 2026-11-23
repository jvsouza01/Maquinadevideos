"""Motor de sincronia por palavra-gatilho (Word-Cue Engine) para HyperFrames.

Extrai timestamps exatos de WordBoundary (edge-tts) e resolve:
- gatilhos de entrada de sub-elementos das artes (cues)
- trocas de pose intra-cena do mascote (pose_cues)
- janelas de articulacao labial / balanco de cabeca (speech envelopes)
- chunks de legenda pill sem sobreposicao temporal
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any


def normalize_token(text: str) -> str:
    """Normaliza palavra para busca robusta (sem acentos, lowercase, alfanumerica)."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", stripped)


def resolve_word_cue(
    words: list[dict[str, Any]],
    cue_word: str | None,
    fallback_ratio: float,
    scene_start: float,
    scene_dur: float,
    after_time: float = 0.0,
) -> float:
    """Retorna o instante absoluto (s) em que `cue_word` ocorre na locucao da cena.

    Se `cue_word` for None ou nao encontrado, usa `scene_start + scene_dur * fallback_ratio`.
    """
    fallback = round(scene_start + max(0.05, min(scene_dur - 0.15, scene_dur * fallback_ratio)), 3)
    if not cue_word or not words:
        return max(fallback, round(after_time, 3))

    target = normalize_token(cue_word)
    if not target:
        return max(fallback, round(after_time, 3))

    # Suporta multi-palavra no cue_word (pega primeira palavra que casa apos after_time)
    target_parts = [normalize_token(p) for p in cue_word.split() if normalize_token(p)]
    first_target = target_parts[0] if target_parts else target

    for idx, w in enumerate(words):
        abs_t = round(scene_start + w["start"], 3)
        if abs_t + 0.02 < after_time:
            continue
        tok = normalize_token(w["text"])
        if not tok:
            continue
        if tok == first_target or first_target in tok or (len(tok) >= 3 and tok in first_target):
            # Se cue tem 2+ palavras, valida proxima palavra quando disponivel
            if len(target_parts) > 1 and idx + 1 < len(words):
                next_tok = normalize_token(words[idx + 1]["text"])
                if target_parts[1] in next_tok or next_tok in target_parts[1]:
                    return abs_t
            return abs_t

    return max(fallback, round(after_time, 3))


def build_speech_envelopes(
    words: list[dict[str, Any]],
    scene_start: float,
    min_gap: float = 0.06,
) -> list[dict[str, float]]:
    """Gera pulsos de fala [start, end, strength] para lip-sync e head-nodding."""
    envelopes: list[dict[str, float]] = []
    for w in words:
        ws = round(scene_start + w["start"], 3)
        we = round(scene_start + w["end"], 3)
        dur = we - ws
        if dur < 0.05:
            we = round(ws + 0.08, 3)
        if envelopes and ws - envelopes[-1]["end"] < min_gap:
            # Mantem separacao minima para ataque de boca visivel
            ws = round(max(ws, envelopes[-1]["end"] + 0.02), 3)
            if we <= ws:
                we = round(ws + 0.07, 3)
        strength = 1.0 if len(normalize_token(w["text"])) >= 4 else 0.72
        envelopes.append({"start": ws, "end": we, "strength": strength})
    return envelopes


def group_caption_chunks(
    words: list[dict[str, Any]],
    scene_start: float,
    scene_end: float,
    max_words: int = 3,
    max_chars: int = 19,
) -> list[dict[str, Any]]:
    """Agrupa palavras em pills curtos (2-3 palavras) sem sobreposicao temporal."""
    if not words:
        return []
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    char_len = 0
    for w in words:
        w_text = w["text"]
        projected = char_len + len(w_text) + (1 if current else 0)
        if current and (len(current) >= max_words or projected > max_chars):
            chunks.append(current)
            current = [w]
            char_len = len(w_text)
        else:
            current.append(w)
            char_len = projected
    if current:
        chunks.append(current)

    result: list[dict[str, Any]] = []
    for i, grp in enumerate(chunks):
        abs_words = [
            {
                "text": w["text"],
                "start": round(scene_start + w["start"], 3),
                "end": round(scene_start + w["end"], 3),
            }
            for w in grp
        ]
        c_start = abs_words[0]["start"]
        if i + 1 < len(chunks):
            next_start = round(scene_start + chunks[i + 1][0]["start"], 3)
            raw_end = max(abs_words[-1]["end"] + 0.04, next_start - 0.01)
            c_end = min(raw_end, next_start - 0.01)
        else:
            c_end = min(scene_end - 0.02, max(abs_words[-1]["end"] + 0.14, c_start + 0.35))
        c_end = round(min(c_end, scene_end - 0.01), 3)
        if c_end <= c_start:
            c_end = round(c_start + 0.18, 3)
        result.append(
            {
                "start": c_start,
                "duration": round(c_end - c_start, 3),
                "words": abs_words,
            }
        )
    return result
