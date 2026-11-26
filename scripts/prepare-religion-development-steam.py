"""Build and validate the Russian Steam guide from its reviewed Markdown source."""
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs/steam-guides'
OUT = DOCS / 'steam-ready/religion-development-ru'
LIMIT = 6000  # Editorial budget in both characters and UTF-8 bytes, not Steam's documented limit.
SOURCE = DOCS / 'religion-development-draft.md'


def bbcode(text):
    text = re.sub(r'<!--.*?-->\n?', '', text, flags=re.S)
    text = re.sub(r'^> ?', '', text, flags=re.M)
    text = re.sub(r'^### (.+)$', r'[h2]\1[/h2]', text, flags=re.M)
    text = re.sub(r'\*\*(.+?)\*\*', r'[b]\1[/b]', text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'[url=\2]\1[/url]', text)
    text = text.replace('`', '')
    text = re.sub(r'(?m)^- (.+)$', r'• \1', text)
    return text.strip()


def validate_tags(text):
    stack = []
    for match in re.finditer(r'\[(/?)(b|h2|url)(?:=[^\]]+)?\]', text):
        closing, tag = match.group(1, 2)
        if closing:
            assert stack and stack.pop() == tag, ('Unbalanced BBCode', match.group())
        else:
            stack.append(tag)
    assert not stack, stack
    assert not re.search(r'<!--|\*\*|^#{1,3} |\]\(https?://', text, re.M), 'Markdown left in Steam output'
    assert '\ufffd' not in text and '\u200b' not in text, 'Invalid or invisible characters'


def render(text):
    text = html.escape(text)
    text = re.sub(r'\[h2\](.*?)\[/h2\]', r'<h3>\1</h3>', text, flags=re.S)
    text = re.sub(r'\[b\](.*?)\[/b\]', r'<strong>\1</strong>', text, flags=re.S)
    text = re.sub(r'\[url=(https?://[^\]]+)\](.*?)\[/url\]', r'<a href="\1">\2</a>', text, flags=re.S)
    return text.replace('\n', '<br>\n')


def main():
    source = SOURCE.read_text(encoding='utf-8')
    expected = json.loads((DOCS / 'religion-development-coverage.json').read_text())['ids']
    all_ids = re.findall(r'<!-- achievement: (a\d+) -->', source)
    assert len(all_ids) == len(set(all_ids)) == 43
    assert all_ids == expected, 'Coverage differs from the series plan'
    steam = json.loads((DOCS / 'religion-development-steam-check.json').read_text(encoding='utf-8'))
    for entry in steam['entries']:
        assert entry['steam'], ('Missing official Steam entry', entry['id'])
        title = re.search(r'^### ([^\n]+)\n<!-- achievement: '+entry['id']+r' -->', source, re.M)[1]
        assert re.sub(r' \([^()]+\)$', '', title) == entry['steam'][0], ('Steam title mismatch', entry['id'])
        match = re.search(r'<!-- achievement: ' + entry['id'] + r' -->\n\*\*Условие:\*\* ([^\n]+)', source)
        assert match and match[1] == entry['steam'][1], ('Steam condition mismatch', entry['id'])
    date = re.search(r'^> (.+)$', source, re.M)[1]
    sections = re.split(r'^## (.+)\n', source, flags=re.M)
    names = ['catalog', 'terms', 'religions', 'theologies-events', 'development', 'laws', 'technologies', 'sources']
    manifest = []
    OUT.mkdir(parents=True, exist_ok=True)
    for title, body in zip(sections[1::2], sections[2::2]):
        if title == 'Оглавление':
            continue
        group_index = len({x['group'] for x in manifest})
        if title == 'Полный каталог и планировщик':
            body = date + '\n\n' + body
        # Keep each achievement whole. Introductory prose may split at paragraph boundaries.
        if '<!-- achievement:' in body:
            blocks = [x.strip() for x in re.split(r'(?=^### )', body, flags=re.M) if x.strip()]
            blocks = ['\n'.join(line for line in x.splitlines() if line.strip()) for x in blocks]
        else:
            blocks = [x for x in body.strip().split('\n\n') if x.strip()]
        chunks, chunk = [], []
        for block in blocks:
            candidate = bbcode('\n\n'.join(chunk + [block])) + '\n'
            if max(len(candidate), len(candidate.encode('utf-8'))) > LIMIT and chunk:
                chunks.append(chunk)
                chunk = []
            assert max(len(bbcode(block)), len(bbcode(block).encode('utf-8'))) < LIMIT
            chunk.append(block)
        if chunk:
            chunks.append(chunk)
        for part, blocks in enumerate(chunks, 1):
            text = bbcode('\n\n'.join(blocks)) + '\n'
            validate_tags(text)
            assert len(text) <= LIMIT and len(text.encode('utf-8')) <= LIMIT
            suffix = f'-{part:02}' if len(chunks) > 1 else ''
            filename = f'{group_index+1:02}-{names[group_index]}{suffix}.txt'
            section_title = title + (f' — часть {part}' if len(chunks) > 1 else '')
            ids = re.findall(r'<!-- achievement: (a\d+) -->', '\n'.join(blocks))
            (OUT / filename).write_text(text, encoding='utf-8', newline='\n')
            manifest.append(dict(file=filename, title=section_title, group=title, ids=ids,
                                 characters=len(text), utf8Bytes=len(text.encode('utf-8')),
                                 sha256=hashlib.sha256(text.encode('utf-8')).hexdigest()))
    emitted = [aid for x in manifest for aid in x['ids']]
    assert emitted == expected, 'Output lost or duplicated an achievement'
    # Stale files must be reviewed explicitly, never silently removed.
    assert {p.name for p in OUT.glob('*.txt')} == {x['file'] for x in manifest}, 'Unexpected .txt files in output'
    (OUT / 'manifest.json').write_text(json.dumps(dict(date='2026-11-25', count=43, sections=manifest), ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    table = '\n'.join(f"| {x['title']} | [{x['file']}]({x['file']}) | {x['characters']} | {x['utf8Bytes']} |" for x in manifest)
    readme = f'''# Религия и развитие державы: файлы для Steam

## Название

Old World: религия и развитие державы — достижения

## Краткое описание

43 достижения Old World: основание религий, теологии, особые события, культура городов, законы и технологии. Проверенные условия и советы, различия между текстом Steam и механикой игры, требования дополнений.

## Перенос в Steam

Каждый TXT-файл — отдельный раздел. Название раздела вводится отдельно по таблице; содержимое файла вставляется целиком. Steam создаёт боковое оглавление по названиям разделов. Названия достижений уже оформлены подзаголовками. Внутри записи строки идут подряд; между достижениями оставлена пустая строка.

| Раздел | Файл | Символов | Байт UTF-8 |
|---|---|---:|---:|
{table}

Рабочий предел — 6000 символов и 6000 байт UTF-8 на раздел с разметкой. Это редакторский запас, а не заявленный лимит Steam. Достижения при разбиении не разрывались.

## Проверки

Все 43 ID совпали с планом серии, названия и краткие условия сверены с текущим русским списком Steam от 25 ноября 2026 года. Механика сверена с XML и исходниками Steam build 26728102. Проверены целостность записей, порядок, отсутствие дублей, баланс BBCode, отсутствие служебных комментариев, Markdown и невидимых символов, размеры файлов и соответствие официальным условиям Steam. Контрольные суммы и распределение ID — в manifest.json.

Подробные основания и ограничения: [проверка руководства](../../religion-development-review.md). Проверка файлов не заменяет игровое прохождение каждой случайной цепочки. Подготовленные материалы не опубликованы в Steam.

[Локальный предпросмотр](preview.html) помогает проверить текст и деление на разделы; точные шрифты и вёрстку определяет Steam. Перед отправкой проверь встроенный предпросмотр редактора Steam. Обложка для загрузки — [cover.jpg](cover.jpg); исходный PNG и запрос встроенного генератора сохранены в ../../covers/.

Повторная сборка и проверка: `python scripts/prepare-religion-development-steam.py` из корня проекта.
'''
    (OUT / 'README.md').write_text(readme, encoding='utf-8', newline='\n')
    previews = []
    for i, item in enumerate(manifest):
        text = (OUT / item['file']).read_text(encoding='utf-8')
        previews.append(f'<section id="s{i}"><h2>{html.escape(item["title"])}</h2>{render(text)}</section>')
    nav = ''.join(f'<li><a href="#s{i}">{html.escape(x["title"])}</a></li>' for i, x in enumerate(manifest))
    preview = '<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Old World — предпросмотр руководства</title><style>body{max-width:900px;margin:32px auto;padding:0 24px;background:#1b2838;color:#d6d7d8;font:17px/1.6 system-ui}a{color:#8cc9ed}h1,h2,h3{color:#fff}section{border-top:1px solid #486070;padding:24px 0}h3{font-size:21px;margin-bottom:4px}nav{padding-bottom:24px}</style><h1>Old World: религия и развитие державы</h1><p>Локальный предпросмотр текста. Точное отображение проверяется в редакторе Steam.</p><nav><ol>'+nav+'</ol></nav>'+''.join(previews)+'</html>\n'
    (OUT / 'preview.html').write_text(preview, encoding='utf-8', newline='\n')
    for item in manifest:
        raw = (OUT / item['file']).read_bytes()
        assert len(raw) == item['utf8Bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
    print(f'PASS: 43 unique achievements, {len(manifest)} Steam sections, max {max(x["utf8Bytes"] for x in manifest)} UTF-8 bytes; official conditions and BBCode validated.')


if __name__ == '__main__':
    main()
