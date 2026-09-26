import flet as ft

from services.api_client import get_menus, get_user

_MAX_ROWS = 3

# Design tokens matching Design1.html
_APP_BG = "#F7F4EF"
_PRIMARY_TEAL = "#116A54"
_ACCENT_BEIGE = "#EEDAA2"
_TEXT_MAIN = "#1C1E1D"
_TEXT_MUTED = "#626A65"
_BORDER_UI = "#2D312E"
_RADIUS_UI = 12


def _feature_row(title: str, subtitle: str, is_last: bool = False, icon: bool = True) -> ft.Container:
    icon_box = (
        [
            ft.Container(
                width=40,
                height=40,
                bgcolor=_APP_BG,
                border=ft.Border.all(1, _BORDER_UI),
                border_radius=8,
            )
        ]
        if icon
        else []
    )
    return ft.Container(
        content=ft.Row(
            controls=[
                *icon_box,
                ft.Column(
                    controls=[
                        ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=_TEXT_MAIN),
                        ft.Text(subtitle, size=12, color=_TEXT_MUTED),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(left=0, top=12, right=0, bottom=0 if is_last else 12),
        border=None if is_last else ft.Border(bottom=ft.BorderSide(1, "#F0ECE6")),
    )


def _info_panel(header: str, controls: list, trailing: str | None = None) -> ft.Container:
    header_row_controls = [
        ft.Text(
            header,
            size=12,
            weight=ft.FontWeight.W_800,
            color=_TEXT_MUTED,
        )
    ]
    if trailing:
        header_row_controls.append(
            ft.Text(trailing, size=12, weight=ft.FontWeight.BOLD, color=_PRIMARY_TEAL)
        )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=header_row_controls,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                *controls,
            ],
            spacing=0,
        ),
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, _BORDER_UI),
        border_radius=_RADIUS_UI,
        padding=16,
    )


def home_view(page: ft.Page):
    """Return the home view controls. Header/drawer/footer come from components.app_frame."""

    user_id = page.session.store.get("current_user") or ""
    contact = ""
    if user_id:
        result = get_user(user_id)
        if result.get("success"):
            user = result["user"]
            contact = user.get("name") or user.get("mobile") or user.get("email") or ""

    hero_column_controls = ""
    if contact:
        hero_column_controls = ft.Text(
            f"Hi {contact},",
            size=13,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
        )

    guest_hero = ft.Container(
        content=ft.Column(
            controls=[
                hero_column_controls,
                ft.Text(
                    "Welcome to EduKoreAI. Discover our values, academic tracking tools, "
                    "and direct administrative modules.",
                    size=13,
                    color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
                ),
            ],
            spacing=6,
            width=float("inf"),
        ),
        bgcolor=_PRIMARY_TEAL,
        padding=ft.Padding(left=20, top=24, right=20, bottom=24),
        border_radius=_RADIUS_UI,
    )

    upgrade_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Received an Invite Code?", size=15, weight=ft.FontWeight.BOLD, color=_TEXT_MAIN),
                        ft.Text(
                            "If you are a Principal, Teacher, Student, or Parent, input your "
                            "institutional activation token to access your specialized portal.",
                            size=12,
                            color=_TEXT_MUTED,
                        ),
                    ],
                    spacing=4,
                ),
                ft.Container(
                    content=ft.Text(
                        "Enter Activation Code",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.WHITE,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    bgcolor=_PRIMARY_TEAL,
                    border=ft.Border.all(1, _BORDER_UI),
                    border_radius=8,
                    padding=12,
                    alignment=ft.Alignment.CENTER,
                    width=float("inf"),
                ),
            ],
            spacing=12,
        ),
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, _PRIMARY_TEAL),
        border_radius=_RADIUS_UI,
        padding=20,
    )

    menu_panels = []
    for panel in get_menus():
        items = sorted(panel.get("items", []), key=lambda i: i.get("order", 0))
        visible = items[:_MAX_ROWS]
        rows = [
            _feature_row(
                item.get("title", ""),
                item.get("description", ""),
                is_last=(idx == len(visible) - 1),
                icon=bool(item.get("icon", False)),
            )
            for idx, item in enumerate(visible)
        ]
        menu_panels.append(
            _info_panel(
                panel.get("panel", ""),
                rows,
                trailing="View All",
            )
        )

    body = ft.Column(
        controls=[
            guest_hero,
            upgrade_card,
            *menu_panels,
        ],
        spacing=20,
        scroll=ft.ScrollMode.HIDDEN,
        expand=True,
    )

    return ft.Container(
        content=body,
        expand=True,
        bgcolor=_APP_BG
    )
