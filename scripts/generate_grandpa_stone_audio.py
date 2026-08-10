"""Generate the original audio cues used by the grandpa-stone theme."""

import math
import wave
from pathlib import Path

import numpy as np


SAMPLE_RATE = 44_100
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "assets" / "themes" / "grandpa-stone" / "audio"
RNG = np.random.default_rng(20260808)


def note_frequency(midi_note):
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def envelope(length, attack=0.02, release=0.08):
    result = np.ones(length, dtype=np.float64)
    attack_samples = min(length, int(SAMPLE_RATE * attack))
    release_samples = min(length, int(SAMPLE_RATE * release))
    if attack_samples:
        result[:attack_samples] = np.linspace(0.0, 1.0, attack_samples, endpoint=False)
    if release_samples:
        result[-release_samples:] = np.linspace(1.0, 0.0, release_samples)
    return result


def tone(frequency, duration, shape="triangle", volume=1.0, vibrato=0.0):
    length = max(1, int(SAMPLE_RATE * duration))
    time = np.arange(length, dtype=np.float64) / SAMPLE_RATE
    phase = 2.0 * math.pi * frequency * time
    if vibrato:
        phase += vibrato * np.sin(2.0 * math.pi * 5.0 * time)

    if shape == "square":
        signal = np.sign(np.sin(phase))
    elif shape == "sine":
        signal = np.sin(phase)
    else:
        signal = 2.0 / math.pi * np.arcsin(np.sin(phase))

    return signal * envelope(length) * volume


def add_clip(track, clip, start_seconds):
    start = int(start_seconds * SAMPLE_RATE)
    end = min(len(track), start + len(clip))
    if end > start:
        track[start:end] += clip[: end - start]


def percussion(duration, kind):
    length = max(1, int(duration * SAMPLE_RATE))
    time = np.arange(length, dtype=np.float64) / SAMPLE_RATE
    noise = RNG.normal(0.0, 1.0, length)
    if kind == "kick":
        phase = 2.0 * math.pi * (80.0 * time - 28.0 * time * time)
        return np.sin(phase) * np.exp(-time * 18.0)
    if kind == "click":
        return noise * np.exp(-time * 55.0)
    return noise * np.exp(-time * 22.0)


def normalize(track, peak=0.9):
    maximum = float(np.max(np.abs(track)))
    if maximum:
        track = track * (peak / maximum)
    return track


def write_wav(path, track):
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(normalize(track), -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(pcm.tobytes())


def make_bgm():
    """Create an original bright electropop/polka homage for the meme theme.

    The arrangement evokes the brisk, buoyant production commonly associated
    with “恩情” edits while deliberately using a newly composed melody.
    """
    beat = 60.0 / 138.0
    step = beat / 2.0
    melody = [
        67, 69, 72, 74, 72, 69, 67, 64,
        65, 67, 69, 72, 69, 67, 65, 60,
        64, 67, 69, 71, 72, 71, 69, 67,
        62, 65, 67, 69, 67, 65, 64, 62,
    ] * 2
    duration = len(melody) * step
    track = np.zeros(int((duration + 0.2) * SAMPLE_RATE), dtype=np.float64)

    chord_roots = (48, 53, 55, 48, 57, 53, 55, 48)

    for index, midi_note in enumerate(melody):
        start = index * step
        lead = tone(note_frequency(midi_note), step * 0.82, "triangle", 0.23, vibrato=0.025)
        brass = tone(note_frequency(midi_note - 12), step * 0.70, "square", 0.055)
        add_clip(track, lead, start)
        add_clip(track, brass, start)

        if index % 2 == 0:
            root = chord_roots[(index // 8) % len(chord_roots)]
            add_clip(track, tone(note_frequency(root - 12), beat * 0.72, "square", 0.105), start)
            add_clip(track, percussion(0.15, "kick") * 0.25, start)
        else:
            root = chord_roots[(index // 8) % len(chord_roots)]
            for interval in (0, 4, 7):
                add_clip(
                    track,
                    tone(note_frequency(root + interval), step * 0.48, "triangle", 0.045),
                    start,
                )
            add_clip(track, percussion(0.09, "snare") * 0.075, start)

        if index % 8 == 7:
            add_clip(track, percussion(0.20, "snare") * 0.11, start)

    return normalize(track, 0.86)


def make_pickup_cue():
    """Create a short, key-neutral EDM pickup/riser.

    Avoiding a melodic arpeggio lets the cue sit over songs in any key without
    producing an accidental competing harmony.
    """
    duration = 0.88
    track = np.zeros(int(duration * SAMPLE_RATE), dtype=np.float64)

    riser_duration = 0.62
    time = np.arange(int(riser_duration * SAMPLE_RATE), dtype=np.float64) / SAMPLE_RATE
    progress = time / riser_duration
    sweep_phase = 2.0 * math.pi * (
        260.0 * time + 0.5 * ((2_300.0 - 260.0) / riser_duration) * time * time
    )
    riser = (
        np.sin(sweep_phase)
        + 0.32 * np.sin(sweep_phase * 1.013 + 0.7)
        + RNG.normal(0.0, 0.32, len(time))
    )
    riser *= np.power(progress, 1.7) * 0.18
    add_clip(track, riser, 0.0)

    # A bright transient marks the end of the lift without establishing a key.
    ping_time = np.arange(int(0.22 * SAMPLE_RATE), dtype=np.float64) / SAMPLE_RATE
    ping = (
        np.sin(2.0 * math.pi * 1_520.0 * ping_time)
        + 0.55 * np.sin(2.0 * math.pi * 2_170.0 * ping_time)
    ) * np.exp(-ping_time * 24.0)
    add_clip(track, ping * 0.24, 0.61)
    add_clip(track, percussion(0.10, "click") * 0.16, 0.61)
    return normalize(track, 0.72)


def make_impact_cue():
    """Create a compact EDM impact with an unpitched tail."""
    duration = 1.35
    track = np.zeros(int(duration * SAMPLE_RATE), dtype=np.float64)

    # Fast pitch-dropping sub hit: perceived as percussion instead of a note.
    hit_time = np.arange(int(0.58 * SAMPLE_RATE), dtype=np.float64) / SAMPLE_RATE
    sub_phase = 2.0 * math.pi * (
        42.0 * hit_time + 8.3 * (1.0 - np.exp(-10.0 * hit_time))
    )
    sub = np.sin(sub_phase) * np.exp(-hit_time * 7.2)
    add_clip(track, sub * 0.78, 0.025)

    # Wide-band crack and short metallic detail give the hit definition on
    # laptop speakers while keeping the tail free of a recognizable pitch.
    crack_time = np.arange(int(0.42 * SAMPLE_RATE), dtype=np.float64) / SAMPLE_RATE
    crack = RNG.normal(0.0, 1.0, len(crack_time)) * np.exp(-crack_time * 19.0)
    add_clip(track, crack * 0.31, 0.02)

    metal_time = np.arange(int(0.25 * SAMPLE_RATE), dtype=np.float64) / SAMPLE_RATE
    metal = (
        np.sin(2.0 * math.pi * 730.0 * metal_time)
        + 0.62 * np.sin(2.0 * math.pi * 1_137.0 * metal_time)
    ) * np.exp(-metal_time * 17.0)
    add_clip(track, metal * 0.15, 0.035)

    for start, volume in ((0.20, 0.12), (0.36, 0.075), (0.54, 0.045)):
        add_clip(track, percussion(0.24, "snare") * volume, start)

    return normalize(track, 0.88)


def main():
    write_wav(OUTPUT_DIR / "bgm.wav", make_bgm())
    write_wav(OUTPUT_DIR / "pickup.wav", make_pickup_cue())
    write_wav(OUTPUT_DIR / "impact.wav", make_impact_cue())
    print(f"Generated theme audio in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
