# 使用示例

以下是一种典型的工作流示例，适用于本 Skill 的素材分析与混剪路径：

## 典型流程

1. 把游戏素材放到待分析目录
2. 执行 `scripts/motion_energy.py` 计算动作能量
3. 执行 `scripts/sharpness_check.py` 检测低清素材
4. 读取 `references/methodology.md` 与 `references/game-profiles.md`
5. 根据 `references/platform-presets.md` 设定目标时长
6. 运行 `scripts/bgm_energy.py` 选择音乐起点和高能窗口
7. 按结构进行前后呼应、黄金分割、最终收尾

## 示例命令

```bash
python scripts/motion_energy.py ./input_clips
python scripts/sharpness_check.py ./input_clips
python scripts/bgm_energy.py ./audio/test.mp3 45
```

## 输出目录建议

- `outputs/`：渲染结果、时间线、裁剪素材
- `data/`：素材索引、缓存、分析结果

## 注意事项

- 先看画面再定段，不要只看数字指标。
- 选段时优先看“出招 → 击杀”的完整结构。
- 调整总时长时，务必重新平衡节奏和 BGM 对齐。
