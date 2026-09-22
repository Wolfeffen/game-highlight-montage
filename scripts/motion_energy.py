# -*- coding: utf-8 -*-
"""素材动作能量分析：signalstats YDIF（帧间差分）-> 0.5s分桶 -> 激战密度排名
用法: python motion_energy.py <素材目录> [输出json路径] [ffmpeg路径] [分析窗口起 止]
默认分析窗口 5-18s（守望POTG表现段）；其他游戏用 0 9999 分析全程。
注意：不要用 ffmpeg scene-detect showinfo 分数做运动强度（提取路径不可靠，会退化为常数）。
"""
import os, re, json, subprocess, sys

BASE = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(BASE.rstrip('/\\')), 'motion_energy.json')
FFMPEG = sys.argv[3] if len(sys.argv) > 3 else 'ffmpeg'
W0 = float(sys.argv[4]) if len(sys.argv) > 4 else 5.0
W1 = float(sys.argv[5]) if len(sys.argv) > 5 else 18.0

files = sorted(f for f in os.listdir(BASE) if f.lower().endswith(('.mp4', '.mov', '.mkv', '.webm')))
result = {}
for f in files:
    p = os.path.join(BASE, f)
    cmd = [FFMPEG, '-i', p, '-vf', 'signalstats,metadata=print:key=lavfi.signalstats.YDIF', '-f', 'null', '-']
    proc = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
    frames, cur_t = [], None
    for line in proc.stderr.splitlines():
        m = re.search(r'pts_time:([0-9.]+)', line)
        if m:
            cur_t = float(m.group(1))
        m = re.search(r'lavfi\.signalstats\.YDIF=([0-9.]+)', line)
        if m and cur_t is not None:
            frames.append((cur_t, float(m.group(1))))
            cur_t = None
    buckets = {}
    for t, v in frames:
        b = round(int(t * 2) / 2, 1)
        buckets.setdefault(b, []).append(v)
    bmax = {b: round(max(v), 1) for b, v in sorted(buckets.items())}
    play = [max(v) for b, v in buckets.items() if W0 <= b < W1]
    energy = round(sum(play) / max(len(play), 1), 2)
    top = sorted(((b, round(max(v), 1)) for b, v in buckets.items() if W0 <= b < W1), key=lambda x: -x[1])[:6]
    result[f] = {'energy': energy, 'top': [[b, s] for b, s in sorted(top)], 'buckets': bmax}
    print(f'{f}: E={energy} top={[[b, s] for b, s in sorted(top)]}', flush=True)

json.dump(result, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n=== RANK (YDIF energy) ===')
for f, r in sorted(result.items(), key=lambda x: -x[1]['energy']):
    print(f"{r['energy']:6.2f}  {f}  peaks={r['top']}")
