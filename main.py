import flet as ft
import json
import urllib.request
import asyncio

def main(page: ft.Page):
    # --- AYARLAR ---
    page.padding = 0
    page.spacing = 0
    ana_liste = ft.ListView(expand=True, spacing=0, padding=0)
    page.add(ana_liste)

    # LİNKİN AYNI
    URL = "https://raw.githubusercontent.com/krrr608-cpu/kpss-uygulama/refs/heads/main/sorular.json"

    # Global Değişkenler
    veriler = {}
    kategoriler = []
    
    # Hafıza Listeleri
    cozulen_sorular = [] 
    hatali_sorular = []
    
    # Oyun Değişkenleri
    aktif_sorular = []
    mevcut_index = 0
    toplam_puan = 0
    dogru_sayisi = 0
    yanlis_sayisi = 0
    durum_mesaji = "Yükleniyor..."
    
    # Oturumdaki cevapları tutmak için (Geri dönünce cevabı hatırlasın)
    oturum_cevaplari = {} 

    # --- VERİ VE HAFIZA YÖNETİMİ ---
    def verileri_guncelle():
        nonlocal veriler, kategoriler, durum_mesaji, cozulen_sorular, hatali_sorular
        
        try:
            response = urllib.request.urlopen(URL, timeout=3)
            data_str = response.read().decode('utf-8')
            veriler = json.loads(data_str)
            page.client_storage.set("kpss_v5_data", data_str)
            durum_mesaji = "Online ✅"
        except:
            durum_mesaji = "Offline 📂"
            if page.client_storage.contains_key("kpss_v5_data"):
                try: veriler = json.loads(page.client_storage.get("kpss_v5_data"))
                except: veriler = {}
            else: veriler = {}
        
        kategoriler = veriler.get("kategoriler", [])
        
        if page.client_storage.contains_key("cozulenler"):
            cozulen_sorular = page.client_storage.get("cozulenler")
        else: cozulen_sorular = []
            
        if page.client_storage.contains_key("hatalar"):
            hatali_sorular = page.client_storage.get("hatalar")
        else: hatali_sorular = []

        ayarlar = veriler.get("ayarlar", {})
        page.bgcolor = ayarlar.get("arka_plan_rengi", "#f3f4f6")
        page.update()

    # --- 1. EKRAN: ANA MENÜ ---
    def ana_menuyu_ciz():
        ana_liste.controls.clear()
        verileri_guncelle()
        
        ayarlar = veriler.get("ayarlar", {})
        baslik = ayarlar.get("baslik", "KPSS")
        ana_renk = ayarlar.get("tema_rengi", "blue")
        
        header = ft.Container(
            content=ft.Column([
                ft.Text(baslik, size=24, weight="bold", color="white"),
                ft.Text("Kategoriyi açmak için BASILI TUTUN", color="white70", size=12, italic=True),
                ft.Text(durum_mesaji, color="white30", size=10)
            ], horizontal_alignment="center"),
            bgcolor=ana_renk, padding=30, width=1000,
            border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20)
        )
        ana_liste.controls.append(header)
        ana_liste.controls.append(ft.Container(height=10))

        # ÖZEL BUTONLAR
        ozel_butonlar = ft.Row(alignment="center", spacing=10)
        
        if len(hatali_sorular) > 0:
            btn_hata = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.WARNING_ROUNDED, color="white"),
                    ft.Text("HATALARIM", weight="bold", color="white"),
                    ft.Text(f"{len(hatali_sorular)} Soru", color="white70", size=12)
                ], horizontal_alignment="center"),
                bgcolor="red", padding=15, border_radius=10, width=160,
                on_long_press=lambda _: ozel_testi_baslat("hatalar"),
                ink=True
            )
            ozel_butonlar.controls.append(btn_hata)

        if len(cozulen_sorular) > 0:
            btn_cozulen = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color="white"),
                    ft.Text("ÇÖZÜLENLER", weight="bold", color="white"),
                    ft.Text(f"{len(cozulen_sorular)} Soru", color="white70", size=12)
                ], horizontal_alignment="center"),
                bgcolor="green", padding=15, border_radius=10, width=160,
                on_long_press=lambda _: ozel_testi_baslat("cozulenler"),
                ink=True
            )
            ozel_butonlar.controls.append(btn_cozulen)
            
        ana_liste.controls.append(ozel_butonlar)
        ana_liste.controls.append(ft.Container(height=10))

        # KATEGORİLER
        for kat in kategoriler:
            tum_sorular = kat.get("sorular", [])
            cozulmemis_sorular = [s for s in tum_sorular if s["metin"] not in cozulen_sorular]
            kalan_sayisi = len(cozulmemis_sorular)
            
            kart_renk = kat.get("renk", "blue")
            if kalan_sayisi == 0: kart_renk = "grey"

            kart = ft.Container(
                content=ft.Row([
                    ft.Icon(name=kat.get("ikon", "book"), size=40, color="white"),
                    ft.Column([
                        ft.Text(kat.get("ad"), size=20, weight="bold", color="white"),
                        ft.Text(f"Kalan: {kalan_sayisi} / Toplam: {len(tum_sorular)}", color="white70") if kalan_sayisi > 0 else ft.Text("TÜMÜ ÇÖZÜLDÜ ✅", color="#ccffcc", weight="bold")
                    ], spacing=2)
                ], alignment="start"),
                bgcolor=kart_renk,
                padding=20, margin=ft.margin.symmetric(horizontal=20, vertical=10),
                border_radius=15,
                shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.2, "black")),
                on_long_press=lambda e, k=kat, s=cozulmemis_sorular: ders_testini_baslat(k, s),
                ink=True
            )
            ana_liste.controls.append(kart)
            
        page.update()

    # --- TEST BAŞLATMA ---
    def ders_testini_baslat(kategori, filtrelenmis_sorular):
        if len(filtrelenmis_sorular) == 0:
            snack = ft.SnackBar(ft.Text(f"Tebrikler! {kategori['ad']} bitti."), bgcolor="green")
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return
        baslat_motoru(filtrelenmis_sorular, kategori['ad'], kategori.get("renk", "blue"), mod="normal")

    def ozel_testi_baslat(tur):
        havuz = []
        baslik = ""
        renk = ""
        tum_raw_sorular = []
        for k in kategoriler: tum_raw_sorular.extend(k.get("sorular", []))
            
        hedef_liste = hatali_sorular if tur == "hatalar" else cozulen_sorular
        
        for s in tum_raw_sorular:
            if s["metin"] in hedef_liste: havuz.append(s)
        
        if tur == "hatalar": baslik, renk = "Hatalarım", "red"
        else: baslik, renk = "Çözülenler Arşivi", "green"
            
        if not havuz: return
        baslat_motoru(havuz, baslik, renk, mod=tur)

    def baslat_motoru(soru_listesi, baslik, renk, mod):
        nonlocal aktif_sorular, mevcut_index, toplam_puan, dogru_sayisi, yanlis_sayisi, oturum_cevaplari
        aktif_sorular = soru_listesi
        mevcut_index = 0
        toplam_puan = 0
        dogru_sayisi = 0
        yanlis_sayisi = 0
        oturum_cevaplari = {} # Oturum cevaplarını sıfırla
        test_ekranini_ciz(renk, baslik, mod)

    # --- 2. EKRAN: TEST ARAYÜZÜ (GÜNCELLENDİ) ---
    def test_ekranini_ciz(renk, baslik, mod):
        ana_liste.controls.clear()
        
        tasarim = veriler.get("tasarim", {})
        RADIUS = tasarim.get("buton_yuvarlakligi", 10)
        FONT_SORU = tasarim.get("soru_yazi_boyutu", 18)

        # Üst Bar
        ust_bar = ft.Container(
            content=ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK, icon_color="white", on_click=lambda _: ana_menuyu_ciz()),
                ft.Text(f"{baslik}", color="white", size=16, weight="bold"),
                ft.Text(f"P: {toplam_puan}", color="white")
            ], alignment="spaceBetween"),
            bgcolor=renk, padding=10
        )
        ana_liste.controls.append(ust_bar)
        
        # NAVİGASYON (GEÇİŞ) BAR
        soru_secenekleri = []
        for i in range(len(aktif_sorular)):
            durum_ikon = ""
            if i in oturum_cevaplari:
                durum_ikon = "✅" if oturum_cevaplari[i] == "dogru" else "❌"
            soru_secenekleri.append(ft.dropdown.Option(key=str(i), text=f"Soru {i+1} {durum_ikon}"))

        nav_bar = ft.Container(
            content=ft.Row([
                ft.ElevatedButton("< Önceki", on_click=lambda _: soru_degistir(-1, renk, baslik, mod), disabled=(mevcut_index==0), color=renk),
                ft.Dropdown(
                    width=150,
                    options=soru_secenekleri,
                    value=str(mevcut_index),
                    on_change=lambda e: soruya_git(int(e.control.value), renk, baslik, mod),
                    text_size=12,
                    content_padding=5,
                    filled=True,
                    bgcolor="white"
                ),
                ft.ElevatedButton("Sonraki >", on_click=lambda _: soru_degistir(1, renk, baslik, mod), disabled=(mevcut_index==len(aktif_sorular)-1), color=renk),
            ], alignment="center", spacing=10),
            padding=10, bgcolor="#e0e0e0"
        )
        ana_liste.controls.append(nav_bar)

        # Soru Alanı
        soru = aktif_sorular[mevcut_index]
        ana_liste.controls.append(
            ft.Container(
                content=ft.Text(soru["metin"], size=FONT_SORU, color="black"),
                bgcolor="white", padding=20, margin=10, border_radius=RADIUS,
                shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.1, "black"))
            )
        )

        # Şıklar
        siklar_grubu = ft.Column()
        
        # Bu soru daha önce çözüldü mü kontrol et
        cozulmus_mu = mevcut_index in oturum_cevaplari
        
        for sec in soru["secenekler"]:
            # Eğer çözüldüyse renkleri ayarla
            btn_renk = "white"
            yazi_renk = "black"
            border_renk = renk
            
            if cozulmus_mu:
                dogru_cvp = soru["cevap"]
                if sec == dogru_cvp:
                    btn_renk = ft.colors.GREEN_100
                    border_renk = "green"
                elif oturum_cevaplari[mevcut_index] == "yanlis" and sec != dogru_cvp:
                    # Yanlış çözdüyse ve bu şık o yanlış şıksa (bunu basit tutmak için sadece doğruyu gösteriyoruz)
                    pass

            btn = ft.Container(
                content=ft.Text(sec, size=16, color=yazi_renk),
                bgcolor=btn_renk, padding=15, margin=ft.margin.symmetric(horizontal=15, vertical=5),
                border=ft.border.all(1, border_renk), border_radius=RADIUS,
                on_click=None if cozulmus_mu else lambda e, s=sec, g=siklar_grubu: cevapla(e, s, g, renk, baslik, mod),
                ink=not cozulmus_mu
            )
            siklar_grubu.controls.append(btn)
        ana_liste.controls.append(siklar_grubu)
        
        # Alt Boşluk
        ana_liste.controls.append(ft.Container(height=50))
        page.update()

    def soru_degistir(yon, renk, baslik, mod):
        nonlocal mevcut_index
        mevcut_index += yon
        test_ekranini_ciz(renk, baslik, mod)

    def soruya_git(index, renk, baslik, mod):
        nonlocal mevcut_index
        mevcut_index = index
        test_ekranini_ciz(renk, baslik, mod)

    def cevapla(e, secilen, grup, renk, baslik, mod):
        nonlocal toplam_puan, dogru_sayisi, yanlis_sayisi, cozulen_sorular, hatali_sorular, oturum_cevaplari
        
        soru_metni = aktif_sorular[mevcut_index]["metin"]
        dogru_cvp = aktif_sorular[mevcut_index]["cevap"]
        tiklanan = e.control
        
        # Oturum kaydı
        sonuc = ""

        if secilen == dogru_cvp:
            dogru_sayisi += 1
            toplam_puan += 5
            sonuc = "dogru"
            tiklanan.bgcolor = ft.colors.GREEN_100
            tiklanan.border = ft.border.all(2, "green")
            if soru_metni not in cozulen_sorular: cozulen_sorular.append(soru_metni)
            if soru_metni in hatali_sorular: hatali_sorular.remove(soru_metni)
        else:
            yanlis_sayisi += 1
            toplam_puan -= 1
            sonuc = "yanlis"
            tiklanan.bgcolor = ft.colors.RED_100
            tiklanan.border = ft.border.all(2, "red")
            if soru_metni not in hatali_sorular: hatali_sorular.append(soru_metni)
            if soru_metni in cozulen_sorular: cozulen_sorular.remove(soru_metni)

        oturum_cevaplari[mevcut_index] = sonuc # Bu sorunun durumunu kaydet
        page.client_storage.set("cozulenler", cozulen_sorular)
        page.client_storage.set("hatalar", hatali_sorular)

        # Kilitle
        for btn in grup.controls:
            btn.on_click = None
            if btn.content.value == dogru_cvp:
                btn.bgcolor = ft.colors.GREEN_50
                btn.border = ft.border.all(2, "green")
            btn.update()
        
        # Otomatik geçiş yerine navigasyonu kullanıyoruz ama bir süre sonra geçsin istersek:
        # await asyncio.sleep(1) -> sonraki_soru() yapılabilir. 
        # Şimdilik kullanıcı "Sonraki" butonuna basmalı.
        page.update()

    ana_menuyu_ciz()

ft.app(target=main)
