# v9-skills

`v9-skills` is a composable toolbox for agent-led video production. It separates triggerable Skills from the references, deterministic scripts, and project artifacts that let those Skills work together.

## Current foundation

This repository starts with the video system because it is the first concrete use case. The architecture is intentionally flat: conceptual roles such as capability, workflow, router, and engine are expressed in each Skill's responsibility, not in four physical parent directories.

| Path | Role | Responsibility and internal owner command |
| --- | --- | --- |
| [`skills/video`](skills/video) | Router Skill | Select the next video workflow or domain Skill |
| [`skills/multi-report-video-script`](skills/multi-report-video-script) | Prompt Skill | Build a multi-bank Debate Map and TTS-ready finance script |
| [`skills/report-video`](skills/report-video) | Workflow Skill | Orchestrate report production end to end.<br>`python3 skills/report-video/scripts/init_project.py INPUT.srt [--factory-root FACTORY_ROOT]` |
| [`skills/srt-visual-director`](skills/srt-visual-director) | Domain Skill | Plan general storyboards or independent narration-matched images with asset requests and prompts |
| [`skills/media-assets`](skills/media-assets) | Domain Skill | Inventory, select, govern, and track reusable media.<br>`python3 skills/media-assets/scripts/intake_assets.py --library-root ASSET_LIBRARY --project-id PROJECT_ID [--source SOURCE]` |
| [`skills/remotion`](skills/remotion) | Engine Skill | Implement assigned scenes with React and frame-based rendering |
| [`skills/hyperframes`](skills/hyperframes) | Engine Skill | Implement assigned scenes with HTML/CSS/GSAP motion design |
| [`skills/render-reliability`](skills/render-reliability) | Verification Skill | Check deterministic, complete, usable render outputs |

The agent runs these internal commands; users provide the SRT or assets and the destination context. The initializer creates `projects/<project-id>/`, and its factory root defaults to the current directory when `--factory-root` is omitted.

## Artifact flow

```text
MULTI-REPORT SOURCES → Debate Map → approved narration
                                      ↓
usable SRT → initialized project → optional BRIEF refinement
                                      ↓
                        timed narration (audio + SRT)
                                      ↓
                                STORYBOARD.md
                                ├→ ASSET_MANIFEST.json
                                └→ per-shot execution.renderer
                                     ↓
                            Remotion / HyperFrames
                                     ↓
                            RENDER_OUTPUT.json + video
                                     ↓
                            render-reliability
```

A usable SRT can initialize a project before a BRIEF exists; BRIEF details may be added or refined afterward. `STORYBOARD.md` is the single visual plan-layer artifact. It records narrative beats, visual intent, candidate assets, timing, and the renderer for each executable shot. Renderer source code does not belong in the storyboard, and a second `execution-plan.json` is not introduced.

## 图片视觉导演：第一版

`srt-visual-director` 的 [image-only 模式](skills/srt-visual-director/references/image-only-workflow.md) 支持文案/SRT → 独立图片分镜 → 已有素材引用或缺图/编辑提示词。它不调用生图 API，不入库，不渲染视频。公共素材库独立于项目，由 `media-assets` 管理；导演只记录画面需求、候选和项目用法。

示例：使用 `$srt-visual-director`，按 image-only 模式处理我的文案和 SRT，参考提供的画风与素材清单，输出 STORYBOARD.md。每镜是一张独立图片；先复用合适素材，缺图给完整提示词。

没有 SRT 时可交付明确无时间的草案；风格未确认或切点为估计时保留待办。图片模式使用 [image-v1 契约](skills/srt-visual-director/references/image-storyboard-contract.md)，结构化数据放在同一个 STORYBOARD.md 的 JSON 区块中。renderer 在执行交接时指定，原通用分镜契约保持有效。

```bash
python3 skills/srt-visual-director/scripts/image_timeline.py parse narration.srt
python3 skills/srt-visual-director/scripts/image_timeline.py validate STORYBOARD.md --srt narration.srt
# 选择过预设的项目还需按原始请求传入预设 ID：
python3 skills/srt-visual-director/scripts/image_timeline.py validate STORYBOARD.md --srt narration.srt \
  --directing-profile health-explainer --visual-style warm-life-illustration
python3 -m unittest discover -s tests -p 'test_image_*.py'
```

时间脚本使用 Python 3 标准库，校验连续覆盖、字幕引用和素材决策等交接约束；审美、真实音画同步与生图效果仍需实际样片验证。

交付前执行 [图片分镜语义审查](skills/srt-visual-director/references/image-plan-review.md)，修复文字分层、主/备用方案连续性、静态画面表达与配置漂移。脚本返回检查范围及未检查项目；`valid=true` 不能代替语义审查或样片验收。

`python3 skills/srt-visual-director/scripts/image_timeline.py review STORYBOARD.md` 提取保存后的实际 JSON 字段，供逐镜交叉核对；可重复传入 `--shot` 分批读取。修改设计须同步关联字段与可读表，保存后重新读取并复查，再写审查结论。此命令不自动判断语义质量，也不创建第二份分镜。

可查看 [19 秒桌面整理分镜样例](tests/fixtures/image-director/STORYBOARD.md)：由独立执行者实际读取本 Skill 后产出，使用合成文案与候选元数据，仅验证策划交接；没有生成图片或视频。

导演方案与画风可以独立配置：已提供「兼听研报」「中老年健康科普」两套表达方案，以及两套可替换的起始画风。查看 [配置目录与项目示例](presets/README.md)。配置随导演 Skill 分发，不新增题材 Skill；本次有效规则保存在项目分镜中。

`jianting-research` 下的 `high_background_podcast` 仅在项目明确选择时启用。90% 背景视频覆盖率是起始目标，独立可用素材时长不是制作门槛；背景覆盖、素材复用与处理、可见度控制仍需分别报告。

## `srt-v1` migration

[`vimson999/srt-v1`](https://github.com/vimson999/srt-v1) was audited, and its capabilities were re-homed in existing modular Skills rather than copied wholesale:

- SRT-only project initialization belongs to [`report-video`](skills/report-video).
- Shared-library intake and catalog rebuilding belong to [`media-assets`](skills/media-assets).
- The explicit finance high-background variant belongs to the `jianting-research` preset under [`srt-visual-director`](skills/srt-visual-director).
- Segmented render recovery remains under the current [`report-video`](skills/report-video), [`remotion`](skills/remotion), and [`render-reliability`](skills/render-reliability) ownership. Its baseline and forward decision scenarios passed, so no duplicate legacy reference was added; those evaluations did not run a real long render.

## Object model

- **Skill** — an independently triggerable, coherent capability.
- **Router Skill** — selects the appropriate workflow or domain Skill.
- **Workflow Skill** — sequences Skills and owns handoffs and stop conditions.
- **Reference / Contract** — durable rules or formats read by a Skill.
- **Preset** — reusable directing or visual-style configuration selected and overridden by a project; not a triggerable Skill.
- **Script** — deterministic mechanical work that should not be reinvented in prose.
- **Project Artifact** — state passed between stages of one production.

## Start here

1. Read the [foundation design](docs/superpowers/specs/2026-09-04-v9-skills-foundation-design.md) for the complete map and decisions.
2. Use [`skills/video/SKILL.md`](skills/video/SKILL.md) as the entry router.
3. Read the relevant Skill and its linked references only for the requested stage.
4. Run `./scripts/validate-foundation.sh` after changing the foundation.

### 多投行研报文案

使用 `$multi-report-video-script` 处理同一家公司的多份投行研报。默认先生成阶段 A 的 Debate Map 并停止；确认后再要求阶段 B，输出可直接用于 TTS 的最终文案和制作备注。完整规则保存在 [`prompt-v1.md`](skills/multi-report-video-script/references/prompt-v1.md)。

## Deliberate non-goals for this phase

`asset-policy`, `technical-director`, `storyboard`, `shot-designer`, `health-video`, and `book-video` are not separate Skills yet. They become candidates only after repeated independent use or after an audit demonstrates a real boundary. The `srt-v1` capability audit and modular migration are complete; the remaining boundary is validation with real projects and samples. Repository scripts use only the Python standard library, but image quality, generated images, paid API behavior, and full video render quality still require that real-world validation.
