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

    # LİNKİN AYNI KALIYOR
    URL = "https://raw.githubusercontent.com/krrr608-cpu/kpss-uygulama/refs/heads/main/sorular.json"

    # Değişkenler
    veriler = {}
    kategoriler = []
    aktif_sorular = []
    hatali_sorular_listesi = [] # Telefonda kayıtlı hatalı soruların metinleri
    
    # Oyun Değişkenleri
    mevcut_index = 0
    toplam_puan = 0
    dogru = 0
    yanlis = 0
    durum_mesaji = "Yükleniyor..."

    # --- VERİ ÇEKME ---
    def verileri_guncelle():
        nonlocal veriler, kategoriler, durum_mesaji, hatali_sorular_listesi
        
        # 1. İnternetten Soruları Çek
        try:
            response = urllib.request.urlopen(URL, timeout=3)
            data_str = response.read().decode('utf-8')
            veriler = json.loads(data_str)
            page.client_storage.set("kpss_kategori_v2", data_str)
            durum_mesaji = "Online ✅"
        except:
            durum_mesaji = "Offline 📂"
            if page.client_storage.contains_key("kpss_kategori_v2"):
                try: veriler = json.loads(page.client_storage.get("kpss_kategori_v2"))
                except: veriler = {}
            else: veriler = {}
        
        kategoriler = veriler.get("kategoriler", [])
        
        # 2. Telefondan "Hatalı Sorular" Listesini Yükle
        if page.client_storage.contains_key("hatali_sorular"):
            hatali_sorular_listesi = page.client_storage.get("hatali_sorular")
        else:
            hatali_sorular_listesi = []

        # Ayarları Uygula
        ayarlar = veriler.get("ayarlar", {})
        page.title = ayarlar.get("baslik", "KPSS")
        page.bgcolor = ayarlar.get("arka_plan_rengi", "#f3f4f6")
        page.update()

    # --- 1. EKRAN: ANA MENÜ ---
    def ana_menuyu_ciz():
        ana_liste.controls.clear()
        verileri_guncelle() # Her menüye dönüşte hataları güncelle
        
        ayarlar = veriler.get("ayarlar", {})
        baslik = ayarlar.get("baslik", "KPSS")
        ana_renk = ayarlar.get("tema_rengi", "blue")
        
        # Başlık
        header = ft.Container(
            content=ft.Column([
                ft.Text(baslik, size=24, weight="bold", color="white"),
                ft.Text(f"Kayıtlı Hatalı Soru: {len(hatali_sorular_listesi)}", color="white70"),
                ft.Text(durum_mesaji, color="white30", size=10)
            ], horizontal_alignment="center"),
            bgcolor=ana_renk, padding=30, width=1000,
            border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20)
        )
        ana_liste.controls.append(header)
        ana_liste.controls.append(ft.Container(height=20))

        # --- ÖZEL BUTON: HATALARIM ---
        # Sadece hata varsa görünsün
        if len(hatali_sorular_listesi) > 0:
            btn_hatalar = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.WARNING_ROUNDED, color="white"),
                    ft.Text("HATALARIMI ÇÖZ", weight="bold", color="white", size=18),
                    ft.Container(
                        content=ft.Text(str(len(hatali_sorular_listesi)), color="red", size=12),
                        bgcolor="white", padding=5, border_radius=10
                    )
                ], alignment="center"),
                bgcolor="red",
                padding=20, margin=ft.margin.symmetric(horizontal=20, vertical=10),
                border_radius=15,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.with_opacity(0.4, "red")),
                on_click=lambda _: hatalari_baslat(), # Hata testini başlat
                ink=True
            )
            ana_liste.controls.append(btn_hatalar)

        # Normal Kategoriler
        if not kategoriler:
            ana_liste.controls.append(ft.Text("Kategori Yok", color="red", text_align="center"))
        
        for kat in kategoriler:
            kart = ft.Container(
                content=ft.Row([
                    ft.Icon(name=kat.get("ikon", "book"), size=40, color="white"),
                    ft.Column([
                        ft.Text(kat.get("ad"), size=20, weight="bold", color="white"),
                        ft.Text(f"{len(kat.get('sorular', []))} Soru", color="white70")
                    ], spacing=2)
                ], alignment="start"),
                bgcolor=kat.get("renk", "blue"),
                padding=20, margin=ft.margin.symmetric(horizontal=20, vertical=10),
                border_radius=15,
                shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.2, "black")),
                on_click=lambda e, k=kat: testi_baslat(k.get("sorular"), k.get("ad"), k.get("renk")),
                ink=True
            )
            ana_liste.controls.append(kart)
        page.update()

    # --- HATALARI AYIKLAYIP BAŞLATAN FONKSİYON ---
    def hatalari_baslat():
        # Tüm kategorileri gez ve metni "hatali_sorular_listesi" içinde olanları bul
        bulunan_sorular = []
        for kat in kategoriler:
            for soru in kat.get("sorular", []):
                if soru["metin"] in hatali_sorular_listesi:
                    bulunan_sorular.append(soru)
        
        if not bulunan_sorular:
            # Liste dolu görünüyor ama sorular JSON'dan silinmişse temizle
            page.client_storage.remove("hatali_sorular")
            ana_menuyu_ciz()
        else:
            testi_baslat(bulunan_sorular, "Hatalarım", "red")

    # --- TEST EKRANI ---
    def testi_baslat(soru_listesi, ders_adi, renk):
        nonlocal aktif_sorular, mevcut_index, toplam_puan, dogru, yanlis
        aktif_sorular = soru_listesi
        mevcut_index = 0
        toplam_puan = 0
        dogru = 0
        yanlis = 0
        test_ekranini_ciz(renk, ders_adi)

    def test_ekranini_ciz(renk, ders_adi):
        ana_liste.controls.clear()
        tasarim = veriler.get("tasarim", {})
        RADIUS = tasarim.get("buton_yuvarlakligi", 10)
        FONT_SORU = tasarim.get("soru_yazi_boyutu", 18)
        
        ust_bar = ft.Container(
            content=ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK, icon_color="white", on_click=lambda _: ana_menuyu_ciz()),
                ft.Text(f"{ders_adi} ({mevcut_index + 1}/{len(aktif_sorular)})", color="white", size=18, weight="bold"),
                ft.Text(f"P: {toplam_puan}", color="white")
            ], alignment="spaceBetween"),
            bgcolor=renk, padding=15
        )
        ana_liste.controls.append(ust_bar)
        ana_liste.controls.append(ft.Container(height=10))

        if mevcut_index < len(aktif_sorular):
            soru = aktif_sorular[mevcut_index]
            
            ana_liste.controls.append(
                ft.Container(
                    content=ft.Text(soru["metin"], size=FONT_SORU, color="black"),
                    bgcolor="white", padding=20, margin=10, border_radius=RADIUS,
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.1, "black"))
                )
            )

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
            # Bitiş
            ana_liste.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.CHECK_CIRCLE, size=80, color=renk),
                        ft.Text("Test Tamamlandı!", size=24, color=renk),
                        ft.Text(f"D: {dogru} | Y: {yanlis}", size=18),
                        ft.ElevatedButton("Menüye Dön", on_click=lambda _: ana_menuyu_ciz(), bgcolor=renk, color="white")
                    ], horizontal_alignment="center"),
                    alignment=ft.alignment.center, padding=30
                )
            )
        page.update()

    def cevapla(e, secilen, grup, renk, ders_adi):
        nonlocal toplam_puan, dogru, yanlis, hatali_sorular_listesi
        
        soru_metni = aktif_sorular[mevcut_index]["metin"]
        dogru_cvp = aktif_sorular[mevcut_index]["cevap"]
        tiklanan = e.control
        
        # --- HATA KAYIT SİSTEMİ ---
        if secilen == dogru_cvp:
            dogru += 1
            toplam_puan += 5
            tiklanan.bgcolor = ft.colors.GREEN_100
            tiklanan.border = ft.border.all(2, "green")
            
            # Doğru bildiyse ve önceden hatalı listesindeyse, SİL (Artık öğrendi)
            if soru_metni in hatali_sorular_listesi:
                hatali_sorular_listesi.remove(soru_metni)
                page.client_storage.set("hatali_sorular", hatali_sorular_listesi)
                
        else:
            yanlis += 1
            toplam_puan -= 1
            tiklanan.bgcolor = ft.colors.RED_100
            tiklanan.border = ft.border.all(2, "red")
            
            # Yanlış bildiyse ve listede yoksa EKLE
            if soru_metni not in hatali_sorular_listesi:
                hatali_sorular_listesi.append(soru_metni)
                page.client_storage.set("hatali_sorular", hatali_sorular_listesi)

        # Kilitleme
        for btn in grup.controls:
            btn.on_click = None
            if btn.content.value == dogru_cvp:
                btn.bgcolor = ft.colors.GREEN_50
                btn.border = ft.border.all(2, "green")
            btn.update()
            
        ana_liste.controls.append(
            ft.Container(
                content=ft.ElevatedButton("Devam >", on_click=lambda _: sonraki(renk, ders_adi), bgcolor=renk, color="white"),
                padding=20, alignment=ft.alignment.center
            )
        )
        page.update()

    def sonraki(renk, ders_adi):
        nonlocal mevcut_index
        mevcut_index += 1
        test_ekranini_ciz(renk, ders_adi)

    ana_menuyu_ciz()

ft.app(target=main)
