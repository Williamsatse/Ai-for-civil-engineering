import flet as ft
from ui.main_windows import MainWindow

def main(page: ft.Page):
    page.title = "Him Foster - Logiciel de Calcul"
    page.window_width = 1200
    page.window_height = 800
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK

    page.add(
        ft.Text(
            "🚀 Bravo ! Flet fonctionne parfaitement !",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_800
        ),
        ft.Text("Tu es prêt à construire l'interface du logiciel.", size=18),
        ft.ElevatedButton("Clique-moi", on_click=lambda e: print("Bouton cliqué !"))
        )


ft.app(target=main)