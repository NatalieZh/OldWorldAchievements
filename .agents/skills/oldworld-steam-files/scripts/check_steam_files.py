"""Validate a local Steam guide package; never changes the package or publishes it."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_bbcode(text, filename):
    allowed = {'b', 'i', 'u', 'strike', 'h1', 'h2', 'h3', 'url', 'list', 'olist',
               'code', 'quote', 'spoiler', 'noparse'}
    stack = []
    for match in re.finditer(r'\[(/?)([A-Za-z]+|\*)(?:=([^\]\r\n]+))?\]', text):
        closing, name, _ = match.groups()
        name = name.lower()
        if name == '*':
            require(not closing and any(x in {'list', 'olist'} for x in stack),
                    f'{filename}: list item outside a list')
            continue
        if name == 'hr' and not closing:
            continue
        require(name in allowed, f'{filename}: unknown BBCode tag {name}')
        if closing:
            require(stack and stack[-1] == name, f'{filename}: mismatched closing tag {name}')
            stack.pop()
        else:
            stack.append(name)
    require(not stack, f'{filename}: unclosed BBCode tags {stack}')


def check(folder, coverage_path, limit):
    folder = folder.resolve()
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    coverage = json.loads(coverage_path.read_text(encoding='utf-8'))
    expected = coverage['ids']
    require(len(expected) == len(set(expected)), 'Coverage contains duplicate IDs')
    require(coverage['count'] == len(expected), 'Coverage count does not match its IDs')
    sections = manifest['sections']
    require(sections, 'Manifest has no sections')
    files, ids = [], []
    largest = 0
    for section in sections:
        filename = section['file']
        require(isinstance(filename, str) and re.fullmatch(r'[^/\\:]+\.txt', filename),
                f'Unsafe or invalid TXT filename: {filename!r}')
        require(section.get('title'), f'{filename}: missing section title')
        files.append(filename)
        raw = (folder / filename).read_bytes()
        require(not raw.startswith(b'\xef\xbb\xbf'), f'{filename}: UTF-8 BOM is not expected')
        text = raw.decode('utf-8', errors='strict')
        require(bool(text.strip()), f'{filename}: empty file')
        require('\r' not in text, f'{filename}: use LF line endings')
        require('\ufffd' not in text and '\u200b' not in text, f'{filename}: damaged or invisible text')
        require(len(text) <= limit and len(raw) <= limit, f'{filename}: exceeds {limit} characters or bytes')
        require(section['characters'] == len(text), f'{filename}: character count differs from manifest')
        require(section['utf8Bytes'] == len(raw), f'{filename}: byte count differs from manifest')
        require(section['sha256'] == hashlib.sha256(raw).hexdigest(), f'{filename}: checksum mismatch')
        require(not re.search(r'<!--|\*\*|(?m:^#{1,3} )|\]\(https?://', text),
                f'{filename}: Markdown or a service comment remains')
        require('Условие Steam:' not in text, f'{filename}: use the established label Условие:')
        check_bbcode(text, filename)
        section_ids = section['ids']
        require(isinstance(section_ids, list), f'{filename}: IDs must be a list')
        if section_ids:
            require(len(re.findall(r'\[h2\]', text, flags=re.I)) == len(section_ids),
                    f'{filename}: achievement heading count differs from ID count')
        ids.extend(section_ids)
        largest = max(largest, len(raw))
    require(len(files) == len(set(files)), 'Manifest lists a TXT file more than once')
    require(set(files) == {p.name for p in folder.glob('*.txt')}, 'TXT files differ from manifest (missing or stale files)')
    require(len(ids) == len(set(ids)), 'Output contains duplicate achievement IDs')
    require(set(ids) == set(expected) and len(ids) == len(expected), 'Output coverage differs from the plan')
    require(manifest['count'] == len(expected), 'Manifest count differs from coverage')
    print(f'PASS: {len(ids)} achievements, {len(sections)} sections; largest {largest} UTF-8 bytes; metadata, coverage and BBCode match.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--coverage', required=True, type=Path)
    parser.add_argument('--limit', type=int, default=6000,
                        help='Editorial budget in characters and UTF-8 bytes, not a documented Steam limit')
    args = parser.parse_args()
    try:
        require(args.limit > 0, 'Limit must be positive')
        check(args.folder, args.coverage, args.limit)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
