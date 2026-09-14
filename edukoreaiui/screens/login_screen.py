import flet as ft
from services.api_client import login_user


def login_view(page: ft.Page):
    """Return the login view with modern design matching the target image."""

    # ── State ────────────────────────────────────────────────────────
    username_field = ft.TextField(
        label="Username or Email",
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        border=ft.InputBorder.OUTLINE,
        border_radius=8,
        height=48,
        bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.BLACK),
        text_size=13,
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

    # ── Tab Button Helper ────────────────────────────────────────────
    def _tab_button(label: str, is_active: bool, on_click):
        """Create a tab button with underline indicator."""
        return ft.Container(
            content=ft.Text(
                label,
                size=15,
                weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL,
                color="#3949AB" if is_active else ft.Colors.GREY_600,
            ),
            on_click=on_click,
            border=ft.Border(
                bottom=ft.BorderSide(2, "#3949AB") if is_active else None,
            ),
            padding=ft.Padding(bottom=8),
        )

    # ── Main Content Layout ──────────────────────────────────────────
    
    # Header: Logo + Branding
    header = ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Icon(ft.Icons.SCHOOL, size=25, color=ft.Colors.WHITE),
                    bgcolor="#3949AB",
                    border_radius=10,
                    width=30,
                    height=30,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Text(
                    "EduKoreAI",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                    color="#1a237e",
                ),
                ft.Text(
                    "L E A R N .  G R O W .  S U C C E E D .",
                    size=9,
                    weight=ft.FontWeight.W_600,
                    color="#3949AB",
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        padding=ft.Padding(top=20, bottom=24),
    )

    # Heading
    heading = ft.Text(
        "Welcome back",
        size=24,
        weight=ft.FontWeight.BOLD,
        color="#1a237e",
    )

    # Subheading
    subheading = ft.Text(
        "Sign in to your EduKoreAI dashboard",
        size=13,
        color=ft.Colors.GREY_600,
    )

    # Tab Switcher
    tab_row = ft.Row(
        controls=[
            _tab_button("Sign In", True, None),
            _tab_button("Sign Up", False, go_signup),
        ],
        spacing=32,
        alignment=ft.MainAxisAlignment.START,
        height=40,
    )

    # Input Fields
    input_section = ft.Column(
        controls=[
            ft.Text("USERNAME OR EMAIL", size=11, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            ft.Container(height=6),
            username_field,
            ft.Container(height=16),
            ft.Text("PASSWORD", size=11, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            ft.Container(height=6),
            password_field,
        ],
        spacing=0,
    )

    # Forgot Password Link
    forgot_link = ft.Container(
        content=ft.Text(
            "Forgot password?",
            size=12,
            color="#3949AB",
            weight=ft.FontWeight.W_500,
        ),
        on_click=go_forgot,
        padding=ft.Padding(top=12, bottom=0),
    )

    # Sign In Button
    signin_button = ft.ElevatedButton(
        "Sign In",
        bgcolor="#3949AB",
        color=ft.Colors.WHITE,
        height=48,
        width=float("inf"),
        style=ft.ButtonStyle(
            bgcolor={"": "#3949AB"},
            color={"": ft.Colors.WHITE},
            shape={"": ft.RoundedRectangleBorder(radius=12)},
            elevation={"": 2},
        ),
        on_click=do_login,
    )

    # Divider
    divider_text = ft.Text(
        "or continue with",
        size=12,
        color=ft.Colors.GREY_500,
        text_align=ft.TextAlign.CENTER,
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
            shape={"": ft.RoundedRectangleBorder(radius=8)},
            side={"": ft.BorderSide(1, ft.Colors.GREY_300)},
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
            shape={"": ft.RoundedRectangleBorder(radius=8)},
            side={"": ft.BorderSide(1, ft.Colors.GREY_300)},
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
                    color={"": "#3949AB"},
                    padding=0,
                ),
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0,
        wrap=True,
    )

    # Guest Login Option
    guest_option = ft.TextButton(
        "or continue as Guest",
        on_click=do_guest_login,
        style=ft.ButtonStyle(
            color={"": ft.Colors.GREY_600},
            padding=0,
        ),
    )

    # Assemble Card Content
    card_content = ft.Container(
        content=ft.Column(
            controls=[
                header,
                ft.Container(height=8),
                heading,
                subheading,
                ft.Container(height=20),
                tab_row,
                ft.Container(height=24),
                input_section,
                ft.Container(height=4),
                ft.Row(
                    controls=[ft.Container(expand=True), forgot_link],
                    alignment=ft.MainAxisAlignment.END,
                ),
                ft.Container(height=20),
                signin_button,
                ft.Container(height=20),
                divider_text,
                ft.Container(height=16),
                social_buttons,
                ft.Container(height=20),
                signup_link,
                ft.Container(height=8),
                ft.Container(
                    content=guest_option,
                    alignment=ft.Alignment.CENTER,
                ),
            ],
            spacing=0,
            scroll=ft.ScrollMode.HIDDEN,
            expand=True,
        ),
        padding=ft.Padding(left=24, right=24, top=24, bottom=24),
        bgcolor=ft.Colors.WHITE,
        expand=True,
    )

    return ft.Container(
        content=ft.Column(
            controls=[card_content],
            spacing=0,
            expand=True,
        ),
        expand=True,
        bgcolor="#F8F9FA",  # Now it works!
    )