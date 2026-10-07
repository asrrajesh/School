# UI Behavior and Design (current state)

> Last synced 2026-10-07 (git `5d3f79f`) from `edukoreaiui/` (Flet). Mockups in `designsamples/` are **target design**, not necessarily implemented; where the app and a mockup agree it is noted.
> Platforms: native desktop window, browser (`UI_MODE=web`, port `WEB_PORT` 8550 locally; in the Cloud Run container the port comes from `$PORT` through Flet's `FLET_SERVER_PORT`, see `nfr.md`), and Android APK (Flet/Flutter build). Default window 400 × 780 (phone-sized), resizable. Startup (`main.py`) prints the active mode; in desktop mode on Windows it also prints a hint to use `UI_MODE=web` if no window opens (for example when Windows code integrity blocks the Flet client).

## 1. App shell (`main.py`, `components/app_frame.py`)

- Client-side routes: `/login` (also `/`), `/signup`, `/forgot_password`, `/home`, `/academics/setup_ebooks`, `/academics/generate_questions`. Unknown routes render nothing.
- **Login and signup** are full-screen with no chrome. **All other routes** (including forgot password) are wrapped by `with_app_frame`: a fixed top header, a floating bottom bar and a shared navigation drawer.
- Header (beige `#ECD8A8`, 43 px): menu icon (opens drawer), a search box **[placeholder]**, notification icon **[placeholder]**, account icon **[placeholder]**.
- Bottom bar (translucent pill): Home (goes to `/home`), Services, Help, You **[placeholders]**.
- Drawer: gradient indigo header with logo, "EduKoreAI" and "Logged In" when a user is in session; expandable **Academics** group with **Setup E-Books** and **Generate Questions**; **Logout** (navigates to `/login`, does not clear the stored user).
- The Setup E-Books and Generate Questions views also set their own indigo `AppBar` with a back arrow to `/home` and then clear it when leaving; the shell header is overlaid on top.
- Session: `page.session.store["current_user"]` holds the user `_id` (or `"Guest"`). It is the only client state shared across screens.

## 2. Screens

### Login (`login_screen.py`)
Logo, "EduKoreAI", spaced tagline "LEARN. GROW. SUCCEED.", subtitle, **Email or Mobile Number** and **Password** (reveal toggle) fields, "Forgot password?", **Sign In**, "or continue with" divider, **Google** and **Apple** buttons, "Create an account" link.
Behavior: empty fields show a red snackbar; failures show the API's error text; success navigates to `/home`. Google button is disabled while the browser flow runs and re-enabled on failure. Apple has no handler. Both fields are **pre-filled with a developer test account**.

### Sign up (`signup_screen.py`)
Username, password and confirm-password fields, plus links back to login. Mismatch and empty-field messages, a "Creating account…" snackbar, then success and redirect to login.

### Forgot password (`forgot_password_screen.py`)
Username field and submit. Shows the API result, then goes back to login. (Inside the app frame.)

### Home (`home_screen.py`)
Scrolling column: teal hero card ("Hi <name>," then welcome text), an "Enter Activation Code" card **[placeholder]**, then one white panel per menu group from `GET /api/menus` showing up to 3 rows (title, description, optional icon box) and a "View All" label **[placeholder]**. If the API returns no menus, only the hero and activation cards show.

### Setup E-Books (`setup_ebooks_screen.py`)
1. Three dense dropdowns (same style as the Generate Questions Class dropdown: label, "Select …" hint, full width, nothing preselected): **Class** (I–X), **Subject** (Science, English, Computer Science, Mathematics), **Chapter** (1–50). The option lists are fixed, the three are independent (no cascading), and selecting a value in any of them tries to load saved chapter text once all three are chosen.
2. **Attach Images** (image picker, multiple) and **SCAN**, with a summary line of the attached file names.
3. Multiline **Chapter Content** box (replaced by scan results, editable).
4. **SUBMIT** (full-width rounded). Messages appear in colored snackbars: blue progress, red error, green success. Success navigates to `/home`.

### Generate Questions (`generate_questions_screen.py`)
Form layout, top to bottom:
1. Row: **Class** and **Subject** dropdowns (populated from saved chapter data, cascading).
2. **Chapters** multi-select chips with a count and Select/Deselect All.
3. Row: **Assessment Category** (FA – Formative, SA – Summative) and **Assessment Number** (1, 2).
4. Row: **Complexity** (Basic, Intermediate, Advanced) and **Downloads** (versions for the selection; "No versions" disabled when empty). Choosing a version asks for a save location and writes the `.docx` (a fallback write is done on desktop where the picker only returns a path).
5. Checkbox **Upload Question Paper (scan images instead of generating with AI)** reveals the upload section: Attach Images, SCAN, and a multiline "Question Paper Content" box.
6. **Question Configuration** repeater: each row has Question Type (8 options, each usable once; used ones are disabled in other rows), Question Count, Marks Per Question, a computed Total Marks, Add and Delete icons. At least one row stays; at most 8.
7. **GENERATE QUESTIONS** button (shows a spinner and "Processing…" while working).
Validation messages (red snackbar): required selections, empty paper content in upload mode, per-row errors. Success (green): "✓ Generated|Uploaded and extracted N questions successfully! (Version V)"; the Downloads list refreshes and the new version is preselected. In upload mode the content box and attachments are cleared after success.
Question types offered: mcq, fib, mtf, sa, tf, short, long, diagram (see [prompt-and-generation-rule.md](prompt-and-generation-rule.md) for which ones the backend actually generates).

## 3. Visual design

| Aspect | Value |
|---|---|
| Theme seed | `THEME_COLOR` `#3949AB` (indigo), used for buttons, app bars, selected chips |
| Page background | `BACKGROUND_COLOR` `#F5F5F5`; login `#F2EFE8` |
| Home tokens (match `homepage1.html`) | app bg `#F7F4EF`, primary teal `#116A54`, accent beige `#EEDAA2`, text `#1C1E1D`, muted `#626A65`, border `#2D312E`, radius 12 |
| Login accents | teal `#146C5A`, beige buttons `#ECD8A8` |
| Typography | "Cambria Regular" (registered from `fonts/`) on the login screen; Flet defaults elsewhere |
| Headings | indigo `#1a237e`, 24 px titles |
| Controls | rounded pill primary buttons (radius 23), chip selectors (radius 14), dense outlined dropdowns |
| Logo | `resources/edukoreai-logo.ico` (`APP_LOGO`) |

Visual inconsistency to note: the shell, Setup E-Books and Generate Questions use the **indigo** palette while Home and Login use the **teal/beige** palette from the design samples.

## 4. Design samples (`designsamples/`)
Five static mobile mockups titled "EduKoreAI – Guest Mode / Mobile App". They share one layout idea: a hero greeting, an invite-code card, and panels of campus features, with different palettes.
| File | Palette | Notable content |
|---|---|---|
| `homepage1.html` | teal `#116A54` + beige `#EEDAA2` | "Explore Our Campus Ecosystem", "Received an Invite Code?", an announcement ("Annual Science & AI Exhibition Next Friday"). The implemented home screen follows this one. |
| `homepage2.html` | same teal/beige | "Hi, Alex" (logged-in variant) |
| `homepage3.html` | same teal/beige | "Hi Username," guest with invite code |
| `homepage4.html` | navy `#1A365D` + gold `#F6AD55` | "Transition to Specialized Account" |
| `homepage5.html` | indigo `#4F46E5` + coral `#FF7A60` | "Connect Your Institutional Profile" |
Which sample (if any) is the chosen target for new screens is not recorded in the code.

## 5. Behaviors worth knowing
- Network calls run in worker threads (`asyncio.to_thread`) so the UI stays responsive; list calls return empty lists on failure, so an unreachable API looks like empty dropdowns.
- Setup E-Books uses hardcoded class, subject and chapter lists, while Generate Questions only offers values that already have saved chapter text.
