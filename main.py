import flet as ft
import json
import urllib.request
import time
import threading

def main(page: ft.Page):
    page.title = "Hilal KPSS"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    
    # --- DEĞİŞKENLER ---
    URL = "https://raw.githubusercontent.com/krrr608-cpu/Hilal_kpss/refs/heads/main/sorular.json"
    veriler = []
    aktif_sorular = []
    mevcut_index = 0
    oturum_cevaplari = {}

    # --- EKRANLAR ---
    ana_liste = ft.ListView(expand=True, spacing=0)
    
    status_text = ft.Text("Veriler Yükleniyor...", weight="bold")
    loader_container = ft.Container(
        content=ft.Column([
            ft.ProgressRing(color="indigo"),
            status_text
        ], horizontal_alignment="center", alignment="center"),
        expand=True
    )
    page.add(loader_container)

    def get_local(key):
        return page.client_storage.get(key) if page.client_storage.contains_key(key) else []

    def set_local(key, data):
        page.client_storage.set(key, data)

    # --- VERİ ÇEKME ---
    def verileri_yukle():
        nonlocal veriler
        try:
            current_url = f"{URL}?v={int(time.time())}"
            req = urllib.request.Request(current_url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                raw_data = response.read().decode('utf-8')
                json_data = json.loads(raw_data)
                veriler = json_data.get("kategoriler", [])
                page.client_storage.set("offline_data", raw_data)
        except Exception as e:
            if page.client_storage.contains_key("offline_data"):
                raw_data = page.client_storage.get("offline_data")
                veriler = json.loads(raw_data).get("kategoriler", [])
            else:
                status_text.value = f"Hata: Veri çekilemedi!\n{str(e)}"
                page.update()
                return

        page.controls.clear()
        page.add(ana_liste)
        ana_menuyu_ciz()

    def ana_menuyu_ciz():
        ana_liste.controls.clear()
        cozulenler = get_local("cozulen_full")
        hatalar = get_local("hatali_full")
        biten_metinler = [s["metin"] for s in cozulenler]

        # Üst Panel (İstatistikler)
        ana_liste.controls.append(ft.Container(
            content=ft.Column([
                ft.Text("HİLAL KPSS", size=24, weight="bold", color="white"),
                ft.Row([
                    ft.Column([ft.Text(str(len(cozulenler)), color="white", weight="bold", size=20), ft.Text("BAŞARI", size=10, color="white70")], horizontal_alignment="center"),
                    ft.Column([ft.Text(str(len(hatalar)), color="#ff8888", weight="bold", size=20), ft.Text("HATA", size=10, color="white70")], horizontal_alignment="center"),
                ], alignment="center", spacing=40)
            ], horizontal_alignment="center"),
            bgcolor="indigo", padding=30, border_radius=ft.border_radius.only(bottom_left=25, bottom_right=25)
        ))

        # Hatalı Sorular Kategorisi
        if hatalar:
            ana_liste.controls.append(ft.Container(
                content=ft.Row([ft.Icon(ft.icons.ERROR, color="red"), ft.Text(f"Hatalı Sorular ({len(hatalar)})", weight="bold")]),
                bgcolor="#FFEBEE", padding=15, margin=ft.margin.symmetric(horizontal=20, vertical=5),
                border_radius=10, on_click=lambda _: test_baslat(hatalar, "Hatalarım", "red"), ink=True
            ))

        # Çözülenler Arşivi Kategorisi
        if cozulenler:
            ana_liste.controls.append(ft.Container(
                content=ft.Row([ft.Icon(ft.icons.CHECK_CIRCLE, color="green"), ft.Text(f"Çözülenler Arşivi ({len(cozulenler)})", weight="bold")]),
                bgcolor="#E8F5E9", padding=15, margin=ft.margin.symmetric(horizontal=20, vertical=5),
                border_radius=10, on_click=lambda _: test_baslat(cozulenler, "Arşiv", "green"), ink=True
            ))

        # Dersler (Dinamik Liste)
        for kat in veriler:
            kalan = [s for s in kat.get("sorular", []) if s["metin"] not in biten_metinler]
            if kalan:
                ana_liste.controls.append(ft.Container(
                    content=ft.Row([ft.Icon(ft.icons.PLAY_ARROW, color="indigo"), ft.Text(f"{kat['ad']} ({len(kalan)} Soru)")]),
                    bgcolor="white", padding=15, margin=ft.margin.symmetric(horizontal=20, vertical=5),
                    border_radius=10, border=ft.border.all(1, "#eeeeee"),
                    on_click=lambda e, s=kalan, a=kat["ad"], r=kat.get("renk", "indigo"): test_baslat(s, a, r),
                    ink=True
                ))
        page.update()

    def test_baslat(soru_listesi, baslik, renk):
        nonlocal aktif_sorular, mevcut_index, oturum_cevaplari
        aktif_sorular = soru_listesi
        mevcut_index = 0
        oturum_cevaplari = {}
        test_ciz(baslik, renk)

    def test_ciz(baslik, renk):
        ana_liste.controls.clear()
        if not aktif_sorular: 
            ana_menuyu_ciz()
            return
        
        soru = aktif_sorular[mevcut_index]
        
        ana_liste.controls.append(ft.Container(
            content=ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: ana_menuyu_ciz()),
                ft.Text(baslik, weight="bold"),
                ft.Text(f"{mevcut_index+1}/{len(aktif_sorular)}")
            ], alignment="spaceBetween"),
            bgcolor="#eeeeee", padding=10
        ))

        ana_liste.controls.append(ft.Container(
            content=ft.Text(soru["metin"], size=18, weight="w500"),
            padding=20, margin=10, bgcolor="white", border_radius=10, shadow=ft.BoxShadow(blur_radius=5, color="black12")
        ))

        for sec in soru["secenekler"]:
            bg = "white"
            border_color = "#dddddd"
            if mevcut_index in oturum_cevaplari:
                if sec == soru["cevap"]: 
                    bg = "#C8E6C9"
                    border_color = "green"
                elif sec == oturum_cevaplari[mevcut_index]: 
                    bg = "#FFCDD2"
                    border_color = "red"

            def cevapla(e, s=sec, cur=soru):
                if mevcut_index in oturum_cevaplari: return
                oturum_cevaplari[mevcut_index] = s
                
                c_list = get_local("cozulen_full")
                h_list = get_local("hatali_full")
                
                if s == cur["cevap"]:
                    # Doğruysa: Çözülenlere ekle
                    if cur["metin"] not in [x["metin"] for x in c_list]:
                        c_list.append(cur)
                        set_local("cozulen_full", c_list)
                    # Hatalardan sil
                    h_list = [x for x in h_list if x["metin"] != cur["metin"]]
                    set_local("hatali_full", h_list)
                else:
                    # Yanlışsa: Hatalara ekle (zaten yoksa)
                    if cur["metin"] not in [x["metin"] for x in h_list]:
                        h_list.append(cur)
                        set_local("hatali_full", h_list)
                
                test_ciz(baslik, renk)

            ana_liste.controls.append(ft.Container(
                content=ft.Text(sec, size=16), padding=15, margin=ft.margin.symmetric(horizontal=20, vertical=5),
                bgcolor=bg, border=ft.border.all(1, border_color), border_radius=8, on_click=cevapla, ink=True
            ))

        ana_liste.controls.append(ft.Row([
            ft.IconButton(ft.icons.NAVIGATE_BEFORE, on_click=lambda _: nav(-1, baslik, renk), disabled=(mevcut_index==0), icon_size=35),
            ft.IconButton(ft.icons.NAVIGATE_NEXT, on_click=lambda _: nav(1, baslik, renk), disabled=(mevcut_index==len(aktif_sorular)-1), icon_size=35),
        ], alignment="center", spacing=50))
        page.update()

    def nav(y, b, r):
        nonlocal mevcut_index
        mevcut_index += y
        test_ciz(b, r)

    threading.Thread(target=verileri_yukle, daemon=True).start()

ft.app(target=main)
