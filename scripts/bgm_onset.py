# -*- coding: utf-8 -*-
"""
BGM 鼓点/重音检测 + 与视频切点对齐校验
把生成的 BGM（通常来自 ACE/Suno）和已渲染成片/时间线做对齐检查。

用法：
  python bgm_onset.py <video.mp4> <timeline.json> [ffmpeg_path]

环境变量：
  FFMPEG=/path/to/ffmpeg  python bgm_onset.py ...

输出：
  - 鼓点强度序列
  - 每个视频切点与最近鼓点的偏差
  - 对齐统计、黄金分割点偏差
"""
import sys, os, json, wave
import numpy as np

VIDEO = sys.argv[1] if len(sys.argv) > 1 else "output.mp4"
TL = sys.argv[2] if len(sys.argv) > 2 else "timeline.json"
FFMPEG = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("FFMPEG", "ffmpeg")

# 用 ffmpeg 抽音频到临时 wav
import tempfile, subprocess
wav_path = os.path.join(tempfile.gettempdir(), os.path.basename(VIDEO) + "_onset.wav")
try:
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", VIDEO,
                    "-vn", "-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le", wav_path], check=True)
except (FileNotFoundError, subprocess.CalledProcessError) as e:
    print(f"ERROR: 无法调用 ffmpeg ({FFMPEG}): {e}")
    print("请把 ffmpeg 放入 PATH，或用第三个参数/FFMPEG 环境变量指定路径。")
    sys.exit(1)

with wave.open(wav_path, "rb") as w:
    sr = w.getframerate()
    n = w.getnframes()
    x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0

hop = int(sr * 0.02)
win = int(sr * 0.04)
nf = max(0, (len(x) - win) // hop)
if nf < 10:
    print("音频太短，无法分析"); sys.exit(0)

times = np.arange(nf) * hop / sr
env = np.array([np.sqrt(np.mean(x[i*hop:i*hop+win]**2) + 1e-12) for i in range(nf)])

# 频谱通量（对鼓点敏感）
nfft = 1024
frames = []
for i in range(nf):
    seg = x[i*hop:i*hop+nfft]
    if len(seg) < nfft:
        seg = np.pad(seg, (0, nfft - len(seg)))
    frames.append(np.abs(np.fft.rfft(seg * np.hanning(nfft)))[:256])
frames = np.array(frames)
flux = np.diff(frames, axis=0).clip(min=0).sum(axis=1)
flux = np.concatenate([[0], flux])
flux_n = flux / (flux.max() + 1e-9)

# 峰值检测
k = float(os.environ.get("ONSET_SENSITIVITY", "1.6"))
min_gap = float(os.environ.get("ONSET_MIN_GAP", "0.18"))
thr = np.median(flux_n) + k * np.std(flux_n)
peaks = []
last = -99
for i in range(2, len(flux_n) - 2):
    if flux_n[i] > thr and flux_n[i] == max(flux_n[i-2:i+3]) and times[i] - last >= min_gap:
        peaks.append((times[i], flux_n[i]))
        last = times[i]

print("=== BGM 重音（鼓点）检测 ===")
print(f"视频: {VIDEO}")
print(f"时长: {times[-1]:.2f}s | 检出重音: {len(peaks)} | 中位间隔: {np.median(np.diff([p[0] for p in peaks])) if len(peaks)>1 else 0:.3f}s")

# 对齐
if os.path.exists(TL):
    with open(TL, encoding="utf-8") as f:
        tl = json.load(f)
    cuts = [float(s["timeline_start"]) for s in tl if s.get("file")]
    total = tl[-1]["timeline_start"] + tl[-1]["dur"]
    gr = total * 0.618
    pk = np.array([p[0] for p in peaks])
    print("\n=== 切点 vs 最近鼓点 ===")
    offs = []
    bad = []
    for c in cuts:
        if c <= 0: continue
        j = int(np.argmin(np.abs(pk - c)))
        d = pk[j] - c
        offs.append(abs(d))
        flag = "  <-- 偏差大" if abs(d) > 0.15 else ""
        if abs(d) > 0.15:
            bad.append(c)
        print(f"切点 {c:6.2f}s  最近鼓点 {pk[j]:6.2f}s  偏差 {d:+.3f}s{flag}")
    if offs:
        offs = np.array(offs)
        print(f"\n对齐统计: 平均 {offs.mean():.3f}s | 中位 {np.median(offs):.3f}s | ≤0.15s 占比 { (offs<=0.15).mean()*100:.0f}% ({(offs<=0.15).sum()}/{len(offs)})")
    # 黄金分割点
    if len(pk):
        j = int(np.argmin(np.abs(pk - gr)))
        print(f"\n黄金分割点 {gr:.2f}s -> 最近鼓点 {pk[j]:.2f}s (偏差 {pk[j]-gr:+.3f}s)")
        print(f"全片时长 {total:.2f}s")
    if bad:
        print(f"\n建议微调的切点: {[round(c,2) for c in bad]}")
else:
    print("未找到 timeline.json，跳过对齐校验")

# 清理临时 wav（可选保留调试）
try: os.remove(wav_path)
except: pass
