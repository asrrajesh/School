# Plan: Setup E-Books class, subject and chapter as dropdowns

- **Intent:** [intent.md](intent.md)
- **Spec:** [spec.md](spec.md)
- **Author:** Rajesh
- **Date:** 2026-10-04
- **Status:** approved

## Approach
Swap the chip-based `SelectorState` selectors in `setup_ebooks_screen.py` for three `ft.Dropdown` controls that reuse the same variable names, so every `.value` read keeps working. Style comes from the Generate Questions Class dropdown (`label`, `hint_text`, `dense=True`, `expand=True`, each inside a `ft.Row`); nothing else on the screen changes.

## Files affected
| File | Change | Why |
|---|---|---|
| `edukoreaiui/screens/setup_ebooks_screen.py` | Remove `SelectorState`; add three `ft.Dropdown` with the existing option lists; wrap each in a `ft.Row` in the form column | Requirements 1-4 |
| `knowledge/ui-behavior-and-design.md` | Update the Setup E-Books section (via `/update-knowledge`, not in this stage) | Keep the as-is docs current |

No other file changes: not `generate_questions_screen.py`, `api_client.py`, the API or data.

## Steps
1. **Replace the selector construction** (lines ~38-97). Delete the `SelectorState` class. Add the option lists as constants (`CLASS_OPTIONS` I-X, `SUBJECT_OPTIONS` the four subjects, `CHAPTER_OPTIONS` "1".."50") and three `ft.Dropdown` named `class_dropdown`, `subject_dropdown`, `chapter_dropdown` with `label`, `hint_text` ("Select Class/Subject/Chapter"), `dense=True`, `expand=True`, `options=[ft.dropdown.Option(o) for o in ...]`, `on_select=lambda e: page.run_task(load_existing_content)`. Serves requirements 1-4.
   - **Proof:** `python -m py_compile edukoreaiui/screens/setup_ebooks_screen.py` exits 0; grep for `SelectorState` returns nothing.
2. **Update the form column** (lines ~185-187): replace `class_dropdown.field`, `subject_dropdown.field`, `chapter_dropdown.field` with `ft.Row([class_dropdown])`, `ft.Row([subject_dropdown])`, `ft.Row([chapter_dropdown])` (spacing as the surrounding column). Serves requirements 2 and 5.
   - **Proof:** grep for `.field` and `.chips` in the file returns nothing; py_compile exits 0.
3. **Check the untouched readers.** Confirm `load_existing_content`, `scan_chapters` and `submit_content` still compile and read `.value` from the three names unchanged. Serves requirement 5.
   - **Proof:** `git diff` shows no change outside the selector block and the three form lines.
4. **Run the screen** with `UI_MODE=web` (the desktop client is blocked on this machine) and the API running. Serves requirements 2-6.
   - **Proof:** open Setup E-Books: three dropdowns labelled Class, Subject, Chapter with the "Select ..." hints, nothing preselected, same look as the Generate Questions Class dropdown; lists contain exactly Class I-X, the four subjects, chapters 1-50; picking all three loads saved text (or leaves the box empty); SCAN and SUBMIT with a missing selection show "Select class, subject, and chapter."
5. **Run the guard checks:** `python .claude/hooks/test_guards.py` and `python .claude/skills/api-contract/scripts/check_endpoints.py` (expect unchanged results; no API files touched).

## Risks
- **What could break:** the layout (a dropdown with `expand=True` directly in the stretch column would expand vertically, hence the `ft.Row` wrappers); the event name (`on_select`) must match Flet 0.86.5; changing one dropdown after content was loaded still triggers a reload, as the chips did.
- **Riskiest step:** step 4. Nothing automated renders the UI, so look-and-feel and event wiring can only be confirmed by opening the screen. I can start the server and confirm it serves, but a person has to look at the page.

## Alternatives considered
- A shared dropdown helper reused by both screens: rejected, it would touch Generate Questions, which the intent leaves unchanged.
- Keeping `SelectorState` and putting a `Dropdown` inside it: rejected, it keeps unused chip code and the old `.field`/`.chips` indirection for no benefit.

## Rollback
`git revert` the `impl(002)` commit (or `git checkout develop -- edukoreaiui/screens/setup_ebooks_screen.py`).

## Open questions
1. Whether the developer will do the visual check in step 4 themselves. Assumption: yes; the implementation log will say what was and was not verified.
