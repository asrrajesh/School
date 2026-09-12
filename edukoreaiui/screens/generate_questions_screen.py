import asyncio
import flet as ft
from services.api_client import get_classes, get_chapters, get_subjects
from services.api_client import generate_questions as api_generate_questions

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

ASSESSMENT_NUMBERS = [
    ("1", "1"),
    ("2", "2"),
]

# Fixed column widths keep the header and every data row aligned as a table.
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
    """Return the Generate Questions screen matching the Scan E-Books layout/style."""

    def go_back(e):
        page.appbar = None
        page.navigate("/home")

    def show_snack(msg: str, color=ft.Colors.RED_600):
        page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor=color))

    # ── Cascading selectors (Class / Subject / Chapter) ─────────────────
    class SelectorState:
        def __init__(self, label, on_change=None):
            self.label = label
            self.options: list[str] = []
            self.value = None
            self._on_change = on_change
            self.chips = ft.Row(spacing=6, wrap=True, scroll=ft.ScrollMode.HIDDEN, expand=True)
            self.empty_message = ft.Text("", size=12, color=ft.Colors.GREY_500, italic=True, visible=False)
            self.field = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(controls=[ft.Text(label, size=12, weight=ft.FontWeight.BOLD)], height=18),
                        self.chips,
                        self.empty_message,
                    ],
                    spacing=4,
                ),
                border=ft.Border.all(1, ft.Colors.GREY_700),
                border_radius=6,
                padding=ft.Padding(left=8, top=5, right=8, bottom=6),
            )

        def set_options(self, options: list[str], empty_text: str = ""):
            self.options = options
            self.value = None
            self.empty_message.value = empty_text
            self.empty_message.visible = not options and bool(empty_text)
            self.refresh()

        def select(self, option):
            self.value = option
            self.refresh()
            if self._on_change:
                page.run_task(self._on_change)

        def refresh(self):
            self.chips.controls = [
                ft.Container(
                    content=ft.Text(
                        option,
                        size=12,
                        color=ft.Colors.WHITE if option == self.value else ft.Colors.GREY_900,
                    ),
                    bgcolor="#3949AB" if option == self.value else ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.GREY_500),
                    border_radius=14,
                    padding=ft.Padding(left=10, top=4, right=10, bottom=4),
                    on_click=lambda e, selected=option: self.select(selected),
                )
                for option in self.options
            ]

    async def on_class_selected():
        subject_selector.set_options([])
        chapter_selector.set_options([])
        update_rows_visibility()
        if class_selector.value:
            subjects = await asyncio.to_thread(get_subjects, class_selector.value)
            subject_selector.set_options(
                subjects, empty_text="No subjects found for this class. Scan e-books first."
            )
        page.update()

    async def on_subject_selected():
        chapter_selector.set_options([])
        update_rows_visibility()
        if class_selector.value and subject_selector.value:
            chapters = await asyncio.to_thread(get_chapters, class_selector.value, subject_selector.value)
            chapter_selector.set_options(
                chapters, empty_text="No chapters found for this subject. Scan e-books first."
            )
        page.update()

    async def on_chapter_selected():
        update_rows_visibility()
        page.update()

    class_selector = SelectorState("Class", on_change=on_class_selected)
    subject_selector = SelectorState("Subject", on_change=on_subject_selected)
    chapter_selector = SelectorState("Chapter", on_change=on_chapter_selected)

    async def on_assessment_selected():
        update_rows_visibility()
        page.update()

    assessment_category_selector = SelectorState("Assessment Category", on_change=on_assessment_selected)
    assessment_category_selector.set_options([label for _, label in ASSESSMENT_CATEGORIES])

    assessment_number_selector = SelectorState("Assessment Number", on_change=on_assessment_selected)
    assessment_number_selector.set_options([label for _, label in ASSESSMENT_NUMBERS])

    # ── Dynamic question rows ────────────────────────────────────────────
    rows: list[QuestionRow] = []
    rows_column = ft.Column(spacing=0, tight=True)
    ready_message = ft.Text(
        "Select class, subject, and chapter to configure questions.",
        color=ft.Colors.GREY_600,
        size=13,
    )
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
    # Single horizontally swipeable strip; ScrollMode.HIDDEN keeps the bar off-screen.
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
    rows_section = ft.Column(
        controls=[
            ft.Text("Question Configuration", size=16, weight=ft.FontWeight.BOLD, color="#1a237e"),
            table,
        ],
        spacing=12,
        visible=False,
    )

    def update_rows_visibility():
        ready = bool(
            class_selector.value
            and subject_selector.value
            and chapter_selector.value
            and assessment_category_selector.value
            and assessment_number_selector.value
        )
        rows_section.visible = ready
        ready_message.visible = not ready

    def used_types(exclude_row: QuestionRow | None = None) -> set:
        return {row.type_dropdown.value for row in rows if row is not exclude_row and row.type_dropdown.value}

    def refresh_dropdown_options():
        for row in rows:
            taken = used_types(exclude_row=row)
            row.type_dropdown.options = [
                ft.DropdownOption(key=key, text=text, disabled=key in taken) for key, text in QUESTION_TYPES
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
            class_selector.value
            and subject_selector.value
            and chapter_selector.value
            and assessment_category_selector.value
            and assessment_number_selector.value
        ):
            show_snack("Select class, subject, chapter, and assessment.")
            return
        if not rows:
            show_snack("Add at least one question row.")
            return
        for row in rows:
            error = row.validate()
            if error:
                show_snack(error)
                return

        # Get current user from session
        current_user = page.session.store.get("current_user") or "unknown"

        # Convert selector chip labels back to their short codes for the API
        assessment_category_code = next(
            code for code, label in ASSESSMENT_CATEGORIES if label == assessment_category_selector.value
        )
        assessment_number_code = int(
            next(code for code, label in ASSESSMENT_NUMBERS if label == assessment_number_selector.value)
        )

        # Show loading indicator
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
            # Prepare question rows data
            question_rows = [
                {
                    "questionType": row.type_dropdown.value,
                    "questionCount": int(row.count_field.value),
                    "marksPerQuestion": float(row.marks_field.value),
                }
                for row in rows
            ]

            # Call API to generate questions
            result = await asyncio.to_thread(
                api_generate_questions,
                class_selector.value,
                subject_selector.value,
                chapter_selector.value,
                assessment_category_code,
                assessment_number_code,
                question_rows,
                current_user,
            )

            if result.get("success"):
                num_questions = len(result.get("questions", []))
                show_snack(
                    f"✓ Generated {num_questions} questions successfully!",
                    color=ft.Colors.GREEN_700,
                )
            else:
                error_msg = result.get("error", "Unknown error occurred.")
                show_snack(f"Generation failed: {error_msg}", color=ft.Colors.RED_600)

        except Exception as exc:
            show_snack(f"Error: {str(exc)}", color=ft.Colors.RED_600)

        finally:
            # Reset button
            generate_button.disabled = False
            generate_button.content = ft.Text("GENERATE QUESTIONS", weight=ft.FontWeight.BOLD)
            page.update()

    def generate_questions(e):
        """Wrapper to run async function."""
        page.run_task(generate_questions_async, e)

    add_row()

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

    # Create button as a variable so we can update it during loading
    generate_button = ft.ElevatedButton(
        content=ft.Text("GENERATE QUESTIONS", weight=ft.FontWeight.BOLD),
        color=ft.Colors.WHITE,
        bgcolor="#3949AB",
        height=46,
        expand=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=23)),
        on_click=generate_questions,
    )

    form_layout = ft.Column(
        scroll=ft.ScrollMode.HIDDEN,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=16,
        controls=[
            ft.Text("Generate Questions", size=24, weight=ft.FontWeight.BOLD, color="#1a237e"),
            ft.Text(
                "Choose the class, subject, and chapter to configure the question paper.",
                color=ft.Colors.GREY_600,
                size=14,
            ),
            class_selector.field,
            subject_selector.field,
            chapter_selector.field,
            assessment_category_selector.field,
            assessment_number_selector.field,
            ready_message,
            rows_section,
            ft.Container(
                content=generate_button,
                width=page.width - 40,
                padding=ft.Padding(left=0, top=10, right=0, bottom=20),
            ),
        ],
    )

    async def load_classes():
        classes = await asyncio.to_thread(get_classes)
        class_selector.set_options(
            classes, empty_text="No class data found. Scan e-books first to add data."
        )
        page.update()

    page.run_task(load_classes)

    return ft.Container(
        content=form_layout,
        padding=ft.Padding(left=20, top=20, right=20, bottom=20),
        expand=True,
    )
