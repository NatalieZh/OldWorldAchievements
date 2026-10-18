const fs = require('fs');

const source = fs.readFileSync('data/achievements.js', 'utf8');
const match = source.match(/^const achievements=(\[.*\]);\s*$/s);
if (!match) {
  console.error('English achievement validation failed: data/achievements.js has an unexpected format.');
  process.exit(1);
}
const achievements = JSON.parse(match[1]);
const requiredFields = ['englishName', 'englishCondition', 'englishApiName', 'englishSource'];
const missing = achievements.flatMap(achievement =>
  requiredFields
    .filter(field => !String(achievement[field] || '').trim())
    .map(field => `${achievement.id}: ${field}`)
);
const apiNames = achievements.map(achievement => achievement.englishApiName).filter(Boolean);
const duplicateApiNames = [...new Set(apiNames.filter((name, index) => apiNames.indexOf(name) !== index))];
const guideScope = achievements.filter(achievement => ['Чудо', 'Сооружение'].includes(achievement.category));
const guideFields = ['englishGuide', 'englishTactic', 'englishEditor'];
const missingGuideFields = guideScope.flatMap(achievement =>
  guideFields
    .filter(field => !String(achievement[field] || '').trim())
    .map(field => `${achievement.id}: ${field}`)
);
const russianGuideFields = guideScope.flatMap(achievement =>
  guideFields
    .filter(field => /[А-Яа-яЁё]/.test(String(achievement[field] || '')))
    .map(field => `${achievement.id}: ${field}`)
);
const characterScope = achievements.filter(achievement => ['Черта / персонаж', 'Семья'].includes(achievement.category));
const missingCharacterFields = characterScope.flatMap(achievement =>
  [...guideFields,
    ...(achievement.mechanicNote ? ['englishMechanicNote'] : []),
    ...(achievement.legitimacyNote ? ['englishLegitimacyNote'] : []),
    ...(achievement.duplicateNote ? ['englishDuplicateNote'] : [])]
    .filter(field => !String(achievement[field] || '').trim())
    .map(field => `${achievement.id}: ${field}`)
);
const russianCharacterFields = characterScope.flatMap(achievement =>
  ['englishGuide', 'englishTactic', 'englishEditor', 'englishMechanicNote', 'englishLegitimacyNote', 'englishDuplicateNote']
    .filter(field => /[А-Яа-яЁё]/.test(String(achievement[field] || '')))
    .map(field => `${achievement.id}: ${field}`)
);
const gameplayScope = achievements.filter(achievement =>
  ['Религия / теология', 'Событие / особое', 'Военное / историческое', 'Юнит'].includes(achievement.category)
);
const gameplayFields = achievement => [
  ...guideFields,
  ...(achievement.mechanicNote ? ['englishMechanicNote'] : []),
  ...(achievement.plannerNote ? ['englishPlannerNote'] : []),
];
const missingGameplayFields = gameplayScope.flatMap(achievement =>
  gameplayFields(achievement)
    .filter(field => !String(achievement[field] || '').trim())
    .map(field => `${achievement.id}: ${field}`)
);
const russianGameplayFields = gameplayScope.flatMap(achievement =>
  gameplayFields(achievement)
    .filter(field => /[А-Яа-яЁё]/.test(String(achievement[field] || '')))
    .map(field => `${achievement.id}: ${field}`)
);
const scenarioScope = achievements.filter(achievement => achievement.category === 'Сценарий / кампания');
const scenarioFields = [...guideFields, 'englishScenarioName'];
const missingScenarioFields = scenarioScope.flatMap(achievement =>
  scenarioFields
    .filter(field => !String(achievement[field] || '').trim())
    .map(field => `${achievement.id}: ${field}`)
);
const russianScenarioFields = scenarioScope.flatMap(achievement =>
  scenarioFields
    .filter(field => /[А-Яа-яЁё]/.test(String(achievement[field] || '')))
    .map(field => `${achievement.id}: ${field}`)
);
const scenarioNameConflicts = [...new Set(scenarioScope.map(achievement => achievement.scenarioName))]
  .filter(name => new Set(scenarioScope.filter(achievement => achievement.scenarioName === name).map(achievement => achievement.englishScenarioName)).size !== 1);
const lowercaseDetailFields = achievements.flatMap(achievement =>
  ['englishGuide', 'englishTactic', 'englishEditor']
    .filter(field => /^[a-z]/.test(String(achievement[field] || '')))
    .map(field => `${achievement.id}: ${field}`)
);

if (missing.length || duplicateApiNames.length || missingGuideFields.length || russianGuideFields.length || missingCharacterFields.length || russianCharacterFields.length || missingGameplayFields.length || russianGameplayFields.length || missingScenarioFields.length || russianScenarioFields.length || scenarioNameConflicts.length || lowercaseDetailFields.length || characterScope.length !== 69 || gameplayScope.length !== 93 || scenarioScope.length !== 113 || achievements.length !== 408) {
  console.error(`English achievement validation failed: ${missing.length} missing identity field(s), ${missingGuideFields.length + missingCharacterFields.length + missingGameplayFields.length + missingScenarioFields.length} missing guide field(s), ${russianGuideFields.length + russianCharacterFields.length + russianGameplayFields.length + russianScenarioFields.length} Russian guide field(s), ${lowercaseDetailFields.length} lowercase detail opening(s), ${scenarioNameConflicts.length} inconsistent scenario label(s), ${duplicateApiNames.length} duplicate API name(s), ${achievements.length} total record(s), ${characterScope.length} character/family record(s), ${gameplayScope.length} gameplay record(s), ${scenarioScope.length} scenario/campaign record(s).`);
  missing.forEach(item => console.error(`  Missing ${item}`));
  missingGuideFields.forEach(item => console.error(`  Missing guide ${item}`));
  russianGuideFields.forEach(item => console.error(`  Russian guide ${item}`));
  missingCharacterFields.forEach(item => console.error(`  Missing character/family guide ${item}`));
  russianCharacterFields.forEach(item => console.error(`  Russian character/family guide ${item}`));
  missingGameplayFields.forEach(item => console.error(`  Missing gameplay guide ${item}`));
  russianGameplayFields.forEach(item => console.error(`  Russian gameplay guide ${item}`));
  missingScenarioFields.forEach(item => console.error(`  Missing scenario guide ${item}`));
  russianScenarioFields.forEach(item => console.error(`  Russian scenario guide ${item}`));
  scenarioNameConflicts.forEach(item => console.error(`  Inconsistent scenario name ${item}`));
  lowercaseDetailFields.forEach(item => console.error(`  Lowercase detail opening ${item}`));
  duplicateApiNames.forEach(item => console.error(`  Duplicate ${item}`));
  process.exit(1);
}

console.log(`English achievement validation passed: ${achievements.length} official Steam entries, ${guideScope.length} Wonder/building guides, ${characterScope.length} character/family guides, ${gameplayScope.length} gameplay guides, and ${scenarioScope.length} scenario/campaign guides.`);
