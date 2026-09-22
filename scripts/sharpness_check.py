# -*- coding: utf-8 -*-
"""素材锐���检测：抽5帧灰度拉普拉斯方差（越低越模糊），低于中位数55%标记为低清晰度
用法: python sharpness_check.py <素材目录> [ffmpeg路径] [抽帧时刻1,时刻2,...]
需要 numpy。默认抽帧时刻 8,10,12,14,16s（守望POTG表现段中部）；短视频素材传自定义时刻。
"""
import os, subprocess, sys
import numpy as np

SRC = sys.argv[1]
FFMPEG = sys.argv[2] if len(sys.argv) > 2 else 'ffmpeg'
TIMES = [float(x) for x in (sys.argv[3].split(',') if len(sys.argv) > 3 else ['8', '10', '12', '14', '16'])]
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sharp_tmp')
os.makedirs(TMP, exist_ok=True)

def lap_var(raw, w, h):
    img = np.frombuffer(raw, dtype=np.uint8).reshape(h, w).astype(np.float64)
    lap = (-4 * img[1:-1, 1:-1] + img[:-2, 1:-1] + img[2:, 1:-1] + img[1:-1, :-2] + img[1:-1, 2:])
    return lap.var()

files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(('.mp4', '.mov', '.mkv', '.webm')))
results = {}
for f in files:
    scores = []
    for t in TIMES:
        raw_p = os.path.join(TMP, 'f.raw')
        cmd = [FFMPEG, '-y', '-v', 'error', '-ss', str(t), '-i', os.path.join(SRC, f),
               '-frames:v', '1', '-vf', 'scale=640:360,format=gray', '-f', 'rawvideo', raw_p]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(raw_p) and os.path.getsize(raw_p) == 640 * 360:
            with open(raw_p, 'rb') as fp:
                scores.append(lap_var(fp.read(), 640, 360))
    results[f] = round(float(np.median(scores)), 1) if scores else 0.0

med = round(float(np.median([v for v in results.values()])), 1)
print(f'中位锐度: {med}')
print('=== 锐度排名（高->低） ===')
for f, v in sorted(results.items(), key=lambda x: -x[1]):
    flag = '  <-- 低清晰度' if v < med * 0.55 else ''
    print(f'{v:10.1f}  {f}{flag}')
