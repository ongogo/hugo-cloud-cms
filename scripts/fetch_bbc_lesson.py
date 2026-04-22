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
