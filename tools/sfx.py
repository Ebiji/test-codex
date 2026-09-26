#!/usr/bin/env python3
"""ティザー動画用の効果音＋BGM を合成する（標準ライブラリのみ）。

    python3 tools/sfx.py out.wav 15
タイミングは video/index.html のシーン構成に合わせてある。
"""
import math
import random
import struct
import sys
import wave

SR = 44100
out_path = sys.argv[1]
dur = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0
N = int(SR * dur)
buf = [0.0] * N
rnd = random.Random(1)


def add(t0, samples, gain=1.0):
    i0 = int(t0 * SR)
    for k, v in enumerate(samples):
        if 0 <= i0 + k < N:
            buf[i0 + k] += v * gain


def env(n, a=0.005, r=None):
    a_n = max(1, int(a * SR))
    for k in range(n):
        yield min(1.0, k / a_n) * (1 - k / n) ** (r or 2)


def pop(freq=900, length=0.09):
    n = int(length * SR)
    return [math.sin(2 * math.pi * (freq * (1 - 0.6 * k / n)) * k / SR) * e for k, e in enumerate(env(n, 0.001, 3))]


def click(length=0.012):
    n = int(length * SR)
    return [(rnd.random() * 2 - 1) * e for e in env(n, 0.0005, 4)]


def thump(length=0.35):
    n = int(length * SR)
    return [math.sin(2 * math.pi * (140 * (1 - 0.7 * k / n)) * k / SR) * e for k, e in enumerate(env(n, 0.002, 2))]


def whoosh(length, f0, f1):
    n = int(length * SR)
    out, lp = [], 0.0
    for k in range(n):
        x = k / n
        lp += (rnd.random() * 2 - 1 - lp) * (0.02 + 0.2 * x)
        tone = math.sin(2 * math.pi * (f0 + (f1 - f0) * x * x) * k / SR) * 0.3
        out.append((lp + tone) * math.sin(math.pi * x) * 0.6)
    return out


def square(freq, length, duty=0.5):
    n = int(length * SR)
    per = SR / freq
    return [(1 if (k % per) / per < duty else -1) * e for k, e in enumerate(env(n, 0.004, 1.5))]


# --- 効果音 ---
add(2.0, whoosh(1.4, 300, 1600), 0.35)             # 流れ星
add(3.38, thump(), 0.9)                              # パッチーン！
add(3.38, pop(1400, 0.12), 0.5)
t = 3.45
while t < 6.8:                                       # クラウンのパチパチ
    add(t, click(), 0.35 * (1 - (t - 3.45) / 4))
    t += rnd.uniform(0.015, 0.08)
add(4.8, pop(700, 0.12), 0.5)                        # 名前
for i, f in enumerate((880, 988, 1175, 1319, 1568)):  # 変身ブリップ
    add(7.1 + i * 0.46, pop(f, 0.1), 0.55)
    add(7.1 + i * 0.46, click(0.02), 0.3)
fz = 10.2                                            # シュワ〜
n = int(1.6 * SR)
lp = 0.0
fizz = []
for k in range(n):
    lp += ((rnd.random() * 2 - 1) - lp) * 0.6
    fizz.append(lp * (rnd.random() < 0.3) * math.sin(math.pi * k / n))
add(fz, fizz, 0.25)
add(11.8, whoosh(0.6, 200, 900), 0.3)                # パッケージ
add(12.9, thump(), 0.7)                              # ロゴ
for i in range(6):
    add(12.9 + i * 0.05, pop(1000 + i * 150, 0.07), 0.35)
for i, f in enumerate((1047, 1319, 1568, 2093)):     # エンドのキラッ
    add(13.4 + i * 0.07, square(f, 0.25, 0.25), 0.08)

# --- BGM（ピコピコ系、128BPM） ---
beat = 60 / 128
mel = [72, 76, 79, 76, 81, 79, 76, 79, 72, 76, 79, 84, 83, 79, 76, 74]
bass = [48, 48, 55, 55, 53, 53, 55, 55]
start = 3.45
k = 0
while start + k * beat / 2 < dur - 0.3:
    t0 = start + k * beat / 2
    note = mel[k % len(mel)]
    add(t0, square(440 * 2 ** ((note - 69) / 12), beat / 2 * 0.9, 0.25), 0.07)
    if k % 2 == 0:
        b = bass[(k // 2) % len(bass)]
        add(t0, square(440 * 2 ** ((b - 69) / 12), beat * 0.8, 0.5), 0.07)
    if k % 2 == 1:
        add(t0, click(0.03), 0.12)
    k += 1

# 最後はフェードアウト
fade = int(0.6 * SR)
for i in range(fade):
    buf[N - fade + i] *= 1 - i / fade

peak = max(1e-9, max(abs(v) for v in buf))
scale = 0.89 / peak
with wave.open(out_path, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v * scale)) * 32767)) for v in buf))
print("wrote", out_path)
