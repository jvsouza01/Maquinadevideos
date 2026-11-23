import os
import subprocess
from collections import Counter

SCRIPT_EVENTS = [
    # (time, type)
    (1.4, "send"),
    (2.8, "receive"),
    (5.8, "send"),
    (8.2, "receive"),
    (10.2, "send"),
    (12.8, "receive"),
    (15.6, "send"),
    (17.6, "receive"),
    (18.9, "receive"),
    (21.0, "receive"),
    (24.0, "send"),
    (25.8, "receive"),
    (27.4, "receive"),
    (29.5, "send"),
    (30.2, "impact"),
]

# Client typing windows to add subtle key clicks
TYPING_WINDOWS = [
    (0.4, 1.4),
    (3.4, 5.8),
    (8.9, 10.2),
    (13.5, 15.6),
    (21.8, 24.0),
    (28.0, 29.5),
]

TOTAL_DURATION = 36.0


def compute_key_times(windows=TYPING_WINDOWS, step=0.15):
    key_times = []
    for start, end in windows:
        curr = start + 0.1
        while curr < end - 0.05:
            key_times.append(round(curr, 2))
            curr += step
    return key_times


def build_filter_complex(script_events=SCRIPT_EVENTS, typing_windows=TYPING_WINDOWS, total_duration=TOTAL_DURATION):
    key_times = compute_key_times(typing_windows)
    event_counts = Counter(evt for _, evt in script_events)

    filter_parts = [
        f"[0:a]volume=0.22,afade=t=in:st=0:d=0.8,afade=t=out:st={total_duration - 2.0:.1f}:d=2.0,"
        f"atrim=0:{total_duration},asetpts=PTS-STARTPTS[a_bgm]"
    ]

    # Split each reused SFX input explicitly to avoid invalid FFmpeg multi-link reuse
    input_map = {"send": "1:a", "receive": "2:a", "impact": "3:a"}
    vol_map = {"send": 0.95, "receive": 0.85, "impact": 1.15}
    sfx_splits = {}
    for evt, stream in input_map.items():
        count = event_counts.get(evt, 0)
        if count > 1:
            labels = [f"[{evt}_src_{i}]" for i in range(count)]
            filter_parts.append(f"[{stream}]asplit={count}{''.join(labels)}")
            sfx_splits[evt] = [f"{evt}_src_{i}" for i in range(count)]
        elif count == 1:
            sfx_splits[evt] = [stream]

    key_count = len(key_times)
    if key_count > 1:
        key_labels = [f"[key_src_{i}]" for i in range(key_count)]
        filter_parts.append(f"[4:a]asplit={key_count}{''.join(key_labels)}")
        key_sources = [f"key_src_{i}" for i in range(key_count)]
    elif key_count == 1:
        key_sources = ["4:a"]
    else:
        key_sources = []

    sfx_delayed = []
    used_idx = Counter()
    for idx, (t, evt) in enumerate(script_events):
        ms = int(round(t * 1000))
        src_label = sfx_splits[evt][used_idx[evt]]
        used_idx[evt] += 1
        out_label = f"sfx_{idx}"
        filter_parts.append(f"[{src_label}]adelay={ms}|{ms},volume={vol_map[evt]}[{out_label}]")
        sfx_delayed.append(f"[{out_label}]")

    key_delayed = []
    for idx, kt in enumerate(key_times):
        ms = int(round(kt * 1000))
        src_label = key_sources[idx]
        out_label = f"key_{idx}"
        filter_parts.append(f"[{src_label}]adelay={ms}|{ms},volume=0.25[{out_label}]")
        key_delayed.append(f"[{out_label}]")

    mix_buses = ["[a_bgm]"]
    if sfx_delayed:
        filter_parts.append(
            f"{''.join(sfx_delayed)}amix=inputs={len(sfx_delayed)}:duration=longest:normalize=0[a_sfx]"
        )
        mix_buses.append("[a_sfx]")
    if key_delayed:
        filter_parts.append(
            f"{''.join(key_delayed)}amix=inputs={len(key_delayed)}:duration=longest:normalize=0[a_keys]"
        )
        mix_buses.append("[a_keys]")

    filter_parts.append(
        f"{''.join(mix_buses)}amix=inputs={len(mix_buses)}:duration=first:dropout_transition=2:normalize=0,"
        f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[outa]"
    )
    return ";".join(filter_parts)


def generate_audio():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, "assets")
    out_audio = os.path.join(base_dir, "final_audio.wav")

    inputs = [
        "-i", os.path.join(assets_dir, "track_berool.mp3"),
        "-i", os.path.join(assets_dir, "sfx_send.wav"),
        "-i", os.path.join(assets_dir, "sfx_receive.wav"),
        "-i", os.path.join(assets_dir, "sfx_impact.wav"),
        "-i", os.path.join(assets_dir, "sfx_key.wav"),
    ]

    fc = build_filter_complex()
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", fc,
        "-map", "[outa]",
        "-t", str(TOTAL_DURATION),
        "-ar", "48000",
        "-ac", "2",
        out_audio,
    ]

    print("Running ffmpeg audio mix...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg Error:", res.stderr[-2000:])
        raise RuntimeError("Audio mix failed")
    print(f"Generated final audio successfully: {out_audio}")
    return out_audio


if __name__ == "__main__":
    generate_audio()
