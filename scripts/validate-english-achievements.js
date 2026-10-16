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

if (missing.length || duplicateApiNames.length || achievements.length !== 408) {
  console.error(`English achievement validation failed: ${missing.length} missing field(s), ${duplicateApiNames.length} duplicate API name(s), ${achievements.length} total record(s).`);
  missing.forEach(item => console.error(`  Missing ${item}`));
  duplicateApiNames.forEach(item => console.error(`  Duplicate ${item}`));
  process.exit(1);
}

console.log(`English achievement validation passed: ${achievements.length} official Steam entries.`);
