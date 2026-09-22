# -*- coding: utf-8 -*-
"""BGM 能量结构分析：0.5s 分桶 RMS，打印能量地图，辅助选择截取窗口
用法: python bgm_energy.py <音频文件> [ffmpeg路径] [目标视频时长s]
选窗口原则：视频黄金分割点(目标时长x0.618)应落在 BGM 高能平台起点附近；
开头亮相段(0-8s)落在 BGM 中低能量区。
"""
import subprocess, array, json, sys, os

MP3 = sys.argv[1]
FFMPEG = sys.argv[2] if len(sys.argv) > 2 else 'ffmpeg'
TARGET = float(sys.argv[3]) if len(sys.argv) > 3 else 45.0
SR = 22050

proc = subprocess.Popen([FFMPEG, '-v', 'error', '-i', MP3, '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'],
                        stdout=subprocess.PIPE)
raw = proc.stdout.read()
proc.wait()
samples = array.array('h', raw)
n = len(samples)
dur = n / SR
print(f'duration: {dur:.1f}s, samples: {n}')

bucket = SR // 2
rms = []
for i in range(0, n, bucket):
    chunk = samples[i:i + bucket]
    if not chunk:
        break
    s = 0
    for v in chunk:
        s += v * v
    rms.append((s / len(chunk)) ** 0.5)

mx = max(rms)
norm = [r / mx for r in rms]

print('\n=== energy map (each char = 0.5s, #>80% +=50% -=20%) ===')
line = ''
for i, v in enumerate(norm):
    c = '#' if v > 0.8 else '+' if v > 0.5 else '-' if v > 0.2 else '.'
    line += c
    if (i + 1) % 30 == 0:
        print(f'{(i - 29) * 0.5:6.1f}s |{line}|')
        line = ''
if line:
    print(f'{(len(rms) - len(line)) * 0.5:6.1f}s |{line.ljust(30)}|')

golden = TARGET * 0.618
best = None
for start_x2 in range(0, len(norm) - int(TARGET * 2)):
    seg = norm[start_x2:start_x2 + int(TARGET * 2)]
    gp = int(golden * 2)
    score = (sum(1 for v in seg[gp:gp + 8] if v > 0.8) * 2
             + sum(1 for v in seg[gp:] if v > 0.6) / max(len(seg) - gp, 1)
             - sum(1 for v in seg[:16] if v > 0.8))
    if best is None or score > best[0]:
        best = (score, start_x2 / 2)
if best:
    print(f'\n推荐截取窗口: 从 BGM {best[1]:.1f}s 起取 {TARGET:.0f}s（黄金分割点 {golden:.1f}s -> BGM {best[1] + golden:.1f}s）')

out = os.path.join(os.path.dirname(os.path.abspath(MP3)), 'bgm_energy.json')
json.dump({'rms_half_sec': [round(r, 1) for r in rms], 'duration': dur,
           'recommended_start': best[1] if best else None}, open(out, 'w'))
print('json ->', out)
