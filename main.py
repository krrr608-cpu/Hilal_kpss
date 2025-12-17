import flet as ft
import json
import time
import asyncio

def main(page: ft.Page):
    page.title = "KPSS Paragraf"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = "auto"

    # Soruları assets klasöründen çekiyoruz
    try:
        with open('assets/sorular.json', 'r', encoding='utf-8') as f:
            sorular = json.load(f)
    except:
        sorular = []
        page.add(ft.Text("HATA: sorular.json dosyası bulunamadı!"))
        return

    mevcut_soru_index = 0
    dogru_sayisi = 0
    yanlis_sayisi = 0
    
    # Görsel Elemanlar
    soru_metni = ft.Text(size=18)
    soru_kutusu = ft.Container(content=soru_metni, padding=15, bgcolor=ft.colors.BLUE_GREY_50, border_radius=10)
    secenekler_column = ft.Column(spacing=10)
    sonuc_metni = ft.Text("", size=16, color="green")
    
    def sonraki_soru(e):
        nonlocal mevcut_soru_index
        mevcut_soru_index += 1
        sonuc_metni.value = ""
        soruyu_goster()

    btn_sonraki = ft.ElevatedButton("Sonraki Soru", on_click=sonraki_soru, visible=False)

    def cevap_kontrol(e):
        nonlocal dogru_sayisi, yanlis_sayisi
        secilen = e.control.data
        dogru = sorular[mevcut_soru_index]["dogru_cevap"]
        
        if secilen == dogru:
            dogru_sayisi += 1
            e.control.bgcolor = "green"
            sonuc_metni.value = "DOĞRU CEVAP!"
            sonuc_metni.color = "green"
        else:
            yanlis_sayisi += 1
            e.control.bgcolor = "red"
            sonuc_metni.value = f"YANLIŞ! Doğru cevap: {dogru}"
            sonuc_metni.color = "red"

        # Şıkları kilitle
        for btn in secenekler_column.controls:
            btn.disabled = True
        
        btn_sonraki.visible = True
        page.update()

    def soruyu_goster():
        if mevcut_soru_index < len(sorular):
            soru = sorular[mevcut_soru_index]
            soru_metni.value = f"Soru {mevcut_soru_index + 1}: {soru['metin']}"
            
            secenekler_column.controls.clear()
            for secenek in soru["secenekler"]:
                btn = ft.ElevatedButton(text=secenek, data=secenek, on_click=cevap_kontrol, width=300)
                secenekler_column.controls.append(btn)
            
            btn_sonraki.visible = False
            page.update()
        else:
            page.clean()
            page.add(ft.Text(f"BİTTİ! Doğru: {dogru_sayisi} Yanlış: {yanlis_sayisi}", size=25))

    page.add(soru_kutusu, ft.Divider(), secenekler_column, sonuc_metni, btn_sonraki)
    soruyu_goster()

ft.app(target=main, assets_dir="assets")