# 导演方案与视觉风格配置

一套通用导演 Skill，组合不同的内容方案、画风与项目覆盖。这些配置不是独立 Skill，不包含制作工作流或公共素材库。

配置唯一源文件随 `srt-visual-director/references/presets/` 一起分发，保证只安装该 Skill 时仍能读取；本目录提供仓库级入口和项目配置示例，不复制第二份规则。项目选择与生效规则最终记录在唯一的 STORYBOARD.md 中。

| 类型 | 配置 | 作用 |
|---|---|---|
| 导演方案 | [jianting-research](../skills/srt-visual-director/references/presets/directing/jianting-research.yaml) | 兼听研报：证据、机构共识与分歧、观察变量 |
| 导演方案 | [health-explainer](../skills/srt-visual-director/references/presets/directing/health-explainer.yaml) | 中老年健康：生活情境、动作、物件、清楚易读 |
| 视觉风格 | [editorial-minimal](../skills/srt-visual-director/references/presets/visual-styles/editorial-minimal.yaml) | 暖白、石墨灰、蓝色的极简编辑插画 |
| 视觉风格 | [warm-life-illustration](../skills/srt-visual-director/references/presets/visual-styles/warm-life-illustration.yaml) | 米白、自然线条、柔和配色的生活手绘插画 |

两种画风是起始方案，尚未通过真实生图确认。导演方案与画风可交叉选择，也可提供实际参考图；不把示例当作已确认的频道规范。

## 使用

“使用 `$srt-visual-director`，纯图片模式，导演方案用 `jianting-research`，画风用 `editorial-minimal`，处理我提供的文案和 SRT，输出分镜与缺图提示词。”

“使用 `$srt-visual-director`，导演方案用 `health-explainer`，画风参考我上传的图片，9:16，每张图独立输出制作需求。”

也可以复制 [研报项目配置](examples/jianting-research.yaml) 或 [健康项目配置](examples/health-explainer.yaml) 到项目中命名为 `DIRECTOR.yaml`，由 agent 读取。复制本身不执行脚本，也不表示用户已确认全部选择。

新增题材通常增加 directing 配置；新增画风通常增加 visual-styles 配置，并在 [选择与覆盖规则](../skills/srt-visual-director/references/director-presets.md) 注册 ID。只有工作方法或交付物明显不同，才考虑增加独立导演 Skill。调整有效规则时递增 revision，既有项目按已保存的规则继续，按需显式更新。
