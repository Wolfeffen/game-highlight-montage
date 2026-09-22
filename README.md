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
├── scripts/                      # 分析脚本与处理脚本
│   ├── motion_energy.py          # 帧差能量分析（YDIF）
│   ├── sharpness_check.py        # 锐度检测脚本
│   └── bgm_energy.py             # BGM 能量分析脚本
├── references/                   # 剪辑方法论与平台参数
│   ├── methodology.md            # 剪辑方法论
│   ├── game-profiles.md          # 游戏类型档案
│   └── platform-presets.md       # 平台时长预设
├── docs/                         # 项目文档与说明
│   └── project-structure.md       # 项目结构说明
├── examples/                     # 参考示例与使用范例
│   └── workflow-example.md       # 工作流示例
├── tests/                        # 测试与验证说明
│   └── README.md                 # 测试说明
├── data/                         # 未来可放素材、输出、缓存等数据
│   └── .gitkeep                  # 占位文件
└── outputs/                      # 产出目录（如预切片、JSON、视频输出）
    └── .gitkeep                  # 占位文件
```

## 设计目标

- 统一脚本、参考文档、示例和测试入口
- 让仓库更适合长期迭代和协作维护
- 保持 Skill 形式不变，同时增加标准工程化结构
- 让新接手的人可以快速理解“什么文件放什么地方”

## 使用方式

1. 先阅读 `SKILL.md` 了解整个剪辑流程。
2. 结合 `references/` 中的剪辑理论和平台参数进行选段与节奏设计。
3. 运行 `scripts/` 下的脚本进行素材分析与 BGM 对齐。
4. 按需输出到 `outputs/` 或 `data/` 中保存结果。

## 维护建议

- 脚本类文件保持在 `scripts/` 中，不要散落在仓库根目录。
- 参考资料统一归档到 `references/`。
- 新增说明文档建议放到 `docs/`，示例放到 `examples/`。
- 可输出结果放到 `outputs/`，原始素材数据放到 `data/`。

## License

MIT License
