# Functional Specification (current state)

> Reverse-engineered from the code on 2026-10-03 (git `67ba196`). Describes what the application **does today**. Items marked **[placeholder]** appear in the UI but do nothing. Purpose statements marked *(inferred)* are guesses to be confirmed.
> Siblings: [data-model.md](data-model.md) · [api-specification.md](api-specification.md) · [prompt-and-generation-rule.md](prompt-and-generation-rule.md) · [ui-behavior-and-design.md](ui-behavior-and-design.md) · [nfr.md](nfr.md)

## 1. Purpose

*(inferred)* EduKoreAI helps school staff build assessment papers. Textbook pages are scanned into chapter text, and an LLM generates structured questions from that text, or extracts questions from a scanned existing paper. Results are versioned and downloaded as a Word document.

## 2. Users and roles

The code has **one role: any authenticated user**. There is no role field, no permission check, and no per-user data isolation. Every logged-in user can see and use all classes, subjects, chapters and question papers.

| Actor | How they arrive | What they can do today |
|---|---|---|
| Registered user | Sign up with email or mobile and a password, or Google sign-in | Everything in section 3 |
| Guest | "Guest" login code path in `login_screen.py` (`do_guest_login`) | **[placeholder]** The function exists but no button is wired to it in the login screen. If reached, it sets `current_user="Guest"` and opens Home. |

Roles such as principal, teacher, parent, student and admin are mentioned only in UI text (the "Received an Invite Code?" card and the home hero copy) and in the design samples. **No role, invite code or activation logic exists.** Any such roles are future work.

## 3. Features and user flows

### F1. Sign up
1. User opens `/signup` from the login screen ("Create an account").
2. Enters email or mobile, a password and a confirmation. The UI checks that the username is present, the password is present and both passwords match.
3. API validates: username must be a valid email or a 10–15 digit mobile number (optional `+`), and the password at least `PASSWORD_MIN_LENGTH` (default 8) characters.
4. On success the user sees "Account created! Please sign in." and returns to login. A duplicate email or mobile is rejected with "already registered".

### F2. Sign in (password)
1. User enters email or mobile and password on `/login` and presses **Sign In**.
2. On success the UI stores the user's `_id` in the page session as `current_user` and opens `/home`.
3. Errors shown: account not found, incorrect password, or cannot reach the API server.
4. Note: the login form is pre-filled with a developer test username and password (see [nfr.md](nfr.md)).

### F3. Sign in with Google
1. User presses **Google**. The app starts a local callback server and opens the system browser at Google's consent page.
2. After consent Google redirects to `http://localhost:<GOOGLE_OAUTH_PORT>/callback?code=...`. The UI sends the code to the API.
3. The API exchanges the code, verifies the ID token, then logs in the existing Google user, **links** the Google ID to an existing account with the same email, or **creates** a new account.
4. The UI stores `current_user` and opens `/home`. The Apple button is a **[placeholder]** with no handler.

### F4. Forgot password
User enters email or mobile; the API only checks that the account exists. **No reset link or OTP is sent.** The UI shows success or error and returns to login. This is a stub.

### F5. Home
After login the home screen shows a greeting ("Hi <name, mobile or email>,"), a teal welcome banner, an "Enter Activation Code" card **[placeholder]**, and menu panels loaded from the `menus` collection (at most 3 rows each, with a "View All" label that does nothing). Header search, notification and account icons and the footer tabs (Services, Help, You) are **[placeholder]**. Only Home and the drawer navigate.

### F6. Navigation
The menu icon opens a drawer with **Academics → Setup E-Books** and **Academics → Generate Questions**, and **Logout** (returns to login; the session value is not cleared).

### F7. Setup E-Books (scan and save chapter text)
1. User picks a class, a subject and a chapter. The choices are **fixed lists in the UI**: classes I–X, subjects Science, English, Computer Science, Mathematics, and chapters 1–50.
2. When all three are chosen, any saved text for that chapter is loaded into the "Chapter Content" box.
3. User attaches one or more images and presses **SCAN**. The API runs OCR and returns text with a `--- <filename> ---` header per image. The text fills the box, replacing earlier content, and can be edited.
4. **SUBMIT** saves the text (create or update by class, subject and chapter), recording the user and times, and returns to Home. Empty content is rejected.

### F8. Generate Questions
1. User chooses **Class, Subject** (from classes and subjects that have saved chapter text), one or more **Chapters** (chip multi-select with Select All), **Assessment Category** (FA or SA), **Assessment Number** (1 or 2) and **Complexity** (Basic, Intermediate or Advanced).
2. The **Question Configuration** has one row per question type: type, count and marks per question, with a row total. Each type may appear once, so there are at most 8 rows and at least 1. Validation requires a type, a positive whole count, and positive marks.
3. Pressing **GENERATE QUESTIONS** sends the selections. The API joins the selected chapters' text, asks the LLM for questions, and saves them as the next version for this class, subject, chapters, category and number. The UI reports the number of questions and the version.
4. The **Downloads** dropdown lists saved versions (Version 1, Version 2, …) for the current selection. Picking one downloads a `.docx` through a save dialog.
5. **Upload mode** (checkbox "Upload Question Paper"): the user attaches images of an existing paper and presses **SCAN**, reviews or edits the text, then presses **GENERATE QUESTIONS**. The API has the LLM extract questions from the text and saves them as a new version with `source="uploaded"`. No generation takes place.

### F9. Export to Word
The `.docx` has a title (for example "FA 1"), a subject and marks line, questions grouped by type in the configured order with Roman-numeral section headings, MCQ options, and an **Answer Key** page. It reads saved data only and makes no AI call. See [prompt-and-generation-rule.md](prompt-and-generation-rule.md) for details and limits.

## 4. Business rules (as implemented)

- Username is an email or mobile number. Email and mobile are each unique; Google ID is unique.
- A paper is identified by class + subject + chapters + category + number, and each save adds a **new version**. Nothing is overwritten and there is no delete.
- Chapter text is unique by class + subject + chapter and is overwritten on save.
- Marks come from the user's configuration and from the LLM. The total is not verified.
- Version lookup matches papers whose chapter list **overlaps** the selected chapters (see [data-model.md](data-model.md)).

## 5. Out of scope today

Roles and permissions, invite and activation codes, real password reset, Apple sign-in, search, notifications, editing or deleting saved questions, in-app preview of questions, per-user history, and any data isolation between users or schools.
