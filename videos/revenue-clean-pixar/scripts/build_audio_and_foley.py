"""Gera vozes PT-BR (edge-tts + WordBoundary) e Foley procedurais para o criativo 3D Pixar."""
from __future__ import annotations

import asyncio
import json
import math
import random
import struct
import subprocess
import wave
from pathlib import Path
from typing import Any

import edge_tts

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "assets" / "audio"
GEN_DIR = AUDIO_DIR / "generated"

SAMPLE_RATE = 44100


def probe_duration(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return round(float(res.stdout.strip()), 3)


def _write_wav(path: Path, samples: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for s in samples:
            clamped = max(-0.98, min(0.98, s))
            frames.extend(struct.pack("<h", int(clamped * 32767)))
        wf.writeframes(bytes(frames))


def generate_foley_assets() -> dict[str, float]:
    foley: dict[str, float] = {}

    # 1. Elevator Ding (two-tone warm bell chime: 880Hz + 1318Hz)
    ding_dur = 1.15
    n_ding = int(SAMPLE_RATE * ding_dur)
    ding_samples = []
    for i in range(n_ding):
        t = i / SAMPLE_RATE
        env1 = math.exp(-t * 4.5)
        s = 0.42 * env1 * (math.sin(2 * math.pi * 880 * t) + 0.35 * math.sin(2 * math.pi * 1760 * t))
        if t > 0.22:
            t2 = t - 0.22
            env2 = math.exp(-t2 * 4.2)
            s += 0.45 * env2 * (math.sin(2 * math.pi * 1174.66 * t2) + 0.3 * math.sin(2 * math.pi * 2349.32 * t2))
        ding_samples.append(s)
    ding_path = GEN_DIR / "foley_elevator_ding.wav"
    _write_wav(ding_path, ding_samples)
    foley["elevator_ding"] = probe_duration(ding_path)

    # 2. Leather strap squeeze (tactile soft low-mid friction)
    rng = random.Random(42)
    sq_dur = 0.65
    n_sq = int(SAMPLE_RATE * sq_dur)
    sq_samples = []
    lp = 0.0
    for i in range(n_sq):
        t = i / SAMPLE_RATE
        env = math.sin(math.pi * min(1.0, t / sq_dur)) ** 1.4
        noise = rng.uniform(-1.0, 1.0)
        lp = lp * 0.88 + noise * 0.12
        creak = 0.14 * math.sin(2 * math.pi * (170 + 35 * math.sin(t * 14)) * t)
        sq_samples.append(env * (0.45 * lp + creak))
    sq_path = GEN_DIR / "foley_leather_squeeze.wav"
    _write_wav(sq_path, sq_samples)
    foley["leather_squeeze"] = probe_duration(sq_path)

    # 3. Chair wood slide on floor
    ch_dur = 0.85
    n_ch = int(SAMPLE_RATE * ch_dur)
    ch_samples = []
    lp = 0.0
    for i in range(n_ch):
        t = i / SAMPLE_RATE
        env = math.sin(math.pi * min(1.0, t / ch_dur))
        noise = rng.uniform(-1.0, 1.0)
        lp = lp * 0.92 + noise * 0.08
        tone = 0.18 * math.sin(2 * math.pi * (125 - 25 * t) * t)
        ch_samples.append(env * (0.50 * lp + tone))
    ch_path = GEN_DIR / "foley_chair_slide.wav"
    _write_wav(ch_path, ch_samples)
    foley["chair_slide"] = probe_duration(ch_path)

    # 4. Packing tape peel + tissue paper rustle
    tp_dur = 1.05
    n_tp = int(SAMPLE_RATE * tp_dur)
    tp_samples = []
    hp_prev = 0.0
    x_prev = 0.0
    for i in range(n_tp):
        t = i / SAMPLE_RATE
        env = (1.0 - math.exp(-t * 24)) * math.exp(-max(0.0, t - 0.55) * 4.5)
        raw = rng.uniform(-1.0, 1.0)
        hp = 0.82 * (hp_prev + raw - x_prev)
        hp_prev, x_prev = hp, raw
        zip_mod = 0.55 + 0.45 * math.sin(2 * math.pi * 28 * t)
        tp_samples.append(0.38 * env * zip_mod * hp)
    tp_path = GEN_DIR / "foley_tape_peel.wav"
    _write_wav(tp_path, tp_samples)
    foley["tape_peel"] = probe_duration(tp_path)

    return foley


async def _tts_line(text: str, voice: str, rate: str, pitch: str, out_mp3: Path) -> tuple[float, list[dict[str, Any]]]:
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    comm = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    words: list[dict[str, Any]] = []
    buf = bytearray()
    async for ch in comm.stream():
        if ch["type"] == "audio":
            buf.extend(ch["data"])
        elif ch["type"] == "WordBoundary":
            ws = ch["offset"] / 10_000_000.0
            wd = ch["duration"] / 10_000_000.0
            words.append({"text": ch["text"], "start": round(ws, 3), "end": round(ws + max(wd, 0.08), 3)})
    out_mp3.write_bytes(bytes(buf))
    return probe_duration(out_mp3), words


async def synthesize_all() -> None:
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    foley = generate_foley_assets()

    lines_spec = [
        # Cena 1 (0 - 7.5s): Passageira comenta aos ~2.5s
        {
            "id": "c1_passageira",
            "speaker": "Passageira",
            "text": "Gente… vocês tão sentindo um cheiro estranho?",
            "voice": "pt-BR-ThalitaMultilingualNeural",
            "rate": "+2%",
            "pitch": "+3Hz",
        },
        # Cena 2 (7.5 - 17.5s): Marina em off
        {
            "id": "c2_marina_off",
            "speaker": "Marina",
            "text": "Eu já tinha percebido que, às vezes, meu cheiro íntimo ficava mais forte no fim do dia. Depois daquele comentário, comecei até a inventar desculpa pro café.",
            "voice": "pt-BR-FranciscaNeural",
            "rate": "+10%",
            "pitch": "-1Hz",
        },
        # Cena 3 (17.5 - 31.8s): Bia -> Marina -> Bia
        {
            "id": "c3_bia_1",
            "speaker": "Bia",
            "text": "Você tá fugindo de mim?",
            "voice": "pt-BR-ThalitaMultilingualNeural",
            "rate": "+6%",
            "pitch": "+2Hz",
        },
        {
            "id": "c3_marina_2",
            "speaker": "Marina",
            "text": "De você, não. É que tem dias em que eu fico com medo de alguém sentir meu cheiro.",
            "voice": "pt-BR-FranciscaNeural",
            "rate": "+6%",
            "pitch": "-1Hz",
        },
        {
            "id": "c3_bia_3",
            "speaker": "Bia",
            "text": "Tá. Posso sentar aqui com você?",
            "voice": "pt-BR-ThalitaMultilingualNeural",
            "rate": "+2%",
            "pitch": "+1Hz",
        },
        # Cena 4 (31.8 - 44.2s): Marina em off + Locucao final
        {
            "id": "c4_marina_off",
            "speaker": "Marina",
            "text": "Quando chegou, eu tava tão curiosa que abri ali mesmo, antes de tirar o casaco.",
            "voice": "pt-BR-FranciscaNeural",
            "rate": "+10%",
            "pitch": "+0Hz",
        },
        {
            "id": "c4_locucao",
            "speaker": "Locução",
            "text": "Conheça Revenue Clean, voltado ao aroma íntimo. Toque em Saiba mais para conhecer o produto e conferir as orientações de uso.",
            "voice": "pt-BR-ThalitaMultilingualNeural",
            "rate": "+14%",
            "pitch": "-1Hz",
        },
    ]

    voices_out: dict[str, Any] = {}
    for spec in lines_spec:
        mp3_path = GEN_DIR / f"{spec['id']}.mp3"
        dur, words = await _tts_line(spec["text"], spec["voice"], spec["rate"], spec["pitch"], mp3_path)
        voices_out[spec["id"]] = {
            "speaker": spec["speaker"],
            "file": f"assets/audio/generated/{mp3_path.name}",
            "duration": dur,
            "words": words,
        }
        print(f"[TTS] {spec['id']}: {dur}s ({len(words)} words)")

    # Build extended 45s BGM cleanly
    bgm_fit = GEN_DIR / "bgm_45s.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(AUDIO_DIR / "bgm.mp3"), "-t", "45.0", "-c:a", "libmp3lame", "-q:a", "4", str(bgm_fit)],
        capture_output=True,
        check=True,
    )

    manifest = {
        "foley": foley,
        "voices": voices_out,
        "bgm_duration": probe_duration(bgm_fit),
    }
    (GEN_DIR / "audio_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[OK] audio_manifest.json written.")


if __name__ == "__main__":
    asyncio.run(synthesize_all())
