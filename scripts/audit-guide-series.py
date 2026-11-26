"""Index guide coverage, public Steam text and installed award records without claiming gameplay verification."""
import argparse,hashlib,json,re,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs/steam-guides'
GAME=Path('C:/Program Files (x86)/Steam/steamapps/common/Old World')
REF=GAME/'Reference'
SLUGS=['victories-modes','civilizations-families','cognomens','characters','warfare','wonders','religion-development','learning-horde','carthage','heroes-aegean','pharaohs-nile']
def topics():
    plan=(DOCS/'steam-guides-structure.md').read_text(encoding='utf8')
    result=[]
    for m in re.finditer(r'^### (\d+)\. ([^\n]+)\n(.*?)(?=^### \d+\.|^## Как проверять)',plan,re.M|re.S):
        n,title,body=m.groups(); sections=[]
        for sec in re.finditer(r'^#### ([^\n]+)\n(.*?)(?=^#### |\Z)',body,re.M|re.S):
            sections.append({'title':sec[1],'ids':re.findall(r'ID: `([^`]+)`',sec[2])})
        result.append({'number':int(n),'slug':SLUGS[int(n)-1],'title':title,'sections':sections,'ids':[i for sec in sections for i in sec['ids']]})
    return result
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--steam',action='store_true');parser.add_argument('--index',action='store_true');args=parser.parse_args()
    cards=json.loads((ROOT/'data/achievements.json').read_text(encoding='utf-8-sig')); db={a['id']:a for a in cards}
    ts=topics(); assigned=[i for t in ts for i in t['ids']];assert len(assigned)==len(set(assigned))==len(cards) and set(assigned)==set(db)
    if args.steam:
        u='https://steamcommunity.com/stats/597180/achievements/?l=russian'; req=urllib.request.Request(u,headers={'Cookie':'Steam_Language=russian','Accept-Language':'ru-RU'})
        raw=urllib.request.urlopen(req,timeout=30).read().decode();assert '<html lang="ru"' in raw
        s=raw.replace('\\"','"'); rows={}
        for m in re.finditer(r'\{"internal_key":',s):
            try:
                x,_=json.JSONDecoder().raw_decode(s[m.start():]);rows[x['api_name']]=x
            except (ValueError,KeyError):pass
        entries=[]
        for a in cards:
            x=rows[a['englishApiName']]; entries.append({'id':a['id'],'apiName':a['englishApiName'],'steam':[x['name'],x['description']]})
        (DOCS/'series-steam-check.json').write_text(json.dumps({'date':'2026-11-26','url':u,'language':'russian','count':len(entries),'entries':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print('Steam:',len(entries),'official Russian entries')
    if args.index:
        nodes=[];hashes={}
        for p in sorted((REF/'XML').rglob('*.xml')):
            if 'Infos' not in p.parts or p.name.startswith(('text','preload-text','genderedText')): continue
            try: tree=ET.parse(p)
            except ET.ParseError: continue
            rel=p.relative_to(GAME).as_posix();hashes[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
            for e in tree.getroot():
                key=e.findtext('zType')
                if key:nodes.append({'file':rel,'type':key,'xml':ET.tostring(e,encoding='unicode')})
        bykey={}; reverse={}
        for node in nodes:
            bykey.setdefault(node['type'],[]).append(node)
            for e in ET.fromstring(node['xml']).iter():
                val=(e.text or '').strip()
                if len(e)==0 and e.tag!='zType' and val:reverse.setdefault(val,[]).append(node)
        code={p.relative_to(GAME).as_posix():p.read_text(encoding='utf-8-sig') for p in (REF/'Source').rglob('*.cs')}
        for t in ts:
            records=[];used=set()
            for aid in t['ids']:
                api=db[aid]['englishApiName']; direct=[n for n in reverse.get(api,[]) if ET.fromstring(n['xml']).find('Achievement') is not None or n['type'].startswith('SCENARIO')]
                contexts=[]
                for n in direct:
                    contexts.extend(x for x in reverse.get(n['type'],[]) if x['type'].startswith(('EVENTOPTION','EVENTSTORY')))
                for n in list(contexts):
                    if n['type'].startswith('EVENTOPTION'):contexts.extend(x for x in reverse.get(n['type'],[]) if x['type'].startswith('EVENTSTORY'))
                seen=set(); contexts=[n for n in contexts if not ((n['file'],n['type']) in seen or seen.add((n['file'],n['type'])))]
                codehits=[]
                for f,s in code.items():
                    lines=s.splitlines()
                    for ix,line in enumerate(lines):
                        if '"'+api+'"' in line:codehits.append({'file':f,'line':ix+1,'context':'\n'.join(lines[max(0,ix-6):ix+8])})
                own=bykey.get(api,[])
                for n in own+direct+contexts:used.add(n['file'])
                for h in codehits:used.add(h['file'])
                records.append({'id':aid,'apiName':api,'achievementRecords':own,'directAwardRecords':direct,'eventContexts':contexts,'codeHits':codehits,'status':'source records located; interpret filters and code before claiming verification'})
            for f in used:
                if f not in hashes:hashes[f]=hashlib.sha256((GAME/f).read_bytes()).hexdigest()
            output={'date':'2026-11-26','buildId':re.search(r'"buildid"\s+"(\d+)"',(GAME.parents[1]/'appmanifest_597180.acf').read_text())[1],'count':len(records),'sourceRoot':str(GAME),'sourceSha256':{f:hashes[f] for f in sorted(used)},'records':records,'note':'Automated source index; not a gameplay test or complete verification of tactics. Human findings are in the review.'}
            # Existing detailed audits remain authoritative and untouched.
            (DOCS/(t['slug']+'-source-index.json')).write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            print(t['slug'],len(records),'records; missing award links',[x['id'] for x in records if not x['directAwardRecords'] and not x['codeHits'] and not x['achievementRecords']])
if __name__=='__main__':main()
