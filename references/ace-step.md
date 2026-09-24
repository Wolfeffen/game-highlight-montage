# ACE / ACE-Step 接入参考

> **2026-09 更新**：此前记录的「ACE Studio 无公开 API」已过时。官方 `acestep.io` 现提供 REST API，
> 同时出现了按量付费的第三方托管端点。本地显卡门槛不再是唯一出路。

## 一、先区分两个东西

| 产品 | 定位 | 现状 |
|---|---|---|
| **ACE Studio** | 时域科技的 AI 音乐工作站（网页/桌面 DAW） | 手工创作用它；程序化接入走下面的 API |
| **ACE-Step** | 其底层开源音乐生成模型（时域科技 × StepFun） | Apache-2.0 / MIT 开源，有本地与云端两条路 |

## 二、四条接入路线

### A. acestep.io 官方 API —— 默认路线，国内可达

- 端点：`POST https://acestep.io/api/v2/generate-audio` → `GET /api/v2/task-status/{task_id}`
- 认证：`Authorization: Bearer <key>`，仅 Studio 订阅者可创建 key
- 计费：普通 5 credits / 次，`studio_quality: true` 10 credits / 次（后期层：人声前置、节奏锁定、跨曲风稳定）
- 特点：输出 royalty-free；任务状态 `queued/completed/failed/cancelled/expired`，6 小时未完成自动退款
- 请求体：`tags`（风格标签）、`lyrics`（纯 BGM 写 `[inst]`）、`seconds`、`steps`、`studio_quality`
- 对纯 BGM 场景，`studio_quality` 的人声优化意义不大，开普通档即可

```bash
curl -X POST https://acestep.io/api/v2/generate-audio \
  -H "Authorization: Bearer $ACESTEP_API_KEY" -H "Content-Type: application/json" \
  -d '{"tags":"aggressive rock, distorted guitar solo","lyrics":"[inst]","seconds":93,"steps":8}'
```

### B. Replicate —— 无需订阅，按次计费

- 模型：`lucataco/ace-step`，约 **$0.033 / 次**，L40S，约 35s 出结果
- 适合不想订阅、偶尔用一次的场景；国内实测可达

### C. EmpirioLabs —— 便宜，但国内实测连不上

> ⚠️ 2026-09 实测：从国内网络（校园网 + 代理）访问 `empiriolabs.ai` 与 `api.empiriolabs.ai`
> 均为连接超时，而 `acestep.io`、`api.replicate.com` 正常返回 200。**先自行 curl 验证再考虑。**

- 端点：`POST https://api.empiriolabs.ai/v1/audio/generations` → `GET /v1/jobs/{job_id}`
- 模型 `ace-step-1-5-xl`，**$0.00025 / 生成秒**（45s 成片 5 候选 ≈ $0.12）
- 支持 `seed` / `audio_duration` / `negative_prompt` / `format`

### D. 本地部署 ACE-Step —— 功能最全，但显卡门槛高

- 唯一支持 **Repaint（局部重绘指定时段）**、**Cover**、**指定 BPM / 调性 / 拍号** 的路线
  （HF Spaces 版 API 参数最全：`bpm`、`key_scale`、`time_signature`、`repainting_start/end`）
- 门槛：官方推荐 8GB 起，完整模型约 60GB 下载
- **本机 RTX 3060 Laptop 6GB 不建议**（需 CPU offload，慢且 LM 被禁用）

| 路线 | 门槛 | 成本(45s成片/5候选) | 国内可达 | 建议 |
|---|---|---|---|---|
| A acestep.io 官方 | Studio 订阅 | 订阅内 credits | 实测可达 | **默认选这个** |
| B Replicate | 注册拿 token | ≈ $0.17 | 实测可达 | 不想订阅时用 |
| C EmpirioLabs | 注册拿 key | ≈ $0.12 | **实测不可达** | 网络能通再考虑 |
| D 本地部署 | 8GB+ 显卡 | 电费 | — | 显卡够再上 |

## 三、为什么必须"批量生成 + 自动选优"

AI 生成无法保证精确落点——这是模型特性，不是提示词写得不够好。
**正确做法是把"生成"当成采样，把"选"交给脚本**：

1. 用 `bgm_generate.py` 一次生成 N 个候选（不同 seed）
2. 生成时长取成片的 2 倍，在长曲上**滑动窗口**（步长 0.25s）
3. 每个窗口按四项自动打分（见下），选最高分的窗口裁出来
4. 装进 Remotion 后再跑 `bgm_onset.py` 复核

评分权重：切点对齐率 40 + 中位偏差 20 + 黄金分割点能量比 25 + 结构匹配（P1低/P4高）15 = 100 分。

> 实测参考：ACE 手工版成片原分 **74.7/100**（对齐 77%、中位偏差 0.060s、黄金点能量比 0.88）。
> 短板在"黄金点能量比 0.88"——收拳点比全片平均还低，即**画面收了但音乐没收**。

## 四、不重新生成也能救：外科手术式补强

当音乐整体不错、只是**收拳点软**或**个别切点落在空档**时，不必重生成，
直接在原曲上叠加合成打击音即可（画面一个不动，重渲都不用）。

实测效果（守望先锋 46.7s 成片）：

| 版本 | 对齐率 | 中位偏差 | 黄金点能量比 | 黄金点偏差 | 总分 |
|---|---|---|---|---|---|
| 原版 | 77% | 0.060s | **0.88** | -0.221s | 74.7 |
| 补强后 | **83%** | **0.050s** | **1.18** | **+0.019s** | **82.3** |

配方：

1. `scripts/make_impacts.py` 合成两种音效——`tick.wav`（0.15s 短促打击）、`impact.wav`（1.5s 大重击）。
2. 用 `bgm_onset.py` 找出**偏差 >0.15s 的切点**，在这些时刻叠 `tick`。
3. 在**黄金分割点最近的那一个切点**叠 `impact`（整片唯一的一记最强重击）。
4. 关键参数：先把原曲 `volume=0.72` 留出余量，混完再 `volume=1.35` 提回来；
   限幅器只做兜底（`limit=1.0`）。**不要用狠限幅**——实测会把动态压掉，
   音头从 128 个掉到 112 个，反而制造新的偏差点。
5. 混回画面：`ffmpeg -i 原片.mp4 -i 新音轨.wav -map 0:v -map 1:a -c:v copy`（视频流直拷，零重渲）。

> 注意：密集打击音会抬高整体频谱通量的标准差，使 `bgm_onset.py` 的检测阈值上移，
> 检出音头数变少。所以**对齐率这个指标会有 2-3 个点的噪声**，
> 判读时以「黄金点能量比」和「黄金点偏差」这两项硬指标为准。

## 五、一键命令

```bash
# 1) 只看施工单和 prompt，不花钱
python scripts/bgm_generate.py timeline.json --dry-run

# 2) 真跑：生成 5 个候选，自动选最优窗口
export ACESTEP_API_KEY=xxxx
python scripts/bgm_generate.py timeline.json --provider acestep --n 5 --out bgm/
# -> bgm/bgm_best.mp3 + bgm/bgm_report.md

# 3) 给现成配乐打分（不调用 API）
python scripts/bgm_generate.py timeline.json --score-only 成片.mp4

# 4) 复核
python scripts/bgm_onset.py 成片.mp4 timeline.json
python scripts/bgm_section_check.py 成片.mp4 timeline.json
```

## 六、商业使用

- ACE-Step 权重与代码 Apache-2.0 / MIT，生成内容一般可商用；云端服务的输出条款以各平台为准（acestep.io 明示 royalty-free）。
- ccMixter 曲目需逐首遵守 CC 授权。
