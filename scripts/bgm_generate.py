# -*- coding: utf-8 -*-
"""
BGM 一键生成器（ACE-Step 云端 API）
把「施工单 → 生成 → 选窗 → 校验 → 落盘」串成一条命令。

核心思路（解决 AI 生成不可控）：
  AI 无法保证精确落点，所以不指望"一次生成就完美"，而是
  **批量生成 N 个候选 → 在长曲上滑动窗口 → 用切点对齐度自动评分 → 选最优窗口**。
  成本极低（按量付费约 $0.00025/秒），但把玄学变成了可验收的搜索问题。

用法：
  python bgm_generate.py <timeline.json> [--provider empiriolabs|acestep|replicate]
                         [--n 5] [--out bgm/] [--dry-run] [--ffmpeg PATH]

环境变量（按 provider 二选一）：
  ACESTEP_API_KEY       https://acestep.io      官方，需 Studio 订阅（默认，国内可达）
  REPLICATE_API_TOKEN   https://replicate.com   按次付费 ≈$0.033/次（国内可达）
  EMPIRIOLABS_API_KEY   https://empiriolabs.ai  按量付费，但国内网络实测不可达（2026-09）

输出：
  <out>/bgm_best.mp3        选中并裁剪好的 BGM（已带淡入淡出）
  <out>/candidates/         所有候选原始音频
  <out>/bgm_report.md       评分报告（含每个候选的最佳窗口与得分）
"""
import sys, os, json, time, wave, argparse, tempfile, subprocess, urllib.request, urllib.error

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------- 参数
ap = argparse.ArgumentParser()
ap.add_argument("timeline")
ap.add_argument("--provider", default=os.environ.get("BGM_PROVIDER", "acestep"),
                choices=["empiriolabs", "acestep", "replicate"])
ap.add_argument("--n", type=int, default=5, help="候选数量")
ap.add_argument("--out", default="bgm")
ap.add_argument("--steps", type=int, default=8)
ap.add_argument("--gen-seconds", type=float, default=0,
                help="生成时长，默认 = 成片时长 x2（上限 240s），留余量给滑动选窗")
ap.add_argument("--dry-run", action="store_true", help="只打印将要发送的 prompt，不调用 API")
ap.add_argument("--ffmpeg", default=os.environ.get("FFMPEG", "ffmpeg"))
ap.add_argument("--style", default="", help="额外风格备注，追加到 prompt")
ap.add_argument("--score-only", default="",
                help="不调用 API，只对已有音频做滑动窗口评分（评估现成 BGM 用）")
a = ap.parse_args()

# ---------------------------------------------------------------- 解析时间线
with open(a.timeline, encoding="utf-8") as f:
    tl = json.load(f)
total = float(tl[-1]["timeline_start"]) + float(tl[-1]["dur"])
cuts = [float(s["timeline_start"]) for s in tl if s.get("file")]
gr = total * 0.618          # 黄金分割点
gen_sec = a.gen_seconds or min(total * 2, 240.0)

SECTION_MAP = {
    "closeup": "P1a", "flyin": "P1b", "collage": "P1c", "tilted-collage": "P1c",
    "play": "P2", "rapid": "P3", "showcase": "P4", "showcase-dodge": "P4",
    "showcase-flank": "P4", "logo-outro": "P5",
}
bounds = {}
for s in tl:
    k = SECTION_MAP.get(s.get("note") or "", s.get("note") or "?")
    st, en = float(s["timeline_start"]), float(s["timeline_start"]) + float(s["dur"])
    bounds[k] = (min(bounds[k][0], st), max(bounds[k][1], en)) if k in bounds else (st, en)

p1_end = max([v[1] for k, v in bounds.items() if k.startswith("P1")] or [0])
p3_start = bounds.get("P3", (0, 0))[0]
p4 = bounds.get("P4", (0, 0))
p5_start = bounds.get("P5", (0, 0))[0]

# ---------------------------------------------------------------- 构造 prompt
# 风格铁律：强鼓点 + 失真吉他 solo（见 references/bgm-style.md）
STYLE = ("intense aggressive rock trailer music, driving powerful drums, "
         "distorted electric guitar solo, punchy snare, brass stabs, "
         "instrumental, no vocals")
STRUCT = (
    f"Structure, aligned to seconds: "
    f"0-{p1_end:.1f}s dark rising tension, low energy pads, subtle percussion; "
    f"{p1_end:.1f}-{p3_start:.1f}s driving rock drums and distorted guitar riffs, building intensity; "
    f"{p3_start:.1f}-{gr:.1f}s fastest section, double-kick and snare rolls, accelerando, no sustained melody; "
    f"at {gr:.1f}s ONE isolated massive impact hit with 1s of space around it; "
    f"{gr:.1f}-{p5_start:.1f}s full distorted electric guitar solo, epic chorus energy; "
    f"{p5_start:.1f}-{total:.1f}s final sustained chord, tail out, leave space for logo."
)
PROMPT = f"{STYLE}, BPM 150-200. {STRUCT}" + (f" {a.style}" if a.style else "")

print("=" * 68)
print("BGM 施工单摘要")
print("=" * 68)
print(f"成片总长    : {total:.2f}s")
print(f"黄金分割点  : {gr:.2f}s")
print(f"切点数      : {len(cuts)}")
print(f"生成时长    : {gen_sec:.1f}s（滑动选窗用）")
print(f"候选数量    : {a.n}")
print(f"Provider    : {a.provider}")
print()
print("--- Prompt ---")
print(PROMPT)
print()

if a.dry_run:
    print("[dry-run] 未调用 API。确认 prompt 无误后去掉 --dry-run 再跑。")
    sys.exit(0)

KEY = {"empiriolabs": os.environ.get("EMPIRIOLABS_API_KEY"),
       "acestep": os.environ.get("ACESTEP_API_KEY"),
       "replicate": os.environ.get("REPLICATE_API_TOKEN")}[a.provider]
if not KEY and not a.score_only:
    print(f"ERROR: 缺少 API key。请设置环境变量 "
          f"{'EMPIRIOLABS_API_KEY' if a.provider=='empiriolabs' else 'ACESTEP_API_KEY' if a.provider=='acestep' else 'REPLICATE_API_TOKEN'}")
    sys.exit(1)

os.makedirs(os.path.join(a.out, "candidates"), exist_ok=True)


def http(url, data=None, headers=None, method=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def submit(seed):
    """提交生成任务，返回 job/task id"""
    if a.provider == "empiriolabs":
        r = http("https://api.empiriolabs.ai/v1/audio/generations",
                 data=json.dumps({"model": "ace-step-1-5-xl", "prompt": PROMPT,
                                  "audio_duration": gen_sec, "num_inference_steps": a.steps,
                                  "seed": seed, "format": "mp3"}).encode(),
                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
        return (r.get("job_id") or r.get("id") or r.get("task_id")), r
    if a.provider == "acestep":
        r = http("https://acestep.io/api/v2/generate-audio",
                 data=json.dumps({"tags": STYLE + ", BPM 150-200", "lyrics": "[inst]",
                                  "seconds": int(gen_sec), "steps": a.steps,
                                  "studio_quality": False}).encode(),
                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
        t = (r.get("data") or {}).get("tasks") or []
        return (t[0].get("task_id") if t else None), r
    if a.provider == "replicate":
        r = http("https://api.replicate.com/v1/predictions",
                 data=json.dumps({"version": None, "input": {"prompt": PROMPT, "duration": int(gen_sec)}}).encode(),
                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                          "Prefer": "wait"})
        return r.get("id"), r
    return None, {}


def poll(jid):
    """轮询直到完成，返回音频 URL"""
    for _ in range(120):
        if a.provider == "empiriolabs":
            r = http(f"https://api.empiriolabs.ai/v1/jobs/{jid}",
                     headers={"Authorization": f"Bearer {KEY}"})
            st = (r.get("status") or "").lower()
            if st in ("completed", "succeeded", "success"):
                return find_url(r)
            if st in ("failed", "error"):
                raise RuntimeError(f"生成失败: {r}")
        elif a.provider == "acestep":
            r = http(f"https://acestep.io/api/v2/task-status/{jid}",
                     headers={"Authorization": f"Bearer {KEY}"})
            d = r.get("data") or {}
            tasks = d.get("tasks") or [d]
            st = (tasks[0].get("status") or "").lower()
            if st == "completed":
                return tasks[0].get("audio_url")
            if st in ("failed", "cancelled", "expired"):
                raise RuntimeError(f"生成失败: {tasks[0]}")
        else:  # replicate
            r = http(f"https://api.replicate.com/v1/predictions/{jid}",
                     headers={"Authorization": f"Bearer {KEY}"})
            st = r.get("status")
            if st == "succeeded":
                out = r.get("output")
                return out[0] if isinstance(out, list) else out
            if st in ("failed", "canceled"):
                raise RuntimeError(f"生成失败: {r}")
        time.sleep(5)
    raise RuntimeError("轮询超时")


def find_url(obj):
    """在任意嵌套结构里找音频 URL"""
    if isinstance(obj, str):
        return obj if obj.startswith("http") else None
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("audio_url", "url", "audio", "first_audio_path") and isinstance(v, str) and v.startswith("http"):
                return v
        for v in obj.values():
            u = find_url(v)
            if u:
                return u
    if isinstance(obj, list):
        for v in obj:
            u = find_url(v)
            if u:
                return u
    return None


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as r, open(path, "wb") as f:
        f.write(r.read())


# ---------------------------------------------------------------- 音频分析（与 bgm_onset.py 同口径）
import numpy as np


def load_wav(path):
    wav = os.path.join(tempfile.gettempdir(), "bgmgen_" + os.path.basename(path) + ".wav")
    subprocess.run([a.ffmpeg, "-y", "-v", "error", "-i", path, "-vn", "-ac", "1",
                    "-ar", "22050", "-c:a", "pcm_s16le", wav], check=True)
    with wave.open(wav, "rb") as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return sr, x


def onsets_of(x, sr):
    hop, win = int(sr * 0.02), int(sr * 0.04)
    nf = max(0, (len(x) - win) // hop)
    t = np.arange(nf) * hop / sr
    env = np.array([np.sqrt(np.mean(x[i * hop:i * hop + win] ** 2) + 1e-12) for i in range(nf)])
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
    thr = np.median(flux_n) + 1.6 * np.std(flux_n)
    pk, last = [], -99
    for i in range(2, len(flux_n) - 2):
        if flux_n[i] > thr and flux_n[i] == max(flux_n[i - 2:i + 3]) and t[i] - last >= 0.18:
            pk.append(t[i]); last = t[i]
    return np.array(pk), t, env


def score_window(pk, t, env, off):
    """给一个起始偏移打分（0-100）"""
    gmean = env[(t >= off) & (t < off + total)].mean()
    if gmean <= 0:
        return None
    seg_pk = pk[(pk >= off) & (pk < off + total)] - off
    if len(seg_pk) < 5:
        return None
    # 1) 切点对齐率 + 中位偏差
    devs = [np.min(np.abs(seg_pk - c)) for c in cuts]
    align = np.mean([d <= 0.15 for d in devs])
    med = float(np.median(devs))
    # 2) 黄金分割点能量（相对全片）
    w = env[(t >= off + gr - 1.5) & (t <= off + gr + 1.5)]
    g_energy = float(w.mean() / gmean) if len(w) else 0
    # 3) 结构匹配：P1 低能、P4 高能
    def seg_mean(a1, b1):
        m = env[(t >= off + a1) & (t < off + b1)]
        return float(m.mean() / gmean) if len(m) else 1.0
    p1e = seg_mean(0, p1_end) if p1_end > 0 else 1.0
    p4e = seg_mean(p4[0], p4[1]) if p4[1] > p4[0] else 1.0
    s = (align * 40
         + max(0.0, 1 - med / 0.20) * 20
         + min(g_energy, 1.5) / 1.5 * 25
         + (10 if p1e <= 1.05 else 0) + (5 if p4e >= 1.05 else 0))
    return {"score": s, "align": align, "med": med, "golden_energy": g_energy,
            "p1_rel": p1e, "p4_rel": p4e}


# ---------------------------------------------------------------- 仅评分模式（评估现成 BGM）
if a.score_only:
    print("=" * 68)
    print(f"评分模式（不调用 API）: {a.score_only}")
    print("=" * 68)
    sr, x = load_wav(a.score_only)
    dur = len(x) / sr
    pk, t, env = onsets_of(x, sr)
    print(f"音频时长 {dur:.2f}s | 检出重音 {len(pk)} 个")
    if dur < total - 0.05:
        print(f"警告：音频比成片短（{dur:.2f}s < {total:.2f}s），只能评估 offset=0 附近的窗口。")
    rows = []
    for off in np.arange(0, max(0.01, dur - total), 0.25):
        r = score_window(pk, t, env, float(off))
        if r:
            rows.append(dict(r, offset=float(off)))
    if not rows:
        print("无法评分（音频过短或重音太少）。")
        sys.exit(1)
    rows.sort(key=lambda r: -r["score"])
    best = rows[0]
    print(f"可评估窗口 {len(rows)} 个（步长 0.25s）\n")
    print("| 窗口起点 | 得分 | 对齐率 | 中位偏差 | 黄金点能量比 | P1 | P4 |")
    print("|---|---|---|---|---|---|---|")
    for r in rows[:8]:
        print(f"| {r['offset']:.2f}s | {r['score']:.1f} | {r['align']*100:.0f}% | "
              f"{r['med']:.3f}s | {r['golden_energy']:.2f} | {r['p1_rel']:.2f} | {r['p4_rel']:.2f} |")
    print()
    print("=" * 68)
    print(f"最佳窗口 {best['offset']:.2f}s -> {best['score']:.1f}/100")
    print(f"  对齐率 {best['align']*100:.0f}% | 中位偏差 {best['med']:.3f}s | "
          f"黄金点能量比 {best['golden_energy']:.2f}")
    print(f"  P1 {best['p1_rel']:.2f} (应≤1.05) | P4 {best['p4_rel']:.2f} (应≥1.05)")
    print()
    print("判读: 黄金点能量比 <1.0 = 收拳软（画面收了音乐没收）;")
    print("      对齐率 <75% 且 P3 切/鼓比接近 1 = 碎片节奏与均分节拍相位漂移。")
    sys.exit(0)

# ---------------------------------------------------------------- 主流程
results = []
for i in range(a.n):
    seed = 1000 + i * 137
    print(f"[{i+1}/{a.n}] 提交生成 (seed={seed}) ...", flush=True)
    try:
        jid, _ = submit(seed)
        if not jid:
            print("   提交失败，跳过"); continue
        url = poll(jid)
        mp3 = os.path.join(a.out, "candidates", f"cand_{i:02d}.mp3")
        download(url, mp3)
        print(f"   已下载 {mp3}", flush=True)
    except Exception as e:
        print(f"   失败: {e}"); continue

    sr, x = load_wav(mp3)
    pk, t, env = onsets_of(x, sr)
    dur = len(x) / sr
    best = None
    for off in np.arange(0, max(0.1, dur - total), 0.25):
        r = score_window(pk, t, env, float(off))
        if r and (best is None or r["score"] > best["score"]):
            best = dict(r, offset=float(off))
    if best:
        best.update(file=mp3, onsets=len(pk))
        results.append(best)
        print(f"   最佳窗口 {best['offset']:.2f}s -> 得分 {best['score']:.1f} "
              f"(对齐 {best['align']*100:.0f}% / 中位偏差 {best['med']:.3f}s / "
              f"黄金点能量比 {best['golden_energy']:.2f})", flush=True)

if not results:
    print("没有可用候选，退出。")
    sys.exit(1)

results.sort(key=lambda r: -r["score"])
best = results[0]
out_bgm = os.path.join(a.out, "bgm_best.mp3")
subprocess.run([a.ffmpeg, "-y", "-v", "error", "-i", best["file"],
                "-ss", str(best["offset"]), "-t", str(total),
                "-af", "afade=t=in:st=0:d=0.5,afade=t=out:st=%.2f:d=1.5" % max(0, total - 1.5),
                "-c:a", "libmp3lame", "-b:a", "192k", out_bgm], check=True)

print()
print("=" * 68)
print(f"最佳 BGM : {out_bgm}")
print(f"来源候选 : {os.path.basename(best['file'])} @ {best['offset']:.2f}s")
print(f"综合得分 : {best['score']:.1f}/100")
print(f"  切点对齐率   {best['align']*100:.0f}%   中位偏差 {best['med']:.3f}s")
print(f"  黄金点能量比 {best['golden_energy']:.2f}  (≥1.0 才算收拳有力)")
print(f"  P1 相对能量  {best['p1_rel']:.2f} (应 ≤1.05)   P4 相对能量 {best['p4_rel']:.2f} (应 ≥1.05)")
print("=" * 68)
print("下一步: python bgm_onset.py <成片.mp4> <timeline.json>  复核最终对齐")

# 报告
with open(os.path.join(a.out, "bgm_report.md"), "w", encoding="utf-8") as f:
    f.write("# BGM 生成评分报告\n\n")
    f.write(f"- 成片总长 {total:.2f}s / 黄金分割点 {gr:.2f}s / 切点 {len(cuts)} 个\n")
    f.write(f"- Provider: {a.provider} / 候选 {len(results)} 个\n\n")
    f.write("| 排名 | 候选 | 窗口起点 | 得分 | 对齐率 | 中位偏差 | 黄金点能量比 | P1 | P4 |\n")
    f.write("|---|---|---|---|---|---|---|---|---|\n")
    for i, r in enumerate(results, 1):
        f.write(f"| {i} | {os.path.basename(r['file'])} | {r['offset']:.2f}s | {r['score']:.1f} | "
                f"{r['align']*100:.0f}% | {r['med']:.3f}s | {r['golden_energy']:.2f} | "
                f"{r['p1_rel']:.2f} | {r['p4_rel']:.2f} |\n")
    f.write(f"\n选中的 prompt:\n\n```\n{PROMPT}\n```\n")
print(f"报告 -> {os.path.join(a.out, 'bgm_report.md')}")
