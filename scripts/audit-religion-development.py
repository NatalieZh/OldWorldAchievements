"""Save source evidence and enforce the guide's critical mechanics against installed game files."""
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs/steam-guides'
GAME = Path('C:/Program Files (x86)/Steam/steamapps/common/Old World')
INFO = GAME / 'Reference/XML/Infos'
CORE = GAME / 'Reference/Source/Base/Game/GameCore'
FILES = ['achievement', 'religion', 'theology', 'tech', 'law', 'lawClass', 'project-event-eoti',
         'bonus', 'bonus-event-sap', 'bonus-event-wog', 'bonus-event-eoti', 'eventStory',
         'eventStory-sap', 'eventStory-wog', 'eventOption-sap', 'eventOption-wog',
         'mission', 'subject', 'subjectRelation', 'nation', 'additionalContent',
         'improvement', 'effectPlayer', 'culture']


def main():
    entries, sources = {}, {}
    for filename in FILES:
        path = INFO / (filename + '.xml')
        sources[str(path.relative_to(GAME)).replace('\\', '/')] = hashlib.sha256(path.read_bytes()).hexdigest()
        for node in ET.parse(path).getroot():
            key = node.findtext('zType')
            if key:
                entries[key] = (filename + '.xml', node)
    def node(key):
        return entries[key][1]
    def text(key, tag):
        return node(key).findtext(tag)
    # These are semantic guards for mistakes found in the initial draft.
    assert text('RELIGION_CHRISTIANITY', 'iRequiresCitizens') == '12'
    assert node('RELIGION_CHRISTIANITY').findtext('aiRequiresReligion/Pair/iValue') == '3'
    assert text('RELIGION_CHRISTIANITY', 'RequiresTech') is None
    assert text('RELIGION_JUDAISM', 'RequiresTech') is None
    assert text('RELIGION_MANICHAEISM', 'RequiresTech') == 'TECH_METAPHYSICS'
    assert text('RELIGION_BUDDHISM', 'iRequiresTheologies') == '4'
    assert text('RELIGION_BUDDHISM', 'RequiresLaw') == 'LAW_PHILOSOPHY'
    assert text('PROJECT_FOUND_BUDDHISM', 'MinimumCulture') == 'CULTURE_DEVELOPING'
    assert text('ACHIEVEMENT_ONE_TRUE_FAITH', 'bTrueFaith') == '1'
    assert text('ACHIEVEMENT_ONE_TRUE_FAITH', 'iNumCities') == '3'
    assert node('ACHIEVEMENT_SACRED_PROFANE_FIVE_CULTS').findtext('aiStatCount/Pair/zIndex') == 'STAT_CULTS'
    assert node('ACHIEVEMENT_SACRED_PROFANE_FIVE_CULTS').findtext('aiStatCount/Pair/iValue') == '5'
    assert node('BONUS_EVENTOPTION_WAYWARD_CULT_OPTION_0_CITY').findtext('aiStats/Pair/iValue') == '-1'
    assert len(node('EVENTSTORY_ACHIEVEMENT_SACRED_PROFANE_DISSENT_ALL').findall('SubjectExtras/Pair')) == 4
    assert text('MISSION_IMPART_STEWARDSHIP', 'iMissionTurns') == '3'
    for f in ['Game.cs', 'Player.cs', 'PlayerGoal.cs', 'City.cs', 'Character.cs', 'Unit.cs', 'Tile.cs', 'PlayerBonus.cs', 'PlayerEvent.cs']:
        path = CORE / f
        sources[str(path.relative_to(GAME)).replace('\\', '/')] = hashlib.sha256(path.read_bytes()).hexdigest()
    for path in INFO.glob('text*.xml'):
        sources[str(path.relative_to(GAME)).replace('\\', '/')] = hashlib.sha256(path.read_bytes()).hexdigest()
    player = (CORE / 'Player.cs').read_text(encoding='utf-8-sig')
    game = (CORE / 'Game.cs').read_text(encoding='utf-8-sig')
    assert 'pLoopCity.getCulture() == eCulture' in player
    assert '(achievement.mbTrueFaith)' in game
    assert 'infos().achievement(eLoopAchievement).meGameMode != AchievementGameType.HOTSEAT' in game
    expected = json.loads((DOCS / 'religion-development-coverage.json').read_text())['ids']
    db = {x['id']: x for x in json.loads((ROOT / 'data/achievements.json').read_text(encoding='utf-8-sig'))}
    steam = {x['id']: x for x in json.loads((DOCS / 'religion-development-steam-check.json').read_text(encoding='utf-8'))['entries']}
    practice = (DOCS / 'practice-evidence.md').read_text(encoding='utf-8')
    records = []
    for aid in expected:
        api = db[aid]['englishApiName']
        direct = [key for key, (_, e) in entries.items() if e.findtext('Achievement') == api]
        if any(node(api).find(tag) is not None for tag in ['aiStatCount', 'aiCultureCount', 'bTrueFaith']):
            direct.append(api)
        assert direct, ('No source award record', aid, api)
        refs = set(direct)
        for _ in range(2):
            refs |= {key for key, (_, e) in entries.items() if any((leaf.text or '').strip() in refs for leaf in e.iter() if leaf.tag != 'zType')}
        records.append(dict(id=aid, apiName=api, steamName=steam[aid]['steam'][0],
                            steamCondition=steam[aid]['steam'][1], verifiedBy='installed XML and source code; not a full gameplay test',
                            markedObtainedInAuthorExport=bool(re.search(r'`'+aid+r'`', practice)),
                            directAwardRecords=direct,
                            relatedRecords=[dict(file=entries[key][0], type=key) for key in sorted(refs)]))
    manifest = (GAME.parents[1] / 'appmanifest_597180.acf').read_text()
    build = re.search(r'"buildid"\s+"(\d+)"', manifest)[1]
    audit = dict(date='2026-11-25', buildId=build, count=len(records),
                 sourceRoot=str(GAME), sourceSha256=sources, records=records,
                 limitations=['Random event timing and every route were not playtested.',
                              'Steam editor rendering is not validated by the local HTML preview.',
                              'Card synchronization is documented separately in religion-development-card-changes.md.'])
    (DOCS / 'religion-development-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(f'PASS: {len(records)} source-backed achievements, build {build}, {len(sources)} source hashes; {sum(x["markedObtainedInAuthorExport"] for x in records)} marked obtained in author export.')


if __name__ == '__main__':
    main()
