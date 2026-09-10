import flet as ft

"""Fixed header/footer shell used on every page except login/signup."""

_ACTIVE_COLOR = "#3949AB"
_INACTIVE_COLOR = ft.Colors.GREY_500


def build_drawer(page: ft.Page) -> ft.NavigationDrawer:
    """Shared navigation drawer opened from the header's menu icon."""
    current_user = page.session.store.get("current_user") or ""

    async def close_drawer(e=None):
        await page.close_drawer()

    async def go_setup_ebooks(e):
        await close_drawer()
        page.navigate("/academics/setup_ebooks")

    async def go_generate_questions(e):
        await close_drawer()
        page.navigate("/academics/generate_questions")

    async def drawer_logout(e):
        await close_drawer()
        page.session.store.remove("current_user")
        page.navigate("/login")

    drawer_header = ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.SCHOOL, size=48, color=ft.Colors.WHITE),
                ft.Text("EduKoreAI", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text(current_user, size=12, color=ft.Colors.with_opacity(0.80, ft.Colors.WHITE)),
            ],
            spacing=4,
        ),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=["#3949AB", "#5C6BC0"],
        ),
        padding=ft.Padding(left=20, top=40, bottom=24, right=20),
        width=float("inf")
    )

    return ft.NavigationDrawer(
        controls=[
            drawer_header,
            ft.Divider(height=1),
            ft.ExpansionTile(
                leading=ft.Icon(ft.Icons.DOCUMENT_SCANNER, color="#3949AB"),
                title=ft.Text("Academics"),
                controls=[
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.MENU_BOOK, color="#3949AB"),
                        title=ft.Text("Setup E-Books"),
                        on_click=go_setup_ebooks,
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.QUIZ, color="#3949AB"),
                        title=ft.Text("Generate Questions"),
                        on_click=go_generate_questions,
                    ),
                ],
            ),
            ft.Divider(height=1),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.RED_400),
                title=ft.Text("Logout"),
                on_click=drawer_logout,
            ),
        ],
    )


def build_header(page: ft.Page) -> ft.Container:
    """Top bar: menu icon (opens the drawer), search box, notification and account icons."""

    async def open_drawer(e):
        await page.show_drawer()

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.MENU, icon_color=ft.Colors.WHITE, on_click=open_drawer),
                ft.Container(
                    content=ft.TextField(
                        hint_text="Search",
                        hint_style=ft.TextStyle(color=ft.Colors.GREY_500, size=13),
                        prefix_icon=ft.Icons.SEARCH,
                        border=ft.InputBorder.NONE,
                        bgcolor=ft.Colors.TRANSPARENT,
                        content_padding=ft.Padding(left=8, top=2, right=8, bottom=0),
                        height=32,
                        text_size=13,
                    ),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                    height=32,
                    expand=True,
                ),
                ft.IconButton(icon=ft.Icons.NOTIFICATIONS_NONE, icon_color=ft.Colors.WHITE),
                ft.IconButton(icon=ft.Icons.ACCOUNT_CIRCLE, icon_color=ft.Colors.WHITE),
            ],
            spacing=4,
        ),
        bgcolor=_ACTIVE_COLOR,
        padding=ft.Padding(left=8, top=4, right=8, bottom=4),
        width=float("inf"),
    )


def _footer_item(icon: str, label: str, active: bool = False, on_click=None) -> ft.Container:
    color = _ACTIVE_COLOR if active else _INACTIVE_COLOR
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(icon, color=color, size=22),
                ft.Text(label, size=11, color=color),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2,
        ),
        on_click=on_click,
        expand=True,
    )


def build_footer(page: ft.Page) -> ft.Container:
    """Bottom bar: Home, Services, TBA1, TBA2 (Services/TBA1/TBA2 are placeholders, not wired yet)."""

    def go_home(e):
        page.navigate("/home")

    return ft.Container(
        content=ft.Row(
            controls=[
                _footer_item(ft.Icons.HOME, "Home", active=True, on_click=go_home),
                _footer_item(ft.Icons.MISCELLANEOUS_SERVICES, "Services"),
                _footer_item(ft.Icons.HELP_OUTLINE, "TBA1"),
                _footer_item(ft.Icons.HELP_OUTLINE, "TBA2"),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        ),
        bgcolor=ft.Colors.WHITE,
        border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_300)),
        padding=ft.Padding(left=8, top=6, right=8, bottom=6),
        width=float("inf"),
    )


def with_app_frame(content: ft.Control, page: ft.Page) -> ft.Column:
    """Wrap page content with the fixed header/footer and attach the shared drawer."""
    page.drawer = build_drawer(page)
    return ft.Column(
        controls=[
            build_header(page),
            ft.Container(content=content, expand=True),
            build_footer(page),
        ],
        spacing=0,
        expand=True,
    )
