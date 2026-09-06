# 导演方案与视觉风格

导演 Skill 负责通用分镜能力；directing profile 决定内容如何被看懂；visual style 决定画面语言。配置是可组合的参考数据，不是额外 Skill，也不包含 TTS、生图、入库或发布权限。

## 读取与选择

当用户指定频道、题材方案、画风预设，或提供 `DIRECTOR.yaml` 时，读取本文件和选中的配置。没有配置时沿用通用流程，不默认套用某个频道。

| 类型 | ID | 文件 |
|---|---|---|
| 导演方案 | jianting-research | [兼听研报](presets/directing/jianting-research.yaml) |
| 导演方案 | health-explainer | [中老年健康科普](presets/directing/health-explainer.yaml) |
| 视觉风格 | editorial-minimal | [极简编辑插画](presets/visual-styles/editorial-minimal.yaml) |
| 视觉风格 | warm-life-illustration | [温暖生活插画](presets/visual-styles/warm-life-illustration.yaml) |

用户说“兼听研报”可选 jianting-research；明确中老年健康科普可选 health-explainer，并记录选择依据。泛称财经、健康或未说明受众时，只建议相关方案，允许带假设继续，不把频道和年龄视为已确认。方案没有强制画风，两类配置可以交叉使用。

配置的 `revision` 是配置内容版本，修改有效规则时递增。`defaults` 是未提供选择时的起点，`rules` 是该方案的内容要求。视觉配置的 `status: starter` 表示候选起点，既不是用户已确认品牌规范，也不是已经生成并验证的视觉效果。

## 项目配置与覆盖

可在 BRIEF 的 Markdown 中写出选择，或使用同目录的可选 `DIRECTOR.yaml`。后者是输入配置，不是第二份分镜；不要把这些键塞进不支持它们的 BRIEF JSON schema。YAML 由执行 Skill 的 agent 读取，不承诺存在自动加载服务或 CLI 配置解析器。

```yaml
director: srt-visual-director
mode: image-only
directing_profile: health-explainer
visual_style: warm-life-illustration
audience: 50岁以上
aspect_ratio: "9:16"
reference_images: []
overrides:
  text: 大字、少字，关键词后期叠加
  image_delivery: 每镜独立图片
  character_consistency: 同一讲解人物保持外貌和服装一致
```

- 内置 ID 只在上表按类型查找，不根据 ID 猜规则。自定义配置使用实际文件路径，相对路径以 `DIRECTOR.yaml` 所在目录为基准；reference_images 同样解析。无配置文件的对话路径按当前项目目录解析。
- 读取选定文件的 id、revision、kind 与规则。未知 ID、类型不符或文件不可读时记录具体缺失，保持 planned；可以按已知要求产出临时分镜，不能虚称已应用缺失预设。
- 优先级为：用户本次明确要求 > 已确认项目配置/BRIEF > 选中配置的默认值 > 通用启发式。项目配置与 BRIEF 实质冲突而对话未解决时记录待定项，先完成不依赖冲突的工作。
- 导演方案控制表达、受众和内容约束；视觉配置控制媒介、配色、构图与纹理。视觉配置不能自动改掉受众、题材事实或选中的导演方案。项目 overrides 对相应项替换，列表整体替换而非静默拼接；未覆盖的要求继续保留。
- 实际查看参考图后提炼配色、线条、人物比例、构图与文字密度，用于替换相应风格默认值。无法读取参考图时保留未决事项，不能仅凭“用之前那个风格”声称已复现。
- style.confirmed 依据用户是否已明确选定当前有效视觉方案。只确认创建两套配置、只选导演方案、自动推断风格或仅复制示例文件，都不等于确认本项目画风。用户明确说“这次用 warm-life-illustration，按文件执行”可视为确认；未确认也可继续 planned 草案，无需重复追问。

## 落到分镜与提示词

先把有效规则合并成一份项目快照，再按 SRT 实际顺序分镜。配置中的表达结构只帮助识别段落，不能重排已录口播、增造钩子、补造证据或固定图片数量。画幅来自项目；需要读图或看动作时调整构图和切点，不机械套用时长。

image-v1 在唯一的 STORYBOARD.md JSON 内使用可选 `direction` 字段记录：

- `directingProfile`、`visualStyle`：已实际读取的配置 `{id,revision,source}`，未使用/无法读取为 null；source 是实际可解析文件路径或来源。
- `audience`：本次受众或 null；`overrides`：实际生效的项目覆盖说明列表。
- `resolvedRules`：展开后的本次有效表达规则，包含推断为临时的选择说明。不能只保存预设 ID，不能把矛盾规则原样并列。

将有效画风完整展开到现有 `style.description`、`textPolicy`、`subtitleSafeArea`；referenceRefs 只记实际查看过的风格参考，未查看来源列在 openQuestions。style 不依赖未来重新读取预设即可理解。逐图 prompt 也展开相应画风、稳定人物特征、比例与留白，不能只写 ID 或“同上”。按需应用 profile 内容要求，不要把整份配置机械粘贴到每条生图提示词。

视觉配置中的 motion 是可覆盖的编排建议，按每镜实际构图写入 image.usage.motion；不要把后期推近、平移误写成要求生图模型生成视频。

兼听研报的机构、单位、时间范围、实际/预测标识应进入图表 designBrief 或后期标签；健康方案的动作部位、视角与步骤应进入 visualIntent/assetNeed/prompt。内部叙事标签仍留在 narrativeBeat，不能因此变成屏幕文字。

通用 general 模式也可读取这些配置，将选项、版本与有效规则写入 STORYBOARD.md 的说明部分，沿用原有 JSON schema，不向旧 JSON 添加 direction。

修改公共预设不自动改写已产出的项目；用户要求换风格时更新同一分镜的 style、direction、逐镜素材需求与提示词，并重新判断现有素材能否复用。裁切、字幕、运动属于本项目，不能改写公共素材身份。
