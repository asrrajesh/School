from turtle import color

import flet as ft
from services.api_client import login_user


def login_view(page: ft.Page):
    """Return the login view with modern design matching the target image."""

    # ── State ────────────────────────────────────────────────────────
    username_field = ft.TextField(
        label="Email or Mobile Number",
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        border=ft.InputBorder.OUTLINE,
        border_radius=8,
        height=48,
        bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.BLACK),
        text_size=13,
        expand=True
    )
    
    password_field = ft.TextField(
        label="Password",
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        password=True,
        can_reveal_password=True,
        border=ft.InputBorder.OUTLINE,
        border_radius=8,
        height=48,
        bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.BLACK),
        text_size=13,
        expand=True
    )

    def show_snack(msg: str, color=ft.Colors.RED_600):
        """Show feedback message to user."""
        page.show_dialog(ft.SnackBar(
            content=ft.Text(msg, color=ft.Colors.WHITE, size=13),
            bgcolor=color,
        ))

    def do_login(e):
        """Handle sign in."""
        username = username_field.value.strip()
        password = password_field.value
        if not username:
            show_snack("Please enter your email or mobile number.")
            return
        if not password:
            show_snack("Please enter your password.")
            return

        result = login_user(username, password)
        if result["success"]:
            page.session.store.set("current_user", result["user"]["username"])
            username_field.value = ""
            password_field.value = ""
            page.navigate("/home")
        else:
            show_snack(result["error"])

    def go_forgot(e):
        """Navigate to forgot password."""
        page.navigate("/forgot_password")

    def go_signup(e):
        """Navigate to signup screen."""
        page.navigate("/signup")

    def do_guest_login(e):
        """Login as guest."""
        page.session.store.set("current_user", "Guest")
        page.navigate("/home")

    # ── Main Content Layout ──────────────────────────────────────────
    logo = ft.Image(
        src="resources/edukoreai-logo.jpg",
        width=50,
        height=50,
        border_radius=10
    )

    branding = ft.Text(
        "EduKoreAI",
        size=26,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLACK,
        font_family="Cambria Regular"
    )

    tagline = ft.Text(
        "L E A R N .  G R O W .  S U C C E E D .",
        size=9,
        weight=ft.FontWeight.W_600,
        color="#146C5A",
        font_family="Cambria Regular"
    )

    # Subheading
    subheading = ft.Text(
        "Sign in to your EduKoreAI dashboard",
        size=13,
        color=ft.Colors.GREY_600,
        font_family="Cambria Regular"
    )

    forgot_link = ft.Text(
        "Forgot password?",
        size=12,
        color="#146C5A",
        weight=ft.FontWeight.W_500,
        font_family="Cambria Regular"
    )

    # Sign In Button
    signin_button = ft.ElevatedButton(
        "Sign In",
        height=48,
        width=float("inf"),
        style=ft.ButtonStyle(
            bgcolor="#146C5A",
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        on_click=do_login,
    )

    # Divider
    divider_text = ft.Row(
        controls=[
            ft.Container(
                expand=True,
                height=1,
                bgcolor=ft.Colors.GREY_400,
            ),
            ft.Text(
                "or continue with",
                size=12,
                color=ft.Colors.GREY_500,
            ),
            ft.Container(
                expand=True,
                height=1,
                bgcolor=ft.Colors.GREY_400,
            ),
        ]
    )

    # Social Login Buttons
    google_button = ft.OutlinedButton(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.LANGUAGE, size=18, color="#3949AB"),
                ft.Text("Google", size=12, weight=ft.FontWeight.W_500),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        height=44,
        expand=True,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            side=ft.BorderSide(1, ft.Colors.GREY_300),
        ),
    )

    apple_button = ft.OutlinedButton(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.APPLE, size=18, color="#000000"),
                ft.Text("Apple", size=12, weight=ft.FontWeight.W_500),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        height=44,
        expand=True,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            side=ft.BorderSide(1, ft.Colors.GREY_300),
        ),
    )

    social_buttons = ft.Row(
        controls=[google_button, apple_button],
        spacing=12,
    )

    # Signup Link
    signup_link = ft.Row(
        controls=[
            ft.Text("New to EduKoreAI? ", size=12, color=ft.Colors.GREY_600),
            ft.TextButton(
                "Create an account",
                on_click=go_signup,
                style=ft.ButtonStyle(
                    color="#146C5A",
                    padding=0,
                ),
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0,
        wrap=True,
        width=float("inf"),
    )

    # Assemble Card Content
    card_content = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(height=50),
                ft.Container(
                    content=logo,
                    alignment=ft.Alignment.CENTER,
                    height=60,
                ),
                ft.Container(
                    content=branding,
                    alignment=ft.Alignment.CENTER,
                    height=40,
                ),
                ft.Container(
                    content=tagline,
                    alignment=ft.Alignment.CENTER,
                    height=20,
                ),
                ft.Container(
                    content=subheading,
                    alignment=ft.Alignment(0, 1), # center horizontally, bottom vertically
                    height=75,
                ),
                ft.Container(
                    content=username_field,
                    alignment=ft.Alignment.CENTER,
                    height=60,
                ),
                ft.Container(
                    content=password_field,
                    alignment=ft.Alignment.CENTER,
                    height=60,
                ),
                ft.Container(
                    content=forgot_link,
                    alignment=ft.Alignment(1, -1), # right horizontally, top vertically
                    on_click=go_forgot,
                    height=30,
                ),
                ft.Container(
                    content=signin_button,
                ),
                ft.Container(
                    content=divider_text,
                    height=80,
                ),
                ft.Container(
                    content=social_buttons
                ),
                ft.Container(
                    content=signup_link,
                    height=80,
                    alignment=ft.Alignment(0, 0),
                ),
            ],
            spacing=0,
            scroll=ft.ScrollMode.HIDDEN,
            expand=True,
        ),
        padding=ft.Padding(left=24, right=24, top=24, bottom=24),
        bgcolor="#F2EFE8",
        expand=True,
    )

    return ft.Container(
        content=ft.Column(
            controls=[card_content],
            spacing=0,
            expand=True,
        ),
        expand=True,
        bgcolor="#F2EFE8",
    )