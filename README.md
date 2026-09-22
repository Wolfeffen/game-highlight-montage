# game-highlight-montage

游戏高光混剪 Skill —— 把多段游戏精彩素材，按专业剪辑方法论做成节奏型混剪视频。

Turn raw gameplay highlight clips into a rhythm-driven montage video using a proven editing methodology, data-driven segment selection, and a code-render pipeline.

## 目录结构

```text
game-highlight-montage/
├── README.md                      # 仓库总览与使用说明
├── SKILL.md                       # 技能定义与工作流说明
├── LICENSE                        # MIT 开源协议
├── .gitignore                     # Git 忽略规则
├── pyproject.toml                 # Python 项目配置，支持标准安装
├── requirements.txt               # Python 依赖
├── scripts/                       # 分析脚本与处理脚本
│   ├── motion_energy.py
│   ├── sharpness_check.py
│   └── bgm_energy.py
├── src/                           # 标准 Python 包目录
│   └── game_highlight_montage/
│       ├── __init__.py
│       └── __main__.py
├── references/                    # 剪辑方法论与平台参数
│   ├── methodology.md
│   ├── game-profiles.md
│   └── platform-presets.md
├── docs/                          # 项目文档与说明
│   └── project-structure.md
├── examples/                      # 参考示例与使用范例
│   └── workflow-example.md
├── tests/                         # 测试与验证说明
│   └── README.md
├── data/                          # 可放素材/缓存/分析数据
│   └── .gitkeep
├── outputs/                       # 产出目录
│   └── .gitkeep
└── .github/                       # GitHub 配置（可选）
```

## Python 项目结构说明

本仓库已升级成更标准的 Python 工程结构：

- `src/game_highlight_montage/`：Python 包目录，适合后续扩展
- `pyproject.toml`：标准项目配置，支持 `pip install -e .`
- `requirements.txt`：基础依赖清单
- `scripts/`：仍保留技能脚本执行入口，兼容现有工作流

## 安装方式

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## 使用方式

1. 阅读 `SKILL.md` 理解整体剪辑流程。
2. 使用 `references/` 中的方法论和参数。
3. 运行 `scripts/` 下的脚本进行分析：

```bash
python scripts/motion_energy.py ./input_clips
python scripts/sharpness_check.py ./input_clips
python scripts/bgm_energy.py ./audio/test.mp3 45
```

4. 如需扩展功能，可在 `src/game_highlight_montage/` 中添加模块。

## 维护建议

- 代码逻辑尽量放入 `src/` 中，避免根目录散落脚本。
- 脚本型处理工具保留在 `scripts/`，便于直接调试和执行。
- 参考资料统一放入 `references/`。
- 中间产物放到 `outputs/`，原始数据放到 `data/`。

## License

MIT License
