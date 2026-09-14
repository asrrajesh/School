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
from services.api_client import save_uploaded_questions as api_save_uploaded_questions

# (key, label) — label is the text shown to the user in the dropdown
QUESTION_TYPES = [
    ("mcq", "Choose the correct answer"),
    ("fib", "Fill in the blanks with a suitable correct answer"),
    ("mtf", "Match the following"),
    ("sa", "Answer the following in one sentence"),
    ("tf", "Answer the following statements are True or False"),
    ("short", "Answer the following questions (Short)"),
    ("long", "Answer the following questions (Long)"),
    ("diagram", "Draw a neat labeled diagram of the following"),
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


class MultiSelect(ft.Container):
    """Custom multi-select chip control for selecting multiple options (e.g. chapters)."""

    def __init__(
        self,
        label: str = "Select",
        hint_text: str = "Select Options",
        options=None,
        on_select=None,
        dense: bool = True,
        expand: bool = True,
        **kwargs,
    ):
        super().__init__(expand=expand)
        self.label_text = label
        self.hint_text = hint_text
        self.on_select = on_select
        self._raw_options = []
        self._selected: set[str] = set()

        self.chips_row = ft.Row(
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.label_control = ft.Text(
            self.label_text,
            size=12,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREY_800,
        )
        self.count_control = ft.Text("", size=11, color=ft.Colors.GREY_600)
        self.select_all_btn = ft.TextButton(
            "Select All",
            style=ft.ButtonStyle(padding=ft.Padding(4, 0, 4, 0)),
            on_click=self._toggle_select_all,
            visible=False,
        )

        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.label_control,
                        self.count_control,
                        ft.Container(expand=True),
                        self.select_all_btn,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    height=20,
                ),
                self.chips_row,
            ],
            spacing=4,
            tight=True,
        )
        self.border = ft.Border.all(1, ft.Colors.GREY_400)
        self.border_radius = 6
        self.padding = ft.Padding(left=10, top=6, right=10, bottom=8)
        self.bgcolor = ft.Colors.WHITE

        if options:
            self.options = options
        else:
            self._render()

    @property
    def options(self):
        return self._raw_options

    @options.setter
    def options(self, opts):
        self._raw_options = list(opts) if opts else []
        valid_keys = {self._get_opt_val(opt) for opt in self._raw_options}
        self._selected = self._selected.intersection(valid_keys)
        self._render()

    @property
    def value(self):
        selected_in_order = [
            self._get_opt_val(opt)
            for opt in self._raw_options
            if self._get_opt_val(opt) in self._selected
        ]
        return selected_in_order if selected_in_order else None

    @value.setter
    def value(self, val):
        if not val:
            self._selected.clear()
        elif isinstance(val, (list, set, tuple)):
            self._selected = {str(v) for v in val}
        else:
            self._selected = {str(val)}
        self._render()

    def _get_opt_val(self, opt):
        if hasattr(opt, "key") and opt.key is not None:
            return str(opt.key)
        if hasattr(opt, "text") and opt.text is not None:
            return str(opt.text)
        return str(opt)

    def _get_opt_text(self, opt):
        if hasattr(opt, "text") and opt.text is not None:
            return str(opt.text)
        if hasattr(opt, "key") and opt.key is not None:
            return str(opt.key)
        return str(opt)

    def _toggle_select(self, val):
        if val in self._selected:
            self._selected.remove(val)
        else:
            self._selected.add(val)
        self._render()
        if self.page:
            self.page.update()
        if self.on_select:
            self.on_select(None)

    def _toggle_select_all(self, e):
        all_vals = [self._get_opt_val(opt) for opt in self._raw_options]
        if len(self._selected) == len(all_vals) and len(all_vals) > 0:
            self._selected.clear()
        else:
            self._selected = set(all_vals)
        self._render()
        if self.page:
            self.page.update()
        if self.on_select:
            self.on_select(None)

    def _render(self):
        if not self._raw_options:
            self.chips_row.controls = [
                ft.Text(
                    self.hint_text or "No options available",
                    size=12,
                    italic=True,
                    color=ft.Colors.GREY_500,
                )
            ]
            self.count_control.value = ""
            self.select_all_btn.visible = False
            return

        all_vals = [self._get_opt_val(opt) for opt in self._raw_options]
        is_all = len(self._selected) == len(all_vals) and len(all_vals) > 0
        self.select_all_btn.text = "Deselect All" if is_all else "Select All"
        self.select_all_btn.visible = len(all_vals) > 1
        self.count_control.value = (
            f"({len(self._selected)} selected)" if self._selected else ""
        )

        chip_controls = []
        for opt in self._raw_options:
            val = self._get_opt_val(opt)
            text = self._get_opt_text(opt)
            is_sel = val in self._selected
            chip_controls.append(
                ft.Container(
                    content=ft.Text(
                        text,
                        size=12,
                        weight=ft.FontWeight.W_500 if is_sel else ft.FontWeight.NORMAL,
                        color=ft.Colors.WHITE if is_sel else ft.Colors.GREY_800,
                    ),
                    bgcolor="#3949AB" if is_sel else "#F5F5F5",
                    border=ft.Border.all(1, "#3949AB" if is_sel else ft.Colors.GREY_400),
                    border_radius=14,
                    padding=ft.Padding(left=10, top=4, right=10, bottom=4),
                    on_click=lambda e, v=val: self._toggle_select(v),
                    ink=True,
                )
            )
        self.chips_row.controls = chip_controls


class QuestionRow:
    """One repeater row: question type, count, marks and the computed row total."""

    def __init__(self, on_type_change, on_remove, on_recalc, on_add):
        self._on_type_change = on_type_change
        self._on_remove = on_remove
        self._on_recalc = on_recalc
        self._on_add = on_add

        self.type_dropdown = ft.Dropdown(
            label="Question Type",
            options=[],
            hint_text="Select type",
            text_size=13,
            dense=True,
            col={"xs": 12, "sm": 6, "md": 4},
            on_select=lambda e: self._on_type_change(),
        )
        self.count_field = ft.TextField(
            label="Question Count",
            text_size=13,
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            col={"xs": 6, "sm": 3, "md": 2},
            on_change=lambda e: self._on_recalc(),
        )
        self.marks_field = ft.TextField(
            label="Marks Per Question",
            text_size=13,
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            col={"xs": 6, "sm": 3, "md": 2},
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

        total_block = ft.Column(
            controls=[
                ft.Text("Total Marks", size=11, color=ft.Colors.GREY_600),
                self.total_text,
            ],
            spacing=2,
            tight=True,
            col={"xs": 6, "sm": 3, "md": 2},
        )
        actions_block = ft.Row(
            controls=[self.add_button, self.delete_button],
            spacing=0,
            tight=True,
            col={"xs": 12, "sm": 3, "md": 2},
        )

        self.row_control = ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    self.type_dropdown,
                    self.count_field,
                    self.marks_field,
                    total_block,
                    actions_block,
                ],
                spacing=8,
                run_spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=4, top=10, right=4, bottom=10),
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
    """Return the Generate Questions screen with an inline upload toggle."""

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
        on_select=lambda e: page.run_task(on_class_selected),
    )

    subject_dropdown = ft.Dropdown(
        hint_text="Select Subject",
        label="Subject",
        dense=True,
        expand=True,
        on_select=lambda e: page.run_task(on_subject_selected),
    )

    chapter_multiselect = MultiSelect(
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
        on_select=lambda e: page.run_task(on_assessment_selected),
    )

    assessment_number_dropdown = ft.Dropdown(
        hint_text="Select Number",
        label="Assessment Number",
        dense=True,
        expand=True,
        options=[ft.dropdown.Option(num, num) for num, num in ASSESSMENT_NUMBERS],
        on_select=lambda e: page.run_task(on_assessment_selected),
    )

    complexity_dropdown = ft.Dropdown(
        hint_text="Select Complexity",
        label="Complexity",
        dense=True,
        expand=True,
        options=[ft.dropdown.Option(code, label) for code, label in COMPLEXITY_LEVELS],
        on_select=lambda e: page.update(),
    )

    downloads_dropdown = ft.Dropdown(
        hint_text="Select Version",
        label="Downloads",
        dense=True,
        expand=True,
        on_select=lambda e: page.run_task(on_download_selected),
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
    # QUESTION CONFIGURATION (required for both generating and uploading)
    # ────────────────────────────────────────────────────────────────────

    rows: list[QuestionRow] = []
    rows_column = ft.Column(spacing=0, tight=True)

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

    add_row()

    question_config_section = ft.Column(
        spacing=12,
        controls=[
            ft.Text("Question Configuration", size=16, weight=ft.FontWeight.BOLD, color="#1a237e"),
            ft.Text(
                "Required for both generating and uploading question papers.",
                color=ft.Colors.GREY_600,
                size=13,
            ),
            rows_column,
        ],
    )

    # ────────────────────────────────────────────────────────────────────
    # UPLOAD QUESTION PAPER (revealed when "Upload Question Paper" is checked)
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

    upload_content_field = ft.TextField(
        label="Question Paper Content",
        multiline=True,
        expand=True,
        min_lines=4,
        max_lines=None,
        text_size=13,
        value="",
    )

    upload_section = ft.Column(
        spacing=12,
        visible=False,
        controls=[
            ft.Text("Upload Question Paper", size=16, weight=ft.FontWeight.BOLD, color="#1a237e"),
            ft.Text(
                "Attach and scan photos of your question paper, then click "
                "Generate Questions below to map them to your selections and save.",
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
        ],
    )

    # ────────────────────────────────────────────────────────────────────
    # UPLOAD MODE TOGGLE
    # ────────────────────────────────────────────────────────────────────

    def toggle_upload_mode(e):
        upload_section.visible = upload_checkbox.value
        page.update()

    upload_checkbox = ft.Checkbox(
        label="Upload Question Paper (scan images instead of generating with AI)",
        value=False,
        on_change=toggle_upload_mode,
    )

    # ────────────────────────────────────────────────────────────────────
    # GENERATE QUESTIONS (single button, branches by upload_checkbox)
    # ────────────────────────────────────────────────────────────────────

    async def generate_questions_async(e):
        nonlocal selected_image_files
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

        is_upload = upload_checkbox.value

        if is_upload:
            content = (upload_content_field.value or "").strip()
            if not content:
                show_snack("Scan or paste the question paper content before generating.", color=ft.Colors.RED_600)
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
                ft.Text("Processing...", weight=ft.FontWeight.BOLD),
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

            if is_upload:
                result = await asyncio.to_thread(
                    api_save_uploaded_questions,
                    class_dropdown.value,
                    subject_dropdown.value,
                    list(chapter_multiselect.value),
                    assessment_category_dropdown.value,
                    int(assessment_number_dropdown.value),
                    complexity_dropdown.value,
                    upload_content_field.value.strip(),
                    question_rows,
                    current_user,
                )
                success_verb = "Uploaded and extracted"
            else:
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
                success_verb = "Generated"

            if result.get("success"):
                num_questions = len(result.get("questions", []))
                version = result.get("version")
                version_note = f" (Version {version})" if version else ""
                show_snack(
                    f"✓ {success_verb} {num_questions} questions successfully!{version_note}",
                    color=ft.Colors.GREEN_700,
                )
                if is_upload:
                    upload_content_field.value = ""
                    selected_image_files = []
                    selected_files.value = "No images selected"
                await refresh_downloads()
                if version:
                    downloads_dropdown.value = f"Version {version}"
            else:
                error_msg = result.get("error", "Unknown error occurred.")
                show_snack(f"{'Upload' if is_upload else 'Generation'} failed: {error_msg}", color=ft.Colors.RED_600)

        except Exception as exc:
            show_snack(f"Error: {str(exc)}", color=ft.Colors.RED_600)

        finally:
            generate_button.disabled = False
            generate_button.content = ft.Text("GENERATE QUESTIONS", weight=ft.FontWeight.BOLD)
            page.update()

    def generate_questions(e):
        """Wrapper to run async function."""
        page.run_task(generate_questions_async, e)

    generate_button = ft.ElevatedButton(
        content=ft.Text("GENERATE QUESTIONS", weight=ft.FontWeight.BOLD),
        color=ft.Colors.WHITE,
        bgcolor="#3949AB",
        height=46,
        expand=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=23)),
        on_click=generate_questions,
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
            upload_checkbox,
            question_config_section,
            upload_section,
            ft.Container(
                content=generate_button,
                padding=ft.Padding(left=0, top=10, right=0, bottom=0),
            ),
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
