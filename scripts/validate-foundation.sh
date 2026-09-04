#!/usr/bin/env bash

set -euo pipefail

repo_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)

skills=(
  video
  report-video
  srt-visual-director
  media-assets
  remotion
  hyperframes
  render-reliability
)

for skill in "${skills[@]}"; do
  skill_file="$repo_dir/skills/$skill/SKILL.md"

  if [[ ! -f "$skill_file" ]]; then
    printf 'Missing Skill entrypoint: %s\n' "$skill_file" >&2
    exit 1
  fi

  if [[ $(sed -n '1p' "$skill_file") != "---" ]]; then
    printf 'Missing YAML frontmatter: %s\n' "$skill_file" >&2
    exit 1
  fi

  frontmatter_end=$(awk 'NR > 1 && $0 == "---" { print NR; exit }' "$skill_file")
  if [[ -z "$frontmatter_end" ]]; then
    printf 'Unclosed YAML frontmatter: %s\n' "$skill_file" >&2
    exit 1
  fi

  frontmatter=$(sed -n "2,$((frontmatter_end - 1))p" "$skill_file")
  if ! printf '%s\n' "$frontmatter" | rg -q '^name: [a-z0-9][a-z0-9-]*$'; then
    printf 'Invalid or missing name field: %s\n' "$skill_file" >&2
    exit 1
  fi
  if ! printf '%s\n' "$frontmatter" | rg -q '^description: .+$'; then
    printf 'Invalid or missing description field: %s\n' "$skill_file" >&2
    exit 1
  fi

  if rg -n 'TODO|TBD|\{\{[^}]+\}\}' "$skill_file" >/dev/null; then
    printf 'Placeholder text found: %s\n' "$skill_file" >&2
    exit 1
  fi
done

schema_count=0
for schema in "$repo_dir"/schemas/*.json; do
  if [[ ! -f "$schema" ]]; then
    printf 'No JSON schemas found in %s\n' "$repo_dir/schemas" >&2
    exit 1
  fi
  if command -v jq >/dev/null 2>&1; then
    jq -e . "$schema" >/dev/null
  elif command -v node >/dev/null 2>&1; then
    node -e 'JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"))' "$schema"
  else
    printf 'Need jq or node to parse JSON schemas.\n' >&2
    exit 1
  fi
  schema_count=$((schema_count + 1))
done

for legacy_dir in capabilities policies engines workflows; do
  if [[ -e "$repo_dir/$legacy_dir" ]]; then
    printf 'Unexpected conceptual parent directory: %s\n' "$repo_dir/$legacy_dir" >&2
    exit 1
  fi
done

printf 'Foundation validation passed: %s Skills and %s JSON schemas checked.\n' "${#skills[@]}" "$schema_count"
