---
name: add-feature
description: Draft or extend a Gherkin .feature file for the Mealie <-> KitchenOwl bridge from a feature request, and sanity-check it - checking tests/bdd/features/ for an existing match or conflict first. Does NOT write step definitions, application code, or tests; implementation is a deliberate separate step taken after a human reviews the drafted scenario. Use this whenever the user describes new bridge behavior or hands over a feature/user story for this project and wants it turned into an acceptance-test scenario - not only when they literally say "add a feature".
---

# Add Feature

Turns a feature request into a Gherkin scenario in `tests/bdd/features/`, matching the
BDD workflow already documented in `AGENTS.md`. This skill only touches `.feature`
files — it never writes step definitions or application code. That's intentional:
drafting the acceptance criteria and implementing them are different kinds of work,
and a human should read the scenario before anyone builds against it.

## Steps

1. **Read `AGENTS.md`'s "BDD workflow" section first.** It's the source of truth for
   conventions used across this project — one feature file per capability, existing
   tag usage (e.g. `@browser` for scenarios that need a real browser), and the
   `Given`/`When`/`Then` phrasing style already in use. Don't duplicate that guidance
   here; just follow it.

2. **Check for an existing match or conflict before writing anything.** Read through
   `tests/bdd/features/*.feature` and classify the request:
   - **Extends an existing capability** (a variation, edge case, or extra detail of a
     feature already described there) → add a `Scenario` to that existing file.
   - **Contradicts an existing scenario's expected behavior** → stop. Do not edit or
     delete the existing scenario. Report the conflict back to the requester and ask
     which behavior should win before touching anything.
   - **Genuinely new capability** → create a new file.

3. **Write or extend the `.feature` file** in Gherkin, matching the style of
   neighboring scenarios in the file (or, for a new file, the style used elsewhere in
   `tests/bdd/features/`).

4. **Sanity-check the result** with the bundled script:
   ```bash
   uv run python .agent/skills/add-feature/scripts/check_feature.py tests/bdd/features/<file>.feature
   ```
   It checks Gherkin syntax, duplicate scenario names within the file, and that any
   `@tags` used are registered pytest markers (catches typos before they silently
   become a new, unintended test tier). Fix anything it flags.

5. **Stop here.** Do not create step definitions, do not touch `src/bridge/`, do not
   run `pytest`. Report the new or changed scenario text back for review — turning it
   into passing code is a separate, deliberate follow-up action, not part of this
   skill.
