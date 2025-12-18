import flet as ft
import json
import urllib.request

def main(page: ft.Page):
    page.padding = 0
    page.spacing = 0
    
    # Ana ekran taşıyıcısı
    ana_liste = ft.ListView(expand=True, spacing=0, padding=ft.padding.only(top=50, bottom=20))
    page.add(ana_liste)

    URL = "https://raw.githubusercontent.com/krrr608-cpu/Hilal_kpss/refs/heads/main/sorular.json"

    # Veri Deposu
    veriler = {}
    cozulen_sorular = [] 
    hatali_sorular = []
    aktif_sorular = []
    mevcut_index = 0
    toplam_puan = 0
    oturum_cevaplari = {} 

    def verileri_guncelle():
        nonlocal veriler, cozulen_sorular, hatali_sorular
        try:
            response = urllib.request.urlopen(URL, timeout=3)
            data_str = response.read().decode('utf-8')
            veriler = json.loads(data_str)
            page.client_storage.set("kpss_v6_data", data_str)
        except:
            if page.client_storage.contains_key("kpss_v6_data"):
                veriler = json.loads(page.client_storage.get("kpss_v6_data"))
        
        cozulen_sorular = page.client_storage.get("cozulenler") if page.client_storage.contains_key("cozulenler") else []
        hatali_sorular = page.client_storage.get("hatalar") if page.client_storage.contains_key("hatalar") else []

    # --- 📖 DERS NOTU PENCERESİ ---
    def ders_notu_ac(baslik, icerik, renk):
        def kapat(e):
            page.close(dlg)
        dlg = ft.AlertDialog(
            title=ft.Text(baslik, weight="bold"),
            content=ft.Container(content=ft.Column([ft.Divider(), ft.Text(icerik, size=16)], scroll=ft.ScrollMode.ADAPTIVE), height=400, width=350),
            actions=[ft.TextButton("Kapat", on_click=kapat)],
            shape=ft.RoundedRectangleBorder(radius=15),
        )
        page.overlay.append(dlg); dlg.open = True; page.update()

    # --- 🏠 ANA MENÜ VE LİSTELEME ---
    def kategorileri_ciz(liste, ust_baslik="Hilal KPSS", renk="indigo", is_sub=False):
        ana_liste.controls.clear()
        
        # Üst Bilgi Alanı
        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.IconButton(ft.icons.ARROW_BACK, icon_color="white", on_click=lambda _: ana_menuyu_ciz()) if is_sub else ft.Container(),
                    ft.Text(ust_baslik, size=22, weight="bold", color="white"),
                ], alignment="start"),
                ft.Text("Başlamak için bir bölüm seçin", color="white70", size=12)
            ]),
            bgcolor=renk, padding=25, border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20)
        )
        ana_liste.controls.append(header)

        for öğe in liste:
            tip = öğe.get("tip", "kategori")
            
            if tip == "not":
                on_click_func = lambda e, b=öğe["ad"], i=öğe["icerik"], r=renk: ders_notu_ac(b, i, r)
                alt_bilgi = "Ders Notu 📖"; kart_renk = "orange"; ikon = ft.icons.DESCRIPTION
            elif "alt_kategoriler" in öğe:
                on_click_func = lambda e, l=öğe["alt_kategoriler"], a=öğe["ad"], r=renk: kategorileri_ciz(l, a, r, True)
                alt_bilgi = f"{len(öğe['alt_kategoriler'])} Alt Bölüm"; kart_renk = "blue"; ikon = ft.icons.FOLDER
            else:
                sorular = öğe.get("sorular", [])
                on_click_func = lambda e, k=öğe, s=sorular: ders_testini_baslat(k, s)
                alt_bilgi = f"Soru Sayısı: {len(sorular)}"; kart_renk = "green"; ikon = ft.icons.QUIZ

            ana_liste.controls.append(
                ft.Container(
                    content=ft.Row([ft.Icon(ikon, color="white"), ft.Column([ft.Text(öğe["ad"], color="white", weight="bold"), ft.Text(alt_bilgi, color="white70", size=11)])]),
                    bgcolor=kart_renk, padding=15, margin=ft.margin.symmetric(horizontal=20, vertical=5),
                    border_radius=10, on_click=on_click_func, ink=True
                )
            )
        page.update()

    # --- ✍️ TEST MOTORU ---
    def ders_testini_baslat(kategori, soru_listesi):
        nonlocal aktif_sorular, mevcut_index, oturum_cevaplari, toplam_puan
        aktif_sorular = soru_listesi
        mevcut_index = 0
        oturum_cevaplari = {}
        toplam_puan = 0
        test_ekranini_ciz(kategori.get("renk", "green"), kategori["ad"])

    def test_ekranini_ciz(renk, baslik):
        ana_liste.controls.clear()
        soru = aktif_sorular[mevcut_index]
        
        # Test Header
        ana_liste.controls.append(ft.Container(
            content=ft.Row([
                ft.IconButton(ft.icons.CLOSE, icon_color="white", on_click=lambda _: ana_menuyu_ciz()),
                ft.Text(baslik, color="white", weight="bold"),
                ft.Text(f"{mevcut_index+1}/{len(aktif_sorular)}", color="white")
            ], alignment="spaceBetween"),
            bgcolor=renk, padding=10
        ))

        # Soru Kartı
        ana_liste.controls.append(ft.Container(
            content=ft.Text(soru["metin"], size=18, weight="w500"),
            padding=20, margin=15, bgcolor="white", border_radius=10, shadow=ft.BoxShadow(blur_radius=5, color="black12")
        ))

        # Şıklar
        for secenek in soru["secenekler"]:
            def cevap_kontrol(e, sec=secenek):
                if mevcut_index in oturum_cevaplari: return # Zaten çözüldüyse basma
                dogru = soru["cevap"]
                if sec == dogru:
                    e.control.bgcolor = "green100"; e.control.border = ft.border.all(2, "green")
                else:
                    e.control.bgcolor = "red100"; e.control.border = ft.border.all(2, "red")
                oturum_cevaplari[mevcut_index] = sec
                page.update()

            ana_liste.controls.append(ft.Container(
                content=ft.Text(secenek, size=16),
                padding=15, margin=ft.margin.symmetric(horizontal=25, vertical=5),
                border=ft.border.all(1, "grey300"), border_radius=8, on_click=cevap_kontrol
            ))

        # Alt Navigasyon
        ana_liste.controls.append(ft.Row([
            ft.TextButton("Geri", on_click=lambda _: navigasyon(-1, renk, baslik), disabled=(mevcut_index==0)),
            ft.TextButton("İleri", on_click=lambda _: navigasyon(1, renk, baslik), disabled=(mevcut_index==len(aktif_sorular)-1))
        ], alignment="center"))
        page.update()

    def navigasyon(yon, renk, baslik):
        nonlocal mevcut_index
        mevcut_index += yon
        test_ekranini_ciz(renk, baslik)

    def ana_menuyu_ciz():
        verileri_guncelle()
        kategorileri_ciz(veriler.get("kategoriler", []))

    ana_menuyu_ciz()

ft.app(target=main)
