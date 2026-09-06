#!/usr/bin/env python3
"""Parse SRT and validate image-v1 planning handoffs; no media/API side effects."""

import argparse
import json
from pathlib import Path
import re
import sys

STAMP = r"(\d{2,}):([0-5]\d):([0-5]\d)[,.](\d{3})"
TIMELINE = re.compile(r"^" + STAMP + r"\s*-->\s*" + STAMP + r"(?:\s+.*)?$")
SCHEMA = Path(__file__).resolve().parents[1] / "references/image-storyboard.schema.json"


def milliseconds(parts):
    h, m, s, ms = map(int, parts)
    return ((h * 60 + m) * 60 + s) * 1000 + ms


def parse_srt(text):
    """Preserve source cue numbers and overlaps; reject malformed/unsorted cues."""
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        raise ValueError("SRT is empty")
    cues, seen, warnings = [], set(), []
    for block in re.split(r"\n\s*\n", text):
        lines = block.splitlines()
        if len(lines) < 3 or not re.fullmatch(r"\d+", lines[0].strip()):
            raise ValueError("Malformed SRT block: expected numeric cue, timing, text")
        number = int(lines[0].strip())
        cue_id = f"srt-{number:03d}"
        match = TIMELINE.fullmatch(lines[1].strip())
        if not match:
            raise ValueError(f"{cue_id}: invalid timestamp line")
        start, end = milliseconds(match.groups()[:4]), milliseconds(match.groups()[4:])
        body = "\n".join(lines[2:]).strip()
        if not body or end <= start or cue_id in seen:
            raise ValueError(f"{cue_id}: empty text, duplicate ID, or nonpositive duration")
        if cues and start < cues[-1]["startMs"]:
            raise ValueError(f"{cue_id}: start times are out of order")
        if cues and start < max(c["endMs"] for c in cues):
            warnings.append(f"{cue_id}: overlapping subtitle interval retained")
        if cues and start > max(c["endMs"] for c in cues):
            warnings.append(f"{cue_id}: subtitle gap retained")
        seen.add(cue_id)
        cues.append({"id": cue_id, "startMs": start, "endMs": end, "text": body})
    return {"cues": cues, "lastCueEndMs": max(c["endMs"] for c in cues), "warnings": warnings}


def load_plan(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    if Path(path).suffix.lower() == ".md":
        blocks = re.findall(r"^```json\s*\n(.*?)^```\s*$", text, flags=re.M | re.S)
        if len(blocks) != 1:
            raise ValueError("STORYBOARD.md must contain exactly one JSON block")
        text = blocks[0]
    return json.loads(text)


def shape_errors(value, schema, at="$", errors=None):
    """Check the structural keywords used by our bundled schema, not arbitrary schemas.

    Semantic cross-field rules live in validate_plan. No third-party dependency.
    """
    errors = [] if errors is None else errors
    if "const" in schema and value != schema["const"]:
        errors.append(f"{at}: expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{at}: invalid enum value")
    types = schema.get("type", [])
    types = [types] if isinstance(types, str) else types
    checks = {"null": value is None, "object": isinstance(value, dict),
              "array": isinstance(value, list), "string": isinstance(value, str),
              "integer": type(value) is int, "boolean": type(value) is bool}
    if types and not any(checks[t] for t in types):
        errors.append(f"{at}: expected {types}")
        return errors
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{at}.{key}: missing")
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                shape_errors(item, properties[key], f"{at}.{key}", errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{at}.{key}: unexpected field")
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{at}: too few items")
        for i, item in enumerate(value):
            shape_errors(item, schema.get("items", {}), f"{at}[{i}]", errors)
    elif isinstance(value, str):
        if len(value.strip()) < schema.get("minLength", 0):
            errors.append(f"{at}: empty string")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{at}: invalid format")
    elif type(value) is int and value < schema.get("minimum", value):
        errors.append(f"{at}: below minimum")
    return errors


def validate_plan(plan, cues=None, *, directing_profile=None, visual_style=None):
    errors = shape_errors(plan, json.loads(SCHEMA.read_text(encoding="utf-8")))
    if errors:
        return errors
    # Expectations come from the request, not from the generated plan itself.
    # Matching metadata does not prove the preset was read or applied faithfully.
    for key, expected in (("directingProfile", directing_profile), ("visualStyle", visual_style)):
        if expected is not None:
            selected = plan.get("direction", {}).get(key)
            if not selected or selected["id"] != expected:
                errors.append(f"direction.{key}: requested preset {expected!r} needs a matching snapshot")
    timing, shots = plan["timing"], plan["shots"]
    timed = timing["kind"] == "srt"
    ready = plan["status"] == "ready"
    if ready and (not plan["style"]["confirmed"] or not plan["style"]["aspectRatio"] or plan["openQuestions"]):
        errors.append("ready requires confirmed style, aspect ratio, and no open questions")
    if plan["assetLibrary"]["status"] == "searched" and not plan["assetLibrary"]["source"]:
        errors.append("searched library must identify actual search source")
    if timed:
        if not timing["srtPath"] or timing["startMs"] is None or timing["endMs"] is None:
            errors.append("srt timing requires source path and range")
        elif timing["endMs"] <= timing["startMs"]:
            errors.append("timing range must have positive duration")
        if cues is None:
            errors.append("SRT-mode validation requires the actual SRT via --srt")
    elif ready or timing["srtPath"] is not None or timing["startMs"] is not None or timing["endMs"] is not None:
        errors.append("untimed plans must be planned with null SRT path and range")
    if errors:
        return errors
    if timed and timing["audioDurationMs"] is not None and timing["endMs"] > timing["audioDurationMs"]:
        errors.append("requested range exceeds known audio duration")
    boundaries = {timing["startMs"], timing["endMs"]}
    for cue in cues or []:
        boundaries.update((cue["startMs"], cue["endMs"]))
    cursor, seen = timing["startMs"], set()
    for shot in shots:
        sid, start, end = shot["id"], shot["startMs"], shot["endMs"]
        if sid in seen:
            errors.append(f"{sid}: duplicate shot ID")
        seen.add(sid)
        basis = shot["timingBasis"]
        if timed:
            if start is None or end is None:
                errors.append(f"{sid}: SRT shot needs integer times")
            else:
                if start != cursor or end <= start:
                    errors.append(f"{sid}: gap, overlap, or nonpositive visual interval")
                cursor = end
                expected = {c["id"] for c in cues if c["startMs"] < end and c["endMs"] > start}
                if set(shot["voiceoverRefs"]) != expected:
                    errors.append(f"{sid}: subtitle references do not match interval; expected {sorted(expected)}")
                if basis == "cue_boundary" and (start not in boundaries or end not in boundaries):
                    errors.append(f"{sid}: internal cut must not claim cue_boundary")
            if basis == "untimed":
                errors.append(f"{sid}: SRT shot cannot be untimed")
        elif start is not None or end is not None or shot["voiceoverRefs"] or basis != "untimed":
            errors.append(f"{sid}: untimed shot must have null times, no cue refs, and untimed basis")
        if len(set(shot["voiceoverRefs"])) != len(shot["voiceoverRefs"]):
            errors.append(f"{sid}: duplicate cue reference")
        if basis in {"estimated", "manual", "audio_verified"} and not shot["timingNote"].strip():
            errors.append(f"{sid}: timing basis needs an explanation")
        image = shot["image"]
        action, ref, prompt = image["action"], image["assetRef"], image["prompt"]
        if action in {"reuse", "edit"}:
            if ref is None or not ref["viewed"] or ref["useStatus"] != "confirmed":
                errors.append(f"{sid}: reuse/edit requires a viewed, confirmed reference")
        elif ref is not None:
            errors.append(f"{sid}: unresolved/new asset must not claim a selected assetRef")
        if action in {"generate", "edit"}:
            if not prompt or not prompt.strip():
                errors.append(f"{sid}: generate/edit requires a complete prompt")
        elif prompt is not None:
            errors.append(f"{sid}: action requires prompt=null")
        if action == "external_design":
            if not image["designBrief"] or not image["designBrief"].strip():
                errors.append(f"{sid}: external_design requires a design brief")
        elif image["designBrief"] is not None:
            errors.append(f"{sid}: designBrief must be null for this action")
        if ready and (basis == "estimated" or action == "search_pending"):
            errors.append(f"{sid}: unresolved timing/assets cannot be planning-ready")
    if timed and cursor != timing["endMs"]:
        errors.append("visual timeline does not end at requested range end")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    parse = sub.add_parser("parse")
    parse.add_argument("srt", type=Path)
    validate = sub.add_parser("validate")
    validate.add_argument("storyboard", type=Path)
    validate.add_argument("--srt", type=Path)
    validate.add_argument("--directing-profile", help="Expected directing preset ID from the user/project request")
    validate.add_argument("--visual-style", help="Expected visual preset ID from the user/project request")
    args = parser.parse_args(argv)
    try:
        if args.command == "parse":
            result = parse_srt(args.srt.read_text(encoding="utf-8-sig"))
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        cues = parse_srt(args.srt.read_text(encoding="utf-8-sig"))["cues"] if args.srt else None
        errors = validate_plan(load_plan(args.storyboard), cues,
                               directing_profile=args.directing_profile, visual_style=args.visual_style)
        checks = ["schema", "timing", "asset_handoff"]
        if args.directing_profile is not None or args.visual_style is not None:
            checks.append("requested_preset_metadata")
        print(json.dumps({"valid": not errors, "errors": errors, "checks": checks,
                          "notChecked": ["preset_rule_fidelity", "visual_semantics", "image_quality", "audio_sync"]},
                         ensure_ascii=False, indent=2))
        return 1 if errors else 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
