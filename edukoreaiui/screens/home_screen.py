import flet as ft


def home_view(page: ft.Page):
    """Return the home view controls. Header/drawer/footer come from components.app_frame."""

    # ── Body ──────────────────────────────────────────────────────────
    body = ft.Column(
        controls=[
            ft.Container(expand=True),
            ft.Column(
                controls=[
                    ft.Icon(ft.Icons.WAVING_HAND, size=64, color="#3949AB"),
                    ft.Text(
                        f"Welcome!",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color="#1a237e",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Tap  ☰  to open the menu and navigate.",
                        size=14,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            ft.Container(expand=True),
        ],
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return ft.Container(
        content=body,
        expand=True,
        bgcolor=ft.Colors.GREY_50,
    )
