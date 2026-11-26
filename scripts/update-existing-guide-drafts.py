"""Update existing prose drafts without changing their established section layout."""
import json,re
from guide_series_support import ROOT,DOCS,DB,CHANGES,effective
STEAM={x['id']:x['steam'] for x in json.loads((DOCS/'series-steam-check.json').read_text(encoding='utf8'))['entries']}
def update():
    for slug in ['characters','warfare']:
        p=DOCS/f'{slug}-draft.md';s=p.read_text(encoding='utf8');ids=[i for topic in __import__('runpy').run_path(str(ROOT/'scripts/audit-guide-series.py'))['topics']() if topic['slug']==slug for i in topic['ids']];seen=[]
        def rewrite(m):
            heading,body=m[1],m[2]
            body=re.sub(r'^<!-- achievement: [^\n]+ -->\n', '', body, count=1)
            hits=[i for i in ids if heading==DB[i]['name'] or heading.startswith(DB[i]['name']+' (')]
            assert len(hits)==1,(slug,heading,hits)
            aid=hits[0];seen.append(aid);a=effective(aid);name,condition=STEAM[aid]
            suffix=heading[len(DB[aid]['name']):]
            if 'dlcName' in CHANGES.get(aid,{}).get('fields',{}):suffix=' ('+a['dlcName']+')'
            if 'guide' in CHANGES.get(aid,{}).get('fields',{}) or 'tactic' in CHANGES.get(aid,{}).get('fields',{}):
                body=f'**Условие:** {condition}\n\n{a["guide"]}\n\n**Совет:** {a["tactic"]}\n\n'
            else:
                body=re.sub(r'^\*\*Условие:\*\*[^\n]*',lambda _: '**Условие:** '+condition,body,count=1,flags=re.M)
            if aid in ['a404','a405','a406','a352'] and 'Источник точной выдачи' not in body:
                body=body.rstrip()+'\n\nИсточник точной выдачи этого достижения не найден в доступной Reference. Условие сверено со Steam; подробный маршрут и скрытые ограничения требуют дополнительной проверки.\n\n'
            return f'### {name}{suffix}\n<!-- achievement: {aid} -->\n'+body
        s=re.sub(r'^### ([^\n]+)\n(.*?)(?=^#{1,3} |\Z)',rewrite,s,flags=re.M|re.S)
        assert set(seen)==set(ids) and len(seen)==len(ids)
        intro='**Последняя проверка: 26 ноября 2026 года.** Публичные названия и условия сверены с текущим Steam, источники выдачи и найденные расхождения — с доступными XML и кодом игры, build 26728102. '+('Для четырёх достижений Wrath of Gods источник выдачи в Reference не найден; подробности и границы проверки — в [заметках](characters-review.md).' if slug=='characters' else 'Способ получения «Александр — какой?» через отречение остаётся непроверенным в игре; подробности — в [заметках](warfare-review.md).')
        s=re.sub(r'^> \*\*Дата подготовки:[^\n]*',intro,s,count=1,flags=re.M)
        if 'Источники сверки 26 ноября:' not in s:s+='\nИсточники сверки 26 ноября: [официальный список Steam](series-steam-check.json), [связи с игровыми файлами](%s-source-index.json).\n'%slug
        p.write_text(s,encoding='utf8');print(slug,len(seen),'sections updated, layout preserved')
    # Keep the accepted compact table format of these two guides.
    for slug in ['civilizations-families','wonders']:
        p=DOCS/f'{slug}-draft.md';s=p.read_text(encoding='utf8');ids=[i for topic in __import__('runpy').run_path(str(ROOT/'scripts/audit-guide-series.py'))['topics']() if topic['slug']==slug for i in topic['ids']];seen=[]
        def table(m):
            label,tail=m[1],m[2];hits=[i for i in ids if label==DB[i]['name'] or label.startswith(DB[i]['name']+' (')]
            if not hits:return m[0]
            assert len(hits)==1,(slug,label);aid=hits[0];seen.append(aid);name,condition=STEAM[aid];suffix=label[len(DB[aid]['name']):]
            # Preserve any agreed explanation after the existing first clause.
            columns=tail.split('|');first=columns[0].strip();extra=''
            if ';' in first:extra=';'+first.split(';',1)[1]
            elif '. ' in first:extra='. '+first.split('. ',1)[1]
            columns[0]=' '+condition.rstrip('.')+extra+' '
            return '| **'+name+suffix+'** |'+'|'.join(columns)
        s=re.sub(r'^\| \*\*([^\n]+?)\*\* \|([^\n]*)',table,s,flags=re.M)
        assert len(seen)==len(ids) and set(seen)==set(ids),(slug,len(seen),len(ids))
        s=re.sub(r'^> Рабочий черновик[^\n]*\n\n','',s,flags=re.M)
        if 'Названия и краткие условия дополнительно' not in s:s+='\nНазвания и краткие условия дополнительно сверены со [Steam](series-steam-check.json) 26 ноября 2026 года; это не повторная игровая проверка всех советов. [Основания сверки](%s-review.md).\n'%slug
        p.write_text(s,encoding='utf8');print(slug,len(seen),'table rows updated, explanations preserved')
    p=DOCS/'cognomens-draft.md';s=p.read_text(encoding='utf8');s+='\nПубличные названия и условия дополнительно сверены со [Steam](series-steam-check.json) 26 ноября 2026 года. Формулы и границы практического подтверждения — в [заметках проверки](cognomens-review.md).\n';p.write_text(s,encoding='utf8')
if __name__=='__main__':update()
