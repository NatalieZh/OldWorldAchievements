"""Apply only reviewed series corrections, retaining exact before/after values and file hashes."""
import copy,hashlib,json,re
from guide_series_support import ROOT,DOCS,CHANGES

def main():
    jp=ROOT/'data/achievements.json';sp=ROOT/'data/achievements.js';jraw=jp.read_bytes();sraw=sp.read_bytes();jt=jraw.decode('utf8');st=sraw.decode('utf8');before=json.loads(jt)
    match=re.fullmatch(r'const achievements=(\[.*\]);\s*',st,re.S);assert match and json.loads(match[1])==before
    after=copy.deepcopy(before);changes=[]
    for a in after:
        if a['id'] in CHANGES:a.update(CHANGES[a['id']]['fields'])
    for old,new in zip(before,after):
        if old==new:continue
        fields={k:{'before':old.get(k),'after':new.get(k)} for k in new if old.get(k)!=new.get(k)}
        changes.append({'id':old['id'],'name':new['name'],'summary':CHANGES[old['id']]['reason'],'fields':fields})
        newline='\r\n' if '\r\n' in jt else '\n'
        def pretty(a):return '\n'.join('  '+line for line in json.dumps(a,ensure_ascii=False,indent=2).splitlines()).replace('\n',newline)
        def compact(a):return json.dumps(a,ensure_ascii=False,separators=(',',':'))
        assert jt.count(pretty(old))==1 and st.count(compact(old))==1,old['id']
        jt=jt.replace(pretty(old),pretty(new),1);st=st.replace(compact(old),compact(new),1)
    assert changes,'No new changes; use the existing before/after report rather than overwriting it.'
    assert json.loads(jt)==after and json.loads(re.fullmatch(r'const achievements=(\[.*\]);\s*',st,re.S)[1])==after
    forbidden={'id','n','rarity','englishName','englishCondition','englishApiName'}
    assert not any(forbidden & set(c['fields']) for c in changes)
    jp.write_bytes(jt.encode('utf8'));sp.write_bytes(st.encode('utf8'))
    report={'date':'2026-11-26','count':len(changes),'scope':'Complete guide series review; official RU Steam text and verified RU/EN mechanical corrections; prior changes preserved','baselineSha256':{'data/achievements.json':hashlib.sha256(jraw).hexdigest(),'data/achievements.js':hashlib.sha256(sraw).hexdigest()},'changes':changes}
    (DOCS/'series-card-changes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    mechanical=sum(bool(set(c['fields'])-{'name','condition'}) for c in changes)
    chunks=[f'# Изменения карточек после завершения серии\n\nДата: 26 ноября 2026 года. Изменено **{len(changes)} карточки**: {mechanical} с содержательными/метаданными исправлениями, остальные — только с актуализацией официального русского названия или условия.\n\n[Полное сравнение до и после, включая английские поля](series-card-changes.json). [Все черновики и вопросы для автора](series-review.md). [Основания подготовленных исправлений](series-reviewed-corrections.json).\n\nID, номера, личный прогресс, редкость и официальные английские названия/условия сохранены. Предыдущие правки других тем не отменены. JSON и JS синхронизированы. Общее правило Hotseat не добавлялось в карточки. Две метки DLC исправлены: a005 → Empires of the Indus; a035 → Heroes of the Aegean. У a313 и a394 обязательная цивилизация заменена мягкой связью, поскольку проверенный источник не требует конкретной нации.\n\nОфициальные тексты Steam могут содержать ошибки: у a292 сохранена лишняя фигурная скобка в заголовке, у a201 — латинская буква внутри русского названия. Эти особенности зафиксированы по текущему ответу Steam, а не добавлены как новые названия игры. У a314 неверная формулировка условия Steam сохранена, расхождение с кодом объяснено в руководстве и карточке.\n\n## Список для проверки\n\n']
    for c in changes:
        names=', '.join('`'+k+'`' for k in c['fields']);chunks.append(f'### {c["name"]} — `{c["id"]}`\n\n{c["summary"]}\n\nПоля: {names}.\n\n')
        if any(k not in ['name','condition'] for k in c['fields']):
            a=next(x for x in after if x['id']==c['id']);chunks.append(f'**Как получить:** {a["guide"]}\n\n**Совет:** {a["tactic"]}\n\n')
        else:
            for k,label in [('name','Название'),('condition','Условие')]:
                if k in c['fields']:chunks.append(f'**{label}:** {c["fields"][k]["after"]}\n\n')
    chunks.append('## Проверка\n\nОбязательные проверки: `node scripts/validate-english-achievements.js`, `node scripts/validate-localization.js` и `python scripts/validate-guide-series.py`. Последняя сверяет все 408 ID и по сохранённому сравнению восстанавливает исходные файлы до этой синхронизации для проверки SHA-256; это подтверждает отсутствие незаявленных изменений полей и форматирования. Новая игровая попытка не выполнялась.\n')
    (DOCS/'series-card-changes.md').write_text(''.join(chunks),encoding='utf8')
    print('Synchronized',len(changes),'cards;',mechanical,'with content/metadata changes;',sum('condition' in c['fields'] for c in changes),'official RU condition updates;',sum('name' in c['fields'] for c in changes),'official RU title updates.')
if __name__=='__main__':main()
