# game-highlight-montage

**简体中文** | [English](./README.en.md)

游戏高光混剪 Skill —— 把多段游戏精彩素材，按专业剪辑方法论做成节奏型混剪视频。

Turn raw gameplay highlight clips into a rhythm-driven montage video using a proven editing methodology, data-driven segment selection, and a code-render pipeline (Remotion).

> 本 Skill 为 AI Agent（如 WorkBuddy / Claude Code 类支持 SKILL.md 规范的环境）设计，加载后 Agent 可按其中的工作流独立完成"素材体检 → 选段 → BGM 对齐 → 预切 → 渲染 → 自检交付"全流程。

## 能力概览

- **数据驱动选段**：帧差能量（YDIF）定位激战窗口 + 拉普拉斯方差锐度检测剔除低清素材
- **剪辑方法论内置**：亮相拼贴 → 能量递增快剪 → 黄金分割点极限快切 → 完整表现前后呼应 → 官方收尾
- **游戏类型适配**：FPS（守望先锋/无畏契约/CS:GO/三角洲）与 MOBA（王者荣耀/英雄联盟）两套节奏档案
- **平台时长参数化**：微博 35s / 抖音 45s / B站 90s 等预设配方，黄金分割硬约束公式
- **BGM 能量对齐**：选窗使视频黄金分割点落在 BGM 高能平台起点
- **BGM 施工单与校验**：`bgm_brief.py` 给 ACE/作曲家输出精确结构单；`bgm_onset.py` 检查生成后的 BGM 鼓点是否卡住视频切点
- **BGM 一键生成**：`bgm_generate.py` 接云端 ACE-Step，批量生成候选 → 滑动窗口自动评分选优 → 直接裁出可用 BGM（45s 成片 5 个候选约 $0.12）
- **BGM 风格手册**：实测确立 FPS 首选「强鼓点 + 失真吉他 solo」，含数据对比、机制解释与验收清单
- **成品强于模板软件**：全部效果代码化（zoom punch、切帧闪光、倾斜切块拼版、电影黑边缓推……）

## 目录结构

```
game-highlight-montage/
├── SKILL.md                        # Skill 主文件（触发条件、三条铁律、七步工作流）
├── scripts/
│   ├── motion_energy.py            # 帧差能量分析（YDIF），输出高能窗口排名
│   ├── sharpness_check.py          # 拉普拉斯方差锐度检测，标记低清素材
│   ├── bgm_energy.py               # BGM 逐秒能量曲线，辅助截取窗口选择
│   ├── bgm_brief.py                # BGM 施工单生成器：给 ACE/作曲家精确结构单
│   ├── bgm_onset.py                # 鼓点/重音检测 + 与视频切点对齐校验
│   ├── bgm_generate.py             # 云端 ACE-Step 一键生成：批量候选 + 滑动窗口自动选优
│   ├── bgm_section_check.py        # 段落级音画结构复核（各段能量/鼓点密度/切鼓比）
│   └── make_impacts.py             # 合成打击音，用于不换音乐的外科手术式补强
└── references/
    ├── methodology.md              # 完整剪辑方法论（实战迭代沉淀）
    ├── game-profiles.md            # 各游戏集锦特点与结构调整档案
    ├── platform-presets.md         # 平台时长预设与参数化公式
    ├── bgm-style.md                # BGM 风格手册：强鼓点+吉他 solo，实测数据与验收标准
    └── ace-step.md                 # ACE/ACE-Step 接入参考：四条云端/本地路线与成本对比
```

## 环境依赖

| 依赖 | 用途 | 获取方式 |
|---|---|---|
| ffmpeg / ffprobe | 素材体检、预切、抽帧 | Windows 便携版：`https://registry.npmmirror.com/-/binary/ffmpeg-static/b6.1.1/ffmpeg-win32-x64.gz`（gunzip 即用） |
| Python 3.10+（含 numpy） | 运行分析脚本 | 任意发行版 |
| Node.js 18+ | Remotion 渲染 | 官方安装包 |
| Remotion 4.x（全家族同精确版本） | 视频渲染 | `npm install remotion@4.0.526 @remotion/cli@4.0.526 react@19 react-dom@19 --registry=https://registry.npmmirror.com` |

## 快速上手（给 Agent 的用法）

1. 下载本仓库（GitHub 的 `Code → Download ZIP`，或直接 clone）
2. 将本目录放入 Agent 的 skills 目录（如 `~/.workbuddy/skills/` 或项目 `.workbuddy/skills/`）
3. 对 Agent 说："帮我做一个游戏混剪，素材在 X 目录，目标平台抖音"
4. Agent 将按 SKILL.md 工作流执行：素材体检 → 读方法论与游戏档案 → BGM 选型对齐 → 生成时间线预切 → Remotion 渲染 → 抽帧自检 → 交付母版+分享版

> **注意**：用 GitHub 的 Download ZIP 下载时，解压出来的目录名会是
> `game-highlight-montage-main`（带分支后缀），放进 skills 目录前请去掉 `-main`，
> 改回 `game-highlight-montage`。从项目主页下载的 `game-highlight-montage.zip`
> 解压后已是正确目录名，无需改动。

## 设计原则（三条铁律）

1. **先看画面再定段** —— 数据只是初筛，每个候选段必须抽帧目检
2. **出招帧数 > 击杀后帧数** —— 出招明确、击杀果断，约六四开
3. **改时间线先算总长** —— 任何增删必须重新配平总时长并复核 BGM 对齐

## 验证记录

本 Skill 提炼自一个完整实战项目：27 段《守望先锋》莫伊拉全场最佳素材 → 46.7 秒混剪成片，经用户 4 轮专业反馈迭代验收通过。守望先锋档案为实战验证；无畏契约/CS:GO 为同族推演；MOBA 档案待实战回写。

## License

MIT（详见 LICENSE 文件）。示例 BGM 检索自 ccMixter，使用时请遵守各曲目的 CC 授权条款。
