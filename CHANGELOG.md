# Changelog

## v1.2.1 — README 英文优先 + 首屏效果展示

- **README 重组**：英文版升为主 `README.md`（国际流量为主），中文版迁移至 `README.zh-CN.md`，两版顶部互链。
- **首屏效果展示**：新增 `assets/structure.svg`（真实时间线五段结构图：切点刻度 + 黄金分割点标记）与 `assets/demo.gif`（亮相拼贴 → 极限快切 → 收拳点实拍预览，380px/8fps/1.4MB）。assets 不打进发布 zip，仅存在于仓库。
- 两版 README 增加「为什么不是把片段拼起来」差异化卖点段落、shields.io 徽章、项目主页下载链接。
- 发布包文件清单变化：`README.en.md` 移除，新增 `README.zh-CN.md`。

## v1.2.0 — BGM 一键生成 + 风格手册

- 新增 `scripts/bgm_generate.py`：云端 ACE-Step 一键生成。批量出候选 → 在长曲上滑动窗口 → 按「切点对齐率 / 中位偏差 / 黄金点能量比 / 结构匹配」自动评分选优 → 直接裁出 `bgm_best.mp3`。支持 `--dry-run` 先看施工单。
- 新增 `scripts/bgm_section_check.py`：段落级音画结构复核（各段音乐能量、鼓点密度、切鼓比、黄金点能量对比）。
- 新增 `references/bgm-style.md`：BGM 风格手册。实测确立 **FPS 首选「强鼓点 + 失真吉他 solo」**，含与纯电子鼓点版的数据对比、机制解释、三条硬规则与验收清单。
- 重写 `references/ace-step.md`：**修正「ACE Studio 无公开 API」的过时结论**，补入 acestep.io 官方 API、EmpirioLabs 按量付费端点、Replicate 三条云端路线与成本对比（45s 成片 5 候选 ≈ $0.12）。
- 新增 `scripts/make_impacts.py`：合成打击音（tick 0.15s / impact 1.5s），用于外科手术式补强。
- 记录**外科手术式补强**技法：不重新生成音乐，只在偏差切点补 tick、黄金分割点补大重击，画面 `-c:v copy` 不动。实测 74.7 → **82.3** 分（黄金点能量比 0.88→1.18、黄金点偏差 0.221→0.019s）。
- 修正云端路线：**EmpirioLabs 国内实测不可达**（连接超时），默认 provider 改为 `acestep`；Replicate 为备选。
- 更新 `scripts/bgm_brief.py`：prompt 加入吉他 solo / accelerando / 黄金点孤立重击留白，校验段落补齐新标准。
- 更新 `SKILL.md`/`README.md`/`README.en.md`。

## v1.1.0 — BGM 施工单与鼓点对齐校验

- 新增 `scripts/bgm_brief.py`：根据 `timeline.json` 自动生成给 ACE/Suno/作曲家的精确 BGM 施工单（段落情绪、关键落点、建议 BPM、可直接粘贴的 Prompt）。
- 新增 `scripts/bgm_onset.py`：检测生成后 BGM 的鼓点/重音，并与视频切点做偏差校验（含黄金分割点偏移量）。
- 更新 `references/methodology.md`：加入「AI/ACE 生成 BGM 的协作流程」四步。
- 更新 `SKILL.md` / `README.md` / `README.en.md`：补充脚本说明与 BGM 工作流。

## v1.0.0 — 初始发布

- 数据驱动选段：`motion_energy.py`（YDIF）+ `sharpness_check.py`（拉普拉斯方差）。
- 剪辑方法论沉淀：`references/methodology.md`（五段式结构、亮相三段式、黄金分割快切、前后呼应、倾斜切块拼版）。
- 游戏类型档案：`references/game-profiles.md`（FPS / MOBA 节奏差异）。
- 平台时长公式：`references/platform-presets.md`（微博 35s / 抖音 45s / B站 90s）。
- BGM 能量分析：`scripts/bgm_energy.py`（ccMixter 选曲用）。
