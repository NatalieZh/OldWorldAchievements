# Project instructions

## Collaboration preferences

- Propose intended changes before making them.
- Do not create or amend commits unless the user explicitly requests a commit.
- Do not create migrations automatically; ask the user first.

## Russian game terminology

- Use the installed game's Russian localization for game mechanics and UI terms. Do not translate English names or internal IDs literally, and do not assume Steam achievement wording matches the game's UI.
- Cultural levels, verified in `Reference/XML/Infos/culture.xml` and `text-infos.xml` on 2026-11-25:
  - `CULTURE_WEAK` / Weak → «Примитивная».
  - `CULTURE_DEVELOPING` / Developing → «Развивающаяся».
  - `CULTURE_STRONG` / Strong → «Развитая».
  - `CULTURE_LEGENDARY` / Legendary → «Легендарная».
- Write, for example, «город с уровнем культуры „Развитая“», not «сильный город» when explaining the cultural requirement.
- Preserve official Steam achievement titles and quoted official conditions. If they differ from game terminology, explain the mapping in the guide text rather than silently renaming the achievement.
- Apply these terms when adapting existing achievement data into new guides; copying a database field does not override this rule. If a term is uncertain, verify localization before using it.

## Steam guide style and delivery

- Keep the established style of the guide series; do not introduce new labels or formatting conventions on each pass. Use «Условие:» and «Совет:», without adding «Steam» to the condition label.
- Keep the achievement heading, condition, explanation, and advice together, with a blank line between achievements in Steam files.
- Deliver the prepared folder of files. Do not create or rebuild archives unless the user explicitly asks for an archive.

## Repository skills

- For drafting or checking an achievement guide, use [oldworld-guide-draft](.agents/skills/oldworld-guide-draft/SKILL.md).
- For preparing reviewed guide text as Steam files, use [oldworld-steam-files](.agents/skills/oldworld-steam-files/SKILL.md).
