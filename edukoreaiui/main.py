import flet as ft
from screens.login_screen import login_view
from screens.signup_screen import signup_view
from screens.forgot_password_screen import forgot_password_view
from screens.home_screen import home_view
from screens.setup_ebooks_screen import setup_ebooks_view
from screens.generate_questions_screen import generate_questions_view
from components.app_frame import with_app_frame
from config.config import (
    APP_TITLE,
    THEME_COLOR,
    BACKGROUND_COLOR,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_RESIZABLE,
)

# 1. Main MUST be an async function to allow 'await' on startup
async def main(page: ft.Page):
    page.title = APP_TITLE
    page.theme = ft.Theme(color_scheme_seed=THEME_COLOR)
    page.bgcolor = BACKGROUND_COLOR
    page.padding = 0
    page.window.width = WINDOW_WIDTH
    page.window.height = WINDOW_HEIGHT
    page.window.resizable = WINDOW_RESIZABLE

    # 2. Handlers must stay standard synchronous functions
    def route_change(e: ft.RouteChangeEvent | None = None):
        page.views.clear()
        route = e.route if e is not None else page.route

        if not route or route == "/login" or route == "/":
            page.views.append(
                ft.View(
                    route="/login",
                    controls=[login_view(page)],
                    padding=0,
                    bgcolor=ft.Colors.WHITE,  
                )
            )
            page.appbar = None
            page.drawer = None

        elif route == "/signup":
            page.views.append(
                ft.View(
                    route="/signup",
                    controls=[signup_view(page)],
                    padding=0,
                    bgcolor=ft.Colors.WHITE,  
                )
            )
            page.appbar = None
            page.drawer = None

        elif route == "/forgot_password":
            page.views.append(
                ft.View(
                    route="/forgot_password",
                    controls=[with_app_frame(forgot_password_view(page), page)],
                    padding=0,
                    bgcolor=ft.Colors.WHITE,  
                )
            )
            page.appbar = None

        elif route == "/home":
            home_view_container = ft.View(
                route="/home",
                controls=[],
                padding=0,
                bgcolor=ft.Colors.GREY_50,  
            )
            page.views.append(home_view_container)
            # home_view no longer builds its own appbar/drawer; the shared frame supplies them
            home_content = home_view(page)
            page.appbar = None
            home_view_container.controls = [with_app_frame(home_content, page)]

        elif route == "/academics/setup_ebooks":
            setup_ebooks_container = ft.View(
                route="/academics/setup_ebooks",
                controls=[],
                padding=0,
                bgcolor=ft.Colors.GREY_50,
            )
            page.views.append(setup_ebooks_container)
            setup_ebooks_content = setup_ebooks_view(page)
            page.appbar = None

            setup_ebooks_container.controls = [with_app_frame(setup_ebooks_content, page)]

        elif route == "/academics/generate_questions":
            generate_questions_container = ft.View(
                route="/academics/generate_questions",
                controls=[],
                padding=0,
                bgcolor=ft.Colors.GREY_50,
            )
            page.views.append(generate_questions_container)
            generate_questions_content = generate_questions_view(page)
            page.appbar = None

            generate_questions_container.controls = [with_app_frame(generate_questions_content, page)]

        page.update()

    async def view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        top_view = page.views[-1]
        await page.push_route(top_view.route)

    # Attach event handlers
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    page.add(login_view(page))

if __name__ == "__main__":
    ft.run(main)
