import flet as ft
import json
import urllib.request

def main(page: ft.Page):
    # --- AYARLAR ---
    page.title = "KPSS Online"
    page.padding = 0
    page.bgcolor = "#f0f2f5" # Göz yormayan gri ton
    
    # GÜVENLİ LİSTE YAPISI (Telefonunda çalışan sistem)
    ana_liste = ft.ListView(expand=True, spacing=0, padding=0)
    page.add(ana_liste)

    # --- SORULARI İNTERNETTEN ÇEKME ---
    # Senin verdiğin linki buraya yerleştirdim 👇
    URL = "https://raw.githubusercontent.com/krrr608-cpu/kpss-uygulama/refs/heads/main/sorular.json"
    
    sorular = []
    durum_mesaji = ""
    
    try:
        # İnternete bağlan ve dosyayı oku
        response = urllib.request.urlopen(URL)
        data = response.read().decode('utf-8')
        sorular = json.loads(data)
        durum_mesaji = "Sorular Güncellendi! ✅"
    except Exception as e:
        # İnternet yoksa veya hata varsa
        durum_mesaji = "Bağlantı Hatası! İnterneti kontrol et. ❌"
        print(e)
        sorular = [] 

    mevcut_index = 0
    dogru_sayisi = 0
    yanlis_sayisi = 0

    def arayuzu_ciz():
        nonlocal mevcut_index
        ana_liste.controls.clear()

        # Üst Başlık (Mavi Alan)
        ust_baslik = ft.Container(
            content=ft.Column([
                ft.Text("KPSS Paragraf", size=24, weight="bold", color="white"),
                ft.Text(durum_mesaji, color="white70", size=14)
            ]),
            bgcolor=ft.colors.BLUE_700,
            padding=20,
            width=1000, # Ekrana yayılması için
            border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20)
        )
        ana_liste.controls.append(ust_baslik)
        ana_liste.controls.append(ft.Container(height=20))

        # Eğer soru çekilemediyse veya bittiyse kontrolü
        if len(sorular) == 0:
             uyari = ft.Container(
                 content=ft.Text("Soru bulunamadı veya internet yok.\nLütfen internetini açıp tekrar dene.", text_align="center"),
                 padding=20,
                 alignment=ft.alignment.center
             )
             ana_liste.controls.append(uyari)
             page.update()
             return

        if mevcut_index < len(sorular):
            soru = sorular[mevcut_index]
            
            # Soru Kartı
            soru_karti = ft.Container(
                content=ft.Text(soru["metin"], size=18, color="black87"),
                bgcolor="white",
                padding=20,
                margin=ft.margin.symmetric(horizontal=15),
                border_radius=15,
                shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.1, "black"))
            )
            ana_liste.controls.append(soru_karti)
            ana_liste.controls.append(ft.Container(height=20))

            # Şıklar
            for secenek in soru["secenekler"]:
                btn = ft.Container(
                    content=ft.Text(secenek, size=16, color="black"),
                    bgcolor="white",
                    padding=15,
                    margin=ft.margin.symmetric(horizontal=15, vertical=5),
                    border_radius=10,
                    border=ft.border.all(1, ft.colors.BLUE_100),
                    on_click=lambda e, s=secenek: cevap_kontrol(e, s),
                    ink=True
                )
                ana_liste.controls.append(btn)
            
            ana_liste.controls.append(ft.Container(height=50))

        else:
            # Bitiş Ekranı
            ana_liste.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.EMOJI_EVENTS, size=80, color="orange"),
                        ft.Text("TEST BİTTİ!", size=30, weight="bold", color="blue"),
                        ft.Text(f"Doğru: {dogru_sayisi}", size=22, color="green"),
                        ft.Text(f"Yanlış: {yanlis_sayisi}", size=22, color="red"),
                        ft.ElevatedButton("Yenile / Güncelle", on_click=lambda _: page.window_reload(), bgcolor="blue", color="white")
                    ], horizontal_alignment="center"),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
            
        page.update()

    def cevap_kontrol(e, secilen_cevap):
        nonlocal dogru_sayisi, yanlis_sayisi
        
        # JSON dosyasındaki anahtar isimlerine dikkat (cevap mı dogru_cevap mı?)
        # Senin attığın formatta "cevap" kullanılmış olabilir veya "dogru_cevap".
        # Kodun çökmemesi için ikisini de deniyoruz:
        dogru_cevap = sorular[mevcut_index].get("cevap") or sorular[mevcut_index].get("dogru_cevap")
        
        tiklanan_kutu = e.control
        
        if secilen_cevap == dogru_cevap:
            dogru_sayisi += 1
            tiklanan_kutu.bgcolor = ft.colors.GREEN_100
            tiklanan_kutu.border = ft.border.all(2, ft.colors.GREEN)
        else:
            yanlis_sayisi += 1
            tiklanan_kutu.bgcolor = ft.colors.RED_100
            tiklanan_kutu.border = ft.border.all(2, ft.colors.RED)
        
        tiklanan_kutu.update()
        
        # Sonraki soru butonu
        ana_liste.controls.append(
            ft.Container(
                content=ft.ElevatedButton("SONRAKİ SORU >", on_click=sonraki_soru, bgcolor="blue", color="white"),
                padding=20,
                alignment=ft.alignment.center
            )
        )
        page.update()

    def sonraki_soru(e):
        nonlocal mevcut_index
        mevcut_index += 1
        arayuzu_ciz()

    arayuzu_ciz()

ft.app(target=main)
