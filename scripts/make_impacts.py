# -*- coding: utf-8 -*-
"""
合成打击音效：给极限快切段补音头、给黄金分割点补大重击。
不重新生成 BGM，只在原曲上做外科手术——画面一个不动。

输出:
  tick.wav    短促打击（0.15s），用于极限快切各切点
  impact.wav  大重击（1.5s），用于黄金分割收拳点
"""
import numpy as np, wave, os

SR = 48000
OUT = os.getcwd()   # 输出到当前工作目录，方便与 ffmpeg 混音命令配合


def bandpass(x, lo, hi, sr=SR):
    """频域带通（够用且无额外依赖）"""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / sr)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def env(n, decay, attack=0.002):
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    return a * np.exp(-t / decay)


def write(name, data):
    data = np.clip(data, -1, 1)
    st = np.stack([data, data], axis=1)
    pcm = (st * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"{name}  {len(data)/SR:.2f}s  峰值 {np.abs(data).max():.2f}")


rng = np.random.default_rng(7)

# ---- tick: 短促打击（噪声瞬态 + 低频body），像一记鼓边/镲点
n = int(SR * 0.15)
noise = rng.standard_normal(n)
tick = bandpass(noise, 1800, 7000) * env(n, 0.030)
body = np.sin(2 * np.pi * 190 * np.arange(n) / SR) * env(n, 0.045)
tick = tick * 0.75 + body * 0.55
tick = tick / np.abs(tick).max() * 0.55
write("tick.wav", tick)

# ---- impact: 大重击（低频扫频 + 宽带冲击 + 长尾）
n = int(SR * 1.5)
t = np.arange(n) / SR
f = 110 * np.exp(-t / 0.10) + 38                      # 110Hz -> 38Hz
sweep = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.42)
crack = bandpass(rng.standard_normal(n), 300, 9000) * env(n, 0.075)
tail = np.sin(2 * np.pi * 42 * t) * env(n, 0.55) * 0.35
impact = sweep * 0.95 + crack * 0.60 + tail
impact = impact / np.abs(impact).max() * 0.92
write("impact.wav", impact)
