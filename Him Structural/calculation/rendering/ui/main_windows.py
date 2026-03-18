import flet as ft

class MainWindow(ft.Column):
    def __init__(self):
        super().__init__(expand=True)

        self.controls = [
            ft.Row(
                expand=True,
                controls=[
                    ft.Container(
                        width=250,
                        bgcolor=ft.Colors.BLUE_GREY_100,
                        content=ft.Text("Panneau gauche"),
                    ),
                    ft.Container(
                        expand=True,
                        bgcolor=ft.Colors.WHITE,
                        content=ft.Text("Canvas 2D - Zone centrale"),
                    ),
                    ft.Container(
                        width=300,
                        bgcolor=ft.Colors.BLUE_GREY_100,
                        content=ft.Text("Panneau propriétés"),
                    ),
                ],
            )
        ]
