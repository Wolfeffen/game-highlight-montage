---
name: game-highlight-montage
description: 游戏高光混剪生成器——把多段游戏精彩素材（守望先锋全场最佳、无畏契约/CSGO/三角洲击杀集锦、王者荣耀/英雄联盟团战片段）按专业剪辑方法论做成节奏型混剪视频。数据驱动选段（帧差能量+锐度检测）+ 黄金分割结构 + Remotion 代码渲染。触发词：游戏混剪、高光合集、POTG混剪、击杀集锦、montage、全场最佳合集、精彩操作合集。
agent_created: true
---

# 游戏高光混剪（Game Highlight Montage）

把 N 段游戏精彩素材做成一支节奏型混剪视频。核心竞争力不是"拼起来"，而是：**镜头语言方法论 + 数据驱动选段 + 可复用的代码管线**，产出强于模板剪辑软件的成品。

## 何时使用

- 用户提供多段游戏录像/集锦素材，要求做混剪、合集、montage
- 适用游戏：守望先锋（全场最佳 POTG）、无畏契约（Valorant/瓦）、CS:GO、三角洲行动、Apex 等 FPS；王者荣耀、英雄联盟等 MOBA（结构需按游戏类型调整，见 references/game-profiles.md）

## 三条铁律（来自实战迭代，违反必返工）

1. **先看画面再定段**：选段不能只看数据。每段候选必须抽帧目检（ffmpeg 抽帧 + Read 看图），确认截取窗口内是"出招→击杀"的有效镜头，没有混入亮相动画/黑场/低清画面。
2. **出招帧数 > 击杀后帧数**：观众快感来自"出招明确、击杀果断"。截取窗口让出招铺垫占约六成，击杀出现后迅速切走。50/50 会显"乱"。
3. **改时间线先算总长**：任何增删段落后，总时长必须重新配平（脚本内 assert），并确认 BGM 高能段仍压住快剪区和黄金分割点。

## 标准工作流

### 1. 素材体检
- ffprobe 批量读取分辨率/帧率/时长，确认规格统一；不统一则预切时统一到输出规格（如 1920×1080@30fps）。
- 跑 `scripts/sharpness_check.py <素材目录>`：拉普拉斯方差锐度排名，**低于中位数 55% 的素材标记为低清晰度**，尽量不上时间线（或只作 <0.3s 碎片）。
- 跑 `scripts/motion_energy.py <素材目录>`：signalstats YDIF 帧差能量，输出每段 0.5s 分桶能量与高能窗口排名。**不要用 ffmpeg scene-detect 的 showinfo 分数做运动强度**（实战中该路径提取的分数退化为常数，不可靠）。

### 2. 读方法论，定结构
读 `references/methodology.md`（用户的完整剪辑理论：亮相拼贴、黄金分割极限快切、前后呼应、倾斜切块）和 `references/game-profiles.md`（目标游戏的集锦特点与结构调整）。

### 3. 定目标时长与平台
读 `references/platform-presets.md`。按平台预设或用户指定时长，用参数化公式分配各阶段时长。微博 ≥30s（建议 35s）、抖音 45s、B站 1-3min。

### 4. BGM 选型与对齐
- 曲库：ccMixter（CC BY 可商用），API：`https://ccmixter.org/api/query?f=json&tags=<风格>&lic=open&sort=score`（用 curl -k 直连；node 脚本在某些代理环境会报 Parse Error）。
- **风格铁律**：FPS 混剪首选**强鼓点 + 失真电吉他 solo**，BPM 150-200。纯合成器电子在密集切点处容易"糊"（短板音色缺音头，切点咬不住）。详见 `references/bgm-style.md`（含实测对比与三条硬规则）。
- 跑 `scripts/bgm_energy.py <音频文件>` 得能量曲线，**选截取窗口使视频黄金分割点（总时长×0.618）落在 BGM 高能平台起点附近**，开头亮相段落在 BGM 中低能量区。
- **AI 生成 BGM 链路**：先跑 `scripts/bgm_brief.py <timeline.json> [风格备注]` 输出精确施工单 → 用 ACE/Suno/作曲家按单生成 → 拿到成品后跑 `scripts/bgm_onset.py <成片.mp4> <timeline.json>` 校验鼓点与切点对齐（目标 ≥80% 切点落在最近鼓点 ±0.15s 内）。详见 `references/ace-step.md`（ACE-Step 开源模型接入说明）。
- **段落级复核**：再跑 `scripts/bgm_section_check.py <成片.mp4> <timeline.json>`，看各画面段落的音乐能量/鼓点密度/切鼓比。重点查两件事：① 黄金分割点 ±1.5s 能量是否 ≥ 全片平均（否则"收拳软"）；② P3 极限快切段若碎片递减（0.45→0.2s），音乐必须滚奏/accelerando，否则只有首切点能对齐，后续逐格漂移。
- **一键生成（云端 ACE-Step）**：`scripts/bgm_generate.py <timeline.json> --provider acestep --n 5 --out bgm/`。原理是**批量生成 + 滑动窗口 + 自动评分选优**——AI 无法保证精确落点，所以靠采样+搜索解决，而不是靠写更好的提示词。先用 `--dry-run` 看施工单。接入路线对比与成本见 `references/ace-step.md`。
- **不换音乐的补救**：若只是收拳点软或个别切点落在空档，不必重生成。用 `scripts/make_impacts.py` 合成打击音，在偏差大的切点补 tick、在黄金分割点补一记大重击，再 `-c:v copy` 混回画面即可。实测 74.7 → 82.3 分。配方见 `references/bgm-style.md` 第四节。

### 5. 生成时间线 + 预切
写 gen_timeline.py 风格的脚本：段表（素材/起点/时长/相位）→ 总长 assert → ffmpeg 预切（`-ss/-to` 精确裁剪 + scale 统一 + CRF18 + 去音轨）→ 输出 timeline.json。

### 6. Remotion 渲染
- 项目模板参考：Remotion + React19 + 统一精确版本（如 remotion@4.0.526 全家族同版本，否则 npm 报 ETARGET）；必须有 tsconfig.json 才能 render。
- 组件结构：Sequence 按 timeline_start 排布；P1 亮相拼贴 → P2 快剪 → P3 极限快切（收拳点=0.618）→ P4 完整表现 → P5 官方收尾+端卡。
- 效果库（已验证）：zoom punch 硬切、紫色切帧闪光（5帧）、递进放大+紫染（极限快切）、电影黑边+缓推（完整表现段）、倾斜切块拼版（-8° 斜条 + objectPosition 错位取景 + 末帧爆闪断开）。

### 7. 自检与交付
- **必须抽帧自检**：渲染完成后抽关键帧（切块拼版、延长段、黄金分割点）Read 目检，确认面部/ID/击杀播报可见、无黑场杂质。
- 交付双版本：无损母版（CRF18 直出）+ 分享版（CRF23 + faststart，约 1/5 体积）。
- 告知用户渲染耗时（1080p30 约 3-4s 视频/秒渲染，45s 成片约 2.5-3 分钟）。

## 环境备忘（Windows + 中国网络）

- ffmpeg 便携版：npmmirror `https://registry.npmmirror.com/-/binary/ffmpeg-static/b6.1.1/ffmpeg-win32-x64.gz`（gunzip 即用，免安装）；GitHub releases 直连常被断。
- npm 装包：`--registry=https://registry.npmmirror.com`。
- bash 环境可能缺核心工具（ls/grep/mkdir），用 curl.exe / tar.exe / 托管 Python 干活。

## 已知边界

- 逐帧级音画同步（卡枪声毫秒级）、复杂变速曲线 → 建议专业剪辑软件；本管线擅长结构、节奏、选段与程序化效果。
- MOBA 素材无官方"亮相格式"，P1 拼贴段改用多杀播报横幅/登场瞬间，详见 game-profiles.md。
