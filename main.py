import flet as ft
import json
import urllib.request
import time
import asyncio

def main(page: ft.Page):
    # --- BAŞLANGIÇ AYARLARI (İnternet yoksa bunlar geçerli) ---
    DEFAULT_AYARLAR = {
        "baslik": "Yükleniyor...",
        "tema_rengi": "grey",
        "arka_plan_rengi": "white",
        "sure_var_mi": False,
        "toplam_sure_dakika": 0,
        "puan_dogru": 1,
        "puan_yanlis": 0
    }
    
    # Güvenli Mod Ayarları
    page.padding = 0
    page.spacing = 0
    
    # Ana Liste (Kaydırma sorunsuz olsun diye)
    ana_liste = ft.ListView(expand=True, spacing=0, padding=0)
    page.add(ana_liste)

    # --- VERİ ÇEKME ---
    # 👇 BURAYA KENDİ RAW LİNKİNİ YAPIŞTIR
    URL = "https://raw.githubusercontent.com/krrr608-cpu/kpss-uygulama/refs/heads/main/sorular.json"
    
    veriler = {}
    sorular = []
    ayarlar = DEFAULT_AYARLAR
    
    try:
        response = urllib.request.urlopen(URL)
        data = response.read().decode('utf-8')
        veriler = json.loads(data)
        
        # Gelen veriyi parçala
        sorular = veriler.get("sorular", [])
        ayarlar = veriler.get("ayarlar", DEFAULT_AYARLAR)
        durum_mesaji = "Güncel Ayarlar Yüklendi! ✅"
    except Exception as e:
        durum_mesaji = "İnternet Yok, Standart Mod ❌"
        print(e)

    # --- AYARLARI UYGULA ---
    page.title = ayarlar.get("baslik")
    page.bgcolor = ayarlar.get("arka_plan_rengi")
    ANA_RENK = ayarlar.get("tema_rengi")
    
    # Değişkenler
    mevcut_index = 0
    toplam_puan = 0
    dogru_sayisi = 0
    yanlis_sayisi = 0
    
    # Süre Hesabı
    kalan_saniye = ayarlar.get("toplam_sure_dakika", 0) * 60
    sure_aktif = ayarlar.get("sure_var_mi", False)

    # --- ARAYÜZ ELEMANLARI ---
    
    # Başlık ve Süre Göstergesi
    txt_baslik = ft.Text(ayarlar.get("baslik"), size=20, weight="bold", color="white")
    txt_puan = ft.Text(f"Puan: {toplam_puan}", color="white")
    txt_sure = ft.Text("", color="white", weight="bold", size=16)
    
    header = ft.Container(
        content=ft.Column([
            ft.Row([txt_baslik], alignment="center"),
            ft.Row([txt_sure, txt_puan], alignment="spaceBetween")
        ]),
        bgcolor=ANA_RENK,
        padding=15,
        border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15)
    )

    # --- ZAMANLAYICI (Async Çalışır) ---
    async def sureyi_baslat():
        nonlocal kalan_saniye
        while kalan_saniye > 0 and sure_aktif:
            dk = kalan_saniye // 60
            sn = kalan_saniye % 60
            txt_sure.value = f"⏳ {dk:02d}:{sn:02d}"
            kalan_saniye -= 1
            txt_sure.update()
            await asyncio.sleep(1)
        
        if sure_aktif and kalan_saniye <= 0:
            txt_sure.value = "SÜRE BİTTİ!"
            txt_sure.update()
            # İstersen burada testi otomatik bitirebiliriz

    # --- EKRAN ÇİZİMİ ---
    def ekrani_ciz():
        nonlocal mevcut_index
        ana_liste.controls.clear()
        ana_liste.controls.append(header)
        ana_liste.controls.append(ft.Container(height=20))

        if not sorular:
            ana_liste.controls.append(ft.Text("Soru yok veya internet hatası.", color="red", text_align="center"))
            page.update()
            return

        if mevcut_index < len(sorular):
            soru = sorular[mevcut_index]
            
            # Soru
            ana_liste.controls.append(
                ft.Container(
                    content=ft.Text(soru["metin"], size=18, color="black"),
                    bgcolor="white",
                    padding=15,
                    margin=10,
                    border_radius=10
                )
            )

            # Şıklar
            for secenek in soru["secenekler"]:
                btn = ft.Container(
                    content=ft.Text(secenek, size=16),
                    bgcolor="white",
                    padding=15,
                    margin=ft.margin.symmetric(horizontal=10, vertical=5),
                    border=ft.border.all(1, ANA_RENK),
                    border_radius=8,
                    on_click=lambda e, s=secenek: cevap_ver(e, s),
                    ink=True
                )
                ana_liste.controls.append(btn)

        else:
            # Bitiş
            ana_liste.controls.append(
                ft.Column([
                    ft.Text("TEST TAMAMLANDI", size=30, weight="bold", color=ANA_RENK),
                    ft.Text(f"Toplam Puan: {toplam_puan}", size=25, color="green"),
                    ft.Text(f"Doğru: {dogru_sayisi} | Yanlış: {yanlis_sayisi}", size=18),
                    ft.ElevatedButton("Yenile", on_click=lambda _: page.window_reload(), bgcolor=ANA_RENK, color="white")
                ], horizontal_alignment="center", spacing=10)
            )
            
        page.update()

    def cevap_ver(e, secilen):
        nonlocal toplam_puan, dogru_sayisi, yanlis_sayisi
        dogru_cvp = sorular[mevcut_index].get("cevap")
        
        kutucuk = e.control
        
        puan_d = ayarlar.get("puan_dogru", 5)
        puan_y = ayarlar.get("puan_yanlis", 0)

        if secilen == dogru_cvp:
            dogru_sayisi += 1
            toplam_puan += puan_d
            kutucuk.bgcolor = ft.colors.GREEN_100
            kutucuk.border = ft.border.all(2, "green")
        else:
            yanlis_sayisi += 1
            toplam_puan += puan_y # Eksi puan varsa düşer
            kutucuk.bgcolor = ft.colors.RED_100
            kutucuk.border = ft.border.all(2, "red")

        # Puanı anlık güncelle
        txt_puan.value = f"Puan: {toplam_puan}"
        header.update()
        kutucuk.update()
        
        # Sonraki butonu
        ana_liste.controls.append(
            ft.Container(
                content=ft.ElevatedButton("SONRAKİ >", on_click=lambda _: sonraki(), bgcolor=ANA_RENK, color="white"),
                padding=20, alignment=ft.alignment.center
            )
        )
        page.update()

    def sonraki():
        nonlocal mevcut_index
        mevcut_index += 1
        ekrani_ciz()

    # Başlat
    ekrani_ciz()
    # Eğer süre aktifse sayacı başlat
    if sure_aktif:
        page.run_task(sureyi_baslat)

ft.app(target=main)
