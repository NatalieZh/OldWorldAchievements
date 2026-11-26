"""Read installed Old World reference XML for guide fact checking (no game edits)."""
import argparse
import re
import json
import itertools
from pathlib import Path
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('file', help='Info XML filename, without extension')
parser.add_argument('pattern', help='Regular expression matched against entry IDs or contents')
parser.add_argument('--contents', action='store_true')
parser.add_argument('--compact', action='store_true')
parser.add_argument('--ru', action='store_true')
parser.add_argument('--tags', help='Comma-separated immediate child tags to display')
args = parser.parse_args()
root = Path('C:/Program Files (x86)/Steam/steamapps/common/Old World/Reference/XML/Infos')
pattern = re.compile(args.pattern, re.I)
paths = list(root.glob(args.file + '.xml'))
if not paths:
    parser.error('No matching XML files: ' + args.file)
for entry in itertools.chain.from_iterable(ET.parse(path).getroot() for path in paths):
    xml = ET.tostring(entry, encoding='unicode')
    if pattern.search(xml if args.contents else entry.findtext('zType', '')):
        if args.tags:
            tags = set(args.tags.split(',')) | {'zType'}
            for child in list(entry):
                if child.tag not in tags:
                    entry.remove(child)
            xml = ET.tostring(entry, encoding='unicode')
        if args.ru:
            print(entry.findtext('zType'), '=', entry.findtext('ru'))
        elif args.compact:
            def compact(node):
                if not len(node):
                    return (node.text or '').strip()
                return [{child.tag: compact(child)} for child in node]
            print(json.dumps(compact(entry), ensure_ascii=False))
        else:
            print(xml)
