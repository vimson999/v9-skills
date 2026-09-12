---
name: multi-report-video-script
description: Use when writing a Chinese finance-video Debate Map or TTS-ready script from multiple investment-bank research reports about the same company, especially for 多投行交叉验证、兼听研报、机构分歧、目标价差异 or What Must Be True analysis.
metadata:
  short-description: Write multi-report finance video scripts
---

# Multi-report Video Script

Build finance-video scripts from competing institutional views. The question is the protagonist, the institutions are witnesses, facts are the base, disagreement supplies the drama, and the conclusion is a decision framework rather than a target-price recital.

## Required reference

Read [`references/prompt-v1.md`](references/prompt-v1.md) in full before producing either stage. Follow its required sections, writing rules, evidence discipline, and final checklist.

## Choose the stage

- **Stage A — Debate Map:** Use by default when the user supplies raw reports or source material. Produce the exact 11-section editorial-planning output defined in the reference, then stop for confirmation.
- **Stage B — final script:** Use only when the user supplies or confirms a Debate Map. Produce only the TTS-ready final script and production notes required by the reference.
- **Explicit one-pass request:** Build Stage A internally, then write Stage B. Preserve unresolved uncertainty instead of silently resolving conflicts.

## Inputs

Use reports about the same company. Accept the company, reports, platform, target duration, and desired length when available. If reports cover different companies, do not combine them into one Debate Map.

## Evidence discipline

1. Use report-supported facts only.
2. Distinguish reported facts, company guidance, institution forecasts, assumptions, and editorial synthesis.
3. Surface unresolved numerical conflicts, missing context, and OCR or extraction uncertainty.
4. Never invent ratings, target prices, EPS, valuation multiples, customers, causes, or timelines.
5. Do not give personalized buy/sell advice or turn uncertainty into certainty.

## Handoff boundary

This Skill writes editorial plans and narration scripts. It does not create visual storyboards, synthesize audio, or render video. After the script is approved, route visual planning and SRT alignment to [`srt-visual-director`](../srt-visual-director/SKILL.md).
