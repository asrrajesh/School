# Intent: Setup E-Books class, subject and chapter as dropdowns

- **ID:** 002
- **Author:** Rajesh
- **Date:** 2026-10-04
- **Status:** implemented (2026-10-04)
- **Type:** change to existing behavior

## Developer request
> Implement the below new feature.
> In the setup ebooks page, there are 3 selection controls class, subject and chapter.
> I wanted to change those controls into dropdowns.
> Dropdowns should be same as class dropdown field of Generate Questions page.
> There is no change in functionality.
> After this implementation, User should be able to select the class, subject and chapter and proceed further.

## Problem
On the Setup E-Books screen (`edukoreaiui/screens/setup_ebooks_screen.py`), **Class** (I–X), **Subject** (Science, English, Computer Science, Mathematics) and **Chapter** (1–50) are single-select chip selectors, per `knowledge/ui-behavior-and-design.md`. The Generate Questions screen uses dropdowns for Class and Subject, so the two screens look and behave differently for the same kind of choice, and a row of 50 chapter chips is long to scan.

## Proposed outcome
- Class, Subject and Chapter on Setup E-Books are dropdowns instead of chip selectors.
- Each dropdown copies **only the visual style** of the **Class** dropdown on the Generate Questions screen (look, label and placeholder style, nothing preselected). None of that dropdown's functionality is copied: no loading options from saved data and no cascading.
- The options stay as they are today (Class I-X, Subject: Science, English, Computer Science, Mathematics, Chapter 1-50), and the three selections stay independent, as the chips are today.
- No change in functionality: after choosing a class, subject and chapter the user can proceed as today (saved chapter text loads once all three are chosen, then attach images, SCAN, edit content, SUBMIT).

## Affected users and systems
- **Users:** anyone who uses Setup E-Books.
- **Screens / UI:** Setup E-Books (`edukoreaiui/screens/setup_ebooks_screen.py`); the Generate Questions Class dropdown is the visual reference.
- **API:** none.
- **Data:** none.
- **Knowledge files to update afterwards:** `knowledge/ui-behavior-and-design.md` (Setup E-Books section).

## Constraints
- No functional change: the same choices, the same load-on-three-selections behavior, the same scan, content and submit flow.
- No API or `api_client.py` change; follow the `ui-conventions` skill.
- Must work in both `UI_MODE` values (desktop and web).

## Open questions
None. Answered by the developer on 2026-10-04: (1) copy only the UI style of the Generate Questions Class dropdown, no functionality; (2) no cascading, independent as the chips are today; (3) same label and placeholder style, nothing preselected.
