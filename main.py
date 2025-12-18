import flet as ft
import json
import urllib.request
import time
import asyncio

async def main(page: ft.Page):
    # --- TEMEL AYARLAR ---
    page.title = "Hilal KPSS"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    page.bgcolor = "#f3f4f6"

    # --- DEĞİŞKENLER ---
    BASE_URL = "https://raw.githubusercontent.com/krrr608-cpu/Hilal_kpss/refs/heads/main/sorular.json"
    veriler = []
    aktif_sorular = []
    mevcut_index = 0
    oturum_cevaplari = {}

    # --- ARAYÜZ ELEMANLARI ---
    ana_liste = ft.ListView(expand=True, spacing=0)
    
    loader = ft.Container(
        content=ft.Column([
            ft.ProgressRing(color="indigo"),
            ft.Text("Sorular Hazırlanıyor...", weight="bold")
        ], horizontal_alignment="center"),
        alignment=ft.alignment.center, expand=True
    )
    page.add(loader)

    # --- HAFIZA FONKSİYONLARI ---
    def get_local(key):
        return page.client_storage.get(key) if page.client_storage.contains_key(key) else []

    def set_local(key, data):
        page.client_storage.set(key, data)

    # --- VERİ ÇEKME (ASYNC) ---
    async def verileri_yukle():
        nonlocal veriler
        try:
            # Cache kırma için zaman damgası
            url = f"{BASE_URL}?v={int(time.time())}"
            # Arka planda veriyi çek (Bloke etmeden)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: urllib.request.urlopen(url, timeout=7).read().decode('utf-8'))
            
            json_data = json.loads(response)
            veriler = json_data.get("kategoriler", [])
            page.client_storage.set("kpss_offline", response)
        except Exception as e:
            # İnternet hatasında çevrimdışı yedeği yükle
            if page.client_storage.contains_key("kpss_offline"):
                backup = page.client_storage.get("kpss_offline")
                veriler = json.loads(backup).get("kategoriler", [])
        
        await ana_menuyu_ciz()

    # --- ANA MENÜ ---
    async def ana_menuyu_ciz():
        page.controls.clear()
        ana_liste.controls.clear()
        
        cozulenler = get_local("cozulen_full")
        hatalar = get_local("hatali_full")
        biten_metinler = [s["metin"] for s in cozulenler]

        # Üst Panel
        ana_liste.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("HİLAL KPSS", size=24, weight="bold", color="white"),
                    ft.Row([
                        ft.Column([ft.Text(str(len(cozulenler)), size=20, weight="bold", color="white"), ft.Text("BAŞARILI", size=10, color="white70")], horizontal_alignment="center"),
                        ft.VerticalDivider(color="white24"),
                        ft.Column([ft.Text(str(len(hatalar)), size=20, weight="bold", color="#ff8888"), ft.Text("HATALI", size=10, color="white70")], horizontal_alignment="center"),
                    ], alignment="center", spacing=40)
                ], horizontal_alignment="center"),
                bgcolor="indigo", padding=35, border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30)
            )
        )

        # Hatalı Sorular
        if hatalar:
            ana_liste.controls.append(
                ft.Container(
                    content=ft.Row([ft.Icon(ft.icons.ERROR_OUTLINE, color="white"), ft.Text(f"Hatalı Sorular ({len(hatalar)})", color="white", weight="bold")]),
                    bgcolor="red", padding=15, margin=ft.margin.symmetric(horizontal=20, vertical=5),
                    border_radius=12, on_click=lambda _: test_ekranina_gec(hatalar, "Hatalarım", "red"), ink=True
                )
            )

        # Çözülenler
        if cozulenler:
            ana_liste.controls.append(
                ft.Container(
                    content=ft.Row([ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, color="white"), ft.Text(f"Çözülenler Arşivi ({len(cozulenler)})", color="white", weight="bold")]),
                    bgcolor="green", padding=15, margin=ft.margin.symmetric(horizontal=20, vertical=5),
                    border_radius=12, on_click=lambda _: test_ekranina_gec(cozulenler, "Arşiv", "green"), ink=True
                )
            )

        # Dinamik Dersler
        for kat in veriler:
            kalan = [s for s in kat.get("sorular", []) if s["metin"] not in biten_metinler]
            if kalan:
                ana_liste.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.BOOK, color="white"),
                            ft.Column([ft.Text(kat["ad"], color="white", weight="bold"), ft.Text(f"{len(kalan)} Soru Kaldı", color="white70", size=11)])
                        ]),
                        bgcolor=kat.get("renk", "blue"), padding=18, margin=ft.margin.symmetric(horizontal=20, vertical=6),
                        border_radius=15, on_click=lambda e, s=kalan, a=kat["ad"], r=kat.get("renk", "blue"): test_ekranina_gec(s, a, r),
                        ink=True
                    )
                )
        
        page.add(ana_liste)
        page.update()

    # --- TEST SİSTEMİ ---
    def test_ekranina_gec(soru_listesi, baslik, renk):
        nonlocal aktif_sorular, mevcut_index, oturum_cevaplari
        aktif_sorular = soru_listesi
        mevcut_index = 0
        oturum_cevaplari = {}
        test_sayfasini_ciz(baslik, renk)

    def test_sayfasini_ciz(baslik, renk):
        ana_liste.controls.clear()
        soru = aktif_sorular[mevcut_index]
        
        ana_liste.controls.append(ft.Container(
            content=ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK, icon_color="white", on_click=lambda _: asyncio.run(ana_menuyu_ciz())),
                ft.Text(baslik, color="white", weight="bold"),
                ft.Text(f"{mevcut_index+1}/{len(aktif_sorular)}", color="white")
            ], alignment="spaceBetween"),
            bgcolor=renk, padding=10
        ))

        ana_liste.controls.append(ft.Container(
            content=ft.Text(soru["metin"], size=18, weight="w500"),
            padding=25, margin=15, bgcolor="white", border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color="black12")
        ))

        for sec in soru["secenekler"]:
            is_ans = mevcut_index in oturum_cevaplari
            bg = "white"
            if is_ans:
                if sec == soru["cevap"]: bg = "#C8E6C9" # Yeşil
                elif sec == oturum_cevaplari[mevcut_index]: bg = "#FFCDD2" # Kırmızı

            def cevapla(e, s=sec, cur=soru):
                if mevcut_index in oturum_cevaplari: return
                oturum_cevaplari[mevcut_index] = s
                
                c_list = get_local("cozulen_full")
                h_list = get_local("hatali_full")

                if s == cur["cevap"]:
                    if cur["metin"] not in [x["metin"] for x in c_list]:
                        c_list.append(cur)
                        set_local("cozulen_full", c_list)
                    h_list = [x for x in h_list if x["metin"] != cur["metin"]]
                    set_local("hatali_full", h_list)
                else:
                    if cur["metin"] not in [x["metin"] for x in h_list]:
                        h_list.append(cur)
                        set_local("hatali_full", h_list)
                test_sayfasini_ciz(baslik, renk)

            ana_liste.controls.append(ft.Container(
                content=ft.Text(sec, size=16),
                padding=15, margin=ft.margin.symmetric(horizontal=25, vertical=5),
                bgcolor=bg, border=ft.border.all(1, "grey300"), border_radius=12, on_click=cevapla
            ))

        ana_liste.controls.append(ft.Row([
            ft.IconButton(ft.icons.ARROW_LEFT, on_click=lambda _: nav(-1, baslik, renk), disabled=(mevcut_index==0), icon_size=40),
            ft.IconButton(ft.icons.ARROW_RIGHT, on_click=lambda _: nav(1, baslik, renk), disabled=(mevcut_index==len(aktif_sorular)-1), icon_size=40),
        ], alignment="center", spacing=60))
        page.update()

    def nav(yon, baslik, renk):
        nonlocal mevcut_index
        mevcut_index += yon
        test_sayfasini_ciz(baslik, renk)

    # Başlangıç
    await verileri_yukle()

ft.app(target=main)
