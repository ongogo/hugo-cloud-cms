#!/usr/bin/env python3
"""
One-off content-hygiene pass for content/bbc-english/*.md.

Fixes, per file:
  1. Missing/non-standard `date:` field (uses `created:` as fallback source).
  2. `level` (CEFR: A2/B1/B2) and `difficulty` (plain English label) fields
     that are missing, inconsistently cased, or swapped with each other.
  3. Brand tag variants ("BBC", "BBC-Learning-English", "bbc-learning-english", ...)
     collapsed to the single canonical tag "BBC Learning English" so tag-based
     browsing isn't fragmented across four spellings of the same thing.
  4. Redundant raw `<audio>...</audio>` HTML blocks embedded in the post body
     (Hugo's default-safe Markdown renderer silently drops these; the theme
     already renders a real player from the `audio_url` front-matter field,
     so the raw block is dead weight, not a second player).

Every change is mechanical and idempotent - rerunning on already-fixed files
is a no-op.
"""
import re
import sys
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content" / "bbc-english"

# CEFR level -> canonical plain-English difficulty label
LEVEL_TO_DIFFICULTY = {
    "A2": "Beginner",
    "B1": "Intermediate",
    "B2": "Upper Intermediate",
}
# Canonical difficulty label -> CEFR level (for reverse inference)
DIFFICULTY_TO_LEVEL = {v.lower(): k for k, v in LEVEL_TO_DIFFICULTY.items()}
# Every synonym we've seen in the wild -> canonical difficulty label
DIFFICULTY_SYNONYMS = {
    "easy": "Beginner",
    "beginner": "Beginner",
    "a2": "Beginner",
    "intermediate": "Intermediate",
    "b1": "Intermediate",
    "upper-intermediate": "Upper Intermediate",
    "upper intermediate": "Upper Intermediate",
    "b2": "Upper Intermediate",
}

BBC_TAG_VARIANTS = {
    "bbc", "bbc learning english", "bbc-learning-english", "english/learning",
}

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
AUDIO_BLOCK_RE = re.compile(
    r"\n<audio controls>\n"
    r"  <source src=\"[^\"]*\" type=\"audio/mpeg\">\n"
    r"  [^\n]*\n"
    r"</audio>\n"
)


def strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def norm_key(name: str, quote: str = '"'):
    """Return a regex + setter for a simple `key: value` front-matter line."""
    return re.compile(rf'^{name}:\s*(.*)$', re.MULTILINE)


def fix_level_and_difficulty(fm: str) -> str:
    level_m = re.search(r'^level:\s*"?([A-Za-z0-9 \-]+?)"?\s*$', fm, re.MULTILINE)
    diff_m = re.search(r'^difficulty:\s*"?([A-Za-z0-9 \-]+?)"?\s*$', fm, re.MULTILINE)

    raw_level = strip_quotes(level_m.group(1)) if level_m else ""
    raw_diff = strip_quotes(diff_m.group(1)) if diff_m else ""

    cefr_re = re.compile(r"^(A2|B1|B2)$", re.IGNORECASE)

    resolved_level = None
    if cefr_re.match(raw_level):
        resolved_level = raw_level.upper()
    elif cefr_re.match(raw_diff):
        # fields were swapped
        resolved_level = raw_diff.upper()
    elif raw_diff.lower() in DIFFICULTY_SYNONYMS:
        resolved_level = DIFFICULTY_TO_LEVEL[DIFFICULTY_SYNONYMS[raw_diff.lower()].lower()]
    elif raw_level.lower() in DIFFICULTY_SYNONYMS:
        resolved_level = DIFFICULTY_TO_LEVEL[DIFFICULTY_SYNONYMS[raw_level.lower()].lower()]

    if resolved_level is None:
        # Nothing usable found; leave untouched.
        return fm

    resolved_difficulty = LEVEL_TO_DIFFICULTY[resolved_level]

    if level_m:
        fm = fm[: level_m.start()] + f'level: "{resolved_level}"' + fm[level_m.end():]
    else:
        fm = fm.rstrip("\n") + f'\nlevel: "{resolved_level}"\n'

    # Re-find difficulty line (offsets may have shifted if level line grew)
    diff_m = re.search(r'^difficulty:\s*"?([A-Za-z0-9 \-]+?)"?\s*$', fm, re.MULTILINE)
    if diff_m:
        fm = fm[: diff_m.start()] + f'difficulty: "{resolved_difficulty}"' + fm[diff_m.end():]
    else:
        fm = fm.rstrip("\n") + f'\ndifficulty: "{resolved_difficulty}"\n'

    return fm


def fix_date(fm: str, filename_date: str) -> str:
    if re.search(r'^date:\s*\S', fm, re.MULTILINE):
        return fm
    created_m = re.search(r'^created:\s*"?([0-9T:+\-]+)"?\s*$', fm, re.MULTILINE)
    date_val = strip_quotes(created_m.group(1)) if created_m else filename_date
    # Insert date: right after title: line if present, else at top.
    title_m = re.search(r'^title:.*$', fm, re.MULTILINE)
    line = f'date: {date_val}\n'
    if title_m:
        insert_at = title_m.end() + 1
        fm = fm[:insert_at] + line + fm[insert_at:]
    else:
        fm = line + fm
    return fm


def fix_bbc_tag(fm: str) -> str:
    def is_bbc_variant(token: str) -> bool:
        return strip_quotes(token).strip().lower() in BBC_TAG_VARIANTS

    def repl(m: re.Match) -> str:
        body = m.group(1)
        # Split on commas that are not inside quotes (tags never contain commas here).
        items = [t.strip() for t in body.split(",") if t.strip()]
        new_items = []
        replaced_once = False
        for item in items:
            if is_bbc_variant(item):
                if not replaced_once:
                    new_items.append('"BBC Learning English"')
                    replaced_once = True
                # drop duplicate BBC-ish tags beyond the first
            else:
                new_items.append(item)
        return "tags: [" + ", ".join(new_items) + "]"

    fm = re.sub(r"^tags:\s*\[(.*)\]\s*$", repl, fm, count=1, flags=re.MULTILINE)

    # Block (YAML list) style:
    #   tags:
    #    - english/learning
    #    - brain
    def repl_block(m: re.Match) -> str:
        lines = m.group(1).splitlines()
        new_lines = []
        replaced_once = False
        for ln in lines:
            item_m = re.match(r"^(\s*-\s*)(.*)$", ln)
            if not item_m:
                new_lines.append(ln)
                continue
            prefix, item = item_m.groups()
            if is_bbc_variant(item):
                if not replaced_once:
                    new_lines.append(f'{prefix}"BBC Learning English"')
                    replaced_once = True
            else:
                new_lines.append(ln)
        return "tags:\n" + "\n".join(new_lines) + "\n"

    fm = re.sub(r"^tags:\n((?:^ *-.*\n?)+)", repl_block, fm, count=1, flags=re.MULTILINE)
    return fm


def strip_redundant_audio_block(body: str) -> str:
    return AUDIO_BLOCK_RE.sub("\n", body, count=1)


def process(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return False
    fm = m.group(1)
    rest = text[m.end():]

    orig_fm, orig_rest = fm, rest

    date_from_filename = path.stem[:10]  # "YYYY-MM-DD"
    fm = fix_date(fm, date_from_filename)
    fm = fix_level_and_difficulty(fm)
    fm = fix_bbc_tag(fm)
    rest = strip_redundant_audio_block(rest)

    if fm == orig_fm and rest == orig_rest:
        return False

    path.write_text(f"---\n{fm.rstrip(chr(10))}\n---\n{rest}", encoding="utf-8")
    return True


def main():
    changed = []
    for path in sorted(CONTENT_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        if process(path):
            changed.append(path.name)
    print(f"Updated {len(changed)} file(s):")
    for name in changed:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
