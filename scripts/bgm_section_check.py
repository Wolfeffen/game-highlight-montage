# -*- coding: utf-8 -*-
"""
成片音画结构匹配度复核
按 timeline.json 的画面段落(P1a..P5)汇总：
  - 该段音乐平均能量(RMS)
  - 该段鼓点密度(个/秒)
  - 该段切点数 vs 鼓点数 -> 判断"切点密度是否超过音乐可承载密度"
用法: python bgm_section_check.py <video.mp4> <timeline.json> [ffmpeg]
"""
import sys, os, json, subprocess, tempfile, wave
import numpy as np

VIDEO = sys.argv[1] if len(sys.argv) > 1 else "output.mp4"
TL = sys.argv[2] if len(sys.argv) > 2 else "timeline.json"
FFMPEG = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("FFMPEG", "ffmpeg")

SECTION_MAP = {
    "closeup": "P1a 压抑特写", "flyin": "P1b 飞入现身",
    "collage": "P1c 倾斜切块", "tilted-collage": "P1c 倾斜切块",
    "play": "P2 快剪主体", "rapid": "P3 极限快切",
    "showcase": "P4 完整表现", "showcase-dodge": "P4 完整表现",
    "showcase-flank": "P4 完整表现", "logo-outro": "P5 收尾",
}
ORDER = ["P1a 压抑特写", "P1b 飞入现身", "P1c 倾斜切块", "P2 快剪主体",
         "P3 极限快切", "P4 完整表现", "P5 收尾"]

wav = os.path.join(tempfile.gettempdir(), "section_check.wav")
subprocess.run([FFMPEG, "-y", "-v", "error", "-i", VIDEO, "-vn", "-ac", "1",
                "-ar", "22050", "-c:a", "pcm_s16le", wav], check=True)
with wave.open(wav, "rb") as w:
    sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0

with open(TL, encoding="utf-8") as f:
    tl = json.load(f)
total = float(tl[-1]["timeline_start"]) + float(tl[-1]["dur"])

# 段落边界
bounds = {}
for s in tl:
    k = SECTION_MAP.get(s.get("note") or "", s.get("note") or "?")
    a = float(s["timeline_start"]); b = a + float(s["dur"])
    if k in bounds:
        bounds[k] = (min(bounds[k][0], a), max(bounds[k][1], b))
    else:
        bounds[k] = (a, b)

# onset 检测：与 scripts/bgm_onset.py 保持完全一致（频谱通量 + 峰值检测）
hop = int(sr * 0.02)
win = int(sr * 0.04)
nf = max(0, (len(x) - win) // hop)
t_env = np.arange(nf) * hop / sr
env = np.array([np.sqrt(np.mean(x[i * hop:i * hop + win] ** 2) + 1e-12) for i in range(nf)])
gmax, gmean = env.max(), env.mean()

nfft = 1024
frames = []
for i in range(nf):
    seg = x[i * hop:i * hop + nfft]
    if len(seg) < nfft:
        seg = np.pad(seg, (0, nfft - len(seg)))
    frames.append(np.abs(np.fft.rfft(seg * np.hanning(nfft)))[:256])
flux = np.diff(np.array(frames), axis=0).clip(min=0).sum(axis=1)
flux = np.concatenate([[0], flux])
flux_n = flux / (flux.max() + 1e-9)

k = float(os.environ.get("ONSET_SENSITIVITY", "1.6"))
min_gap = float(os.environ.get("ONSET_MIN_GAP", "0.18"))
thr = np.median(flux_n) + k * np.std(flux_n)
onsets, last = [], -99
for i in range(2, len(flux_n) - 2):
    if flux_n[i] > thr and flux_n[i] == max(flux_n[i - 2:i + 3]) and t_env[i] - last >= min_gap:
        onsets.append(t_env[i]); last = t_env[i]
onsets = np.array(onsets)
onsets = onsets[onsets <= total]

print(f"成片: {os.path.basename(VIDEO)}  总长 {total:.2f}s")
print(f"全局: 峰值能量 {gmax:.3f} | 平均 {gmean:.3f} | 重音 {len(onsets)} 个 | "
      f"中位间隔 {np.median(np.diff(onsets)) if len(onsets) > 1 else 0:.3f}s "
      f"(等效 BPM {60 / np.median(np.diff(onsets)) if len(onsets) > 1 else 0:.0f})")
print()
print("| 段落 | 起止 | 时长 | 平均能量 | 峰值能量 | 鼓点密度 | 切点数 | 切/鼓 |")
print("|---|---|---|---|---|---|---|---|")
for k in ORDER:
    if k not in bounds:
        continue
    a, b = bounds[k]
    seg = env[(t_env >= a) & (t_env < b)]
    if len(seg) == 0:
        continue
    cuts = [s for s in tl if SECTION_MAP.get(s.get("note") or "", s.get("note")) == k
            and a <= float(s["timeline_start"]) < b]
    drum = onsets[(onsets >= a) & (onsets < b)]
    dens = len(drum) / (b - a) if b > a else 0
    ratio = len(cuts) / len(drum) if len(drum) else float("nan")
    print(f"| {k} | {a:.1f}-{b:.1f}s | {b-a:.1f}s | {seg.mean():.3f} | {seg.max():.3f} | "
          f"{dens:.1f}/s | {len(cuts)} | {ratio:.2f} |")

# 黄金分割点
gr = total * 0.618
near = onsets[np.argmin(np.abs(onsets - gr))]
print()
print(f"黄金分割点 {gr:.2f}s -> 最近鼓点 {near:.2f}s (偏差 {near-gr:+.3f}s)")
w = env[(t_env >= gr - 1.5) & (t_env <= gr + 1.5)]
print(f"黄金点±1.5s 能量: 均值 {w.mean():.3f} vs 全片均值 {gmean:.3f} "
      f"({'高于' if w.mean() > gmean else '低于'}全片平均 {abs(w.mean()-gmean)/gmean*100:.0f}%)")
