# Spec: Setup E-Books class, subject and chapter as dropdowns

- **Intent:** [intent.md](intent.md)
- **Author:** Rajesh
- **Date:** 2026-10-04
- **Status:** implemented (2026-10-04)

## Summary
Replace the three chip selectors (Class, Subject, Chapter) on the Setup E-Books screen with Flet dropdowns styled like the Class dropdown on Generate Questions. Only the look changes: options, independence of the three fields and the load/scan/submit behavior stay exactly as they are.

## Findings
- `edukoreaiui/screens/setup_ebooks_screen.py:38-80`: a local `SelectorState` class builds each selector as a bordered container of clickable chips (`self.chips`, `self.field`). `select()` stores `self.value`, refreshes the chips and calls `page.run_task(load_existing_content)`.
- `setup_ebooks_screen.py:86-97`: three instances are created with fixed options (Class I-X, Subject: Science, English, Computer Science, Mathematics, Chapter "1".."50") and aliased to `class_dropdown`, `subject_dropdown`, `chapter_dropdown`.
- The rest of the screen only reads `<name>.value` (lines 28-33, 119, 137, 149-151) and places `<name>.field` in the form column (lines 185-187). So the swap is local to the selector construction and the three `.field` placements.
- `load_existing_content` (lines 26-36) already runs only when all three values are set, and is the only side effect of a selection.
- Reference style, `generate_questions_screen.py:388-394`: `ft.Dropdown(hint_text="Select Class", label="Class", dense=True, expand=True, on_select=...)`, placed inside a `ft.Row` (line 901) so `expand=True` is horizontal. Options use `ft.dropdown.Option(...)`. Flet is pinned at 0.86.5.
- No API, data or `api_client.py` involvement.

## Requirements
1. Class, Subject and Chapter on Setup E-Books are `ft.Dropdown` controls, not chips.
2. Each copies only the Generate Questions Class dropdown's style: `label` ("Class", "Subject", "Chapter"), `hint_text` ("Select Class", "Select Subject", "Select Chapter"), `dense=True`, `expand=True` (inside a `ft.Row`). None of its data-loading or cascading logic is copied.
3. Options are unchanged: Class I-X, Subject (the four existing), Chapter 1-50. Nothing is preselected.
4. The three dropdowns are independent. Selecting a value in any of them calls `load_existing_content`, which loads saved chapter text only once all three have values (current behavior).
5. Attach Images, SCAN, Chapter Content, SUBMIT, validation messages and navigation are unchanged and still read the selected values.
6. The user can select class, subject and chapter and proceed (scan or edit content, then submit) in both `UI_MODE=desktop` and `UI_MODE=web`.

## Design
Edit only `edukoreaiui/screens/setup_ebooks_screen.py`:
- Remove the `SelectorState` class. In its place build three `ft.Dropdown` instances named `class_dropdown`, `subject_dropdown`, `chapter_dropdown` (same names, so `.value` reads elsewhere stay valid), with `options=[ft.dropdown.Option(o) for o in OPTIONS]` and `on_select=lambda e: page.run_task(load_existing_content)`.
- In the form column replace `class_dropdown.field` etc. with `ft.Row([class_dropdown])` (and the same for subject and chapter) so `expand=True` expands horizontally, matching Generate Questions.
- Keep the fixed option lists as module-level or local constants next to the dropdowns.
- Chosen over a shared component: Generate Questions' dropdowns are inline and tied to its own cascading logic, so extracting a helper would touch a screen the intent says not to change.

## Out of scope / must not change
- `generate_questions_screen.py` and all other screens, `api_client.py`, API, data.
- Option values, load-on-three-selections behavior, scan, submit, snackbar messages, routes.

## Verification
- `python -m py_compile edukoreaiui/screens/setup_ebooks_screen.py` succeeds; grep shows no remaining `SelectorState`, `.field` or `.chips`.
- Run the UI (`UI_MODE=web` on this machine, API running): Setup E-Books shows three dropdowns labelled Class, Subject, Chapter with the hints above and nothing preselected, visually matching the Generate Questions Class dropdown.
- Select a class, subject and chapter: saved chapter text loads (or the box stays empty if none); changing any one reloads; SCAN and SUBMIT validation still reports "Select class, subject, and chapter." until all three are chosen.
- Dropdown lists contain exactly Class I-X, the four subjects, and chapters 1-50.
- Not verifiable here: no UI tests exist; the desktop client is blocked on this machine, so desktop mode is unverified.

## Flagged concerns
- UX: a 50-item Chapter dropdown scrolls as a menu; this is accepted by the intent. Typing to search is not part of this change.
- The Flet `Dropdown` API (`on_select`, `ft.dropdown.Option`) is used the same way as on Generate Questions, which works on the pinned 0.86.5.

## Open questions
None.
