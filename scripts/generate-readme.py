#!/usr/bin/env python3
"""
Generate README.md from Hugo content files.

Usage:
    python3 scripts/generate-readme.py
"""

import re
from pathlib import Path
from collections import defaultdict

ROOT       = Path(__file__).parent.parent
TOOLS_DIR  = ROOT / "content" / "tools"
CATS_FILE  = ROOT / "data" / "categories.yaml"
README_OUT = ROOT / "README.md"

REPO_URL   = "https://github.com/best-of-ai/best-of-ai"
SITE_URL   = "https://bestofai.io"


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_frontmatter(text):
    """Extract key: 'value' pairs from YAML frontmatter."""
    m = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    result = {}
    for line in block.splitlines():
        kv = re.match(r"^(\w+):\s*'(.*)'$", line)
        if kv:
            result[kv.group(1)] = kv.group(2).replace("''", "'")
            continue
        kv2 = re.match(r'^(\w+):\s*(true|false|\d+)$', line)
        if kv2:
            v = kv2.group(2)
            result[kv2.group(1)] = True if v == 'true' else (False if v == 'false' else int(v))
    return result


def parse_categories_yaml(text):
    """Parse the flat YAML list into a list of dicts."""
    cats = []
    current = {}
    for line in text.splitlines():
        if line.strip() == '-':
            if current:
                cats.append(current)
            current = {}
        else:
            kv = re.match(r"^\s+(\w+):\s*'(.*)'$", line)
            if kv:
                current[kv.group(1)] = kv.group(2).replace("''", "'")
                continue
            kv2 = re.match(r'^\s+(\w+):\s*(-?\d+)$', line)
            if kv2:
                current[kv2.group(1)] = int(kv2.group(2))
    if current:
        cats.append(current)
    return cats


# ── Load data ─────────────────────────────────────────────────────────────────

categories = parse_categories_yaml(CATS_FILE.read_text())
# Sort: named categories (sort_order > 0) first by sort_order, then alphabetical
categories.sort(key=lambda c: (0 if c.get('sort_order', 0) > 0 else 1, c.get('sort_order', 99), c.get('name', '')))

cat_by_slug = {c['slug']: c for c in categories}

tools_by_cat = defaultdict(list)
for f in sorted(TOOLS_DIR.glob('*.md')):
    tool = parse_frontmatter(f.read_text())
    if tool.get('category'):
        tools_by_cat[tool['category']].append(tool)

# Sort tools within each category alphabetically
for slug in tools_by_cat:
    tools_by_cat[slug].sort(key=lambda t: t.get('name', '').lower())

total_tools = sum(len(v) for v in tools_by_cat.values())
active_cats = [c for c in categories if tools_by_cat.get(c['slug'])]


# ── Price badge ───────────────────────────────────────────────────────────────

PRICE_BADGE = {
    'Free':     '![Free](https://img.shields.io/badge/-Free-3fb950?style=flat-square)',
    'Freemium': '![Freemium](https://img.shields.io/badge/-Freemium-d29922?style=flat-square)',
    'Paid':     '![Paid](https://img.shields.io/badge/-Paid-8b949e?style=flat-square)',
}

def price_badge(price):
    return PRICE_BADGE.get(price, f'`{price}`')


# ── Build README ──────────────────────────────────────────────────────────────

lines = []

# Header
lines += [
    '<div align="center">',
    '',
    '# Awesome Best of AI',
    '',
    '> Handpicked AI tools — no fluff, no mediocre apps. Every tool carefully selected for quality, innovation, and real-world impact.',
    '',
    f'[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)',
    f'[![Tools](https://img.shields.io/badge/tools-{total_tools}-f97316?style=flat-square)]({REPO_URL})',
    f'[![Categories](https://img.shields.io/badge/categories-{len(active_cats)}-f97316?style=flat-square)]({REPO_URL})',
    f'[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)',
    '',
    f'**[🌐 Website]({SITE_URL})** &nbsp;·&nbsp; **[➕ Submit a Tool]({REPO_URL}/issues/new?template=submit-tool.md&title=Submit+Tool%3A+)** &nbsp;·&nbsp; **[🤝 Contributing](CONTRIBUTING.md)**',
    '',
    '</div>',
    '',
    '---',
    '',
]

# Table of Contents
lines += ['## Contents', '']
for cat in active_cats:
    slug    = cat['slug']
    name    = cat['name']
    count   = len(tools_by_cat[slug])
    anchor  = slug.lower().replace(' ', '-')
    lines.append(f'- [{name}](#{anchor}) ({count})')
lines += ['', '---', '']

# Category sections
for cat in active_cats:
    slug  = cat['slug']
    name  = cat['name']
    desc  = cat.get('description', '').strip()
    tools = tools_by_cat[slug]

    lines.append(f'## {name}')
    lines.append('')
    if desc:
        lines.append(f'> {desc}')
        lines.append('')

    for t in tools:
        tool_name = t.get('name', '')
        website   = t.get('website', '')
        desc_text = t.get('description', '')
        price     = t.get('price', '')

        # Truncate long descriptions
        if len(desc_text) > 120:
            desc_text = desc_text[:117].rstrip() + '...'

        badge = price_badge(price) if price else ''

        if website:
            entry = f'- **[{tool_name}]({website})**'
        else:
            entry = f'- **{tool_name}**'

        if desc_text:
            entry += f' — {desc_text}'
        if badge:
            entry += f' {badge}'

        lines.append(entry)

    lines += ['', '---', '']

# Footer
lines += [
    '## Contributing',
    '',
    f'See [CONTRIBUTING.md](CONTRIBUTING.md) to add or update tools.',
    '',
    f'Found a bug or want to suggest something? [Open an issue]({REPO_URL}/issues/new).',
    '',
    '## License',
    '',
    'MIT — see [LICENSE](LICENSE).',
    '',
    '---',
    '',
    f'<sub>This file is auto-generated from [`content/tools/`](content/tools/). Edit the source files, not this file directly.</sub>',
    '',
]

README_OUT.write_text('\n'.join(lines), encoding='utf-8')
print(f"README.md written — {total_tools} tools, {len(active_cats)} categories")
