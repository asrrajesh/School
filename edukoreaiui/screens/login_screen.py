import flet as ft
from services.api_client import login_user


def login_view(page: ft.Page):
    """Return the login view controls."""

    # ── State ────────────────────────────────────────────────────────
    username_field = ft.TextField(
        label="Email or Mobile Number",
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        border=ft.InputBorder.OUTLINE,
        border_radius=12,
        height=56,
    )
    password_field = ft.TextField(
        label="Password",
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        password=True,
        can_reveal_password=True,
        border=ft.InputBorder.OUTLINE,
        border_radius=12,
        height=56,
    )

    # FIXED: Clean synchronous helper function
    def show_snack(msg: str, color=ft.Colors.RED_600):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg, color=ft.Colors.WHITE),
            bgcolor=color,
        )
        page.snack_bar.open = True
        page.update()  # FIXED: Removed 'await'

    # FIXED: Clean synchronous event handler
    def do_login(e):
        username = username_field.value.strip()
        password = password_field.value
        if not username:
            show_snack("Please enter your email or mobile number.")  # FIXED: Removed 'await'
            return
        if not password:
            show_snack("Please enter your password.")  # FIXED: Removed 'await'
            return

        result = login_user(username, password)
        if result["success"]:
            page.session.store.set("current_user", result["user"]["username"])
            username_field.value = ""
            password_field.value = ""
            page.navigate("/home")
        else:
            show_snack(result["error"])  # FIXED: Removed 'await'

    # FIXED: Clean synchronous event handler
    def go_forgot(e):
        page.navigate("/forgot_password")

    # FIXED: Clean synchronous event handler
    def go_signup(e):
        page.navigate("/signup")

    def do_guest_login(e):
        page.session.store.set("current_user", "Guest")
        page.navigate("/home")

    # ── UI ───────────────────────────────────────────────────────────
    header = ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.SCHOOL, size=56, color=ft.Colors.WHITE),
                ft.Text(
                    "EduKoreAI",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE, 
                ),
                ft.Text(
                    "Learn. Grow. Succeed.",
                    size=15,
                    color=ft.Colors.WHITE, 
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        ),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_CENTER,
            end=ft.Alignment.BOTTOM_CENTER,
            colors=["#3949AB", "#5C6BC0"],
        ),
        padding=ft.Padding(top=52, bottom=36, left=24, right=24),
        width=float("inf"),
    )

    card_content = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Welcome Back", size=22, weight=ft.FontWeight.BOLD, color="#1a237e"),
                ft.Row(
                    controls=[
                        ft.Text("Sign in to continue", size=13, color=ft.Colors.GREY_600),
                        ft.Text("/", size=13, color=ft.Colors.GREY_600),
                        ft.TextButton(
                            "Continue as Guest",
                            on_click=do_guest_login,
                            style=ft.ButtonStyle(color={"": "#3949AB"}, padding=0),
                        ),
                    ],
                    spacing=4,
                ),
                ft.Container(height=8),
                username_field,
                ft.Container(height=4),
                password_field,
                ft.Container(height=8),
                ft.ElevatedButton(
                    "LOGIN", 
                    on_click=do_login,
                    style=ft.ButtonStyle(
                        bgcolor={"": "#3949AB"},
                        color={"": ft.Colors.WHITE}, 
                        shape={"": ft.RoundedRectangleBorder(radius=12)},
                        elevation={"": 3},
                        text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD),
                    ),
                    height=50,
                ),
                ft.TextButton(
                    "Forgot Password?", 
                    on_click=go_forgot,
                    style=ft.ButtonStyle(color={"": "#3949AB"}),
                ),
                ft.Row(
                    controls=[
                        ft.Text("Don't have an account?", size=13, color=ft.Colors.GREY_600), 
                        ft.TextButton(
                            "Sign Up", 
                            on_click=go_signup,
                            style=ft.ButtonStyle(color={"": "#3949AB"}),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0,
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
