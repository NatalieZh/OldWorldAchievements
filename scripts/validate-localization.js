const fs = require('fs');
const vm = require('vm');
const assert = require('assert').strict;

const html = fs.readFileSync('index.html', 'utf8');
const cards = JSON.parse(fs.readFileSync('data/achievements.json', 'utf8'));
const jsCopy = fs.readFileSync('data/achievements.js', 'utf8').match(/^const achievements=(\[.*\]);\s*$/s);
assert(jsCopy && JSON.stringify(JSON.parse(jsCopy[1])) === JSON.stringify(cards), 'JSON and JS card data differ');

const storage = new Map();
const saved = {
  done: ['a017', 'a128'],
  run: { mode: 'Singleplayer', difficulty: 'Новый', style: 'balanced', special: '', dlc: 'all', scenario: 'none', civ: 'Рим', goals: ['a017', 'a028'], planSize: 'standard' },
};
storage.set('ow-guide-v4', JSON.stringify(saved));
const events = new Map();
const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {
    value: '', textContent: '', innerHTML: '', style: {}, dataset: {},
    classList: { toggle() {}, contains: () => true },
  });
  return elements.get(id);
}
const window = {
  location: { href: 'https://example.test/OldWorldAchievements/?lang=en', search: '?lang=en', protocol: 'https:' },
  localStorage: { getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value) },
  sessionStorage: { getItem: () => null, setItem() {} },
  history: { replaceState(_state, _title, href) { window.location.href = href; window.location.search = new URL(href).search; } },
  addEventListener(type, callback) { events.set(type, callback); },
  dispatchEvent(event) { events.get(event.type)?.(event); },
  name: '',
};
const document = {
  title: '', documentElement: { lang: 'ru' },
  addEventListener() {},
  querySelectorAll: () => [], getElementById: id => id === 'referenceToggle' ? null : element(id),
};
class FileReader {
  readAsText(file) { this.result = file.text; this.onload(); }
}
const context = vm.createContext({
  window, document, URL, URLSearchParams, FileReader,
  CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options.detail; } },
  requestAnimationFrame: callback => callback(),
  setTimeout: callback => { callback(); return 1; },
  confirm: () => true,
  console,
});
for (const file of ['locales/ru.js', 'locales/en.js', 'i18n.js']) {
  vm.runInContext(fs.readFileSync(file, 'utf8'), context, { filename: file });
}
context.AppI18n = window.AppI18n;
const inline = html.match(/<script>\s*([\s\S]*?)<\/script>/)?.[1];
assert(inline, 'Inline app script not found');
new vm.Script(inline);
vm.runInContext('const achievements=' + JSON.stringify(cards) + ';', context);
vm.runInContext(inline.replace(/\binitialize\(\);\s*$/, ''), context, { filename: 'index.html' });
vm.runInContext('globalThis.realRenderProgressList=renderProgressList;', context);
vm.runInContext('render=()=>{}; renderLocalizedSelects=()=>{}; updatePlannerSpecialOptions=()=>{}; updatePlannerScenarioOptions=()=>{}; renderProgressList=()=>{}; setImportBusy=()=>{}; toast=()=>{}; downloadJson=payload=>{globalThis.captured=payload};', context);
const run = expression => vm.runInContext(expression, context);

const ru = window.APP_LOCALES.ru, en = window.APP_LOCALES.en;
assert.equal(Object.keys(ru).length, Object.keys(en).length, 'Locale dictionary sizes differ');
for (const key of Object.keys(ru)) {
  assert(key in en && String(en[key]).trim(), `Missing English UI key: ${key}`);
  assert(!/[А-Яа-яЁё]/.test(en[key]), `Russian text in English UI key: ${key}`);
}
for (const key of [...html.matchAll(/data-i18n(?:-html|-placeholder|-aria-label)?="([^"]+)"/g)].map(match => match[1])) {
  assert(key in ru && key in en, `Untranslated HTML key: ${key}`);
}
for (const key of [...html.matchAll(/\bt\('([^']+)'/g)].map(match => match[1]).filter(key => !key.endsWith('.'))) {
  assert(key in ru && key in en, `Untranslated JavaScript key: ${key}`);
}

const visibleFields = ['guide', 'tactic', 'editor', 'mechanicNote', 'plannerNote', 'legitimacyNote', 'duplicateNote', 'guideLinkLabel'];
for (const card of cards) {
  for (const field of ['name', 'condition', ...visibleFields.filter(field => card[field])]) {
    const localized = 'english' + field[0].toUpperCase() + field.slice(1);
    assert(String(card[localized] || '').trim(), `${card.id}: missing ${localized}`);
    assert(!/[А-Яа-яЁё]/.test(card[localized]), `${card.id}: Russian text in ${localized}`);
  }
}

assert.equal(window.AppI18n.getLocale(), 'en', '?lang=en did not select English');
assert.equal(run('achievementName(achievements.find(card=>card.id==="a017"))'), 'Rome');
assert.equal(run('achievementDetail(achievements.find(card=>card.id==="a017"),"guide").startsWith("Start a game as Rome")'), true);
assert.equal(run('scenarioLabel("Орда варваров")'), 'The Barbarian Horde');
for (const city of [...new Set(cards.map(card => card.requiredCity).filter(Boolean))]) {
  assert(!/[А-Яа-яЁё]/.test(run(`cityLabel(${JSON.stringify(city)})`)), `Untranslated city: ${city}`);
}
for (const scenario of [...new Set(cards.map(card => card.scenarioName).filter(Boolean))]) {
  assert(!/[А-Яа-яЁё]/.test(run(`scenarioLabel(${JSON.stringify(scenario)})`)), `Untranslated scenario: ${scenario}`);
}

const filterIds = ['catalogSearch', 'categoryFilter', 'dlcFilter', 'scenarioFilter', 'specialFilter', 'civFilter', 'statusFilter',
  'pSearch', 'pCategory', 'pDlc', 'pScenario', 'pSpecial', 'pCiv', 'pStatus', 'pSort'];
for (const id of filterIds) element(id).value = '';
run('catalogPage=100; renderCatalog(); realRenderProgressList()');
assert(!/[А-Яа-яЁё]/.test(element('catalogGrid').innerHTML), 'Russian text in rendered English catalog');
assert(!/[А-Яа-яЁё]/.test(element('progressList').innerHTML), 'Russian text in rendered English progress list');
element('categoryFilter').value = 'Победа за цивилизацию';
element('pCategory').value = 'Победа за цивилизацию';
const catalogEn = run('catalogFiltered().map(card=>card.id).join(",")');
const progressEn = run('progressFiltered().map(card=>card.id).join(",")');
assert(catalogEn.includes('a017') && catalogEn === progressEn, 'Catalog and progress filters disagree');
const progressBefore = storage.get('ow-guide-v4');
for (const locale of ['ru', 'en', 'ru', 'en']) {
  window.AppI18n.setLocale(locale);
  assert.equal(document.documentElement.lang, locale);
  assert.equal(storage.get('ow-guide-v4'), progressBefore, 'Language switching changed progress or active run');
  assert.equal(run('catalogFiltered().map(card=>card.id).join(",")'), catalogEn, 'Catalog filter changed with language');
  assert.equal(run('progressFiltered().map(card=>card.id).join(",")'), progressEn, 'Progress filter changed with language');
}
assert.equal(new URL(window.location.href).searchParams.get('lang'), 'en');
assert.equal(run('state.run.goals.join(",")'), saved.run.goals.join(','));
assert.equal(run('state.done.join(",")'), saved.done.join(','));
assert.equal(run('catalogMatchesSearch(achievements.find(card=>card.id==="a017"),"Rome")'), true);
assert.equal(run('catalogMatchesSearch(achievements.find(card=>card.id==="a017"),"Рим")'), true);
assert.equal(run('cityLabel("Рим")'), 'Roma');
assert.equal(run('civsLabel("Египет, Рим")'), 'Egypt, Rome');
assert.equal(run('plannerRunMeta(state.run).includes("Singleplayer")'), true);

run('exportProgress()');
assert.equal(context.captured.kind, 'progress');
assert.deepEqual(Array.from(context.captured.progress.done), saved.done);
run('exportPlan()');
assert.equal(context.captured.kind, 'plan');
assert.equal(context.captured.plan.civ, saved.run.civ);
const progressFile = { target: { files: [{ name: 'test.json', text: JSON.stringify({ progress: { done: ['a017', 'a017', 'a128', 'invalid'] } }) }], value: '' } };
context.progressFile = progressFile;
run('importProgress(progressFile)');
assert.equal(run('state.done.join(",")'), 'a017,a128');
assert.equal(run('state.run.goals.join(",")'), saved.run.goals.join(','), 'Progress import replaced active run');
const planFile = { target: { files: [{ name: 'plan.json', text: JSON.stringify({ plan: saved.run }) }], value: '' } };
context.planFile = planFile;
run('importPlan(planFile)');
assert.equal(run('state.run.goals.join(",")'), saved.run.goals.join(','));

run('applyPlannerRunSettings=()=>{}; prepareExistingRunForEdit=()=>{}; showPlannerStep=()=>{}; openModal=()=>{}; openPlanner(true)');
assert.equal(element('plannerModalTitle').textContent, en['planner.editTitle']);
assert.equal(element('plannerModalIntro').textContent, en['planner.editIntro']);
run('openPlanner(false)');
assert.equal(element('plannerModalTitle').textContent, en['planner.title']);
assert.equal(element('plannerModalIntro').textContent, en['planner.intro']);

run(`plannerState.selectedCiv='Рим'; plannerState.goals=[
  {a:achievements.find(a=>a.id==='a017'),tier:'core',score:4,selected:true},
  {a:achievements.find(a=>a.id==='a194'),tier:'affinity',score:2,selected:true},
  {a:achievements.find(a=>a.id==='a001'),tier:'optional',score:1,selected:true}
]; updatePlannerSummary(); state.run={...state.run,civ:'Рим',goals:plannerState.goals.map(g=>g.a.id)}; renderCurrentRunDashboard()`);
assert(element('plannerReview').innerHTML.includes('3 goals: 1 core, 1 compatible, and 1 optional'), 'Planner review does not match run grouping');
assert(element('selectedGoalBreakdown').innerHTML.includes('Compatible 1'), 'Planner selection summary does not match run grouping');
assert(!element('selectedGoalBreakdown').innerHTML.includes('Natural'), 'Planner selection summary still uses a different grouping');
assert.equal(element('runCoreCount').textContent, 1);
assert.equal(element('runCompatCount').textContent, 1);
assert.equal(element('runOptionalCount').textContent, 1);

console.log(`Localization checks passed: ${cards.length} cards, ${Object.keys(en).length} UI keys, search, filters, planner review, language switching, progress and plan import/export.`);
