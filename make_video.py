"""Render bum.mp4: an animated title card roasting Kaitlyn Symoun.

Usage: python3 make_video.py   (needs Pillow and ffmpeg on PATH)
"""
import math
import os
import subprocess
import tempfile
import wave
import struct

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUT = "bum.mp4"

# (text, start_s, end_s, size, color)
LINES = [
    ("BREAKING NEWS", 0.0, 2.0, 90, (255, 220, 0)),
    ("KAITLYN SYMOUN", 2.0, 8.0, 110, (255, 255, 255)),
    ("IS A", 3.2, 8.0, 80, (200, 200, 200)),
    ("BUM", 4.2, 8.0, 220, (255, 60, 60)),
]
DURATION = 8.0


def ease_out(t):
    return 1 - (1 - min(max(t, 0), 1)) ** 3


def frame(t):
    # Pulsing dark background with diagonal stripes
    img = Image.new("RGB", (W, H), (20, 20, 30))
    d = ImageDraw.Draw(img)
    shift = int(t * 120) % 80
    for x in range(-80, W + H + 80, 80):
        d.polygon([(x + shift, 0), (x + shift + 40, 0),
                   (x + shift + 40 - H, H), (x + shift - H, H)], fill=(30, 30, 45))

    if t < 2.0:
        # Intro: flashing "BREAKING NEWS" banner
        text, _, _, size, color = LINES[0]
        f = ImageFont.truetype(FONT, size)
        d.rectangle([0, H // 2 - 80, W, H // 2 + 80], fill=(180, 0, 0))
        if int(t * 4) % 2 == 0:
            d.text((W // 2, H // 2), text, font=f, fill=color, anchor="mm")
        return img

    ys = {"KAITLYN SYMOUN": 170, "IS A": 300, "BUM": 480}
    for text, start, end, size, color in LINES[1:]:
        if not (start <= t < end):
            continue
        p = ease_out((t - start) / 0.5)
        if text == "BUM":
            # Slam-in zoom with a little shake afterwards
            scale = 3.0 - 2.0 * p
            f = ImageFont.truetype(FONT, max(10, int(size * scale)))
            jitter = int(8 * math.sin(t * 60)) if p >= 1 and t < start + 1.2 else 0
            d.text((W // 2 + jitter, ys[text]), text, font=f, fill=color,
                   anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
        else:
            f = ImageFont.truetype(FONT, size)
            x = int(-W / 2 + (W) * p) if text == "KAITLYN SYMOUN" else W // 2
            d.text((x, ys[text]), text, font=f, fill=color, anchor="mm",
                   stroke_width=4, stroke_fill=(0, 0, 0))
    return img


def write_audio(path):
    """Sad trombone 'wah wah wah waaah' timed to land on BUM."""
    sr = 44100
    total = int(DURATION * sr)
    samples = [0.0] * total
    notes = [(4.2, 0.4, 293.66), (4.65, 0.4, 277.18), (5.1, 0.4, 261.63), (5.55, 1.6, 246.94)]
    for start, dur, freq in notes:
        s0 = int(start * sr)
        for i in range(int(dur * sr)):
            tt = i / sr
            wobble = 1 + (0.02 * math.sin(2 * math.pi * 6 * tt) if dur > 1 else 0)
            env = min(1, tt / 0.03) * min(1, (dur - tt) / 0.1)
            ph = 2 * math.pi * freq * wobble * tt
            v = 0.5 * math.sin(ph) + 0.25 * math.sin(2 * ph) + 0.12 * math.sin(3 * ph)
            if s0 + i < total:
                samples[s0 + i] += 0.35 * env * v
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s)) * 32767)) for s in samples))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        for n in range(int(DURATION * FPS)):
            frame(n / FPS).save(os.path.join(tmp, f"{n:05d}.png"))
        audio = os.path.join(tmp, "audio.wav")
        write_audio(audio)
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.png"),
            "-i", audio, "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", OUT,
        ], check=True)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
