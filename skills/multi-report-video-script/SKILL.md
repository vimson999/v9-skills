---
name: multi-report-video-script
description: Use when writing a Chinese finance-video Debate Map or TTS-ready script from multiple investment-bank research reports about the same company, especially for 多投行交叉验证、兼听研报、机构分歧、目标价差异 or What Must Be True analysis.
metadata:
  short-description: Write multi-report finance video scripts
---

# Multi-report Video Script

Build finance-video scripts from competing institutional views. The question is the protagonist, institutions are witnesses, facts are the base, and disagreement supplies the drama. Research proves the claims; the TTS deliverable tells the story. Never mix those layers.

## Required reference

Read [`references/prompt-v1.md`](references/prompt-v1.md) in full before producing either stage. Its output contract overrides the instinct to display research provenance inside the TTS copy.

## Choose the stage

- **Stage A — research and Debate Map:** Use by default with raw reports. Build a sourced evidence layer and the exact 11-section Debate Map, then stop for confirmation.
- **Stage B — delivery:** Use only from a supplied or approved Debate Map. Stage B changes how approved research is told; it does not introduce a new thesis, dispute, fact, or structure.
- **Explicit one-pass request:** Complete the evidence and Debate Map layers internally before Stage B. Preserve unresolved uncertainty.

## Strict delivery flow

1. **Research evidence layer:** Verify facts, ratings, targets, forecasts, and models with report-level citations.
2. **Debate Map:** Fix the mother question, disputes, institution positions, second climax, and validation metrics.
3. **TTS master draft:** Follow only the approved map; remove citations, source markers, visual directions, and writing commentary.
4. **TTS cleanup:** Normalize abbreviations, symbols, sentence length, number density, repeated phrases, and spoken rhythm. Formula on screen; logic in narration.
5. **Delivery gate:** Require opening anomaly, mother question, second climax, Takeaway, and a short disclaimer unless the user explicitly opts out.
6. **Production notes:** Put source mapping, on-screen numbers, interactions, and validation metrics outside the TTS copy.

## Inputs

Use reports about the same company. Accept the company, reports, platform, target duration, and desired length when available. If reports cover different companies, do not combine them into one Debate Map.

## Evidence discipline

1. Use report-supported facts only.
2. Distinguish reported facts, company guidance, institution forecasts, assumptions, and editorial synthesis.
3. Surface unresolved numerical conflicts, missing context, and OCR or extraction uncertainty.
4. Never invent ratings, target prices, EPS, valuation multiples, customers, causes, or timelines.
5. Do not give personalized buy/sell advice or turn uncertainty into certainty.

## Stage B output contract

Return exactly two parts. Part A is clean, copy-ready TTS prose ordered as body → Takeaway → disclaimer. It contains no `filecite`, source label, footnote, URL, Markdown table, visual direction, or writing note. Part B contains production notes and the source-check map. Run the reference checklist before returning either part; if Part A contains a forbidden marker, rewrite it rather than explaining the mistake.

## Handoff boundary

This Skill writes editorial plans and narration scripts. It does not create visual storyboards, synthesize audio, or render video. After the script is approved, route visual planning and SRT alignment to [`srt-visual-director`](../srt-visual-director/SKILL.md).
