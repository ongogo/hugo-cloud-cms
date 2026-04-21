#!/usr/bin/env python3
"""
BBC Learning English Content Processor
Fetches BBC Learning English lessons and generates Hugo markdown files.

Usage:
    python scripts/fetch_bbc_lesson.py <BBC_LEARNING_ENGLISH_URL>

Requirements:
    - requests
    - A Hugo site at ../hugo-cloud-cms/
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import quote
from datetime import datetime

import requests


def translate_words(words: list) -> dict:
    """Translate English words to Chinese using Google Translate batch API.
    Returns dict mapping original word -> Chinese translation.
    """
    if not words:
        return {}
    try:
        base_url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t"
        query_params = "".join(f"&q={quote(w)}" for w in words)
        url = base_url + query_params
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        translations = {}
        # data structure: list of [ [[translated, ...]], ... ] + "en"
        # We iterate through data[:-1] to skip language code at end if present
        for i, entry in enumerate(data[:-1]):
            if isinstance(entry, list) and entry and entry[0]:
                translated = entry[0][0]
                translations[words[i]] = translated
        return translations
    except Exception as e:
        # Fail silently, return empty dict
        pass
    return {}


def extract_audio_url(html: str) -> str:
    """Extract audio URL from BBC page HTML."""
    # Look for <audio> with <source>
    match = re.search(r'<audio[^>]*>.*?<source[^>]*src="([^"]+)"', html, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1)
    # Alternative: data-audio-url attribute
    match = re.search(r'data-audio-url="([^"]+)"', html)
    if match:
        return match.group(1)
    # Some pages use mp3 link directly
    match = re.search(r'href="([^"]+\.mp3)"', html, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def extract_transcript(html: str) -> str:
    """Extract transcript text from BBC page HTML."""
    # BBC uses various structures; try common ones
    match = re.search(
        r'<div class="(?:transcription|transcript)"[^>]*>(.*?)</div>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        content = match.group(1)
        # Remove any inner tags but keep text
        content = re.sub(r'<[^>]+>', '', content)
        return "\n".join(line.strip() for line in content.splitlines() if line.strip())
    # Fallback: find a <div> with id containing transcript
    match = re.search(r'<div[^>]*id="[^"]*transcript[^"]*"[^>]*>(.*?)</div>', html, re.IGNORECASE | re.DOTALL)
    if match:
        content = match.group(1)
        content = re.sub(r'<[^>]+>', '', content)
        return "\n".join(line.strip() for line in content.splitlines() if line.strip())
    return "(Transcript not available)"


def extract_key_vocabulary(html: str) -> list:
    """Extract highlighted vocabulary words from BBC page HTML.
    Limit to 12 words max to keep content focused.
    """
    vocab = []
    # BBC sometimes marks vocabulary with <strong> or <b> in a certain section
    # Looking for pattern: <strong>word</strong> followed by parenthetical definition
    pairs = re.finditer(
        r'<strong>([^<]+)</strong>\s*\(([^\)]+)\)',
        html,
        re.IGNORECASE,
    )
    for m in pairs:
        word = m.group(1).strip()
        definition = m.group(2).strip()
        vocab.append((word, definition))
    # Also try pattern: <b>word</b> - definition
    if not vocab:
        pairs = re.finditer(r'<b>([^<]+)</b>\s*\-\s*([^<\n]+)', html, re.IGNORECASE)
        for m in pairs:
            word = m.group(1).strip()
            definition = m.group(2).strip()
            vocab.append((word, definition))
    # If still none, try to extract capitalized words from headings
    if not vocab:
        # Simple heuristic: extract words longer than 5 chars that appear in h2/h3
        potential = re.findall(r'<h[23][^>]*>([^<]+)</h[23]>', html, re.IGNORECASE)
        for phrase in potential:
            words = re.findall(r'\b[A-Za-z]{6,}\b', phrase)
            for w in words:
                vocab.append((w, ''))
    # Limit to 12 words max
    return vocab[:12]


def extract_date_from_url(url: str) -> str:
    """Try to extract date from BBC URL, e.g., /260408 -> 2026-04-08"""
    # Find last segment: e.g., .../260408
    match = re.search(r'/([0-9]{6})[^/]*$', url)
    if match:
        digits = match.group(1)
        try:
            # Assume format: YYMMDD or similar
            # For BBC 260408 => 2026-04-08
            year = "20" + digits[:2]
            month = digits[2:4]
            day = digits[4:6]
            # Validate date
            datetime(int(year), int(month), int(day))
            return f"{year}-{month}-{day}"
        except Exception:
            pass
    # Default to today's date
    return datetime.now().strftime("%Y-%m-%d")


def generate_markdown(data: dict, output_path: Path) -> Path:
    """Generate Hugo markdown file from extracted data."""
    # Sanitize filename
    slug = re.sub(r'[^a-z0-9]+', '-', data['title'].lower()).strip('-')
    date_str = data.get('date', '')
    filename = f"{date_str}-{slug}.md"
    filepath = output_path / filename

    # Build markdown content
    lines = []
    # Front matter
    lines.append("---")
    lines.append(f'title: "{data["title"]}"')
    lines.append(f"date: {date_str}T10:00:00+08:00")
    tags = data.get('tags', [])
    lines.append(f"tags: {tags}")
    lines.append(f"author: \"BBC Learning English\"")
    lines.append(f'audio_url: "{data["audio_url"]}"')
    lines.append(f'level: "{data["level"]}"')
    lines.append(f'description: "{data["description"]}"')
    lines.append('difficulty: "intermediate"')
    lines.append('topic: "BBC Listening"')
    lines.append(f'summary_zh: "{data["summary_zh"]}"')
    lines.append(f'source_url: "{data["source_url"]}"')
    lines.append("---")
    lines.append("")
    # Title and metadata
    lines.append(f"# 【BBC 听力】{data['title']}")
    lines.append("")
    lines.append("**来源**: BBC Learning English  ")
    lines.append(f"**等级**: {data['level']} (Intermediate)  ")
    lines.append(f"**时长**: {data.get('duration', '未知')}  ")
    lines.append("**学习目标**: Listening & Vocabulary")
    lines.append("")
    lines.append("---")
    lines.append("")
    # Audio section
    lines.append("## 播放音频")
    lines.append("")
    if data['audio_url']:
        lines.append(f"{{{{< audio \"{data['audio_url']}\" >}}}}")
        lines.append("")
        lines.append("*点击播放按钮收听音频*")
    else:
        lines.append("*音频文件暂不可用*")
    lines.append("")
    lines.append("---")
    lines.append("")
    # Transcript section
    lines.append("## 听力原文 (Transcript)")
    lines.append("")
    transcript = data.get('transcript', '').strip()
    lines.append(transcript)
    lines.append("")
    lines.append("---")
    lines.append("")
    # Vocabulary - translate in batch
    vocab = data.get('vocabulary', [])
    if vocab:
        # Extract words for batch translation
        words = [word for word, _ in vocab]
        translations = translate_words(words)
        lines.append("## 重点词汇与短语")
        lines.append("")
        lines.append("| English | 中文释义 | 词性 | 例句 |")
        lines.append("|---------|---------|------|------|")
        for word, def_eng in vocab:
            chinese = translations.get(word, "")
            # Part of speech placeholder
            pos = ""
            if def_eng:
                if "noun" in def_eng.lower():
                    pos = "n."
                elif "verb" in def_eng.lower():
                    pos = "v."
                elif "adjective" in def_eng.lower():
                    pos = "adj."
                elif "adverb" in def_eng.lower():
                    pos = "adv."
            example = def_eng if def_eng else ""
            lines.append(f"| {word} | {chinese} | {pos} | {example} |")
        lines.append("")
        lines.append("---")
        lines.append("")
    # Chinese summary
    lines.append("## 中文总结")
    lines.append("")
    lines.append(data.get('summary_zh', 'BBC 听力课程内容'))
    lines.append("")
    lines.append("---")
    lines.append("")
    # Practice questions
    lines.append("## 练习题")
    lines.append("")
    lines.append("1. 根据听力内容，回答以下问题：")
    lines.append("   - What is the main topic of this lesson?")
    lines.append("   - What new vocabulary did you learn?")
    lines.append("")
    lines.append("2. 词汇练习：用今天学到的单词造句。")
    lines.append("")
    lines.append("3. 听写练习：听音频并尝试写下关键句子。")
    lines.append("")
    lines.append("---")
    lines.append("")
    # Teacher tip
    lines.append("## Teacher's Tip")
    lines.append("")
    lines.append(
        "建议先完整听一遍音频，获取整体理解；第二遍听时，关注重点词汇和表达方式；"
        "对照原文检查理解程度；模仿语音语调，提升口语表达。"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**标签**: BBC, Listening, B1, Vocabulary, Intermediate")

    # Write to file
    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Fetch BBC Learning English lesson and generate Hugo markdown")
    parser.add_argument("url", help="BBC Learning English lesson URL")
    parser.add_argument("--output", "-o", default="/home/ongogo/Al-Projects/hugo-cloud-cms/content/bbc-english", help="Output directory")
    parser.add_argument("--level", "-l", default="B1", help="Difficulty level (default: B1)")
    parser.add_argument("--tags", "-t", nargs="*", default=[], help="Additional tags")
    args = parser.parse_args()

    print(f"Fetching BBC lesson from: {args.url}")
    try:
        resp = requests.get(args.url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"Error fetching URL: {e}")
        sys.exit(1)

    # Extract data
    title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else "BBC Learning English"

    # Default tags
    base_tags = ["BBC", "Listening", args.level]
    base_tags.extend(args.tags)

    data = {
        "title": title,
        "date": extract_date_from_url(args.url),
        "audio_url": extract_audio_url(html),
        "level": args.level,
        "duration": "",
        "description": "",
        "summary_zh": "BBC 英语学习课程",
        "transcript": extract_transcript(html),
        "vocabulary": extract_key_vocabulary(html),
        "source_url": args.url,
        "tags": base_tags,
    }

    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    filepath = generate_markdown(data, output_path)
    print(f"Generated markdown file: {filepath}")
    print(f"Next steps:")
    print(f"1. Review and edit the generated file: {filepath}")
    print(f"2. Customize the summary and description if needed")
    print(f"3. Run 'hugo' to build the site")


if __name__ == "__main__":
    main()
