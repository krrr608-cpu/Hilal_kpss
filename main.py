import flet as ft
import json
import urllib.request
import asyncio

def main(page: ft.Page):
    # --- VARSAYILAN AYARLAR ---
    DEFAULT_VERI = {
        "ayarlar": {
            "baslik": "KPSS", 
            "tema_rengi": "blue", 
            "arka_plan_rengi": "white"
        },
        "tasarim": {
            "buton_yuvarlakligi": 10,
            "soru_yazi_boyutu": 18,
            "sik_yazi_boyutu": 16,
            "baslik_ortala": True,
            "golge_olsun_mu": False
        },
        "sorular": []
    }
    
    # Güvenli Mod
    page.padding = 0
    page.spacing = 0
    ana_liste = ft.ListView(expand=True, spacing=0, padding=0)
    page.add(ana_liste)

    # --- LİNKİN BURADA ---
    URL = "https://raw.githubusercontent.com/krrr608-cpu/kpss-uygulama/refs/heads/main/sorular.json"
    
    veriler = {}
    durum_mesaji = ""
    
    try:
        response = urllib.request.urlopen(URL, timeout=3)
        data_str = response.read().decode('utf-8')
        veriler = json.loads(data_str)
        page.client_storage.set("kpss_final_v2", data_str)
        durum_mesaji = "Güncel (Online) ✅"
    except:
        durum_mesaji = "Offline Mod 📂"
        if page.client_storage.contains_key("kpss_final_v2"):
            try: veriler = json.loads(page.client_storage.get("kpss_final_v2"))
            except: veriler = DEFAULT_VERI
        else: veriler = DEFAULT_VERI

    # --- VERİLERİ AYIKLA ---
    sorular = veriler.get("sorular", [])
    genel_ayar = {**DEFAULT_VERI["ayarlar"], **veriler.get("ayarlar", {})}
    tasarim = {**DEFAULT_VERI["tasarim"], **veriler.get("tasarim", {})}

    # --- TASARIM DEĞİŞKENLERİ ---
    BASLIK = genel_ayar.get("baslik")
    RENK = genel_ayar.get("tema_rengi")
    BG_RENK = genel_ayar.get("arka_plan_rengi")
    RADIUS = tasarim.get("buton_yuvarlakligi", 10)
    FONT_SORU = tasarim.get("soru_yazi_boyutu", 18)
    FONT_SIK = tasarim.get("sik_yazi_boyutu", 16)
    ORTALA = ft.MainAxisAlignment.CENTER if tasarim.get("baslik_ortala") else ft.MainAxisAlignment.START
    GOLGE = ft.BoxShadow(blur_radius=10, color=ft.colors.with_opacity(0.1, "black")) if tasarim.get("golge_olsun_mu") else None

    page.bgcolor = BG_RENK
    page.title = BASLIK

    # Değişkenler
    mevcut_index = 0
    toplam_puan = 0
    dogru = 0
    yanlis = 0
    kalan_sure = genel_ayar.get("toplam_sure_dakika", 0) * 60
    sure_var = genel_ayar.get("sure_var_mi", False)

    # --- ARAYÜZ ---
    txt_baslik = ft.Text(BASLIK, size=20, weight="bold", color="white")
    txt_bilgi = ft.Text(durum_mesaji, color="white70", size=12)
    txt_puan = ft.Text("Puan: 0", color="white")
    txt_sure = ft.Text("", color="white", weight="bold")

    header = ft.Container(
        content=ft.Column([
            ft.Row([txt_baslik], alignment=ORTALA),
            ft.Row([txt_bilgi], alignment=ORTALA),
            ft.Row([txt_sure, txt_puan], alignment="spaceBetween")
        ]),
        bgcolor=RENK,
        padding=20,
        border_radius=ft.border_radius.only(bottom_left=RADIUS, bottom_right=RADIUS)
    )

    async def zamanlayici():
        nonlocal kalan_sure
        while kalan_sure > 0 and sure_var:
            dk, sn = divmod(kalan_sure, 60)
            txt_sure.value = f"{dk:02d}:{sn:02d}"
            txt_sure.update()
            kalan_sure -= 1
            await asyncio.sleep(1)
        if sure_var and kalan_sure <= 0:
            txt_sure.value = "SÜRE BİTTİ"
            txt_sure.update()

    def ciz():
        nonlocal mevcut_index
        ana_liste.controls.clear()
        ana_liste.controls.append(header)
        ana_liste.controls.append(ft.Container(height=20))

        if not sorular:
            ana_liste.controls.append(ft.Text("Soru Yok", color="red", text_align="center"))
            page.update()
            return

        if mevcut_index < len(sorular):
            soru = sorular[mevcut_index]
            
            # Soru
            ana_liste.controls.append(
                ft.Container(
                    content=ft.Text(soru["metin"], size=FONT_SORU, color="black"),
                    bgcolor="white", padding=20, margin=10, border_radius=RADIUS, shadow=GOLGE
                )
            )

            # Şıkları Gruplamak İçin Kolon
            siklar_grubu = ft.Column()

            for sec in soru["secenekler"]:
                btn_kapsayici = ft.Container(
                    content=ft.Text(sec, size=FONT_SIK, weight="w500", color="black"),
                    bgcolor="white",
                    padding=15,
                    margin=ft.margin.symmetric(horizontal=15, vertical=5),
                    border=ft.border.all(1, RENK),
                    border_radius=RADIUS,
                    # Tıklama olayına hem seçeneği hem de tüm grubun listesini gönderiyoruz
                    on_click=lambda e, s=sec, g=siklar_grubu: cevapla(e, s, g),
                    ink=True
                )
                siklar_grubu.controls.append(btn_kapsayici)
            
            ana_liste.controls.append(siklar_grubu)

        else:
            # Bitiş
            ana_liste.controls.append(
                ft.Column([
                    ft.Text("TEST BİTTİ", size=30, color=RENK, weight="bold"),
                    ft.Text(f"Toplam Puan: {toplam_puan}", size=20),
                    ft.Text(f"Doğru: {dogru} | Yanlış: {yanlis}", size=16),
                    ft.ElevatedButton("Yenile", on_click=lambda _: page.window_reload(), bgcolor=RENK, color="white")
                ], horizontal_alignment="center", spacing=10)
            )
        page.update()

    def cevapla(e, secilen, grup_kolonu):
        nonlocal toplam_puan, dogru, yanlis
        data = sorular[mevcut_index]
        dogru_cvp = data.get("cevap") or data.get("dogru_cevap")
        
        tiklanan_kutu = e.control
        
        # 1. PUANLAMA
        if secilen == dogru_cvp:
            dogru += 1
            toplam_puan += genel_ayar.get("puan_dogru", 5)
            # Doğruysa Yeşil yap
            tiklanan_kutu.bgcolor = ft.colors.GREEN_100
            tiklanan_kutu.border = ft.border.all(2, "green")
            tiklanan_kutu.content.color = "green" # Yazıyı da yeşil yap
        else:
            yanlis += 1
            toplam_puan += genel_ayar.get("puan_yanlis", 0)
            # Yanlışsa Kırmızı yap
            tiklanan_kutu.bgcolor = ft.colors.RED_100
            tiklanan_kutu.border = ft.border.all(2, "red")
            tiklanan_kutu.content.color = "red"

        # 2. KİLİTLEME VE DOĞRUYU GÖSTERME (KRİTİK BÖLÜM)
        for kutu in grup_kolonu.controls:
            kutu.on_click = None  # Tıklama özelliğini iptal et (Kilitle)
            kutu.ink = False      # Dalgalanma efektini kapat
            
            # Eğer kullanıcı yanlışı seçtiyse, doğru olan şıkkı bulup yeşil yakalım
            kutu_icindeki_yazi = kutu.content.value
            if kutu_icindeki_yazi == dogru_cvp:
                kutu.bgcolor = ft.colors.GREEN_50
                kutu.border = ft.border.all(2, "green")
                kutu.content.color = "green"
            
            kutu.update()

        # Puan Güncelle
        txt_puan.value = f"Puan: {toplam_puan}"
        header.update()
        
        # Devam Butonu
        ana_liste.controls.append(
            ft.Container(
                content=ft.ElevatedButton("SONRAKİ >", on_click=lambda _: sonraki(), bgcolor=RENK, color="white"),
                padding=20, alignment=ft.alignment.center
            )
        )
        page.update()

    def sonraki():
        nonlocal mevcut_index
        mevcut_index += 1
        ciz()

    ciz()
    if sure_var:
        page.run_task(zamanlayici)

ft.app(target=main)
