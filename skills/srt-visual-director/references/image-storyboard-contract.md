# Image storyboard profile: image-v1

本规范是现有 STORYBOARD.md 的图片策划扩展，不替换通用 storyboard.schema.json。一个项目仍只有一个分镜文件，包含：

1. 项目、视觉规范与未决事项。
2. 按 shot ID 排列的可读表：时间、原文、画面、素材路径、屏幕文字与运动。
3. **恰好一个 json 代码区块**，按本规范保存同一方案的结构化数据与完整提示词。表格是摘要，不单独修改成另一套分镜；变更时同步更新两者。

JSON 投影若由下游明确需要，可以从该区块提取，不作为第二份可独立维护的计划。完整结构见 [image-storyboard.schema.json](image-storyboard.schema.json)，随 Skill 一起安装；仓库 `schemas/image-storyboard.schema.json` 引用同一规范。时间与引用约束由 `scripts/image_timeline.py` 检查。

## 字段

| 对象 | 字段和语义 |
|---|---|
| 根 | profile=image-v1；project={id,title}；status=planned/ready |
| direction（可选） | directingProfile/visualStyle 为实际读取配置的 {id,revision,source} 或 null；audience 为字符串或 null；overrides 为有效覆盖说明列表；resolvedRules 为展开的有效规则列表。详见 [配置规则](director-presets.md) |
| timing | kind=srt/untimed；srtPath 真实路径或 null；startMs/endMs 为指定片段绝对毫秒或 null；audioDurationMs 已知实际音频总时长或 null |
| style | aspectRatio 明确比例或 null；description 可执行风格；referenceRefs 真实参考来源列表；textPolicy；subtitleSafeArea；confirmed 布尔值 |
| assetLibrary | status=not_provided/unavailable/searched；source 真正读取的清单/返回结果来源或 null；notes 搜索范围说明 |
| assumptions/openQuestions | 字符串列表，区分采用的假设和仍未解决的问题 |
| shot | id=shot-001 等稳定 ID；startMs/endMs；voiceoverRefs 为解析器输出的 srt-编号；voiceText；timingBasis；timingNote；narrativeBeat；visualIntent；image；可选 execution |
| image | assetNeed；action；assetRef；candidateIds；prompt；fallbackPrompt；designBrief；inImageText；overlay；usage |
| assetRef | assetId 公共库真实 ID；source 实际来源；version 实际版本或 null；viewed 布尔值；useStatus=confirmed/unverified/restricted/forbidden（来自素材管理者或用户确认，不由导演凭空推断） |
| overlay | title（可为空）；keywords 和 labels 字符串列表；只含观众看到的文字 |
| usage | crop、motion、transition 为项目级编排描述；不回写公共素材 |
| execution | 仅执行阶段需要，{renderer: remotion/hyperframes,pattern: ...}；规划时可省略 |

所有表中列出的字段除 execution、direction 外均需出现；没有值时按 schema 使用 null/空列表，不编造来源。使用预设的新方案填写 direction；旧方案可以不包含此字段，仍兼容 image-v1。direction 一旦提供，其内部五个字段均需出现。

timingBasis 为 cue_boundary/audio_verified/estimated/manual/untimed。estimated、manual、audio_verified 需在 timingNote 解释依据；audio_verified 必须真实核验过，脚本无法证明此点。

reuse/edit 的 assetRef 必须 viewed=true 且 useStatus=confirmed。其余 action 的 assetRef=null；尚未确定的素材 ID 只放 candidateIds。generate/edit 的 prompt 为非空字符串；reuse/search_pending/external_design 的 prompt=null；search_pending 可给 fallbackPrompt。external_design 需要非空 designBrief（准确数据、来源、标签及布局），其余情况 null。

## 时间、状态与素材限制

- SRT 模式使用非负毫秒整数；每镜 startMs < endMs，相邻边界完全衔接并覆盖 timing 指定范围。
- 每镜 voiceoverRefs 包含与其时间重叠的所有字幕；允许重复引用同一字幕以表达内部切分，不允许重复伪造字幕。纯静音镜头可为空。
- cue_boundary 的切点取真实字幕边界或目标片段边界；内部估计切点用 estimated，不能仅用精确数字伪装真实对齐。
- 无 SRT 草案使用 kind=untimed，所有时间与 srtPath=null、voiceoverRefs=[]、timingBasis=untimed、status=planned。
- ready 要求已确认风格和比例、没有 openQuestions、没有 estimated 或 search_pending；ready 表示可制作，不表示图片/视频已完成。
- 不要求生成前存在真实素材 ID。后续制作、检查、入库完成后，由素材能力返回真实记录，再将 action 改为 reuse 并保存制作来源记录于素材库。

## 与既有执行契约的交接

通用 storyboard.schema.json 继续适用于旧项目，不迁移或重写它。image-v1 在执行时为每镜补充 execution 和已解析的素材引用；引擎接收该 profile 时按以下映射理解，不猜测：

- startMs/endMs → 标准时间字符串 start/end，保留绝对时间；取局部片段时才减片段起点。
- narrativeBeat/visualIntent/voiceoverRefs/execution 保持原意。
- 经素材能力确认的 assetRef.assetId → assetCandidates 与项目 ASSET_MANIFEST.json 记录。
- image.usage/overlay → 动作、切换和后期文字需求；prompt 是素材制作指令，不是渲染源代码。

render-ready 还需要真实图片、音频/字幕处理约定、素材可解析、renderer 指派与实际渲染验收；本 Skill 的 ready 不替代这些检查。
