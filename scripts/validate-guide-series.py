"""Validate full series coverage, official text, local links and exact card-change scope."""
import collections,copy,hashlib,json,re,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs/steam-guides'
def main():
    topics=runpy.run_path(str(ROOT/'scripts/audit-guide-series.py'))['topics']()
    cards=json.loads((ROOT/'data/achievements.json').read_text(encoding='utf8'));db={a['id']:a for a in cards}
    steam={x['id']:x['steam'] for x in json.loads((DOCS/'series-steam-check.json').read_text(encoding='utf8'))['entries']}
    english={x['id']:x['steam'] for x in json.loads((DOCS/'series-steam-check-en.json').read_text(encoding='utf8'))['entries']}
    norm=lambda s:re.sub(r'\s+',' ',s).strip().rstrip('.')
    allids=[];checked=[];unlocated=[]
    for t in topics:
        slug=t['slug'];coverage=json.loads((DOCS/f'{slug}-coverage.json').read_text(encoding='utf8'));ids=coverage['ids']
        assert coverage['count']==len(ids)==len(set(ids)) and set(ids)==set(t['ids']),slug
        allids.extend(ids);draft=DOCS/f'{slug}-draft.md';text=draft.read_text(encoding='utf8');assert '\ufffd' not in text
        markers=re.findall(r'<!-- achievement: ([^ ]+) -->',text)
        if markers:
            assert len(markers)==len(ids) and set(markers)==set(ids),(slug,'markers')
            for aid in ids:
                name,cond=steam[aid];m=re.search(r'<!-- achievement: '+re.escape(aid)+r' -->\s*\*\*Условие:\*\* ([^\n]+)',text)
                assert m and norm(m[1])==norm(cond),(slug,aid,'condition')
                h=re.search(r'^### ([^\n]+)\n<!-- achievement: '+re.escape(aid)+r' -->',text,re.M)
                assert h and (h[1]==name or h[1].startswith(name+' (') or h[1].startswith(name+' —')),(slug,aid,'heading')
        else:
            assert slug in ['wonders','civilizations-families']
            for aid in ids:
                name,cond=steam[aid]
                row=re.search(r'^\| \*\*'+re.escape(name)+r'(?: \([^\n]*?\))?\*\* \|([^\n]+)',text,re.M)
                assert row and norm(row[1].split('|')[0]).startswith(norm(cond)),(slug,aid,'table')
        assert (DOCS/f'{slug}-review.md').exists()
        for p in [draft,DOCS/f'{slug}-review.md']:
            checked.append(p)
        index=json.loads((DOCS/f'{slug}-source-index.json').read_text(encoding='utf8'))
        assert set(x['id'] for x in index['records'])==set(ids)
        unlocated.extend(x['id'] for x in index['records'] if not x['achievementRecords'] and not x['directAwardRecords'] and not x['codeHits'])
    assert len(allids)==len(set(allids))==len(cards) and set(allids)==set(db)
    assert set(unlocated)=={'a404','a405','a406','a352'}
    for aid,a in db.items():
        assert norm(a['name'])==norm(steam[aid][0]) and norm(a['condition'])==norm(steam[aid][1]),('Steam RU',aid)
        assert [a['englishName'],a['englishCondition']]==english[aid],('Steam EN',aid)
    report=json.loads((DOCS/'series-card-changes.json').read_text(encoding='utf8')); assert report['count']==len(report['changes'])==len({x['id'] for x in report['changes']})
    for filename in ['data/achievements.json','data/achievements.js']:
        raw=(ROOT/filename).read_bytes();restored=raw
        for change in report['changes']:
            now=db[change['id']];old=copy.deepcopy(now)
            for key,values in change['fields'].items():
                assert now[key]==values['after'];old[key]=values['before']
            if filename.endswith('.json'):
                newline='\r\n' if b'\r\n' in raw else '\n'
                def enc(a):return '\n'.join('  '+line for line in json.dumps(a,ensure_ascii=False,indent=2).splitlines()).replace('\n',newline).encode('utf8')
            else:
                def enc(a):return json.dumps(a,ensure_ascii=False,separators=(',',':')).encode('utf8')
            assert restored.count(enc(now))==1,(filename,change['id']);restored=restored.replace(enc(now),enc(old),1)
        assert hashlib.sha256(restored).hexdigest()==report['baselineSha256'][filename],('unreported changes',filename)
    js=(ROOT/'data/achievements.js').read_text(encoding='utf8');assert json.loads(re.fullmatch(r'const achievements=(\[.*\]);\s*',js,re.S)[1])==cards
    checked.extend([DOCS/'README.md',DOCS/'series-review.md',DOCS/'series-card-changes.md'])
    for p in checked:
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
            if re.match(r'https?://|#',target):continue
            if (p.parent/target)==DOCS/'series-validation.json':continue # Written below only after all checks pass.
            assert (p.parent/target.split('#')[0]).exists(),(p.name,target)
    results={'date':'2026-11-26','guideCount':len(topics),'achievementCount':len(cards),'duplicateAssignments':len(allids)-len(set(allids)),'changedCardCount':report['count'],'missingInstalledAwardSources':unlocated,'checks':['coverage matches plan and data','official RU/EN text','all local draft/review links','JSON/JS equality','reported changes restore both baseline SHA-256 hashes'],'limits':'No new gameplay tests; unresolved source/route questions are recorded in series-review.md.'}
    (DOCS/'series-validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(f'PASS: {len(topics)} drafts; {len(cards)} achievements; no omissions or duplicate assignments; {report["count"]} changed cards exactly match before/after report. Official RU/EN text, local links and baseline hashes verified. Four unavailable award sources explicitly recorded.')
if __name__=='__main__':main()
