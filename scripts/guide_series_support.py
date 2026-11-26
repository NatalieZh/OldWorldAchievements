"""Helpers for reviewed guide corrections; cards are updated only by the final synchronization step."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs/steam-guides'
PATCH=DOCS/'series-reviewed-corrections.json'
CARDS=json.loads((ROOT/'data/achievements.json').read_text(encoding='utf-8-sig'))
DB={a['id']:a for a in CARDS}
CHANGES=json.loads(PATCH.read_text(encoding='utf8')) if PATCH.exists() else {}
def queue(aid,reason,guide=None,tactic=None,enGuide=None,enTactic=None,**fields):
    item=CHANGES.setdefault(aid,{'reason':reason,'fields':{}})
    if reason not in item['reason']: item['reason']+=' '+reason
    for key,value in [('guide',guide),('tactic',tactic),('englishGuide',enGuide),('englishTactic',enTactic)]:
        if value is not None:item['fields'][key]=value
    item['fields'].update(fields)
def save():
    PATCH.write_text(json.dumps(CHANGES,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('Reviewed corrections queued:',len(CHANGES),'; cards not yet modified.')
def effective(aid):
    a=DB[aid].copy();a.update(CHANGES.get(aid,{}).get('fields',{}));return a
