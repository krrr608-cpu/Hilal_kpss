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

    # LİNKİNİ BURAYA YAPIŞTIR
    URL = "https://raw.githubusercontent.com/krrr608-cpu/kpss-uygulama/refs/heads/main/sorular.json"

    # Global Değişkenler
    veriler = {}
    kategoriler = []
    aktif_sorular = []
    
    # Oyun Değişkenleri
    mevcut_index = 0
    toplam_puan = 0
    dogru = 0
    yanlis = 0
    durum_mesaji = "Yükleniyor..."

    # --- VERİ ÇEKME FONKSİYONU ---
    def verileri_guncelle():
        nonlocal veriler, kategoriler, durum_mesaji
        try:
            response = urllib.request.urlopen(URL, timeout=3)
            data_str = response.read().decode('utf-8')
            veriler = json.loads(data_str)
            page.client_storage.set("kpss_kategori_v1", data_str)
            durum_mesaji = "Veriler Güncel (Online) ✅"
        except:
            durum_mesaji = "Offline Mod 📂"
            if page.client_storage.contains_key("kpss_kategori_v1"):
                try: veriler = json.loads(page.client_storage.get("kpss_kategori_v1"))
                except: veriler = {}
            else: veriler = {}
        
        kategoriler = veriler.get("kategoriler", [])
        
        # Genel Ayarları Uygula
        ayarlar = veriler.get("ayarlar", {})
        page.title = ayarlar.get("baslik", "KPSS")
        page.bgcolor = ayarlar.get("arka_plan_rengi", "#f3f4f6")
        page.update()

    # --- 1. EKRAN: ANA MENÜ (KATEGORİLER) ---
    def ana_menuyu_ciz():
        ana_liste.controls.clear()
        
        # Başlık Alanı
        ayarlar = veriler.get("ayarlar", {})
        baslik = ayarlar.get("baslik", "KPSS")
        ana_renk = ayarlar.get("tema_rengi", "blue")
        
        header = ft.Container(
            content=ft.Column([
                ft.Text(baslik, size=24, weight="bold", color="white"),
                ft.Text("Lütfen bir ders seçiniz", color="white70"),
                ft.Text(durum_mesaji, color="white30", size=10)
            ], horizontal_alignment="center"),
            bgcolor=ana_renk,
            padding=30,
            width=1000,
            border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20)
        )
        ana_liste.controls.append(header)
        ana_liste.controls.append(ft.Container(height=20))

        if not kategoriler:
            ana_liste.controls.append(ft.Text("Kategori Bulunamadı!", color="red", text_align="center"))
            # Yenile Butonu
            ana_liste.controls.append(
                ft.Container(
                    content=ft.ElevatedButton("Tekrar Dene", on_click=lambda _: baslat()),
                    alignment=ft.alignment.center, padding=20
                )
            )
        
        # Kategorileri Listele
        for kat in kategoriler:
            # Kategori Kartı
            kart = ft.Container(
                content=ft.Row([
                    ft.Icon(name=kat.get("ikon", "book"), size=40, color="white"),
                    ft.Column([
                        ft.Text(kat.get("ad"), size=20, weight="bold", color="white"),
                        ft.Text(f"{len(kat.get('sorular', []))} Soru", color="white70")
                    ], spacing=2)
                ], alignment="start"),
                bgcolor=kat.get("renk", "blue"), # Her dersin kendi rengi
                padding=20,
                margin=ft.margin.symmetric(horizontal=20, vertical=10),
                border_radius=15,
                shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.2, "black")),
                on_click=lambda e, k=kat: testi_baslat(k), # Tıklanınca o dersi başlat
                ink=True
            )
            ana_liste.controls.append(kart)
            
        page.update()

    # --- 2. EKRAN: TEST EKRANI ---
    def testi_baslat(secilen_kategori):
        nonlocal aktif_sorular, mevcut_index, toplam_puan, dogru, yanlis
        
        aktif_sorular = secilen_kategori.get("sorular", [])
        mevcut_index = 0
        toplam_puan = 0
        dogru = 0
        yanlis = 0
        
        # O anki dersin rengini al
        test_rengi = secilen_kategori.get("renk", "blue")
        
        test_ekranini_ciz(test_rengi, secilen_kategori.get("ad"))

    def test_ekranini_ciz(renk, ders_adi):
        ana_liste.controls.clear()
        
        tasarim = veriler.get("tasarim", {})
        RADIUS = tasarim.get("buton_yuvarlakligi", 10)
        FONT_SORU = tasarim.get("soru_yazi_boyutu", 18)
        
        # Üst Bilgi Çubuğu
        ust_bar = ft.Container(
            content=ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK, icon_color="white", on_click=lambda _: ana_menuyu_ciz()),
                ft.Text(f"{ders_adi} - Soru {mevcut_index + 1}/{len(aktif_sorular)}", color="white", size=18, weight="bold"),
                ft.Text(f"P: {toplam_puan}", color="white")
            ], alignment="spaceBetween"),
            bgcolor=renk,
            padding=15
        )
        ana_liste.controls.append(ust_bar)
        ana_liste.controls.append(ft.Container(height=10))

        if mevcut_index < len(aktif_sorular):
            soru = aktif_sorular[mevcut_index]
            
            # Soru Metni
            ana_liste.controls.append(
                ft.Container(
                    content=ft.Text(soru["metin"], size=FONT_SORU, color="black"),
                    bgcolor="white", padding=20, margin=10, border_radius=RADIUS,
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.1, "black"))
                )
            )

            # Şıklar
            siklar_grubu = ft.Column()
            for sec in soru["secenekler"]:
                btn = ft.Container(
                    content=ft.Text(sec, size=16),
                    bgcolor="white", padding=15, margin=ft.margin.symmetric(horizontal=15, vertical=5),
                    border=ft.border.all(1, renk), border_radius=RADIUS,
                    on_click=lambda e, s=sec, g=siklar_grubu, r=renk: cevapla(e, s, g, r, ders_adi),
                    ink=True
                )
                siklar_grubu.controls.append(btn)
            ana_liste.controls.append(siklar_grubu)
            
        else:
            # Ders Bitti Ekranı
            ana_liste.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.CHECK_CIRCLE, size=80, color=renk),
                        ft.Text(f"{ders_adi} Tamamlandı!", size=24, weight="bold", color=renk),
                        ft.Text(f"Doğru: {dogru} | Yanlış: {yanlis}", size=18),
                        ft.Text(f"Toplam Puan: {toplam_puan}", size=20, color="green", weight="bold"),
                        ft.Container(height=20),
                        ft.ElevatedButton("Ana Menüye Dön", on_click=lambda _: ana_menuyu_ciz(), bgcolor=renk, color="white", width=200)
                    ], horizontal_alignment="center"),
                    alignment=ft.alignment.center, padding=30
                )
            )
        page.update()

    def cevapla(e, secilen, grup, renk, ders_adi):
        nonlocal toplam_puan, dogru, yanlis
        dogru_cvp = aktif_sorular[mevcut_index]["cevap"]
        tiklanan = e.control
        
        if secilen == dogru_cvp:
            dogru += 1
            toplam_puan += 5
            tiklanan.bgcolor = ft.colors.GREEN_100
            tiklanan.border = ft.border.all(2, "green")
        else:
            yanlis += 1
            toplam_puan -= 1
            tiklanan.bgcolor = ft.colors.RED_100
            tiklanan.border = ft.border.all(2, "red")

        # Kilitle
        for btn in grup.controls:
            btn.on_click = None
            if btn.content.value == dogru_cvp:
                btn.bgcolor = ft.colors.GREEN_50
                btn.border = ft.border.all(2, "green")
            btn.update()
            
        # Sonraki butonu
        ana_liste.controls.append(
            ft.Container(
                content=ft.ElevatedButton("Devam Et >", on_click=lambda _: sonraki(renk, ders_adi), bgcolor=renk, color="white"),
                padding=20, alignment=ft.alignment.center
            )
        )
        page.update()

    def sonraki(renk, ders_adi):
        nonlocal mevcut_index
        mevcut_index += 1
        test_ekranini_ciz(renk, ders_adi)

    def baslat():
        verileri_guncelle()
        ana_menuyu_ciz()

    baslat()

ft.app(target=main)
