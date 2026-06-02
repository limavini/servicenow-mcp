#!/usr/bin/env bash
#
# Installs the ServiceNow Claude skills bundled in this repo into the local
# Claude Code user skills directory (~/.claude/skills) via symlinks.
#
# Symlinks (not copies) so that pulling new commits updates the skills with no
# reinstall. Run again any time; it is idempotent.
#
#   bash claude-skills/install.sh
#
set -euo pipefail

SKILLS_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

mkdir -p "$SKILLS_DEST"

for dir in "$SKILLS_SRC"/*/; do
  name="$(basename "$dir")"
  dest="$SKILLS_DEST/$name"

  if [ -e "$dest" ] && [ ! -L "$dest" ]; then
    echo "!! skip '$name': $dest already exists and is NOT a symlink."
    echo "   Back it up and remove it, then re-run this script."
    continue
  fi

  ln -sfn "$dir" "$dest"
  echo "linked $name -> $dir"
done

echo "Done. Open Claude Code and the skills will be available (e.g. /servicenow-story-builder)."
