import flet as ft
import json
import urllib.request

def main(page: ft.Page):
    page.title = "Hilal KPSS"
    page.padding = 0
    page.spacing = 0
    page.theme_mode = ft.ThemeMode.LIGHT

    # --- Değişkenler ---
    URL = "https://raw.githubusercontent.com/krrr608-cpu/Hilal_kpss/refs/heads/main/sorular.json"
    veriler = []
    aktif_sorular = []
    mevcut_index = 0
    oturum_cevaplari = {}

    ana_liste = ft.ListView(expand=True, spacing=0, padding=ft.padding.only(top=40, bottom=20))
    page.add(ana_liste)

    # --- Hafıza Yönetimi (Doğru/Yanlış Takibi) ---
    def istatistik_getir(key):
        if page.client_storage.contains_key(key):
            return page.client_storage.get(key)
        return []

    def istatistik_ekle(key, soru_metni):
        liste = istatistik_getir(key)
        if soru_metni not in liste:
            liste.append(soru_metni)
            page.client_storage.set(key, liste)

    def verileri_cek():
        nonlocal veriler
        try:
            response = urllib.request.urlopen(URL, timeout=5)
            data = response.read().decode('utf-8')
            json_data = json.loads(data)
            veriler = json_data.get("kategoriler", [])
        except:
            veriler = []

    # --- ANA MENÜ ---
    def ana_menuyu_ciz():
        verileri_cek()
        ana_liste.controls.clear()
        
        cozulenler = istatistik_getir("cozulen_sorular")
        hatalar = istatistik_getir("hatali_sorular")

        # Üst Panel (İstatistikler)
        ana_liste.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("Hilal KPSS", size=28, weight="bold", color="white"),
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(str(len(cozulenler)), size=20, weight="bold", color="white"),
                                ft.Text("Çözülen", size=12, color="white70")
                            ], horizontal_alignment="center"),
                            expand=1
                        ),
                        ft.VerticalDivider(color="white24"),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(str(len(hatalar)), size=20, weight="bold", color="red100"),
                                ft.Text("Hatalı", size=12, color="white70")
                            ], horizontal_alignment="center"),
                            expand=1
                        ),
                    ], alignment="center")
                ]),
                bgcolor="indigo", padding=30, 
                border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30)
            )
        )

        # Kategoriler
        for kat in veriler:
            renk = kat.get("renk", "blue")
            ana_liste.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.PLAY_CIRCLE_FILL, color="white", size=30),
                        ft.Column([
                            ft.Text(kat["ad"], color="white", weight="bold", size=18),
                            ft.Text(f"{len(kat.get('sorular', []))} Soru", color="white70", size=12)
                        ], spacing=0)
                    ]),
                    bgcolor=renk, padding=20, margin=ft.margin.symmetric(horizontal=20, vertical=8),
                    border_radius=15, on_click=lambda e, s=kat.get("sorular", []), a=kat["ad"], r=renk: test_baslat(s, a, r),
                    ink=True
                )
            )
        
        # İstatistikleri Sıfırla Butonu (Opsiyonel)
        if len(cozulenler) > 0 or len(hatalar) > 0:
            ana_liste.controls.append(
                ft.TextButton("İstatistikleri Sıfırla", icon=ft.icons.DELETE_SWEEP, 
                              on_click=istatistikleri_resetle, style=ft.ButtonStyle(color="red"))
            )
            
        page.update()

    def istatistikleri_resetle(e):
        page.client_storage.remove("cozulen_sorular")
        page.client_storage.remove("hatali_sorular")
        ana_menuyu_ciz()

    # --- TEST EKRANI ---
    def test_baslat(soru_listesi, baslik, renk):
        nonlocal aktif_sorular, mevcut_index, oturum_cevaplari
        aktif_sorular = soru_listesi
        mevcut_index = 0
        oturum_cevaplari = {}
        test_ciz(baslik, renk)

    def test_ciz(baslik, renk):
        ana_liste.controls.clear()
        if not aktif_sorular: return
        
        soru = aktif_sorular[mevcut_index]
        
        # Üst Bar
        ana_liste.controls.append(ft.Container(
            content=ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK, icon_color="white", on_click=lambda _: ana_menuyu_ciz()),
                ft.Text(baslik, color="white", weight="bold"),
                ft.Text(f"{mevcut_index+1}/{len(aktif_sorular)}", color="white")
            ], alignment="spaceBetween"),
            bgcolor=renk, padding=10
        ))

        # Soru Kartı
        ana_liste.controls.append(ft.Container(
            content=ft.Text(soru["metin"], size=18, weight="w500"),
            padding=25, margin=15, bgcolor="white", border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color="black12")
        ))

        # Şıklar
        for secenek in soru["secenekler"]:
            is_answered = mevcut_index in oturum_cevaplari
            bg = "white"; brdr = ft.border.all(1, "grey300")
            
            if is_answered:
                if secenek == soru["cevap"]:
                    bg = ft.colors.GREEN_100; brdr = ft.border.all(2, "green")
                elif secenek == oturum_cevaplari[mevcut_index]:
                    bg = ft.colors.RED_100; brdr = ft.border.all(2, "red")

            def kontrol(e, s=secenek):
                if mevcut_index in oturum_cevaplari: return
                oturum_cevaplari[mevcut_index] = s
                
                # İstatistik Kaydı
                if s == soru["cevap"]:
                    istatistik_ekle("cozulen_sorular", soru["metin"])
                else:
                    istatistik_ekle("hatali_sorular", soru["metin"])
                
                test_ciz(baslik, renk)

            ana_liste.controls.append(ft.Container(
                content=ft.Text(secenek, size=16),
                padding=15, margin=ft.margin.symmetric(horizontal=25, vertical=5),
                bgcolor=bg, border=brdr, border_radius=12, on_click=kontrol
            ))

        # Navigasyon
        ana_liste.controls.append(ft.Row([
            ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=lambda _: nav(-1, baslik, renk), disabled=(mevcut_index==0), icon_size=40),
            ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=lambda _: nav(1, baslik, renk), disabled=(mevcut_index==len(aktif_sorular)-1), icon_size=40),
        ], alignment="center", spacing=60))
        page.update()

    def nav(yon, baslik, renk):
        nonlocal mevcut_index
        mevcut_index += yon
        test_ciz(baslik, renk)

    ana_menuyu_ciz()

ft.app(target=main)

