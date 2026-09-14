import asyncio
import re
from pathlib import Path

import flet as ft
from services.api_client import (
    get_classes,
    get_chapters,
    get_subjects,
    get_question_versions,
)
from services.api_client import generate_questions as api_generate_questions
from services.api_client import (
    download_question_paper as api_download_question_paper,
)
from services.api_client import upload_questions as api_upload_questions

# (key, label) — label is the text shown to the user in the dropdown
QUESTION_TYPES = [
    ("mcq", "Choose the correct answer"),
    ("short", "Answer the following questions (Short)"),
    ("long", "Answer the following questions (Long)"),
]

ASSESSMENT_CATEGORIES = [
    ("fa", "FA - Formative Assessment"),
    ("sa", "SA - Summative Assessment"),
]

ASSESSMENT_NUMBERS = [("1", "1"), ("2", "2")]

COMPLEXITY_LEVELS = [
    ("basic", "Basic"),
    ("intermediate", "Intermediate"),
    ("advanced", "Advanced"),
]

# Matches the "Version {v}" labels downloads_selector builds
_VERSION_LABEL_RE = re.compile(r"Version (\d+)")


def _parse_version_number(label: str | None) -> int | None:
    """'Version 3' -> 3. Returns None for anything that doesn't match."""
    if not label:
        return None
    match = _VERSION_LABEL_RE.fullmatch(label)
    return int(match.group(1)) if match else None


def _write_fallback_if_needed(saved_path: str | None, data: bytes) -> None:
    """
    FilePicker.save_file(src_bytes=...) writes the file natively on mobile/web.
    On desktop, per Flet's docs, save_file() only opens the picker and returns
    the chosen path -- the file itself is not created there, so write it here.
    """
    if not saved_path:
        return
    try:
        path = Path(saved_path)
        if path.exists() and path.stat().st_size == len(data):
            return
        path.write_bytes(data)
    except OSError:
        pass


# Fixed column widths for table layout
COL_TYPE_WIDTH = 260
COL_COUNT_WIDTH = 120
COL_MARKS_WIDTH = 140
COL_TOTAL_WIDTH = 80
COL_ACTION_WIDTH = 90
CELL_SPACING = 8
ROW_HEIGHT = 52


def _cell(control, width):
    """Fixed-width table cell wrapper."""
    return ft.Container(
        content=control,
        width=width,
        height=ROW_HEIGHT,
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding(left=4, top=0, right=4, bottom=0),
    )


def _header_cell(label, width):
    return ft.Container(
        content=ft.Text(
            label,
            size=12,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER,
            max_lines=2,
        ),
        width=width,
        height=42,
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding(left=4, top=0, right=4, bottom=0),
    )


class QuestionRow:
    """One repeater row: question type, count, marks and the computed row total."""

    def __init__(self, on_type_change, on_remove, on_recalc, on_add):
        self._on_type_change = on_type_change
        self._on_remove = on_remove
        self._on_recalc = on_recalc
        self._on_add = on_add

        self.type_dropdown = ft.Dropdown(
            options=[],
            hint_text="Select type",
            text_size=13,
            dense=True,
            expand=True,
            on_select=lambda e: self._on_type_change(),
        )
        self.count_field = ft.TextField(
            text_size=13,
            dense=True,
            text_align=ft.TextAlign.CENTER,
            expand=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: self._on_recalc(),
        )
        self.marks_field = ft.TextField(
            text_size=13,
            dense=True,
            text_align=ft.TextAlign.CENTER,
            expand=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: self._on_recalc(),
        )
        self.total_text = ft.Text("0", size=15, weight=ft.FontWeight.BOLD, color="#1a237e")
        self.add_button = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            icon_color="#3949AB",
            tooltip="Add",
            on_click=lambda e: self._on_add(),
        )
        self.delete_button = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=ft.Colors.RED_400,
            tooltip="Delete",
            on_click=lambda e: self._on_remove(self),
        )

        self.row_control = ft.Container(
            content=ft.Row(
                controls=[
                    _cell(self.type_dropdown, COL_TYPE_WIDTH),
                    _cell(self.count_field, COL_COUNT_WIDTH),
                    _cell(self.marks_field, COL_MARKS_WIDTH),
                    _cell(self.total_text, COL_TOTAL_WIDTH),
                    _cell(self.add_button, COL_ACTION_WIDTH),
                    _cell(self.delete_button, COL_ACTION_WIDTH),
                ],
                spacing=CELL_SPACING,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=False,
                tight=True,
            ),
            border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
        )

    def refresh_total(self):
        self.total_text.value = self._compute_total_display()

    def _compute_total_display(self) -> str:
        try:
            count = int(self.count_field.value)
            marks = float(self.marks_field.value)
            if count <= 0 or marks <= 0:
                return "0"
            return f"{count * marks:g}"
        except (TypeError, ValueError):
            return "0"

    def validate(self) -> str | None:
        if not self.type_dropdown.value:
            return "Select a question type for every row."
        try:
            count = int(self.count_field.value)
            if count <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return "Question count must be a positive whole number."
        try:
            marks = float(self.marks_field.value)
            if marks <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return "Marks per question must be a positive number."
        return None

    def to_dict(self) -> dict:
        count = int(self.count_field.value)
        marks = float(self.marks_field.value)
        return {
            "questionType": self.type_dropdown.value,
            "questionCount": count,
            "marksPerQuestion": marks,
            "rowTotalMarks": count * marks,
        }


def generate_questions_view(page: ft.Page):
    """Return the Generate Questions screen with tabs for Generate and Upload."""

    def go_back(e):
        page.appbar = None
        page.navigate("/home")

    def show_snack(msg: str, color=ft.Colors.RED_600):
        page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor=color))

    # ────────────────────────────────────────────────────────────────────
    # DROPDOWN SELECTORS (Class, Subject, Assessment Category, Number, Complexity)
    # ────────────────────────────────────────────────────────────────────

    class_dropdown = ft.Dropdown(
        hint_text="Select Class",
        label="Class",
        dense=True,
        expand=True,
        on_change=lambda e: page.run_task(on_class_selected),
    )

    subject_dropdown = ft.Dropdown(
        hint_text="Select Subject",
        label="Subject",
        dense=True,
        expand=True,
        on_change=lambda e: page.run_task(on_subject_selected),
    )

    chapter_multiselect = ft.MultiSelect(
        hint_text="Select Chapters",
        label="Chapters",
        dense=True,
        expand=True,
        on_select=lambda e: page.run_task(on_chapters_selected),
    )

    assessment_category_dropdown = ft.Dropdown(
        hint_text="Select Assessment",
        label="Assessment Category",
        dense=True,
        expand=True,
        options=[ft.dropdown.Option(code, label) for code, label in ASSESSMENT_CATEGORIES],
        on_change=lambda e: page.run_task(on_assessment_selected),
    )

    assessment_number_dropdown = ft.Dropdown(
        hint_text="Select Number",
        label="Assessment Number",
        dense=True,
        expand=True,
        options=[ft.dropdown.Option(num, num) for num, num in ASSESSMENT_NUMBERS],
        on_change=lambda e: page.run_task(on_assessment_selected),
    )

    complexity_dropdown = ft.Dropdown(
        hint_text="Select Complexity",
        label="Complexity",
        dense=True,
        expand=True,
        options=[ft.dropdown.Option(code, label) for code, label in COMPLEXITY_LEVELS],
        on_change=lambda e: page.update(),
    )

    downloads_dropdown = ft.Dropdown(
        hint_text="Select Version",
        label="Downloads",
        dense=True,
        expand=True,
        on_change=lambda e: page.run_task(on_download_selected),
    )

    # ────────────────────────────────────────────────────────────────────
    # EVENT HANDLERS FOR CASCADING SELECTORS
    # ────────────────────────────────────────────────────────────────────

    async def on_class_selected():
        subject_dropdown.options = []
        subject_dropdown.value = None
        chapter_multiselect.options = []
        chapter_multiselect.value = None
        downloads_dropdown.options = []
        downloads_dropdown.value = None
        if class_dropdown.value:
            subjects = await asyncio.to_thread(get_subjects, class_dropdown.value)
            subject_dropdown.options = [ft.dropdown.Option(s) for s in subjects]
        page.update()

    async def on_subject_selected():
        chapter_multiselect.options = []
        chapter_multiselect.value = None
        downloads_dropdown.options = []
        downloads_dropdown.value = None
        if class_dropdown.value and subject_dropdown.value:
            chapters = await asyncio.to_thread(
                get_chapters, class_dropdown.value, subject_dropdown.value
            )
            chapter_multiselect.options = [ft.dropdown.Option(ch) for ch in chapters]
        page.update()

    async def on_chapters_selected():
        downloads_dropdown.options = []
        downloads_dropdown.value = None
        await refresh_downloads()
        page.update()

    async def on_assessment_selected():
        downloads_dropdown.options = []
        downloads_dropdown.value = None
        await refresh_downloads()
        page.update()

    # ────────────────────────────────────────────────────────────────────
    # DOWNLOADS & FILE OPERATIONS
    # ────────────────────────────────────────────────────────────────────

    download_file_picker = ft.FilePicker()
    page.services.append(download_file_picker)
    _download_in_progress = {"value": False}

    async def on_download_selected():
        page.update()
        version = _parse_version_number(downloads_dropdown.value)
        if version is None or _download_in_progress["value"]:
            return

        _download_in_progress["value"] = True
        show_snack("Preparing document...", color=ft.Colors.BLUE_700)
        try:
            chapters_str = ",".join(chapter_multiselect.value) if chapter_multiselect.value else ""
            try:
                docx_bytes = await asyncio.to_thread(
                    api_download_question_paper,
                    class_dropdown.value,
                    subject_dropdown.value,
                    chapters_str,
                    assessment_category_dropdown.value,
                    int(assessment_number_dropdown.value),
                    version,
                )
            except Exception as exc:
                show_snack(f"Download failed: {exc}", color=ft.Colors.RED_600)
                return

            chapters_label = "-".join(chapter_multiselect.value) if chapter_multiselect.value else "chapters"
            safe_subject = (subject_dropdown.value or "subject").replace("/", "-")
            safe_chapters = chapters_label.replace("/", "-")
            category_code = assessment_category_dropdown.value or "fa"
            file_name = f"{category_code.upper()}{assessment_number_dropdown.value} - {safe_subject} - {safe_chapters} - v{version}.docx"

            try:
                saved_path = await download_file_picker.save_file(
                    dialog_title="Save Question Paper",
                    file_name=file_name,
                    file_type=ft.FilePickerFileType.CUSTOM,
                    allowed_extensions=["docx"],
                    src_bytes=docx_bytes,
                )
            except Exception as exc:
                show_snack(f"Could not open save dialog: {exc}", color=ft.Colors.RED_600)
                return
            if saved_path is None:
                return

            _write_fallback_if_needed(saved_path, docx_bytes)
            show_snack(f"✓ Saved {file_name}", color=ft.Colors.GREEN_700)
        finally:
            _download_in_progress["value"] = False

    async def refresh_downloads():
        ready = bool(
            class_dropdown.value
            and subject_dropdown.value
            and chapter_multiselect.value
            and assessment_category_dropdown.value
            and assessment_number_dropdown.value
        )
        if not ready:
            downloads_dropdown.options = []
            downloads_dropdown.value = None
            return

        chapters_str = ",".join(chapter_multiselect.value)
        versions = await asyncio.to_thread(
            get_question_versions,
            class_dropdown.value,
            subject_dropdown.value,
            chapters_str,
            assessment_category_dropdown.value,
            int(assessment_number_dropdown.value),
        )
        downloads_dropdown.options = [
            ft.dropdown.Option(f"Version {v}") for v in versions
        ]
        if not versions:
            downloads_dropdown.options = [
                ft.dropdown.Option("No versions", disabled=True)
            ]

    # ────────────────────────────────────────────────────────────────────
    # TAB 1: GENERATE QUESTIONS
    # ────────────────────────────────────────────────────────────────────

    rows: list[QuestionRow] = []
    rows_column = ft.Column(spacing=0, tight=True)
    header_row = ft.Container(
        content=ft.Row(
            controls=[
                _header_cell("Question Type", COL_TYPE_WIDTH),
                _header_cell("Question Count", COL_COUNT_WIDTH),
                _header_cell("Marks Per Question", COL_MARKS_WIDTH),
                _header_cell("Total", COL_TOTAL_WIDTH),
                _header_cell("Add", COL_ACTION_WIDTH),
                _header_cell("Delete", COL_ACTION_WIDTH),
            ],
            spacing=CELL_SPACING,
            wrap=False,
            tight=True,
        ),
        bgcolor=ft.Colors.GREY_100,
        border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_400)),
    )
    table = ft.Row(
        controls=[
            ft.Column(
                controls=[header_row, rows_column],
                spacing=0,
                tight=True,
            )
        ],
        scroll=ft.ScrollMode.HIDDEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    def used_types(exclude_row: QuestionRow | None = None) -> set:
        return {row.type_dropdown.value for row in rows if row is not exclude_row and row.type_dropdown.value}

    def refresh_dropdown_options():
        for row in rows:
            taken = used_types(exclude_row=row)
            row.type_dropdown.options = [
                ft.dropdown.Option(key, text, disabled=key in taken) for key, text in QUESTION_TYPES
            ]

    def render_rows(update_page: bool = True):
        rows_column.controls = [row.row_control for row in rows]
        refresh_dropdown_options()
        at_max = len(rows) >= len(QUESTION_TYPES)
        for row in rows:
            row.add_button.disabled = at_max
            row.delete_button.disabled = len(rows) <= 1
        if update_page:
            page.update()

    def recalc_row(row: QuestionRow):
        row.refresh_total()
        page.update()

    def add_row():
        if len(rows) >= len(QUESTION_TYPES):
            return
        row = QuestionRow(
            on_type_change=lambda: (refresh_dropdown_options(), page.update()),
            on_remove=remove_row,
            on_recalc=lambda: None,
            on_add=lambda: add_row(),
        )
        row._on_recalc = lambda r=row: recalc_row(r)
        rows.append(row)
        render_rows()

    def remove_row(row: QuestionRow):
        if len(rows) <= 1:
            return
        rows.remove(row)
        render_rows()

    async def generate_questions_async(e):
        if not (
            class_dropdown.value
            and subject_dropdown.value
            and chapter_multiselect.value
            and assessment_category_dropdown.value
            and assessment_number_dropdown.value
            and complexity_dropdown.value
        ):
            show_snack("Select all required fields: class, subject, chapters, assessment, and complexity.")
            return
        if not rows:
            show_snack("Add at least one question row.")
            return
        for row in rows:
            error = row.validate()
            if error:
                show_snack(error)
                return

        current_user = page.session.store.get("current_user") or "unknown"

        generate_button.disabled = True
        generate_button.content = ft.Row(
            controls=[
                ft.CircleAvatar(content=ft.ProgressRing(width=16, height=16)),
                ft.Text("Generating...", weight=ft.FontWeight.BOLD),
            ],
            spacing=8,
            tight=True,
        )
        page.update()

        try:
            question_rows = [
                {
                    "questionType": row.type_dropdown.value,
                    "questionCount": int(row.count_field.value),
                    "marksPerQuestion": float(row.marks_field.value),
                }
                for row in rows
            ]

            result = await asyncio.to_thread(
                api_generate_questions,
                class_dropdown.value,
                subject_dropdown.value,
                list(chapter_multiselect.value),
                assessment_category_dropdown.value,
                int(assessment_number_dropdown.value),
                complexity_dropdown.value,
                question_rows,
                current_user,
            )

            if result.get("success"):
                num_questions = len(result.get("questions", []))
                version = result.get("version")
                version_note = f" (Version {version})" if version else ""
                show_snack(
                    f"✓ Generated {num_questions} questions successfully!{version_note}",
                    color=ft.Colors.GREEN_700,
                )
                await refresh_downloads()
                if version:
                    downloads_dropdown.value = f"Version {version}"
            else:
                error_msg = result.get("error", "Unknown error occurred.")
                show_snack(f"Generation failed: {error_msg}", color=ft.Colors.RED_600)

        except Exception as exc:
            show_snack(f"Error: {str(exc)}", color=ft.Colors.RED_600)

        finally:
            generate_button.disabled = False
            generate_button.content = ft.Text("GENERATE QUESTIONS", weight=ft.FontWeight.BOLD)
            page.update()

    def generate_questions(e):
        """Wrapper to run async function."""
        page.run_task(generate_questions_async, e)

    add_row()

    generate_button = ft.ElevatedButton(
        content=ft.Text("GENERATE QUESTIONS", weight=ft.FontWeight.BOLD),
        color=ft.Colors.WHITE,
        bgcolor="#3949AB",
        height=46,
        expand=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=23)),
        on_click=generate_questions,
    )

    generate_tab_content = ft.Column(
        scroll=ft.ScrollMode.HIDDEN,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=12,
        controls=[
            ft.Text("Question Configuration", size=16, weight=ft.FontWeight.BOLD, color="#1a237e"),
            table,
            ft.Container(
                content=generate_button,
                padding=ft.Padding(left=0, top=10, right=0, bottom=0),
            ),
        ],
    )

    # ────────────────────────────────────────────────────────────────────
    # TAB 2: UPLOAD QUESTIONS
    # ────────────────────────────────────────────────────────────────────

    upload_file_picker = ft.FilePicker()
    page.services.append(upload_file_picker)
    selected_files = ft.Text("No images selected", color=ft.Colors.GREY_600, size=12)
    selected_image_files = []

    async def choose_images(e):
        nonlocal selected_image_files
        files = await upload_file_picker.pick_files(
            allow_multiple=True,
            file_type=ft.FilePickerFileType.IMAGE,
            with_data=True,
        )
        selected_image_files = files
        if files:
            selected_files.value = f"{len(files)} image(s) selected: " + ", ".join(
                file.name for file in files
            )
        else:
            selected_files.value = "No images selected"
        page.update()

    async def scan_paper_images(e):
        nonlocal selected_image_files
        if not selected_image_files:
            show_snack("Attach at least one image.", color=ft.Colors.RED_600)
            return

        show_snack("Scanning question paper...", color=ft.Colors.BLUE_700)
        try:
            # Import the OCR function to extract text from images
            from services.api_client import scan_images
            content = await asyncio.to_thread(scan_images, selected_image_files)
            upload_content_field.value = content
            page.update()
        except Exception as exc:
            show_snack(f"Scan failed: {exc}", color=ft.Colors.RED_600)

    async def submit_uploaded_questions(e):
        if not (
            class_dropdown.value
            and subject_dropdown.value
            and chapter_multiselect.value
            and assessment_category_dropdown.value
            and assessment_number_dropdown.value
            and complexity_dropdown.value
        ):
            show_snack("Select all required fields.", color=ft.Colors.RED_600)
            return

        content = (upload_content_field.value or "").strip()
        if not content:
            show_snack("Add question paper content before submitting.", color=ft.Colors.RED_600)
            return

        current_user = page.session.store.get("current_user") or "unknown"

        upload_button.disabled = True
        upload_button.content = ft.Row(
            controls=[
                ft.CircleAvatar(content=ft.ProgressRing(width=16, height=16)),
                ft.Text("Uploading...", weight=ft.FontWeight.BOLD),
            ],
            spacing=8,
            tight=True,
        )
        page.update()

        try:
            result = await asyncio.to_thread(
                api_upload_questions,
                class_dropdown.value,
                subject_dropdown.value,
                list(chapter_multiselect.value),
                assessment_category_dropdown.value,
                int(assessment_number_dropdown.value),
                complexity_dropdown.value,
                current_user,
                selected_image_files,
            )

            if result.get("success"):
                num_questions = len(result.get("questions", []))
                version = result.get("version")
                version_note = f" (Version {version})" if version else ""
                show_snack(
                    f"✓ Uploaded and extracted {num_questions} questions successfully!{version_note}",
                    color=ft.Colors.GREEN_700,
                )
                upload_content_field.value = ""
                selected_image_files = []
                selected_files.value = "No images selected"
                await refresh_downloads()
                if version:
                    downloads_dropdown.value = f"Version {version}"
            else:
                error_msg = result.get("error", "Unknown error occurred.")
                show_snack(f"Upload failed: {error_msg}", color=ft.Colors.RED_600)

        except Exception as exc:
            show_snack(f"Error: {str(exc)}", color=ft.Colors.RED_600)

        finally:
            upload_button.disabled = False
            upload_button.content = ft.Text("SUBMIT", weight=ft.FontWeight.BOLD)
            page.update()

    def upload_questions_handler(e):
        page.run_task(submit_uploaded_questions, e)

    upload_content_field = ft.TextField(
        label="Question Paper Content",
        multiline=True,
        expand=True,
        min_lines=4,
        max_lines=None,
        text_size=13,
        value="",
    )

    upload_button = ft.ElevatedButton(
        content=ft.Text("SUBMIT", weight=ft.FontWeight.BOLD),
        color=ft.Colors.WHITE,
        bgcolor="#3949AB",
        height=46,
        expand=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=23)),
        on_click=upload_questions_handler,
    )

    upload_tab_content = ft.Column(
        scroll=ft.ScrollMode.HIDDEN,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=12,
        controls=[
            ft.Text("Upload Question Paper", size=16, weight=ft.FontWeight.BOLD, color="#1a237e"),
            ft.Text(
                "Upload photos of your question paper to extract and save questions.",
                color=ft.Colors.GREY_600,
                size=13,
            ),
            ft.Row(
                controls=[
                    ft.OutlinedButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.ATTACH_FILE, size=16),
                                ft.Text("Attach Images", size=13),
                            ],
                            tight=True,
                            spacing=6,
                        ),
                        on_click=choose_images,
                        height=36,
                    ),
                    ft.ElevatedButton(
                        content=ft.Text("SCAN", size=13),
                        on_click=lambda e: page.run_task(scan_paper_images, e),
                        style=ft.ButtonStyle(
                            bgcolor={"": "#3949AB"},
                            color={"": ft.Colors.WHITE},
                        ),
                        height=36,
                    ),
                ],
                spacing=12,
            ),
            selected_files,
            upload_content_field,
            ft.Container(
                content=upload_button,
                padding=ft.Padding(left=0, top=10, right=0, bottom=0),
            ),
        ],
    )

    # ────────────────────────────────────────────────────────────────────
    # MAIN TAB CONTROL
    # ────────────────────────────────────────────────────────────────────

    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(
                text="Generate Questions",
                content=generate_tab_content,
            ),
            ft.Tab(
                text="Upload Questions",
                content=upload_tab_content,
            ),
        ],
    )

    # ────────────────────────────────────────────────────────────────────
    # MAIN LAYOUT
    # ────────────────────────────────────────────────────────────────────

    page.appbar = ft.AppBar(
        leading=ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_color=ft.Colors.WHITE,
            on_click=go_back,
        ),
        title=ft.Text("Generate Questions", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor="#3949AB",
    )
    page.drawer = None

    form_layout = ft.Column(
        scroll=ft.ScrollMode.HIDDEN,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=16,
        controls=[
            ft.Text("Generate Questions", size=24, weight=ft.FontWeight.BOLD, color="#1a237e"),
            ft.Text(
                "Configure and generate or upload question papers.",
                color=ft.Colors.GREY_600,
                size=14,
            ),
            # Selector fields row 1
            ft.Row(
                controls=[class_dropdown, subject_dropdown],
                spacing=12,
            ),
            # Selector fields row 2
            ft.Row(
                controls=[chapter_multiselect],
                spacing=12,
            ),
            # Assessment selectors row
            ft.Row(
                controls=[assessment_category_dropdown, assessment_number_dropdown],
                spacing=12,
            ),
            # Complexity and Downloads row
            ft.Row(
                controls=[complexity_dropdown, downloads_dropdown],
                spacing=12,
            ),
            # Tabs
            tabs,
        ],
    )

    async def load_classes_initial():
        classes = await asyncio.to_thread(get_classes)
        class_dropdown.options = [ft.dropdown.Option(c) for c in classes]
        page.update()

    page.run_task(load_classes_initial)

    return ft.Container(
        content=form_layout,
        padding=ft.Padding(left=20, top=20, right=20, bottom=20),
        expand=True,
    )
