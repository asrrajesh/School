import asyncio
import flet as ft
from services.api_client import get_scanned_chapter, save_scanned_chapter, scan_images


def setup_ebooks_view(page: ft.Page):
    """Return the Setup E-Books scan/review form as a single page."""
    selected_files = ft.Text("No images selected", color=ft.Colors.GREY_600, size=12)
    selected_image_files = []

    content_field = ft.TextField(
        label="Chapter Content",
        multiline=True,
        expand=True,
        min_lines=4,          # Set higher baseline lines so it looks solid upfront
        max_lines=None,
        text_size=13,
        value="",
    )

    def go_back(e):
        page.appbar = None
        page.drawer = None
        page.navigate("/home")

    async def load_existing_content(e=None):
        # Fetch and display saved content when class/subject/chapter are all selected.
        if class_dropdown.value and subject_dropdown.value and chapter_dropdown.value:
            record = await asyncio.to_thread(
                get_scanned_chapter,
                class_dropdown.value,
                subject_dropdown.value,
                chapter_dropdown.value,
            )
            content_field.value = record["content"] if record else ""
            page.update()

    class SelectorState:
        def __init__(self, label, options):
            self.label = label
            self.options = options
            self.value = None
            self.chips = ft.Row(spacing=6, scroll=ft.ScrollMode.HIDDEN, expand=True)
            self.field = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(label, size=12, weight=ft.FontWeight.BOLD),
                            ],
                            height=18,
                        ),
                        self.chips,
                    ],
                    spacing=4,
                ),
                border=ft.Border.all(1, ft.Colors.GREY_700),
                border_radius=6,
                padding=ft.Padding(left=8, top=5, right=8, bottom=6),
                height=62,
            )
            self.refresh()

        def select(self, option):
            self.value = option
            self.refresh()
            page.run_task(load_existing_content)

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

    class_dropdown_state = SelectorState(
        "Class", ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    )
    subject_dropdown_state = SelectorState(
        "Subject", ["Science", "English", "Computer Science", "Mathematics"]
    )
    chapter_dropdown_state = SelectorState(
        "Chapter", [str(chapter) for chapter in range(1, 51)]
    )
    class_dropdown = class_dropdown_state
    subject_dropdown = subject_dropdown_state
    chapter_dropdown = chapter_dropdown_state

    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    async def choose_images(e):
        nonlocal selected_image_files
        files = await file_picker.pick_files(
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

    async def scan_chapters(e):
        if not class_dropdown.value or not subject_dropdown.value or not chapter_dropdown.value:
            page.show_dialog(ft.SnackBar(content=ft.Text("Select class, subject, and chapter."), bgcolor=ft.Colors.RED_600))
            return
        if not selected_image_files:
            page.show_dialog(ft.SnackBar(content=ft.Text("Attach at least one image."), bgcolor=ft.Colors.RED_600))
            return

        page.show_dialog(ft.SnackBar(content=ft.Text("Scanning images. This may take a moment."), bgcolor=ft.Colors.BLUE_700))
        try:
            content = await asyncio.to_thread(scan_images, selected_image_files)
        except Exception as exc:
            page.show_dialog(ft.SnackBar(content=ft.Text(f"Scan failed: {exc}"), bgcolor=ft.Colors.RED_600))
            return

        content_field.value = content
        page.update()

    async def submit_content(e):
        if not class_dropdown.value or not subject_dropdown.value or not chapter_dropdown.value:
            page.show_dialog(ft.SnackBar(content=ft.Text("Select class, subject, and chapter."), bgcolor=ft.Colors.RED_600))
            return
        content = (content_field.value or "").strip()
        if not content:
            page.show_dialog(ft.SnackBar(content=ft.Text("Add chapter content before submitting."), bgcolor=ft.Colors.RED_600))
            return

        page.show_dialog(ft.SnackBar(content=ft.Text("Saving chapter content..."), bgcolor=ft.Colors.BLUE_700))
        username = page.session.store.get("current_user") or ""
        result = await asyncio.to_thread(
            save_scanned_chapter,
            class_dropdown.value,
            subject_dropdown.value,
            chapter_dropdown.value,
            content,
            username,
        )
        if result["success"]:
            page.show_dialog(ft.SnackBar(content=ft.Text("Chapter content saved."), bgcolor=ft.Colors.GREEN_700))
            page.navigate("/home")
        else:
            page.show_dialog(ft.SnackBar(content=ft.Text(result["error"]), bgcolor=ft.Colors.RED_600))

    page.appbar = ft.AppBar(
        leading=ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_color=ft.Colors.WHITE,
            on_click=go_back,
        ),
        title=ft.Text("Setup E-Books", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor="#3949AB",
    )
    page.drawer = None

    field_row_height = 36

    # Balanced form layout matching clean production styling constraints
    form_layout = ft.Column(
        scroll=ft.ScrollMode.HIDDEN,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=16,
        controls=[
            ft.Text("Scan E-Books pages", size=24, weight=ft.FontWeight.BOLD, color="#1a237e"),
            ft.Text("Choose the class, subject, chapter, and images to scan.", color=ft.Colors.GREY_600, size=14),
            
            # Dropdowns stacked cleanly into a clear column block
            class_dropdown.field,
            subject_dropdown.field,
            chapter_dropdown.field,
            
            # Operational execution actions
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
                        height=field_row_height,
                        style=ft.ButtonStyle(
                            padding=ft.Padding(left=12, top=0, right=12, bottom=0),
                        ),
                    ),
                    ft.ElevatedButton(
                        content=ft.Text("SCAN", size=13),
                        on_click=scan_chapters,
                        style=ft.ButtonStyle(
                            bgcolor={"": "#3949AB"},
                            color={"": ft.Colors.WHITE},
                            padding=ft.Padding(left=20, top=0, right=20, bottom=0),
                        ),
                        height=field_row_height,
                    ),
                ],
                spacing=12,
            ),
            selected_files,
            content_field,
            
            # Submission UI element positioning anchors
            ft.Container(
                content=ft.ElevatedButton(
                    content=ft.Text("SUBMIT", weight=ft.FontWeight.BOLD),
                    color=ft.Colors.WHITE,
                    bgcolor="#3949AB",
                    height=46,
                    expand=True,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=23),
                    ),
                    on_click=submit_content,
                ),
                width=page.width - 40,
                padding=ft.Padding(left=0, top=10, right=0, bottom=20),
            )
        ]
    )

    return ft.Container(
        content=form_layout,
        padding=ft.Padding(left=20, top=20, right=20, bottom=20),
        expand=True
    )