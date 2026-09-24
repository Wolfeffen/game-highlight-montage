# -*- coding: utf-8 -*-
"""
BGM 施工单生成器
根据 timeline.json 输出给作曲家 / ACE 的精确结构单：
- 总长、建议 BPM、段落情绪与配器
- 关键落点（P1→P2 断开、黄金分割点、P4 高潮、P5 收尾）
- ACE-Step / ccMixter 搜索用 prompt / tags

用法：
  python bgm_brief.py path/to/timeline.json [风格备注] > brief.md

说明：timeline.json 里的 phase 或 note 字段均可被识别。
      推荐 note 取值：closeup / flyin / collage / play / rapid / showcase / logo-outro
"""
import json, sys

TL = sys.argv[1] if len(sys.argv) > 1 else "timeline.json"
STYLE = sys.argv[2] if len(sys.argv) > 2 else ""

with open(TL, encoding="utf-8") as f:
    tl = json.load(f)

# 把每一段按 note 或 phase 映射到概念段落
SECTION_MAP = {
    "closeup": "P1a 压抑特写",
    "flyin": "P1b 飞入现身",
    "collage": "P1c 倾斜切块拼版",
    "tilted-collage": "P1c 倾斜切块拼版",
    "play": "P2 快剪主体",
    "rapid": "P3 极限快切",
    "showcase": "P4 完整表现",
    "showcase-dodge": "P4 完整表现",
    "showcase-flank": "P4 完整表现",
    "logo-outro": "P5 LOGO + 端卡",
}

# 当 note 缺失时的 phase 兜底映射（仅覆盖常见约定）
PHASE_FALLBACK = {
    4: "showcase",
    5: "logo-outro",
    6: "tilted-collage",
    7: "closeup",
    8: "flyin",
}

def section_key(s):
    note = s.get("note") or ""
    if note in SECTION_MAP:
        return SECTION_MAP[note]
    # note 缺失时按 phase 兜底
    phase = s.get("phase")
    if phase in PHASE_FALLBACK:
        return SECTION_MAP[PHASE_FALLBACK[phase]]
    return f"phase_{phase if phase is not None else '?'}"

sections = {}
for s in tl:
    key = section_key(s)
    sections.setdefault(key, []).append(s)

# 计算每段起止
def bounds(segs):
    start = float(segs[0]["timeline_start"])
    end = max(float(s["timeline_start"]) + float(s["dur"]) for s in segs)
    return start, end

section_meta = {k: bounds(v) for k, v in sections.items()}
ordered = sorted(section_meta.items(), key=lambda kv: kv[1][0])

# 总时长
total = tl[-1]["timeline_start"] + tl[-1]["dur"]
gr = total * 0.618
nearest_gr = min(tl, key=lambda s: abs(s["timeline_start"] - gr))

# 关键落点
p1_end = max(section_meta[k][1] for k in section_meta if k.startswith("P1")) if any(k.startswith("P1") for k in section_meta) else 0
p2_start = section_meta.get("P2 快剪主体", (0, 0))[0]
p3_start = section_meta.get("P3 极限快切", (0, 0))[0]
p3_end = section_meta.get("P3 极限快切", (0, 0))[1]
p4 = section_meta.get("P4 完整表现", (0, 0))
p5_start = section_meta.get("P5 LOGO + 端卡", (0, 0))[0]

# 建议 BPM：FPS 强鼓点摇滚/电子通常 140-180；用 P2/P3 最短片段校验鼓脉冲密度
p2_segs = sections.get("P2 快剪主体", [])
p3_segs = sections.get("P3 极限快切", [])
if p2_segs:
    p2_min = min(s["dur"] for s in p2_segs)
    p2_med = sorted(s["dur"] for s in p2_segs)[len(p2_segs) // 2]
else:
    p2_min = 0.5
    p2_med = 1.0
p3_min = min(s["dur"] for s in p3_segs) if p3_segs else 0.3
bpm_low, bpm_high = 140, 180
# 若极限快切碎片极短，推荐上限提高
if p3_min <= 0.25:
    bpm_high = 190
bpm = (bpm_low + bpm_high) // 2

print("# BGM 施工单（Construction Brief for Composer / ACE）")
print()
print(f"**成片目标时长**：{total:.2f}s")
print(f"**建议 BPM 范围**：{bpm_low}-{bpm_high} BPM")
print(f"**切点密度参考**：P2 最短片段 {p2_min:.2f}s / P3 最短片段 {p3_min:.2f}s")
print(f"**鼓脉冲要求**：极限快切区至少每 {max(p3_min, 0.2):.2f}s 有一个可感知的鼓/镲脉冲")
print(f"**黄金分割点**：{gr:.2f}s（落在 *{nearest_gr.get('note','无备注')}*）")
print(f"**用户风格备注**：{STYLE if STYLE else '（无）'}")
print()

print("## 段落结构")
print()
print("| 阶段 | 起止时间 | 时长 | 音乐表情 | 配器/打击乐建议 |")
print("|---|---|---|---|---|")
intent = {
    "P1a 压抑特写": "压抑、蓄势、低能量铺垫",
    "P1b 飞入现身": "压迫感上升，动作飞行音效感",
    "P1c 倾斜切块拼版": "张力积累，等待最后释放",
    "P2 快剪主体": "鼓组逐渐堆叠，能量上行，保持紧凑",
    "P3 极限快切": "速度感推满，军鼓/踩镲密集滚奏，**不要连绵旋律 solo**（会抹平碎片的脆）",
    "P4 完整表现": "完整叙事线，主副歌推进，强旋律支撑",
    "P5 LOGO + 端卡": "仪式感收尾，留尾巴/淡出",
}
inst = {
    "P1a 压抑特写": "低沉合成器铺底 + 弱鼓，可加少量 pad 或贝斯动机",
    "P1b 飞入现身": "低音增强 + 快速上升音效/扫频，为断开做准备",
    "P1c 倾斜切块拼版": "鼓 fill 蓄势，每块切点配重音，末帧大鼓断开",
    "P2 快剪主体": "鼓组逐层加入；踩镲/军鼓；电吉他 riff；避免人声",
    "P3 极限快切": "双踩鼓/军鼓滚奏 + 加速感(accelerando)；**禁止 sustained 旋律线**（碎片时长递减时会与均分节拍逐格相位漂移）",
    "P4 完整表现": "主歌-副歌交替；鼓组全开；贝斯 + breakdown 段制造呼应",
    "P5 LOGO + 端卡": "淡出/最后一个重击 + 长音 pad，为 LOGO 留出空间",
}
for key, (start, end) in ordered:
    dur = end - start
    print(f"| {key} | {start:.2f}-{end:.2f}s | {dur:.2f}s | {intent.get(key,'自由发挥')} | {inst.get(key,'自由发挥')} |")
print()

print("## 关键落点（要求精确到 0.1s）")
print()
print("| 时间 | 事件 | 音乐要求 |")
print("|---|---|---|")
print(f"| {p1_end:.2f}s | P1→P2 断开 | **一记高能量重击/鼓 fill**，把亮相压暗后的张力突然释放 |")
print(f"| {p2_start:.2f}s | 快剪区起 | 鼓组密度上来；每段切点落在强拍或反拍 |")
print(f"| {p3_start:.2f}s | 极限快切起 | 进入最快段落；**每 0.25-0.4s 一个军鼓/踩镲脉冲**；若碎片时长递减则此处需 accelerando/滚奏，否则只有首切点能对齐 |")
print(f"| {gr:.2f}s | 黄金分割收拳点 | **整个曲子最强的一击**（大鼓 + 电吉他强力和弦/铜管）；要求该点前后各 1s 内**不要密集音符**，留白才能砸出冲击 |")
print(f"| {p3_end:.2f}s | 极限快切结束 | 从高速碎片过渡到完整段，鼓点可适当放大一拍 |")
if p4[1] > p4[0]:
    print(f"| {p4[0]:.2f}-{p4[1]:.2f}s | P4 完整表现 | 旋律线最突出，可视为'伪副歌'，结尾前留鼓 fill |")
print(f"| {p5_start:.2f}s | P5 收尾 | 能量自然下坡，避免戛然而止，留一点余韵给端卡 |")
print()

print("## 给 ACE-Step / Suno 的 Prompt（复制可用）")
print()
base_tags = ("intense, aggressive rock, driving drums, distorted electric guitar solo, "
             "powerful brass stabs, trailer music, short form video, instrumental, no vocals")
print("```")
print(f"Style tags: {base_tags}, BPM {bpm_low}-{bpm_high}")
print(f"Duration: {total:.1f}s")
print()
print("Structure (must be aligned exactly):")
print(f"- 0-{p1_end:.1f}s: dark, rising tension, low-energy pads, subtle percussion")
print(f"- {p1_end:.1f}-{p3_start:.1f}s: driving rock drums, distorted guitar riffs, building intensity")
print(f"- {p3_start:.1f}-{gr:.1f}s: fastest cuts, double-kick + snare rolls, accelerando, NO sustained melody")
print(f"- {gr:.1f}s: ONE isolated massive impact hit - keep 1s of space before and after it")
print(f"- {gr:.1f}-{p5_start:.1f}s: full-performance section, distorted electric guitar SOLO, epic chorus energy")
print(f"- {p5_start:.1f}-{total:.1f}s: final sustained chord, tail out, leave space for logo")
print("```")
print()

print("## 给 ccMixter 的搜索标签")
print()
print("```")
print("tags=rock,electronic,drums,aggressive&limit=10&sort=score&lic=open")
print("可选替换: metal, synth, hard, dubstep, action, trailer")
print("```")
print()

print("## 一键生成（可选）")
print()
print("若走云端 ACE-Step，本施工单无需手工搬运，直接跑：")
print("```bash")
print(f"python scripts/bgm_generate.py {TL} --provider empiriolabs --n 5 --out bgm/")
print("```")
print("会批量生成候选 → 滑动窗口自动选优 → 输出 bgm/bgm_best.mp3 与评分报告。")
print("AI 无法保证精确落点，靠「采样 + 搜索」而非「更好的提示词」解决。")
print()
print("## 生成后校验")
print()
print("1. `scripts/bgm_onset.py 成片.mp4 timeline.json` —— 目标：≥80% 切点落在最近鼓点 ±0.15s 内。")
print("2. `scripts/bgm_section_check.py 成片.mp4 timeline.json` —— 段落级结构复核，重点看：")
print("   - **黄金分割点 ±1.5s 能量 ≥ 全片平均**（否则收拳软：画面收了音乐没收）")
print("   - P1 段相对能量 ≤1.05、P4 段相对能量 ≥1.05（铺得低、高潮起得来）")
print("   - P3 段切/鼓比：碎片密度接近或超过音头密度时，只有首切点能对上，需音乐滚奏配合")
print()
print(f"当前黄金分割点 {gr:.2f}s 对应的鼓点允许偏差 ≤0.15s，且该点 ±1.5s 能量不得低于全片平均。")
