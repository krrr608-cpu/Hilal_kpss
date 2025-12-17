import flet as ft

def main(page: ft.Page):
    # Sayfa ayarları
    page.title = "Test Uygulaması"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.colors.BLUE_GREY_100

    # Basit bir yazı ve ikon
    yazi = ft.Text("MERHABA!", size=40, color="blue", weight="bold")
    alt_yazi = ft.Text("Eğer bunu görüyorsan sorun çözüldü.", size=20)
    ikon = ft.Icon(name=ft.icons.CHECK_CIRCLE, size=50, color="green")

    page.add(ikon, yazi, alt_yazi)

ft.app(target=main)
