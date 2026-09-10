import flet as ft
from services.api_client import request_password_reset


def forgot_password_view(page: ft.Page):
    """Return the forgot password view controls."""

    username_field = ft.TextField(
        label="Email or Mobile Number",
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        border=ft.InputBorder.OUTLINE,
        border_radius=12,
        height=56,
        expand=True,
    )

    def show_snack(msg: str, color=ft.Colors.RED_600):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg, color=ft.Colors.WHITE),
            bgcolor=color,
        )
        page.snack_bar.open = True
        page.update()

    def do_reset(e):
        username = username_field.value.strip()
        if not username:
            show_snack("Please enter your email or mobile number.")
            return

        result = request_password_reset(username)
        if result["success"]:
            show_snack(
                "Reset instructions sent! Check your email / SMS.",
                color=ft.Colors.GREEN_700,
            )
            username_field.value = ""
            page.navigate("/login")
        else:
            show_snack(result["error"])

    def go_back(e):
        username_field.value = ""
        page.navigate("/login")

    # ── UI ───────────────────────────────────────────────────────────
    header = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            icon_color=ft.Colors.WHITE,
                            on_click=go_back,
                        ),
                    ],
                ),
                ft.Text(
                    "Forgot Password",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                ft.Text(
                    "We'll help you reset it",
                    size=14,
                    color=ft.Colors.with_opacity(0.88, ft.Colors.WHITE),
                ),
            ],
            spacing=6,
        ),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_CENTER,
            end=ft.Alignment.BOTTOM_CENTER,
            colors=["#3949AB", "#5C6BC0"],
        ),
        padding=ft.Padding(top=40, bottom=36, left=16, right=24),
        width=float("inf"),
    )

    card_content = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "Reset your password",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color="#1a237e",
                ),
                ft.Text(
                    "Enter the email or mobile number associated with your account "
                    "and we will send you a password reset link.",
                    size=13,
                    color=ft.Colors.GREY_600,
                ),
                ft.Container(height=8),
                username_field,
                ft.Container(height=12),
                ft.ElevatedButton(
                    content="SEND RESET LINK",
                    on_click=do_reset,
                    style=ft.ButtonStyle(
                        bgcolor={"": "#3949AB"},
                        color={"": ft.Colors.WHITE},
                        shape={"": ft.RoundedRectangleBorder(radius=12)},
                        elevation={"": 3},
                        text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD),
                    ),
                    height=50,
                    width=float("inf"),
                ),
                ft.OutlinedButton(
                    content="Back to Sign In",
                    on_click=go_back,
                    style=ft.ButtonStyle(
                        color={"": "#3949AB"},
                        shape={"": ft.RoundedRectangleBorder(radius=12)},
                    ),
                    height=48,
                    width=float("inf"),
                ),
            ],
            spacing=10,
        ),
        bgcolor=ft.Colors.WHITE,
        border_radius=ft.BorderRadius(top_left=32, top_right=32, bottom_left=0, bottom_right=0),
        padding=ft.Padding(left=28, right=28, top=32, bottom=32),
        expand=True,
    )

    return ft.Column(
        controls=[header, card_content],
        spacing=0,
        expand=True,
    )
