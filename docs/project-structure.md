# 项目结构说明

本文档用于说明此仓库的工程组织方式，避免文件分散和命名混乱。

## 结构原则

- 代码类文件放 `scripts/`
- 资料类文件放 `references/`
- 使用说明放 `docs/`
- 示例放 `examples/`
- 测试说明放 `tests/`
- 可生成文件放 `outputs/`、`data/`

## 目录作用

### scripts/

用于放置所有可执行分析脚本，主要包括：

- `motion_energy.py`：计算片段动作能量，定位高能窗口
- `sharpness_check.py`：分析素材锐度，剔除模糊素材
- `bgm_energy.py`：分析音乐能量分布，辅助 BGM 截取窗口选择

### references/

用于放置剪辑方法论和规则说明：

- `methodology.md`：剪辑镜头语言与叙事逻辑
- `game-profiles.md`：不同游戏类型的结构适配规则
- `platform-presets.md`：平台时长与参数公式

### docs/

用于放置项目说明、设计文档、维护说明等。

### examples/

用于放置与任务相关的示例工作流，便于用户快速理解使用方式。

### tests/

用于放置测试脚本、验证步骤、测试说明。

### outputs/

用于存放生成的 JSON、预切素材、渲染输出等中间产物。

### data/

用于存放原始素材目录索引、缓存文件和未来需要纳管的数据。

## 维护规则

1. 根目录只保留项目入口文件，如 `README.md`、`SKILL.md`、`LICENSE`。
2. 需要执行的脚本不要直接放在仓库根目录。
3. 文档统一落到 `docs/` 或 `references/`，避免散落在根目录。
4. 输出性内容不要直接污染源代码目录。
