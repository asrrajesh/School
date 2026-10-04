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

    def make_dropdown(label, options):
        # Same style as the Class dropdown on the Generate Questions screen.
        return ft.Dropdown(
            hint_text=f"Select {label}",
            label=label,
            dense=True,
            expand=True,
            options=[ft.dropdown.Option(option) for option in options],
            on_select=lambda e: page.run_task(load_existing_content),
        )

    class_dropdown = make_dropdown(
        "Class", ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    )
    subject_dropdown = make_dropdown(
        "Subject", ["Science", "English", "Computer Science", "Mathematics"]
    )
    chapter_dropdown = make_dropdown(
        "Chapter", [str(chapter) for chapter in range(1, 51)]
    )

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
            ft.Row([class_dropdown]),
            ft.Row([subject_dropdown]),
            ft.Row([chapter_dropdown]),
            
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