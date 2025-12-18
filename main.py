import flet as ft
import json
import urllib.request
import threading

def main(page: ft.Page):
    page.title = "Hilal KPSS"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Ana Liste (Scrollable)
    ana_liste = ft.ListView(expand=True, spacing=0, padding=ft.padding.only(top=40, bottom=20))
    loading_screen = ft.Container(
        content=ft.Column([
            ft.ProgressRing(),
            ft.Text("Veriler Yükleniyor...", color="indigo")
        ], horizontal_alignment="center"),
        alignment=ft.alignment.center,
        expand=True
    )
    page.add(loading_screen)

    # Global Değişkenler
    URL = "https://raw.githubusercontent.com/krrr608-cpu/Hilal_kpss/refs/heads/main/sorular.json"
    veriler = []
    aktif_sorular = []
    mevcut_index = 0
    oturum_cevaplari = {}

    def get_storage(key):
        return page.client_storage.get(key) if page.client_storage.contains_key(key) else []

    def save_storage(key, data):
        page.client_storage.set(key, data)

    def verileri_cek():
        nonlocal veriler
        try:
            # Zaman aşımını 10 saniyeye çıkardık
            response = urllib.request.urlopen(URL, timeout=10)
            data = response.read().decode('utf-8')
            json_data = json.loads(data)
            veriler = json_data.get("kategoriler", [])
            page.client_storage.set("kpss_cache", data)
        except Exception as e:
            print(f"Hata: {e}")
            if page.client_storage.contains_key("kpss_cache"):
                json_data = json.loads(page.client_storage.get("kpss_cache"))
                veriler = json_data.get("kategoriler", [])
        
        # Yükleme ekranını kaldır ve ana menüyü çiz
        page.controls.clear()
        page.add(ana_liste)
        ana_menuyu_ciz()

    def ana_menuyu_ciz():
        ana_liste.controls.clear()
        cozulenler_full = get_storage("cozulen_full")
        hatalar_full = get_storage("hatali_full")
        biten_metinler = [s["metin"] for s in cozulenler_full]

        # Üst Panel
        ana_liste.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("HİLAL KPSS", size=24, weight="bold", color="white"),
                    ft.Row([
                        ft.Column([ft.Text(str(len(cozulenler_full)), size=20, weight="bold", color="white"), ft.Text("BAŞARILI", size=10, color="white70")], horizontal_alignment="center"),
                        ft.VerticalDivider(color="white24"),
                        ft.Column([ft.Text(str(len(hatalar_full)), size=20, weight="bold", color="#ff8888"), ft.Text("HATALI", size=10, color="white70")], horizontal_alignment="center"),
                    ], alignment="center", spacing=40)
                ], horizontal_alignment="center"),
                bgcolor="indigo", padding=30, border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30)
            )
        )

        # Hatalı Sorular Kategorisi
        if hatalar_full:
            ana_liste.controls.append(
                ft.Container(
                    content=ft.Row([ft.Icon(ft.icons.REPORT_PROBLEM, color="white"), ft.Text(f"Hatalı Sorular ({len(hatalar_full)})", color="white", weight="bold")]),
                    bgcolor="red", padding=15, margin=ft.margin.symmetric(horizontal=20, vertical=5),
                    border_radius=10, on_click=lambda _: test_baslat(hatalar_full, "Hatalarım", "red")
                )
            )

        # Ders Kategorileri
        for kat in veriler:
            kalan_sorular = [s for s in kat.get("sorular", []) if s["metin"] not in biten_metinler]
            if kalan_sorular:
                ana_liste.controls.append(
                    ft.Container(
                        content=ft.Row([ft.Icon(ft.icons.BOOKMARK, color="white"), ft.Column([ft.Text(kat["ad"], color="white", weight="bold"), ft.Text(f"{len(kalan_sorular)} Soru Kaldı", color="white70", size=11)])]),
                        bgcolor=kat.get("renk", "blue"), padding=15, margin=ft.margin.symmetric(horizontal=20, vertical=5),
                        border_radius=12, on_click=lambda e, s=kalan_sorular, a=kat["ad"], r=kat.get("renk", "blue"): test_baslat(s, a, r)
                    )
                )
        page.update()

    # Test Başlatma ve Çizme Fonksiyonları (Buraya önceki test_baslat, test_ciz ve nav eklenecek)
    # [Buradaki test kodları önceki stabil sürümle aynıdır]
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
        
        ana_liste.controls.append(ft.Container(
            content=ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK, icon_color="white", on_click=lambda _: ana_menuyu_ciz()),
                ft.Text(baslik, color="white", weight="bold"),
                ft.Text(f"{mevcut_index+1}/{len(aktif_sorular)}", color="white")
            ], alignment="spaceBetween"),
            bgcolor=renk, padding=10
        ))

        ana_liste.controls.append(ft.Container(
            content=ft.Text(soru["metin"], size=18, weight="w500"),
            padding=25, margin=15, bgcolor="white", border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color="black12")
        ))

        for secenek in soru["secenekler"]:
            is_answered = mevcut_index in oturum_cevaplari
            bg = "white"; brdr = ft.border.all(1, "grey300")
            
            if is_answered:
                if secenek == soru["cevap"]: bg = ft.colors.GREEN_100; brdr = ft.border.all(2, "green")
                elif secenek == oturum_cevaplari[mevcut_index]: bg = ft.colors.RED_100; brdr = ft.border.all(2, "red")

            def kontrol(e, s=secenek, curr_soru=soru):
                if mevcut_index in oturum_cevaplari: return
                oturum_cevaplari[mevcut_index] = s
                
                if s == curr_soru["cevap"]:
                    c_list = get_storage("cozulen_full")
                    h_list = get_storage("hatali_full")
                    if curr_soru["metin"] not in [x["metin"] for x in c_list]:
                        c_list.append(curr_soru)
                        save_storage("cozulen_full", c_list)
                    save_storage("hatali_full", [x for x in h_list if x["metin"] != curr_soru["metin"]])
                else:
                    h_list = get_storage("hatali_full")
                    if curr_soru["metin"] not in [x["metin"] for x in h_list]:
                        h_list.append(curr_soru)
                        save_storage("hatali_full", h_list)
                test_ciz(baslik, renk)

            ana_liste.controls.append(ft.Container(
                content=ft.Text(secenek, size=16),
                padding=15, margin=ft.margin.symmetric(horizontal=25, vertical=5),
                bgcolor=bg, border=brdr, border_radius=12, on_click=kontrol
            ))

        ana_liste.controls.append(ft.Row([
            ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=lambda _: nav(-1, baslik, renk), disabled=(mevcut_index==0), icon_size=40),
            ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=lambda _: nav(1, baslik, renk), disabled=(mevcut_index==len(aktif_sorular)-1), icon_size=40),
        ], alignment="center", spacing=60))
        page.update()

    def nav(yon, baslik, renk):
        nonlocal mevcut_index
        mevcut_index += yon
        test_ciz(baslik, renk)

    # Veri çekme işlemini ayrı bir thread'de başlat ki arayüz donmasın
    threading.Thread(target=verileri_cek, daemon=True).start()

ft.app(target=main)
