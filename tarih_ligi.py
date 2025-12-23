import streamlit as st
import sqlite3
import pandas as pd
import time
import random
import os
import base64
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="TARİH LİGİ - YKS",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 📍 İÇERİK HARİTASI (27 KONU)
# ==============================================================================
OGM_IMG_BASE = "https://ogmmateryal.eba.gov.tr/kitap/mebi-konu-ozetleri/ayt-tarih/files/mobile/"

KONU_AYARLARI = {
    "1. Tarih ve Zaman": { "ogm_pages": range(9, 14), "wiki": "https://tr.wikipedia.org/wiki/Tarih" },
    "2. İnsanlığın İlk Dönemleri": { "ogm_pages": range(14, 28), "wiki": "https://tr.wikipedia.org/wiki/Tarih%C3%B6ncesi" },
    "3. Orta Çağ’da Dünya": { "ogm_pages": range(28, 36), "wiki": "https://tr.wikipedia.org/wiki/Orta_%C3%87a%C4%9F" },
    "4. İlk ve Orta Çağlarda Türk Dünyası": { "ogm_pages": range(36, 50), "wiki": "https://tr.wikipedia.org/wiki/T%C3%BCrk_tarihi" },
    "5. İslam Medeniyetinin Doğuşu": { "ogm_pages": range(50, 60), "wiki": "https://tr.wikipedia.org/wiki/%C4%B0slam_tarihi" },
    "6. Türklerin İslamiyet’i Kabulü ve İlk Türk İslam Devletleri": { "ogm_pages": range(60, 66), "wiki": "https://tr.wikipedia.org/wiki/Karahanl%C4%B1lar" },
    "7. Yerleşme ve Devletleşme Sürecinde Selçuklu Türkiyesi": { "ogm_pages": range(66, 80), "wiki": "https://tr.wikipedia.org/wiki/Anadolu_Sel%C3%A7uklu_Devleti" },
    "8. Beylikten Devlete Osmanlı Siyaseti": { "ogm_pages": range(80, 87), "wiki": "https://tr.wikipedia.org/wiki/Osmanl%C4%B1_%C4%B0mparatorlu%C4%9Fu_kurulu%C5%9F_d%C3%B6nemi" },
    "9. Devletleşme Sürecinde Savaşçılar ve Askerler": { "ogm_pages": range(87, 90), "wiki": "https://tr.wikipedia.org/wiki/Osmanl%C4%B1_Ordusu" },
    "10. Beylikten Devlete Osmanlı Medeniyeti": { "ogm_pages": range(90, 95), "wiki": "https://tr.wikipedia.org/wiki/Osmanl%C4%B1_k%C3%BClt%C3%BCr%C3%BC" },
    "11. Dünya Gücü Osmanlı": { "ogm_pages": range(95, 107), "wiki": "https://tr.wikipedia.org/wiki/Osmanl%C4%B1_%C4%B0mparatorlu%C4%9Fu_y%C3%BCkselme_d%C3%B6nemi" },
    "12. Sultan ve Osmanlı Merkez Teşkilatı": { "ogm_pages": range(107, 110), "wiki": "https://tr.wikipedia.org/wiki/Osmanl%C4%B1_te%C5%9Fkilat_yap%C4%B1s%C4%B1" },
    "13. Klasik Çağda Osmanlı Toplum Düzeni": { "ogm_pages": range(110, 116), "wiki": "https://tr.wikipedia.org/wiki/Osmanl%C4%B1_toplumu" },
    "14. Değişen Dünya Dengeleri Karşısında Osmanlı Siyaseti": { "ogm_pages": range(116, 125), "wiki": "https://tr.wikipedia.org/wiki/Osmanl%C4%B1_%C4%B0mparatorlu%C4%9Fu_duraklama_d%C3%B6nemi" },
    "15. Değişim Çağında Avrupa ve Osmanlı": { "ogm_pages": range(125, 136), "wiki": "https://tr.wikipedia.org/wiki/Yeni_%C3%87a%C4%9F" },
    "16. Devrimler Çağında Değişen Devlet-Toplum İlişkileri": { "ogm_pages": range(136, 140), "wiki": "https://tr.wikipedia.org/wiki/Frans%C4%B1z_Devrimi" },
    "17. XIX. ve XX. Yüzyılda Değişen Gündelik Hayat": { "ogm_pages": range(140, 144), "wiki": "https://tr.wikipedia.org/wiki/Osmanl%C4%B1_toplumu" },
    "18. Uluslararası İlişkilerde Denge Stratejisi (1774-1914)": { "ogm_pages": range(144, 156), "wiki": "https://tr.wikipedia.org/wiki/Osmanl%C4%B1_%C4%B0mparatorlu%C4%9Fu_da%C4%9F%C4%B1lma_d%C3%B6nemi" },
    "19. Sermaye ve Emek": { "ogm_pages": range(156, 160), "wiki": "https://tr.wikipedia.org/wiki/Sanayi_Devrimi" },
    "20. XX. Yüzyıl Başlarında Osmanlı Devleti ve Dünya": { "ogm_pages": range(160, 179), "wiki": "https://tr.wikipedia.org/wiki/I._D%C3%BCnya_Sava%C5%9F%C4%B1" },
    "21. Milli Mücadele": { "ogm_pages": range(179, 199), "wiki": "https://tr.wikipedia.org/wiki/T%C3%BCrk_Kurtulu%C5%9F_Sava%C5%9F%C4%B1" },
    "22. Atatürkçülük ve Türk İnkılabı": { "ogm_pages": range(199, 210), "wiki": "https://tr.wikipedia.org/wiki/Atat%C3%BCrk_Devrimleri" },
    "23. İki Savaş Arasındaki Dönemde Türkiye ve Dünya": { "ogm_pages": range(210, 217), "wiki": "https://tr.wikipedia.org/wiki/T%C3%BCrkiye_tarihi" },
    "24. II. Dünya Savaşı Sürecinde Türkiye ve Dünya": { "ogm_pages": range(217, 223), "wiki": "https://tr.wikipedia.org/wiki/II._D%C3%BCnya_Sava%C5%9F%C4%B1" },
    "25. II. Dünya Savaşı Sonrasında Türkiye ve Dünya": { "ogm_pages": range(223, 226), "wiki": "https://tr.wikipedia.org/wiki/So%C4%9Fuk_Sava%C5%9F" },
    "26. Toplumsal Devrim Çağında Dünya ve Türkiye": { "ogm_pages": range(226, 235), "wiki": "https://tr.wikipedia.org/wiki/Yak%C4%B1n_%C3%87a%C4%9F" },
    "27. XXI. Yüzyılın Eşiğinde Türkiye ve Dünya": { "ogm_pages": range(235, 246), "wiki": "https://tr.wikipedia.org/wiki/T%C3%BCrkiye" }
}

# ==============================================================================
# 📍 GÜÇLENDİRİLMİŞ WIKIPEDIA MOTORU (TASARIMLI & OTO-SCROLL)
# ==============================================================================
def get_wiki_content_by_url(url):
    try:
        if not url: return "Henüz kaynak eklenmedi."
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return f"""<div style='color:black;text-align:center;'>
            <h3>⚠️ Bağlantı Hatası: {response.status_code}</h3>
            <p><a href='{url}' target='_blank'>Kaynağa gitmek için tıklayın.</a></p>
            </div>"""

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # İçerik Seçimi
        content = soup.find('div', {'id': 'content'}) or \
                  soup.find('div', {'id': 'bodyContent'}) or \
                  soup.find('div', {'id': 'mw-content-text'})
        
        if not content: return "İçerik yapısı okunamadı."
        
        # TEMİZLİK
        for tag in content.find_all(["div", "span", "table"], {'class': ['mw-indicators', 'noprint', 'mw-editsection', 'vector-body-before-content', 'navbox', 'reflist', 'catlinks', 'sidebar', 'mw-jump-link']}): 
            tag.decompose()
        
        site_sub = content.find('div', {'id': 'siteSub'})
        if site_sub: site_sub.decompose()

        cutoff_ids = ['Kaynakça', 'Dış_bağlantılar', 'Ayrıca_bakınız', 'Notlar']
        for c_id in cutoff_ids:
            cutoff_tag = content.find('span', {'id': c_id})
            if cutoff_tag:
                parent = cutoff_tag.find_parent('h2')
                if parent:
                    for sibling in parent.find_next_siblings(): sibling.decompose()
                    parent.decompose()

        # LINK VE RESİM DÜZENLEME
        for a in content.find_all('a', href=True):
            a['target'] = '_blank'
            if a['href'].startswith('/wiki/'): a['href'] = 'https://tr.wikipedia.org' + a['href']
            if 'action=edit' in a['href']: a.decompose()

        for img in content.find_all('img', src=True):
            if img['src'].startswith('//'): img['src'] = 'https:' + img['src']
            if 'width' in img.attrs: del img['width']
            if 'height' in img.attrs: del img['height']

        # CSS (CİLTLİ ANSİKLOPEDİ)
        custom_css_js = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&family=Merriweather:wght@300;700&display=swap');
            
            body { 
                background-color: #fffcec !important; 
                color: #222222 !important; 
                font-family: 'Segoe UI', sans-serif; 
                line-height: 1.6; 
                font-size: 15px;
                
                border: 6px double #800000;
                outline: 3px solid #DAA520;
                outline-offset: 2px;
                padding: 30px;
                margin: 15px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.4);
                border-radius: 4px;
            }
            
            h1, h2, h3, h4 { color: #800000 !important; font-family: 'Merriweather', serif; margin-top: 25px; border-bottom: 2px solid #800000; padding-bottom: 5px; }
            h1 { font-size: 28px; text-align: center; border: none; text-transform: uppercase; letter-spacing: 1px; margin-top:0; }
            a { color: #b8860b !important; text-decoration: none; font-weight: 600; }
            a:hover { text-decoration: underline; color: #800000 !important; }
            
            table { background-color: #fcfcfc !important; color: #333 !important; border: 2px solid #800000 !important; border-radius: 8px; margin: 20px auto !important; width: 100%; border-collapse: collapse; }
            th { background-color: #800000 !important; color: white !important; padding: 8px; font-size: 14px; }
            td { padding: 8px; border-bottom: 1px solid #eee; font-size: 14px; }
            
            .thumb, .tright, .floatright { float: right; margin: 10px 0 10px 20px; clear: right; max-width: 40%; }
            .tleft, .floatleft { float: left; margin: 10px 20px 10px 0; clear: left; max-width: 40%; }
            .thumbinner { background-color: #f8f8f8 !important; border: 1px solid #ccc !important; border-radius: 4px; padding: 6px !important; text-align: center; }
            img { max-width: 100% !important; height: auto !important; border-radius: 2px; }
            .thumbcaption { font-size: 12px; color: #666; margin-top: 4px; line-height: 1.2; }
            
            @media (max-width: 600px) { .thumb, .tright, .tleft { float: none; margin: 10px auto; max-width: 100%; text-align: center; } }
            .mw-parser-output, #content, #bodyContent { background-color: transparent !important; }
            ul li { margin-bottom: 6px; }
        </style>
        <script>
            function forceScroll() { try { var el = window.frameElement; if(el) { el.scrollIntoView({behavior: 'smooth', block: 'center'}); } } catch(e) {} }
            window.onload = forceScroll;
            setTimeout(forceScroll, 300);
        </script>
        """
        return custom_css_js + str(content)
    except Exception as e: return f"Hata: {str(e)}"

# ==============================================================================
# --- VERİTABANI & AYARLAR ---
# ==============================================================================
def get_db():
    conn = sqlite3.connect('tarih_ligi_final_v40.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, xp INTEGER DEFAULT 0, total_questions INTEGER DEFAULT 0, last_seen DATETIME, active_seconds INTEGER DEFAULT 0)''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN active_seconds INTEGER DEFAULT 0")
    except:
        pass

    c.execute('''CREATE TABLE IF NOT EXISTS system (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS module_config (module_key TEXT PRIMARY KEY, title TEXT, icon TEXT, display_order INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS theme_config (setting_key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, receiver TEXT, message TEXT, is_read INTEGER DEFAULT 0, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mistakes (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, topic TEXT, question TEXT, wrong_answer TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    default_theme = {"gold_color": "#DAA520", "app_title": "TARİH LİGİ", "crown_text": "👑 YKS TARİH 👑"}
    for k, v in default_theme.items(): c.execute("INSERT OR IGNORE INTO theme_config (setting_key, value) VALUES (?, ?)", (k, v))
    
    c.execute("DELETE FROM module_config")
    konu_listesi = list(KONU_AYARLARI.keys())
    ikonlar = ["⏳", "🦴", "🏰", "🐺", "🕌", "☪️", "🏹", "🌱", "⚔️", "🎨", "🌍", "👑", "📜", "⚖️", "⚙️", "🇫🇷", "🎩", "🤝", "🏭", "💣", "🇹🇷", "🌞", "🏛️", "☢️", "❄️", "🚀", "🔭"]
    
    for i, konu in enumerate(konu_listesi):
        title_short = konu.split(". ", 1)[1] if ". " in konu else konu
        icon = ikonlar[i % len(ikonlar)]
        c.execute("INSERT OR IGNORE INTO module_config (module_key, title, icon, display_order) VALUES (?, ?, ?, ?)", (konu, title_short, icon, i+1))
        
    conn.commit(); conn.close()

init_db()

# --- FONKSİYONLAR ---
def get_theme():
    conn = get_db(); c = conn.cursor(); c.execute("SELECT setting_key, value FROM theme_config"); rows = c.fetchall(); conn.close()
    return {row["setting_key"]: row["value"] for row in rows}

def get_modules():
    conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM module_config ORDER BY display_order ASC"); rows = c.fetchall(); conn.close(); return rows

def get_sys_val(key, default=""):
    conn = get_db(); c = conn.cursor(); c.execute("SELECT value FROM system WHERE key=?", (key,)); res = c.fetchone(); conn.close(); return res[0] if res else default

def set_sys_val(key, val):
    conn = get_db(); c = conn.cursor(); c.execute("INSERT OR REPLACE INTO system (key, value) VALUES (?, ?)", (key, val)); conn.commit(); conn.close()

def update_user_activity(user):
    conn = get_db(); c = conn.cursor()
    now = datetime.now()
    c.execute("SELECT last_seen, active_seconds FROM users WHERE username = ?", (user,))
    row = c.fetchone()
    if row and row['last_seen']:
        last_seen_time = datetime.strptime(row['last_seen'], "%Y-%m-%d %H:%M:%S")
        time_diff = (now - last_seen_time).total_seconds()
        if time_diff < 600:
            new_active_seconds = row['active_seconds'] + int(time_diff)
            c.execute("UPDATE users SET active_seconds = ? WHERE username = ?", (new_active_seconds, user))
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE users SET last_seen = ? WHERE username = ?", (now_str, user))
    conn.commit(); conn.close()

def get_all_users_status():
    conn = get_db(); 
    try: df = pd.read_sql("SELECT username, xp, last_seen FROM users WHERE username != 'ADMIN' ORDER BY xp DESC", conn)
    except: df = pd.DataFrame(columns=["username", "xp", "last_seen"])
    conn.close(); return df

def send_message(receiver, msg):
    conn = get_db(); c = conn.cursor(); c.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)", ("ADMIN", receiver, msg)); conn.commit(); conn.close()

def get_unread_messages(user):
    conn = get_db(); c = conn.cursor(); c.execute("SELECT id, message FROM messages WHERE receiver=? AND is_read=0", (user,)); msgs = c.fetchall(); conn.close(); return msgs

def mark_message_read(msg_id):
    conn = get_db(); c = conn.cursor(); c.execute("UPDATE messages SET is_read=1 WHERE id=?", (msg_id,)); conn.commit(); conn.close()

def update_user_xp(user, new_xp):
    conn = get_db(); c = conn.cursor(); c.execute("UPDATE users SET xp=? WHERE username=?", (new_xp, user)); conn.commit(); conn.close()

def get_detailed_user_report(user):
    conn = get_db()
    mistakes = pd.read_sql("SELECT topic as 'Konu', question as 'Soru', wrong_answer as 'Verilen Yanlış Cevap', timestamp as 'Tarih' FROM mistakes WHERE username=? ORDER BY id DESC LIMIT 60", conn, params=(user,))
    stats = pd.read_sql("SELECT xp, total_questions, active_seconds FROM users WHERE username=?", conn, params=(user,))
    conn.close()
    return mistakes, stats

def log_attempt(user, topic, q, choice, is_correct):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE users SET total_questions = total_questions + 1 WHERE username = ?", (user,))
    if not is_correct: c.execute("INSERT INTO mistakes (username, topic, question, wrong_answer) VALUES (?, ?, ?, ?)", (user, topic, q, choice))
    conn.commit(); conn.close()

# ==============================================================================
# 📝 SORU HAVUZU (BURAYA YAPIŞTIRACAKSIN)
# ==============================================================================
SORU_HAVUZU = {
   "1. Tarih ve Zaman": [
        {"q": "Tarih biliminin yöntemi, diğer bilim dallarından farklılık gösterir. Tarihçi, geçmişte yaşanmış olayları incelediği için deney ve gözlem yapma şansına sahip değildir. Buna göre tarih biliminin temel yöntemi aşağıdakilerden hangisidir?", "opts": ["Kaynak taraması ve belge incelemesi", "Laboratuvar ortamında analiz", "Formüllerle kesin sonuçlara ulaşma", "Geleceğe yönelik tahminlerde bulunma", "Doğa yasalarını keşfetme"], "a": "Kaynak taraması ve belge incelemesi"},
        {"q": "Tarihi olaylar hakkında bilgi veren her türlü malzemeye 'kaynak' denir. Aşağıdakilerden hangisi 'birinci elden kaynak' grubuna girer?", "opts": ["Ders kitapları", "Ansiklopediler", "İstiklal Madalyası", "Tarihi romanlar", "Araştırma makaleleri"], "a": "İstiklal Madalyası"},
        {"q": "Tarih; 'Olay' ve 'Olgu' olmak üzere iki kavramla açıklanır. Olay; kısa süreli gelişmelerdir. Olgu ise uzun süreli gelişmelerdir. Buna göre hangisi tarihi bir 'olgu'ya örnektir?", "opts": ["Malazgirt Savaşı", "Anadolu'nun Türkleşmesi", "İstanbul'un Fethi", "Cumhuriyetin İlanı", "Lozan Antlaşması"], "a": "Anadolu'nun Türkleşmesi"},
        {"q": "Türklerin tarih boyunca kullandığı takvimlerden hangisi 'Ay Yılı' esaslıdır?", "opts": ["12 Hayvanlı Türk Takvimi", "Celali Takvim", "Rumi Takvim", "Hicri Takvim", "Miladi Takvim"], "a": "Hicri Takvim"},
        {"q": "Olayların zaman sıralamasını inceleyen tarihe yardımcı bilim dalı aşağıdakilerden hangisidir?", "opts": ["Coğrafya", "Kronoloji", "Diplomatik", "Arkeoloji", "Nümizmatik"], "a": "Kronoloji"},
        {"q": "Bir tarihçinin günümüz değer yargılarıyla geçmişi yargılaması hatasına ne ad verilir?", "opts": ["Anakronizm", "Objektiflik", "Terkip", "Tasnif", "Tenkit"], "a": "Anakronizm"},
        {"q": "Osmanlı Devleti'nde mali işlerin düzenlenmesi amacıyla Güneş yılı esas alınarak hazırlanan takvim hangisidir?", "opts": ["Hicri Takvim", "Celali Takvim", "Rumi Takvim", "12 Hayvanlı Takvim", "Miladi Takvim"], "a": "Rumi Takvim"},
        {"q": "Tarih öncesi devirlerin aydınlatılmasında en çok yararlanılan tarihe yardımcı bilim dalı hangisidir?", "opts": ["Paleografya", "Epigrafya", "Arkeoloji", "Nümizmatik", "Diplomatik"], "a": "Arkeoloji"},
        {"q": "Büyük Selçuklu Sultanı Melikşah adına Ömer Hayyam başkanlığındaki heyet tarafından hazırlanan takvim hangisidir?", "opts": ["Celali Takvim", "Rumi Takvim", "Hicri Takvim", "Miladi Takvim", "12 Hayvanlı Takvim"], "a": "Celali Takvim"},
        {"q": "Tarih yazıcılığında 'Hikayeci Tarih' anlayışının temsilcisi ve 'Tarihin Babası' kimdir?", "opts": ["Thukydides", "Herodot", "Halil İnalcık", "Voltaire", "İbn-i Haldun"], "a": "Herodot"},
        {"q": "Eski paraları inceleyerek devletlerin ekonomik güçleri hakkında bilgi veren bilim dalı hangisidir?", "opts": ["Paleografya", "Epigrafya", "Nümizmatik", "Heraldik", "Antropoloji"], "a": "Nümizmatik"},
        {"q": "Tarih araştırmalarında elde edilen verilerin güvenilirliğinin araştırıldığı aşama hangisidir?", "opts": ["Tarama", "Tasnif", "Tahlil", "Tenkit", "Terkip"], "a": "Tenkit"},
        {"q": "Milattan Önceki (M.Ö.) tarihlerle ilgili hangisi yanlıştır?", "opts": ["Sayısal değeri büyük olan tarih daha eskidir", "M.Ö. 2000, M.Ö. 1000'den daha eskidir", "Milat takviminde '0' başlangıçtır", "İki M.Ö. tarih arasındaki fark toplanarak bulunur", "Sayısal değer küçüldükçe günümüze yaklaşılır"], "a": "İki M.Ö. tarih arasındaki fark toplanarak bulunur"},
        {"q": "Orhun Kitabeleri'ni okuyarak Türk tarihi hakkında bilgi edinmemizi sağlayan bilim dalı hangisidir?", "opts": ["Epigrafya", "Nümizmatik", "Antropoloji", "Etnografya", "Heraldik"], "a": "Epigrafya"},
        {"q": "1453 yılı kaçıncı yüzyılın, hangi çeyreğine denk gelir?", "opts": ["14. YY - 2. Çeyrek", "15. YY - 2. Çeyrek", "15. YY - 3. Çeyrek", "14. YY - 3. Çeyrek", "15. YY - 4. Çeyrek"], "a": "15. YY - 3. Çeyrek"},
        {"q": "Hangisi tarihin sınıflandırılmasında 'Zamana Göre Sınıflandırma'ya örnektir?", "opts": ["Orta Çağ Tarihi", "Türkiye Tarihi", "Tıp Tarihi", "Avrupa Tarihi", "Sanat Tarihi"], "a": "Orta Çağ Tarihi"},
        {"q": "Bir olayın tarihi olay niteliği taşıyabilmesi için hangisi gerekli değildir?", "opts": ["İnsan yapımı olması", "Yer ve zamanının belli olması", "Üzerinden zaman geçmesi", "Tarihçi tarafından görülmesi", "Belgeye dayanması"], "a": "Tarihçi tarafından görülmesi"},
        {"q": "Tarihçinin olaylara duygusal yaklaşmayıp, tarafsızlığını korumasına ne ad verilir?", "opts": ["Öznellik", "Nesnellik", "Tutuculuk", "Milliyetçilik", "Anakronizm"], "a": "Nesnellik"},
        {"q": "12 Hayvanlı Türk Takvimi ile ilgili hangisi yanlıştır?", "opts": ["Güneş yılı esaslıdır", "Her yıl bir hayvan ismiyle anılır", "12 yılda bir devreder", "Aylar sayılarla belirtilir", "İslamiyet'ten sonra hazırlanmıştır"], "a": "İslamiyet'ten sonra hazırlanmıştır"},
        {"q": "Geçmişteki insanların kültürlerini, örf ve adetlerini inceleyen bilim dalı hangisidir?", "opts": ["Etnografya", "Paleografya", "Diplomatik", "Heraldik", "Kimya"], "a": "Etnografya"},
        {"q": "Olaylardan ders çıkarmayı amaçlayan 'Öğretici (Pragmatik) Tarih' anlayışının temsilcisi kimdir?", "opts": ["Herodot", "Thukydides", "İbn-i Haldun", "Aristo", "Halil İnalcık"], "a": "Thukydides"},
        {"q": "Hangisi tarihe kaynaklık eden 'sözlü kaynaklar' arasında yer alır?", "opts": ["Fermanlar", "Destanlar", "Heykeller", "Kitabeler", "Paralar"], "a": "Destanlar"},
        {"q": "Dillerin yapısını ve gelişimini inceleyerek tarihe yardımcı olan bilim dalı hangisidir?", "opts": ["Filoloji", "Etnografya", "Paleografya", "Antropoloji", "Heraldik"], "a": "Filoloji"},
        {"q": "Tarihi olayların coğrafi yerinin belirlenmesinde etkili olan bilim dalı hangisidir?", "opts": ["Sosyoloji", "Coğrafya", "Psikoloji", "Felsefe", "Arkeoloji"], "a": "Coğrafya"},
        {"q": "1789 Fransız İhtilali kaçıncı yüzyılın hangi yarısına denk gelir?", "opts": ["17. YY - 2. Yarı", "18. YY - 1. Yarı", "18. YY - 2. Yarı", "19. YY - 1. Yarı", "17. YY - 1. Yarı"], "a": "18. YY - 2. Yarı"},
        {"q": "Resmi belgeleri, fermanları şekil ve içerik bakımından inceleyen bilim dalı hangisidir?", "opts": ["Diplomatik", "Nümizmatik", "Epigrafya", "Antropoloji", "Heraldik"], "a": "Diplomatik"},
        {"q": "Türklerin kullandığı takvimlerden hangisi hem Güneş yılı esaslı olup hem de başlangıç olarak Hicret'i kabul etmiştir?", "opts": ["Hicri Takvim", "Celali Takvim", "Rumi Takvim", "12 Hayvanlı Takvim", "Miladi Takvim"], "a": "Rumi Takvim"},
        {"q": "Hitit krallarının tanrılara hesap vermek amacıyla yazdıkları yıllıklara ne ad verilir?", "opts": ["Kitabe", "Anal", "Şecere", "Menkıbe", "Destan"], "a": "Anal"},
        {"q": "İnsan ırklarını ve kemik yapılarını inceleyerek tarihe ışık tutan bilim dalı hangisidir?", "opts": ["Antropoloji", "Filoloji", "Etnografya", "Sosyoloji", "Paleografya"], "a": "Antropoloji"},
        {"q": "Armaları inceleyen tarihe yardımcı bilim dalı hangisidir?", "opts": ["Sigilografya", "Heraldik", "Epigrafya", "Onomastik", "Toponomi"], "a": "Heraldik"},
        {"q": "Hangisi tarihi olayların özelliklerinden biri değildir?", "opts": ["Tekrarlanamazlar", "Deney yapılamaz", "Yer ve zaman bellidir", "Kesin değişmez kanunları vardır", "Belgeye dayanır"], "a": "Kesin değişmez kanunları vardır"},
        {"q": "Tarihi bilgilerin değişebilirliği ilkesi ne anlama gelir?", "opts": ["Zamanla unutulması", "Yeni belgelerle bilgilerin değişebilmesi", "Keyfi yorumlanması", "Geçmişin değiştirilmesi", "Bilimsel olmaması"], "a": "Yeni belgelerle bilgilerin değişebilmesi"},
        {"q": "Toplumların gelenek ve göreneklerini inceleyen bilim dalı hangisidir?", "opts": ["Etnografya", "Paleografya", "Arkeoloji", "Diplomatik", "Kronoloji"], "a": "Etnografya"},
        {"q": "Mühürleri inceleyen tarihe yardımcı bilim dalı hangisidir?", "opts": ["Sigilografya", "Nümizmatik", "Epigrafya", "Heraldik", "Paleografya"], "a": "Sigilografya"},
        {"q": "Yer adlarını inceleyerek tarihe yardımcı olan bilim dalı hangisidir?", "opts": ["Toponomi", "Antroponomi", "Filoloji", "Diplomatik", "Kronoloji"], "a": "Toponomi"},
        {"q": "Tarih biliminin 'yer ve zaman' göstermesinin en önemli faydası nedir?", "opts": ["Olayı kanıtlamak", "Hikayeleştirmek", "Kahramanları övmek", "Neden-sonuç ilişkisi kurmak", "İlgiyi artırmak"], "a": "Neden-sonuç ilişkisi kurmak"},
        {"q": "Hangisi 'İkinci elden kaynaklar'a örnektir?", "opts": ["O döneme ait para", "Olayın tanığı", "O döneme ait ferman", "Tarihçinin yazdığı ders kitabı", "Arkeolojik buluntu"], "a": "Tarihçinin yazdığı ders kitabı"},
        {"q": "Miladi takvim ile ilgili hangisi doğrudur?", "opts": ["Ay yılı esaslıdır", "Başlangıcı Hicret'tir", "Romalılar ve Papa tarafından geliştirilmiştir", "İlk Türk takvimidir", "Sadece mali işlerde kullanılır"], "a": "Romalılar ve Papa tarafından geliştirilmiştir"},
        {"q": "Karbon-14 metodu tarihçiye hangi konuda yardımcı olur?", "opts": ["Belge tercümesi", "Buluntuların yaşının hesaplanması", "Para analizi", "Yer adı kökeni", "Kültürel yapı"], "a": "Buluntuların yaşının hesaplanması"},
        {"q": "Araştırma basamaklarının sonuncusu, eserin yazıldığı aşama hangisidir?", "opts": ["Terkip", "Tenkit", "Tahlil", "Tasnif", "Tarama"], "a": "Terkip"},
        {"q": "Olayların sebeplerini ve sonuçlarını derinlemesine inceleyen tarih türü hangisidir?", "opts": ["Hikayeci Tarih", "Öğretici Tarih", "Bilimsel (Araştırmacı) Tarih", "Kronik Tarih", "Sosyal Tarih"], "a": "Bilimsel (Araştırmacı) Tarih"},
        {"q": "Osmanlı Devleti'nde resmi tarih yazıcılarına verilen isim nedir?", "opts": ["Şehnameci", "Vakanüvis", "Nişancı", "Reisülküttab", "Kazasker"], "a": "Vakanüvis"},
        {"q": "Aşağıdaki eşleştirmelerden hangisi yanlıştır?", "opts": ["Paleografya - Yazı Bilimi", "Nümizmatik - Para Bilimi", "Epigrafya - Kitabe Bilimi", "Diplomatik - Dinler Tarihi", "Antropoloji - Irk Bilimi"], "a": "Diplomatik - Dinler Tarihi"},
        {"q": "Tarihin 'Konusuna Göre Sınıflandırılması'na hangisi örnektir?", "opts": ["İlk Çağ Tarihi", "Asya Tarihi", "Dinler Tarihi", "19. YY Tarihi", "Anadolu Tarihi"], "a": "Dinler Tarihi"},
        {"q": "Bir olayın 'evrensel' nitelik taşıması ne anlama gelir?", "opts": ["Tek bir milleti ilgilendirmesi", "Çok eski olması", "Tüm insanlığı etkilemesi", "Dini olması", "Yazılı olması"], "a": "Tüm insanlığı etkilemesi"},
        {"q": "Tarih bilimi neden deney ve gözlem metodunu kullanamaz?", "opts": ["Teknoloji yetersizliği", "Olayların tekrarlanamaması", "Yöntem bilinmemesi", "Belge yetersizliği", "Sanat olması"], "a": "Olayların tekrarlanamaması"},
        {"q": "M.S. 2023 yılı kaçıncı yüzyıl ve hangi çeyreğe aittir?", "opts": ["20. YY - 1. Çeyrek", "21. YY - 1. Çeyrek", "21. YY - 4. Çeyrek", "20. YY - 4. Çeyrek", "21. YY - 2. Çeyrek"], "a": "21. YY - 1. Çeyrek"},
        {"q": "Türklerin kullandığı takvimlerden hangisi sadece dini günlerde kullanılır?", "opts": ["Rumi Takvim", "Celali Takvim", "Hicri Takvim", "12 Hayvanlı Takvim", "Miladi Takvim"], "a": "Hicri Takvim"},
        {"q": "Şecere (Soy kütüğü) incelemeleri yapan bilim dalı hangisidir?", "opts": ["Geneoloji", "Paleografya", "Arkeoloji", "Kronoloji", "Diplomatik"], "a": "Geneoloji"},
        {"q": "Atatürk'ün 'Tarih yazmak, tarih yapmak kadar mühimdir...' sözü neyi vurgular?", "opts": ["Öznelliği", "Objektifliği ve Doğruluğu", "Milliyetçiliği", "Edebi dili", "Hızlı yazmayı"], "a": "Objektifliği ve Doğruluğu"}
    ],"2. İnsanlığın İlk Dönemleri": [
        {"q": "Tarih öncesi devirlerin (Taş ve Maden) birbirinden ayrılmasında aşağıdakilerden hangisi temel ölçüt olarak alınmıştır?", "opts": ["Yazının bulunması", "Kullanılan araç ve gereçlerin niteliği", "Dini inanışlar", "Devlet şekilleri", "Paranın kullanımı"], "a": "Kullanılan araç ve gereçlerin niteliği"},
        {"q": "İnsanlık tarihinde ilk yerleşimlerin, tarımsal üretimin ve toplumsal hayatın başladığı dönem hangisidir?", "opts": ["Eski Taş (Paleolitik)", "Orta Taş (Mezolitik)", "Yeni Taş (Neolitik)", "Bakır Çağı", "Demir Çağı"], "a": "Yeni Taş (Neolitik)"},
        {"q": "Anadolu'da bulunan ve 'Dünyanın bilinen en eski tapınak merkezi' olarak kabul edilen yerleşim yeri neresidir?", "opts": ["Çatalhöyük", "Çayönü", "Göbeklitepe", "Alacahöyük", "Truva"], "a": "Göbeklitepe"},
        {"q": "Tarih öncesi dönemlerde ateşin kontrol altına alınması insanlara hangi alanda kolaylık sağlamamıştır?", "opts": ["Isınma", "Aydınlanma", "Yiyecekleri pişirme", "Vahşi hayvanlardan korunma", "Madenleri işleme (Başlangıçta)"], "a": "Madenleri işleme (Başlangıçta)"},
        {"q": "Sümerler tarafından icat edilen ve Tarih Çağları'nın başlamasını sağlayan gelişme nedir?", "opts": ["Tekerlek", "Yazı (Çivi Yazısı)", "Para", "Takvim", "Hukuk kuralları"], "a": "Yazı (Çivi Yazısı)"},
        {"q": "Tarihte bilinen ilk yazılı kanunları yapan Sümer kralı kimdir?", "opts": ["Hammurabi", "Urkagina", "Sargon", "Nabukadnezar", "Ramses"], "a": "Urkagina"},
        {"q": "Anadolu'da kurulan ilk medeniyetlerden biri olan ve başkenti Hattuşaş olan devlet hangisidir?", "opts": ["Hititler", "Frigler", "Lidyalılar", "Urartular", "İyonlar"], "a": "Hititler"},
        {"q": "Parayı icat ederek takas usulüne son veren ve Kral Yolu'nu geliştiren Anadolu uygarlığı hangisidir?", "opts": ["Hititler", "Lidyalılar", "Frigler", "Urartular", "İyonlar"], "a": "Lidyalılar"},
        {"q": "Mısır medeniyetinde firavunların tanrı-kral olarak görülmesi aşağıdakilerden hangisinin göstergesidir?", "opts": ["Demokrasinin geliştiğinin", "Teokratik mutlakiyetin", "Laik devlet yapısının", "Sınıfsız toplumun", "Bilimsel gelişmelerin"], "a": "Teokratik mutlakiyetin"},
        {"q": "İlk Çağ'da Mısır'da kullanılan resim yazısına ne ad verilir?", "opts": ["Çivi yazısı", "Hiyeroglif", "Kiril", "Fenike alfabesi", "Latin"], "a": "Hiyeroglif"},
        {"q": "Tarihte ilk kez 'Güneş Yılı' esaslı takvimi kimler geliştirmiştir?", "opts": ["Sümerler", "Babiller", "Mısırlılar", "Romalılar", "Yunanlılar"], "a": "Mısırlılar"},
        {"q": "Mezopotamya'da kurulan ve tarihin ilk imparatorluğu olarak bilinen devlet hangisidir?", "opts": ["Akadlar", "Sümerler", "Babiller", "Asurlular", "Elamlar"], "a": "Akadlar"},
        {"q": "Hititlerde kraliçeye (Tavananna) de yönetimde söz hakkı tanınması neyin göstergesidir?", "opts": ["Kadınların yönetimde etkili olduğunun", "Demokrasinin tam uygulandığının", "Askeri yapının zayıf olduğunun", "Dini kuralların geçersizliğinin", "Sınıf farkı olmadığının"], "a": "Kadınların yönetimde etkili olduğunun"},
        {"q": "Doğu Anadolu'da kurulan, madencilik ve taş işçiliğinde ileri giden, başkenti Tuşpa olan uygarlık hangisidir?", "opts": ["Hititler", "Frigler", "Urartular", "Lidyalılar", "İyonlar"], "a": "Urartular"},
        {"q": "Friglerin tarımı korumak için sert kanunlar yapması (öküz kesmenin cezasının ölüm olması) neyi gösterir?", "opts": ["Ekonomilerinin tarıma dayalı olduğunu", "Çok savaşçı olduklarını", "Dini inançlarının zayıflığını", "Ticaretle uğraştıklarını", "Denizcilikte geliştiklerini"], "a": "Ekonomilerinin tarıma dayalı olduğunu"},
        {"q": "Tarihte ilk alfabeyi (harf yazısını) bulan uygarlık hangisidir?", "opts": ["Mısırlılar", "Sümerler", "Fenikeliler", "Yunanlılar", "Romalılar"], "a": "Fenikeliler"},
        {"q": "Yunan medeniyetinde şehir devletlerine ne ad verilirdi?", "opts": ["Nom", "Polis", "Site", "Satraplık", "Eyalet"], "a": "Polis"},
        {"q": "İyonların bilim ve felsefede (Özgür Düşünce) ileri gitmelerinin temel nedeni nedir?", "opts": ["Askeri güçleri", "Dini baskı", "Ekonomik refah ve özgür düşünce ortamı", "Krallıkla yönetilmeleri", "Tarım yapmaları"], "a": "Ekonomik refah ve özgür düşünce ortamı"},
        {"q": "Tarihte 'Kadeş Antlaşması' hangi iki devlet arasında imzalanmıştır?", "opts": ["Hitit - Mısır", "Sümer - Akad", "Lidya - Pers", "Asur - Babil", "Yunan - Pers"], "a": "Hitit - Mısır"},
        {"q": "Babil Kralı Hammurabi'nin kanunlarının en belirgin özelliği nedir?", "opts": ["Fidye esasına dayanması", "Kısasa kısas (Sert) olması", "Sadece ticareti düzenlemesi", "Kadınlara geniş haklar vermesi", "Yazılı olmaması"], "a": "Kısasa kısas (Sert) olması"},
        {"q": "Asurluların Anadolu'da kurdukları ticaret kolonileri (Karum) sayesinde Anadolu'ya taşıdıkları en önemli yenilik nedir?", "opts": ["Para", "Yazı", "Tekerlek", "Demir", "Takvim"], "a": "Yazı"},
        {"q": "Anadolu'da tarih çağlarının başlamasını sağlayan uygarlık hangisidir?", "opts": ["Hititler", "Lidyalılar", "Asurlular", "Sümerler", "Mısırlılar"], "a": "Asurlular"},
        {"q": "Hitit krallarının tanrıya hesap vermek amacıyla tuttukları yıllıklara ne ad verilir?", "opts": ["Anal", "Pankuş", "Tavananna", "Fibula", "Tablet"], "a": "Anal"},
        {"q": "Pers İmparatorluğu'nda ülkenin yönetildiği eyalet sistemine ne ad verilirdi?", "opts": ["Nom", "Polis", "Satraplık", "Site", "Dükalık"], "a": "Satraplık"},
        {"q": "İlk Çağ'da tek tanrılı inancı (Musevilik) benimseyen ilk topluluk hangisidir?", "opts": ["İbraniler", "Fenikeliler", "Mısırlılar", "Romalılar", "Babiller"], "a": "İbraniler"},
        {"q": "Hint medeniyetinde toplumu kesin sınıflara ayıran sisteme ne ad verilir?", "opts": ["Kast Sistemi", "Feodalite", "Polis", "Site", "Nom"], "a": "Kast Sistemi"},
        {"q": "Çin medeniyetinin dünya kültürüne en büyük katkıları nelerdir?", "opts": ["Kağıt, Barut, Pusula, Matbaa", "Yazı, Tekerlek", "Para, Alfabe", "Takvim, Güneş Saati", "Demir, Çelik"], "a": "Kağıt, Barut, Pusula, Matbaa"},
        {"q": "İnsanlığın ilk şehir yerleşmesi olarak kabul edilen 'Çatalhöyük' hangi ilimizdedir?", "opts": ["Konya", "Diyarbakır", "Şanlıurfa", "Çorum", "Yozgat"], "a": "Konya"},
        {"q": "İlk tarımsal üretimin başladığı yerlerden biri olan 'Çayönü' hangi ilimizdedir?", "opts": ["Diyarbakır", "Konya", "Şanlıurfa", "Batman", "Mardin"], "a": "Diyarbakır"},
        {"q": "Sümerlerin tapınaklarına verilen ve aynı zamanda okul/rasathane olarak kullanılan yapı nedir?", "opts": ["Piramit", "Ziggurat", "Akropol", "Agora", "Höyük"], "a": "Ziggurat"},
        {"q": "Friglerin bereket tanrıçasına verdikleri isim nedir?", "opts": ["Kibele", "Zeus", "Artemis", "Afrodit", "Hera"], "a": "Kibele"},
        {"q": "Lidyalıların başkenti neresidir?", "opts": ["Hattuşaş", "Gordion", "Sardes", "Tuşpa", "Efes"], "a": "Sardes"},
        {"q": "Urartuların en önemli tanrısı olan savaş tanrısının adı nedir?", "opts": ["Haldi", "Kibele", "Zeus", "Enlil", "Ra"], "a": "Haldi"},
        {"q": "Hititlerde soylulardan oluşan ve kralın yetkilerini kısıtlayabilen meclise ne ad verilir?", "opts": ["Kurultay", "Pankuş", "Senato", "Agora", "Divan"], "a": "Pankuş"},
        {"q": "Mısır'da ölülerin mumyalanması hangi bilim dallarının gelişmesini sağlamıştır?", "opts": ["Tıp ve Eczacılık", "Astronomi", "Matematik", "Hukuk", "Felsefe"], "a": "Tıp ve Eczacılık"},
        {"q": "Mısırlıların Nil Nehri'nin taşma zamanını hesaplarken geliştirdikleri bilim dalı hangisidir?", "opts": ["Astronomi ve Geometri", "Tıp", "Tarih", "Coğrafya", "Kimya"], "a": "Astronomi ve Geometri"},
        {"q": "Asurluların başkenti olup, tarihte bilinen ilk kütüphanenin kurulduğu şehir hangisidir?", "opts": ["Ninova", "Babil", "Uruk", "Lagaş", "Susa"], "a": "Ninova"},
        {"q": "Perslerde kralların gözü kulağı olarak bilinen istihbarat teşkilatına ne ad verilirdi?", "opts": ["Şahgözü", "Satraplık", "Posta", "Karum", "Agora"], "a": "Şahgözü"},
        {"q": "Büyük İskender'in Asya seferi sonucunda Doğu ve Batı kültürlerinin kaynaşmasıyla ortaya çıkan medeniyet nedir?", "opts": ["Helenistik", "Rönesans", "Gotik", "Barok", "Bizans"], "a": "Helenistik"},
        {"q": "Roma İmparatorluğu'nda halkın soylular (Patriciler) ve halk (Plepler) olarak ayrılması neye yol açmıştır?", "opts": ["Sınıf çatışmalarına ve 12 Levha Kanunları'na", "Demokrasinin hemen gelmesine", "Krallığın yıkılmasına", "Ticaretin bitmesine", "Ordunun dağılmasına"], "a": "Sınıf çatışmalarına ve 12 Levha Kanunları'na"},
        {"q": "Orta Asya'da bilinen en eski kültür merkezi hangisidir?", "opts": ["Anav", "Afanesyevo", "Andronovo", "Karasuk", "Tagar"], "a": "Anav"},
        {"q": "Tarih öncesi devirlerde insanların ilk kullandığı maden hangisidir?", "opts": ["Bakır", "Tunç", "Demir", "Altın", "Gümüş"], "a": "Bakır"},
        {"q": "Friglerin 'Fibula' adını verdikleri icat nedir?", "opts": ["Çengelli İğne", "Tekerlek", "Para", "Kiremit", "Yazı"], "a": "Çengelli İğne"},
        {"q": "Mısır ile Hititler arasındaki Kadeş Antlaşması'nın önemi nedir?", "opts": ["Tarihte bilinen ilk yazılı antlaşmadır", "İlk ticaret antlaşmasıdır", "Mısır'ın yıkılışıdır", "Anadolu'nun işgalidir", "Yazının bulunmasıdır"], "a": "Tarihte bilinen ilk yazılı antlaşmadır"},
        {"q": "Sümerlerde site krallarına verilen unvanlar nelerdir?", "opts": ["Ensi veya Patesi", "Firavun", "Şah", "Sultan", "İmparator"], "a": "Ensi veya Patesi"},
        {"q": "İyon şehir devletleri (İzmir, Efes, Milet) hangi yönetim şekliyle yönetilmiştir?", "opts": ["Demokrasi (Şehir Devletleri)", "Mutlakiyet", "Teokrasi", "İmparatorluk", "Feodalite"], "a": "Demokrasi (Şehir Devletleri)"},
        {"q": "Hangi uygarlık 'Tapates' adı verilen halı ve kilimleriyle ünlüdür?", "opts": ["Frigler", "Lidyalılar", "Hititler", "Urartular", "Sümerler"], "a": "Frigler"},
        {"q": "Tarihte ilk kez düzenli orduyu kuran Mezopotamya uygarlığı hangisidir?", "opts": ["Akadlar", "Sümerler", "Babiller", "Elamlar", "Asurlular"], "a": "Akadlar"},
        {"q": "Babil Kulesi ve Babil'in Asma Bahçeleri hangi uygarlığa aittir?", "opts": ["Babiller", "Sümerler", "Akadlar", "Asurlular", "Mısırlılar"], "a": "Babiller"},
        {"q": "Fenikelilerin denizcilikte (kolonicilikte) ilerlemesinin temel sebebi nedir?", "opts": ["Yaşadıkları coğrafyanın tarıma elverişsiz olması", "Savaşçı olmaları", "Çok nüfuslu olmaları", "Dini inançları", "Maden zenginlikleri"], "a": "Yaşadıkları coğrafyanın tarıma elverişsiz olması"}
    ],"3. Orta Çağ’da Dünya": [
        {"q": "Orta Çağ Avrupa'sında siyasi parçalanmışlığın en belirgin göstergesi olan yönetim biçimi hangisidir?", "opts": ["Feodalite (Derebeylik)", "Mutlak Monarşi", "Cumhuriyet", "Teokrasi", "Oligarşi"], "a": "Feodalite (Derebeylik)"},
        {"q": "Kavimler Göçü sonucunda Roma İmparatorluğu'nun ikiye ayrılmasıyla başlayan ve İstanbul'un Fethi ile sona eren çağ hangisidir?", "opts": ["İlk Çağ", "Orta Çağ", "Yeni Çağ", "Yakın Çağ", "Maden Çağı"], "a": "Orta Çağ"},
        {"q": "Orta Çağ Avrupa'sında kilisenin savunduğu, deney ve gözlemi reddeden, dogmatik düşünce sistemine ne ad verilir?", "opts": ["Hümanizm", "Skolastik Düşünce", "Pozitivizm", "Rasyonalizm", "Materyalizm"], "a": "Skolastik Düşünce"},
        {"q": "Feodalite rejiminde toprağa bağlı yaşayan ve hiçbir hakkı olmayan köylü sınıfına ne ad verilir?", "opts": ["Senyör", "Vassal", "Serf", "Burjuva", "Şövalye"], "a": "Serf"},
        {"q": "Orta Çağ'da Avrupa'da soylular ve din adamları dışındaki halkın oluşturduğu, ticaretle uğraşan sınıfa ne ad verilir?", "opts": ["Burjuva", "Serf", "Baron", "Kont", "Dük"], "a": "Burjuva"},
        {"q": "Bizans İmparatoru Jüstinyen'in hukuk alanında yaptığı en önemli çalışma nedir?", "opts": ["12 Levha Kanunları'nı derleyip güncellemek (Jüstinyen Kanunları)", "Magna Carta'yı imzalamak", "Hammurabi Kanunları'nı uygulamak", "Laik hukuk sistemini getirmek", "Demokrasiye geçmek"], "a": "12 Levha Kanunları'nı derleyip güncellemek (Jüstinyen Kanunları)"},
        {"q": "1215 yılında İngiltere Kralı Yurtsuz John ile soylular arasında imzalanan ve kralın yetkilerini ilk kez kısıtlayan belge hangisidir?", "opts": ["Magna Carta", "Nantes Fermanı", "Veda Hutbesi", "İnsan Hakları Bildirgesi", "Kadeş Antlaşması"], "a": "Magna Carta"},
        {"q": "Orta Çağ'da Çin'den başlayıp Orta Asya üzerinden Karadeniz'e ve Akdeniz'e ulaşan tarihi ticaret yolu hangisidir?", "opts": ["Baharat Yolu", "İpek Yolu", "Kürk Yolu", "Kral Yolu", "Amber Yolu"], "a": "İpek Yolu"},
        {"q": "Hindistan'dan başlayıp Mısır ve Suriye limanlarına ulaşan, taşınan ürünlerin niteliğiyle adlandırılan ticaret yolu hangisidir?", "opts": ["İpek Yolu", "Baharat Yolu", "Kürk Yolu", "Kral Yolu", "Makedonya Yolu"], "a": "Baharat Yolu"},
        {"q": "Orta Çağ'da Papa'nın bir kişiyi dinden çıkarma yetkisine ne ad verilir?", "opts": ["Aforoz", "Enterdi", "Endüljans", "Vaftiz", "Günah Çıkarma"], "a": "Aforoz"},
        {"q": "Papa'nın bir kralı veya ülkeyi cezalandırarak oradaki tüm dini faaliyetleri durdurmasına (topluca dinden çıkarmaya) ne ad verilir?", "opts": ["Aforoz", "Enterdi", "Endüljans", "Engizisyon", "Konsil"], "a": "Enterdi"},
        {"q": "Katolik Kilisesi'nin cennetten arsa satma veya günahları affetme karşılığında sattığı belgeye ne ad verilir?", "opts": ["Endüljans", "Aforoz", "Enterdi", "Ferman", "Berat"], "a": "Endüljans"},
        {"q": "Orta Çağ'da Katolik Kilisesi'nin yargılama yetkisini kullandığı mahkemelere ne ad verilir?", "opts": ["Engizisyon", "Kadı", "Divan", "Senato", "Kurultay"], "a": "Engizisyon"},
        {"q": "Hristiyan dünyasının İslam dünyası üzerine düzenlediği, 11. yüzyılda başlayıp 13. yüzyıla kadar süren seferlere ne ad verilir?", "opts": ["Coğrafi Keşifler", "Rönesans", "Haçlı Seferleri", "Yüzyıl Savaşları", "Otuz Yıl Savaşları"], "a": "Haçlı Seferleri"},
        {"q": "Aşağıdakilerden hangisi Haçlı Seferleri'nin dini nedenlerinden biridir?", "opts": ["Kudüs'ü Müslümanlardan geri almak", "Doğunun zenginliklerine ulaşmak", "Derebeylerin macera arayışı", "Ticaret yollarını ele geçirmek", "Kralların güç kazanma isteği"], "a": "Kudüs'ü Müslümanlardan geri almak"},
        {"q": "Haçlı Seferleri sonucunda Avrupa'da hangi siyasi rejim zayıflamaya başlamıştır?", "opts": ["Feodalite", "Mutlakiyet", "Cumhuriyet", "Demokrasi", "Teokrasi"], "a": "Feodalite"},
        {"q": "Haçlı Seferleri sırasında Müslümanlardan öğrenilen pusula, barut, kağıt ve matbaa Avrupa'da neye zemin hazırlamıştır?", "opts": ["Feodalitenin güçlenmesine", "Karanlık Çağ'ın devamına", "Kültürel ve bilimsel gelişmelere (Rönesans)", "Kilisenin otoritesinin artmasına", "Tarımın gelişmesine"], "a": "Kültürel ve bilimsel gelişmelere (Rönesans)"},
        {"q": "İngiltere ve Fransa arasında 1337-1453 yılları arasında süren ve Fransa'nın galibiyetiyle biten savaşlar hangisidir?", "opts": ["Yüzyıl Savaşları", "Güller Savaşı", "Otuz Yıl Savaşları", "Yedi Yıl Savaşları", "Haçlı Seferleri"], "a": "Yüzyıl Savaşları"},
        {"q": "Orta Çağ'da İran coğrafyasında hüküm süren ve Hz. Ömer döneminde İslam orduları tarafından yıkılan devlet hangisidir?", "opts": ["Sasaniler", "Bizans", "Göktürkler", "Akhunlar", "Persler"], "a": "Sasaniler"},
        {"q": "Orta Çağ'da Türk devletlerinde, hükümdarın yetkiyi Tanrı'dan aldığına inanılan anlayışa ne ad verilir?", "opts": ["Kut", "Töre", "Kurultay", "Toy", "Yargu"], "a": "Kut"},
        {"q": "Bizans İmparatorluğu'nda (Doğu Roma) spor müsabakaları yüzünden çıkan ve İmparator Jüstinyen'i zor durumda bırakan isyan hangisidir?", "opts": ["Nika Ayaklanması", "Celali İsyanları", "Babai İsyanı", "Mazin İsyanı", "Spartaküs İsyanı"], "a": "Nika Ayaklanması"},
        {"q": "Feodalitenin ortaya çıkmasında etkili olan en önemli olay hangisidir?", "opts": ["Kavimler Göçü", "Haçlı Seferleri", "Yüzyıl Savaşları", "Magna Carta", "İstanbul'un Fethi"], "a": "Kavimler Göçü"},
        {"q": "Orta Çağ Avrupa'sında eğitimin kilisenin kontrolünde olması neyi engellemiştir?", "opts": ["Ticaretin gelişmesini", "Özgür düşünce ve bilimsel gelişmeyi", "Savaşları", "Nüfus artışını", "Şehirleşmeyi"], "a": "Özgür düşünce ve bilimsel gelişmeyi"},
        {"q": "İpek Yolu üzerinde tüccarların konaklaması ve güvenliği için yapılan yapılara ne ad verilir?", "opts": ["Kervansaray", "Medrese", "Külliye", "Bedesten", "Arasta"], "a": "Kervansaray"},
        {"q": "Orta Çağ'da Avrupa'da nüfusun büyük bir kısmının ölümüne yol açan salgın hastalık hangisidir?", "opts": ["Veba (Kara Ölüm)", "Çiçek", "Sıtma", "Kolera", "İspanyol Gribi"], "a": "Veba (Kara Ölüm)"},
        {"q": "Magna Carta'nın dünya tarihindeki en büyük önemi nedir?", "opts": ["Anayasal düzene geçişin ilk adımı olması", "Feodaliteyi güçlendirmesi", "Kiliseyi kapatması", "Ticaret yollarını değiştirmesi", "Savaşları bitirmesi"], "a": "Anayasal düzene geçişin ilk adımı olması"},
        {"q": "Orta Çağ'da esnaf ve zanaatkarların kurduğu mesleki dayanışma örgütüne ne ad verilir?", "opts": ["Lonca", "Feodalite", "Burjuva", "Kast", "Senato"], "a": "Lonca"},
        {"q": "Aşağıdakilerden hangisi Feodalitenin özelliklerinden biri değildir?", "opts": ["Merkezi krallıkların zayıf olması", "Toprağa dayalı ekonomi", "Sınıflı toplum yapısı", "Kapalı tarım ekonomisi", "Güçlü merkezi otorite"], "a": "Güçlü merkezi otorite"},
        {"q": "Orta Çağ'da Moğol İmparatorluğu'nu kurarak dünyanın en geniş bitişik kara imparatorluğunu oluşturan lider kimdir?", "opts": ["Cengiz Han", "Timur", "Attila", "Balamir", "Kubilay Han"], "a": "Cengiz Han"},
        {"q": "Sasanilerde krala verilen unvan nedir?", "opts": ["Şehinşah", "Firavun", "Sezar", "Sultan", "Kağan"], "a": "Şehinşah"},
        {"q": "Orta Çağ'da Avrupa'nın siyasi yapısını belirleyen en temel unsur nedir?", "opts": ["Toprak mülkiyeti", "Ticaret", "Sanayi", "Denizcilik", "Madencilik"], "a": "Toprak mülkiyeti"},
        {"q": "Batı Roma İmparatorluğu'nun yıkılış tarihi (Orta Çağ'ın başlangıcı sayılan olaylardan biri) nedir?", "opts": ["375", "395", "476", "1071", "1453"], "a": "476"},
        {"q": "1054 yılında Hristiyan dünyasının Katolik ve Ortodoks olarak ikiye ayrılmasına ne ad verilir?", "opts": ["Büyük Şizma (Ayrılık)", "Reform", "Rönesans", "Engizisyon", "Haçlı Seferi"], "a": "Büyük Şizma (Ayrılık)"},
        {"q": "Bizans İmparatorluğu'nun başkenti neresidir?", "opts": ["Konstantinopolis (İstanbul)", "Roma", "Atina", "Venedik", "İskenderiye"], "a": "Konstantinopolis (İstanbul)"},
        {"q": "Orta Çağ'da 'Kürk Yolu' hangi coğrafyadan geçmektedir?", "opts": ["Karadeniz'in kuzeyi (Rusya)", "Hindistan", "Mısır", "Anadolu", "İran"], "a": "Karadeniz'in kuzeyi (Rusya)"},
        {"q": "Feodal sistemde senyörün (soylunun) koruması altındaki kişiye ne ad verilir?", "opts": ["Vassal", "Süzeren", "Kral", "Rahip", "Burjuva"], "a": "Vassal"},
        {"q": "Orta Çağ'da İslam dünyasında bilim ve felsefenin zirveye ulaştığı döneme ne ad verilir?", "opts": ["İslam'ın Altın Çağı", "Karanlık Çağ", "Rönesans", "Aydınlanma Çağı", "Reform"], "a": "İslam'ın Altın Çağı"},
        {"q": "Yüzyıl Savaşları'nda İngilizlere karşı mücadele eden ve Fransa'nın milli kahramanı sayılan kadın savaşçı kimdir?", "opts": ["Jeanne d'Arc", "Boudicca", "I. Elizabeth", "Marie Curie", "Kleopatra"], "a": "Jeanne d'Arc"},
        {"q": "Orta Çağ'da Avrupa'da kralların otoritelerini artırmalarını sağlayan teknolojik gelişme nedir?", "opts": ["Top ve barutun kullanılması", "Matbaanın icadı", "Pusulanın bulunması", "Buharlı makine", "Kağıt üretimi"], "a": "Top ve barutun kullanılması"},
        {"q": "Bizans İmparatorluğu'nda eyalet valilerine verilen isim nedir?", "opts": ["Tekfur", "Satrap", "Vali", "Bey", "Dük"], "a": "Tekfur"},
        {"q": "Orta Çağ'da Hindistan'da uygulanan ve sınıflar arası geçişin yasak olduğu sistem hangisidir?", "opts": ["Kast Sistemi", "Feodalite", "Lonca", "Satraplık", "Demokrasi"], "a": "Kast Sistemi"},
        {"q": "Aşağıdakilerden hangisi Kavimler Göçü'nün sonuçlarından biri değildir?", "opts": ["Roma İmparatorluğu ikiye ayrıldı", "Avrupa'nın etnik yapısı değişti", "Feodalite ortaya çıktı", "Skolastik düşünce yayıldı", "Barut bulundu"], "a": "Barut bulundu"},
        {"q": "Vikingler Orta Çağ'da hangi bölgeden çıkarak Avrupa'ya akınlar düzenlemişlerdir?", "opts": ["İskandinavya", "Balkanlar", "Anadolu", "Kuzey Afrika", "İber Yarımadası"], "a": "İskandinavya"},
        {"q": "Orta Çağ'da şehirlerde yaşayan, ticaret ve zanaatla uğraşan, zamanla zenginleşen sınıfa ne ad verilir?", "opts": ["Burjuva", "Aristokrat", "Ruhban", "Köylü", "Serf"], "a": "Burjuva"},
        {"q": "Jüstinyen Kanunları hangi hukuk sisteminin temelini oluşturur?", "opts": ["Roma Hukuku (Kara Avrupası)", "İslam Hukuku", "Türk Töresi", "İngiliz Hukuku", "Hammurabi Kanunları"], "a": "Roma Hukuku (Kara Avrupası)"},
        {"q": "Orta Çağ İngiltere'sinde Lordlar Kamarası ve Avam Kamarası'nın kurulması neyin başlangıcı sayılır?", "opts": ["Parlamenter sistemin", "Mutlakiyetin", "Teokrasinin", "Diktatörlüğün", "Sömürgeciliğin"], "a": "Parlamenter sistemin"},
        {"q": "Haçlı Seferleri'nin ekonomik sonucu aşağıdakilerden hangisidir?", "opts": ["Akdeniz limanları önem kazandı", "Kudüs el değiştirdi", "Kilise güç kaybetti", "Feodalite zayıfladı", "Krallar güçlendi"], "a": "Akdeniz limanları önem kazandı"},
        {"q": "Orta Çağ'da 'Süzeren' kime denir?", "opts": ["Koruyan (Üst Soylu)", "Korunan (Vassal)", "Köylü", "Tüccar", "Rahip"], "a": "Koruyan (Üst Soylu)"},
        {"q": "Hangi gelişme Orta Çağ'ın sonu, Yeni Çağ'ın başlangıcı olarak kabul edilir?", "opts": ["İstanbul'un Fethi (1453)", "Kavimler Göçü", "Magna Carta", "Yüzyıl Savaşları", "Roma'nın yıkılışı"], "a": "İstanbul'un Fethi (1453)"},
        {"q": "Sasanilerin İpek Yolu ticaretinde Bizans ile rekabet etmesi, Bizans'ın hangi devletle ittifak yapmasına neden olmuştur?", "opts": ["Göktürkler", "Çin", "Hint", "Avarlar", "Hunlar"], "a": "Göktürkler"}
    ],"4. İlk ve Orta Çağlarda Türk Dünyası": [
        {"q": "Tarihte bilinen ilk Türk devleti aşağıdakilerden hangisidir?", "opts": ["Asya Hun", "Göktürk", "Uygur", "Avar", "Kutluk"], "a": "Asya Hun"},
        {"q": "Türk adını ilk kez resmi bir devlet adı olarak kullanan devlet hangisidir?", "opts": ["I. Kök Türk", "Asya Hun", "Uygur", "Hazar", "Osmanlı"], "a": "I. Kök Türk"},
        {"q": "Türk ordusunda 'Onlu Sistemi' kurarak dünya ordularına örnek olan hükümdar kimdir?", "opts": ["Mete Han", "Teoman", "Attila", "Bumin Kağan", "Bilge Kağan"], "a": "Mete Han"},
        {"q": "Tarihte yerleşik hayata geçen ilk Türk devleti hangisidir?", "opts": ["Uygurlar", "Hunlar", "Göktürkler", "İskitler", "Hazarlar"], "a": "Uygurlar"},
        {"q": "İlk Türk devletlerinde devlet işlerinin görüşülüp karara bağlandığı meclise ne ad verilir?", "opts": ["Kurultay (Toy)", "Divan", "Pankuş", "Senato", "Lonca"], "a": "Kurultay (Toy)"},
        {"q": "Türklerde hükümdara yönetme yetkisinin Tanrı tarafından verildiğine inanılan anlayışa ne ad verilir?", "opts": ["Kut", "Töre", "Yargu", "Toy", "Balg"], "a": "Kut"},
        {"q": "İslamiyet öncesi Türklerde ölen kişinin mezarının başına hayattayken öldürdüğü düşman sayısı kadar dikilen taşa ne ad verilir?", "opts": ["Balbal", "Kurgan", "Bengütaş", "Stel", "Oba"], "a": "Balbal"},
        {"q": "Orhun Abideleri (Göktürk Kitabeleri) hangi Türk devleti döneminde dikilmiştir?", "opts": ["II. Kök Türk (Kutluk)", "I. Kök Türk", "Uygur", "Asya Hun", "Kırgız"], "a": "II. Kök Türk (Kutluk)"},
        {"q": "Aşağıdakilerden hangisi Kavimler Göçü'nü başlatan Türk topluluğudur?", "opts": ["Hunlar", "Avarlar", "Macarlar", "Peçenekler", "Oğuzlar"], "a": "Hunlar"},
        {"q": "Uygurların Maniheizm dinini kabul etmesinin en önemli toplumsal sonucu nedir?", "opts": ["Yerleşik hayata geçmeleri ve savaşçılık özelliklerinin zayıflaması", "Ordu sisteminin güçlenmesi", "Ticaretin zayıflaması", "Göçebe yaşamın artması", "Hayvancılığın gelişmesi"], "a": "Yerleşik hayata geçmeleri ve savaşçılık özelliklerinin zayıflaması"},
        {"q": "Türk tarihinde 'Tanrının Kırbacı' olarak bilinen ve Avrupa Hun Devleti'nin en parlak dönemini yaşatan hükümdar kimdir?", "opts": ["Attila", "Balamir", "Uldız", "Rua", "Mete Han"], "a": "Attila"},
        {"q": "Tarihte Museviliği kabul eden ilk ve tek Türk devleti hangisidir?", "opts": ["Hazarlar", "Bulgarlar", "Macarlar", "Avarlar", "Peçenekler"], "a": "Hazarlar"},
        {"q": "İlk Türk devletlerinde yazısız hukuk kurallarına ne ad verilir?", "opts": ["Töre", "Yasa", "Şeriat", "Kanunname", "Yargu"], "a": "Töre"},
        {"q": "Türklerin kullandığı ilk milli alfabe hangisidir?", "opts": ["Göktürk (Orhun) Alfabesi", "Uygur Alfabesi", "Sogd Alfabesi", "Kiril Alfabesi", "Arap Alfabesi"], "a": "Göktürk (Orhun) Alfabesi"},
        {"q": "Aşağıdakilerden hangisi Türklerin tarih boyunca kullandığı takvimlerden biridir?", "opts": ["12 Hayvanlı Türk Takvimi", "Maya Takvimi", "Aztek Takvimi", "Çin Takvimi", "Sümer Takvimi"], "a": "12 Hayvanlı Türk Takvimi"},
        {"q": "Malazgirt Savaşı'nda taraf değiştirerek Selçukluların kazanmasını sağlayan Türk boyu hangisidir?", "opts": ["Peçenekler", "Kumanlar", "Avarlar", "Hazarlar", "Karluklar"], "a": "Peçenekler"},
        {"q": "İstanbul'u kuşatan ilk Türk devleti hangisidir?", "opts": ["Avarlar", "Hunlar", "Bulgarlar", "Peçenekler", "Çaka Beyliği"], "a": "Avarlar"},
        {"q": "Türk adının anlamı Çin kaynaklarında nasıl geçer?", "opts": ["Miğfer", "Güçlü", "Türeyen", "Kanun Nizam Sahibi", "Olgunluk Çağı"], "a": "Miğfer"},
        {"q": "Türk adının anlamı Ziya Gökalp'e göre nedir?", "opts": ["Töreli (Kanun ve Nizam Sahibi)", "Güçlü", "Miğfer", "Türeyen", "Deniz kıyısındaki adam"], "a": "Töreli (Kanun ve Nizam Sahibi)"},
        {"q": "Asya Hun Devleti'nin kurucusu kimdir?", "opts": ["Teoman", "Mete Han", "Kişok", "Bumin Kağan", "Kutluk Kağan"], "a": "Teoman"},
        {"q": "İkili teşkilat sisteminde doğuyu Hakan yönetirken, batıyı yöneten kardeşe ne unvan verilirdi?", "opts": ["Yabgu", "Tigin", "Şad", "Ayguci", "Toygun"], "a": "Yabgu"},
        {"q": "Kürşat Ayaklanması'nın Türk tarihindeki önemi nedir?", "opts": ["İlk bağımsızlık isyanı olması", "İlk yerleşik hayata geçiş", "İlk yazılı eserlerin verilmesi", "İslamiyet'in kabulü", "Avrupa'ya göç edilmesi"], "a": "İlk bağımsızlık isyanı olması"},
        {"q": "Uygurların kağıt ve matbaayı kullanmaları neyin göstergesidir?", "opts": ["Kültürel etkileşime açık olduklarının", "Savaşçı olduklarının", "Göçebe olduklarının", "Tek tanrılı dine inandıklarının", "Ticaret yapmadıklarının"], "a": "Kültürel etkileşime açık olduklarının"},
        {"q": "Orhun Kitabeleri'nde 'Aç milleti doyurdum, çıplak milleti giydirdim' ifadesi hangi devlet anlayışını gösterir?", "opts": ["Sosyal Devlet", "Laik Devlet", "Teokratik Devlet", "Mutlakiyetçi Devlet", "Federal Devlet"], "a": "Sosyal Devlet"},
        {"q": "Kendi adına para bastıran ilk Türk hükümdarı (Türgişler) kimdir?", "opts": ["Baga Tarkan", "Mete Han", "Bilge Kağan", "Attila", "Teoman"], "a": "Baga Tarkan"},
        {"q": "Aşağıdaki Türk topluluklarından hangisi Hristiyanlığı kabul ederek benliğini kaybetmiştir?", "opts": ["Tuna Bulgarları", "İtil Bulgarları", "Karluklar", "Oğuzlar", "Kırgızlar"], "a": "Tuna Bulgarları"},
        {"q": "İlk Türk devletlerinde ölülerin gömüldüğü mezara ne ad verilir?", "opts": ["Kurgan", "Balbal", "Uçmağ", "Tamu", "Yuğ"], "a": "Kurgan"},
        {"q": "Türklerde cenaze törenine ne ad verilir?", "opts": ["Yuğ", "Şölen", "Toy", "Sagu", "Koşuk"], "a": "Yuğ"},
        {"q": "İlk Türk devletlerinde hükümet (bakanlar kurulu) anlamına gelen kavram nedir?", "opts": ["Ayuki", "Ayguci", "Buyruk", "Tigin", "Bitikçi"], "a": "Ayuki"},
        {"q": "Mısır'da kurulan ilk Türk devleti hangisidir?", "opts": ["Tolunoğulları", "İhşidler", "Eyyubiler", "Memlükler", "Osmanlılar"], "a": "Tolunoğulları"},
        {"q": "Türklerin ana yurdu neresidir?", "opts": ["Orta Asya", "Anadolu", "Balkanlar", "Mezopotamya", "Kafkasya"], "a": "Orta Asya"},
        {"q": "Ergenekon ve Bozkurt destanları hangi Türk devletine aittir?", "opts": ["Göktürkler", "Hunlar", "Uygurlar", "İskitler", "Kırgızlar"], "a": "Göktürkler"},
        {"q": "Manas Destanı hangi Türk topluluğuna aittir?", "opts": ["Kırgızlar", "Kazaklar", "Özbekler", "Uygurlar", "Oğuzlar"], "a": "Kırgızlar"},
        {"q": "Oğuz Kağan Destanı'nda anlatılan hükümdarın kim olduğu düşünülmektedir?", "opts": ["Mete Han", "Teoman", "Attila", "Bumin Kağan", "Alper Tunga"], "a": "Mete Han"},
        {"q": "Alper Tunga ve Şu destanları hangi Türk topluluğuna aittir?", "opts": ["İskitler (Sakalar)", "Hunlar", "Göktürkler", "Uygurlar", "Avarlar"], "a": "İskitler (Sakalar)"},
        {"q": "Bilinen ilk Türk kadın hükümdar (İskitler) kimdir?", "opts": ["Tomris Hatun", "Altuncan Hatun", "Hayme Ana", "Terken Hatun", "Gevher Nesibe"], "a": "Tomris Hatun"},
        {"q": "Tarihte ilk kez bütün Türk boylarını tek bayrak altında toplayan hükümdar kimdir?", "opts": ["Mete Han", "Teoman", "Bumin Kağan", "İlteriş Kağan", "Mokan Kağan"], "a": "Mete Han"},
        {"q": "Uygurların sanat eserlerinde (fresk, minyatür) dini motiflerin ağır basmasının sebebi nedir?", "opts": ["Maniheizm ve Budizm'in etkisi", "İslamiyet'in etkisi", "Savaşçı olmaları", "Göçebe olmaları", "Ticaret yapmaları"], "a": "Maniheizm ve Budizm'in etkisi"},
        {"q": "Rusların meşhur 'İgor Destanı'na konu olan Türk boyu hangisidir?", "opts": ["Kumanlar (Kıpçaklar)", "Peçenekler", "Uzlar", "Avarlar", "Hazarlar"], "a": "Kumanlar (Kıpçaklar)"},
        {"q": "Hazarların Müslümanlar, Hristiyanlar ve Musevileri bir arada yaşatması tarihte ne olarak adlandırılır?", "opts": ["Hazar Barış Çağı (Pax Hazaria)", "Türk Cihan Hakimiyeti", "Kavimler Göçü", "Rönesans", "Altın Çağ"], "a": "Hazar Barış Çağı (Pax Hazaria)"},
        {"q": "Orta Asya'da kurulan son büyük Türk devleti hangisidir?", "opts": ["Kırgızlar", "Uygurlar", "Göktürkler", "Hunlar", "Türgişler"], "a": "Kırgızlar"},
        {"q": "İslamiyet'i kabul eden ilk Türk boyu hangisidir?", "opts": ["Karluklar", "Oğuzlar", "Kıpçaklar", "Yağma", "Çiğil"], "a": "Karluklar"},
        {"q": "Türklerde 'Cihan Hakimiyeti' anlayışı neyi ifade eder?", "opts": ["Güneşin doğduğu yerden battığı yere kadar dünyayı yönetme", "Sadece Türkleri yönetme", "Anadolu'ya yerleşme", "Çin'i vergiye bağlama", "Dini yayma"], "a": "Güneşin doğduğu yerden battığı yere kadar dünyayı yönetme"},
        {"q": "Eski Türklerde hekimlere (doktorlara) ne ad verilirdi?", "opts": ["Otacı (Emçi)", "Baksı", "Kam", "Yarguci", "Bitikçi"], "a": "Otacı (Emçi)"},
        {"q": "Türk ordusunun temelini oluşturan birliklere ne ad verilir?", "opts": ["Süvari (Atlı Birlik)", "Piyade", "Donanma", "Topçu", "Lağımcı"], "a": "Süvari (Atlı Birlik)"},
        {"q": "Kutluk (II. Göktürk) Devleti'nin kurucusu ve 'İlteriş' (Devleti derleyen toplayan) unvanını alan hükümdar kimdir?", "opts": ["Kutluk Kağan", "Kapgan Kağan", "Bilge Kağan", "Bumin Kağan", "İstemi Yabgu"], "a": "Kutluk Kağan"},
        {"q": "Göktürkler ile Bizans'ın Sasanilere karşı ittifak yapması neyin göstergesidir?", "opts": ["Diplomasinin kullanıldığının", "Savaşçı olmadıklarının", "Dini birlikteliğin", "Çin korkusunun", "Anadolu'ya yerleşme isteğinin"], "a": "Diplomasinin kullanıldığının"},
        {"q": "Uygurlarda fresk (duvar resmi) sanatının gelişmesi neyin kanıtıdır?", "opts": ["Mimari yapıların (Tapınak/Ev) olduğunun", "Savaşçılığın", "Hayvancılığın", "Göçebeliğin", "Sözlü kültürün"], "a": "Mimari yapıların (Tapınak/Ev) olduğunun"},
        {"q": "Eski Türklerde 'Nevruz' neyi ifade eder?", "opts": ["Baharın gelişini (Yeni Gün)", "Savaş hazırlığını", "Hasat zamanını", "Kışın gelişini", "Hükümdarın tahta çıkışını"], "a": "Baharın gelişini (Yeni Gün)"},
        {"q": "Türklerde 'Veraset Sistemi'nin (Ülke hanedanın ortak malıdır) en olumsuz sonucu nedir?", "opts": ["Taht kavgaları ve devletlerin kısa ömürlü olması", "Merkezi otoritenin güçlenmesi", "Demokrasinin gelişmesi", "Ordunun güçlenmesi", "Halkın zenginleşmesi"], "a": "Taht kavgaları ve devletlerin kısa ömürlü olması"}
    ],

    "5. İslam Medeniyetinin Doğuşu": [
        {"q": "İslamiyet öncesi Arap Yarımadası'nda yaşanan siyasi birliğin olmadığı, putperestliğin yaygın olduğu döneme ne ad verilir?", "opts": ["Cahiliye Dönemi", "Altın Çağ", "Lale Devri", "Fetret Devri", "Asr-ı Saadet"], "a": "Cahiliye Dönemi"},
        {"q": "Müslümanların Mekkeli müşriklerin baskısından kurtulmak için yaptıkları ilk hicret (göç) nereye olmuştur?", "opts": ["Habeşistan", "Medine", "Taif", "Şam", "Yemen"], "a": "Habeşistan"},
        {"q": "622 yılında Mekke'den Medine'ye yapılan Hicret'in en önemli siyasi sonucu nedir?", "opts": ["Medine İslam Devleti'nin temellerinin atılması", "Ticaretin artması", "Savaşların bitmesi", "Putperestliğin sona ermesi", "Kabe'nin yıkılması"], "a": "Medine İslam Devleti'nin temellerinin atılması"},
        {"q": "Müslümanların Mekkeli müşriklere karşı kazandığı ilk askeri zafer hangisidir?", "opts": ["Bedir Savaşı", "Uhud Savaşı", "Hendek Savaşı", "Mute Savaşı", "Huneyn Savaşı"], "a": "Bedir Savaşı"},
        {"q": "Bedir Savaşı sonunda ganimetlerin paylaşılması ve esirlerin okuma-yazma öğretmesi karşılığında serbest bırakılması neye örnektir?", "opts": ["İslam Savaş Hukuku'nun oluşmasına ve eğitime verilen öneme", "Arapların zenginleşmesine", "Savaşların sona ermesine", "Medine'nin başkent olmasına", "Halifeliğin başlamasına"], "a": "İslam Savaş Hukuku'nun oluşmasına ve eğitime verilen öneme"},
        {"q": "Müslümanların Uhud Savaşı'nda yenilgiye uğramasının temel nedeni nedir?", "opts": ["Okçuların yerlerini terk etmesi", "Ordunun sayıca az olması", "Mühimmat eksikliği", "Hava şartları", "İhanet edilmesi"], "a": "Okçuların yerlerini terk etmesi"},
        {"q": "Mekkeli müşriklerin Müslümanları hukuken tanıdığı ilk antlaşma hangisidir?", "opts": ["Hudeybiye Barış Antlaşması", "Akabe Biatı", "Medine Sözleşmesi", "Kadeş Antlaşması", "Mekke Antlaşması"], "a": "Hudeybiye Barış Antlaşması"},
        {"q": "İslam tarihinde 'Hendek Savaşı'nda şehrin etrafına hendek kazılmasını öneren sahabi kimdir?", "opts": ["Selman-ı Farisi", "Hz. Ali", "Hz. Ömer", "Halid bin Velid", "Bilal-i Habeşi"], "a": "Selman-ı Farisi"},
        {"q": "Müslümanların Bizans ordusuyla yaptığı ilk savaş hangisidir?", "opts": ["Mute Savaşı", "Yermük Savaşı", "Ecnadin Savaşı", "Kadisiye Savaşı", "Nihavend Savaşı"], "a": "Mute Savaşı"},
        {"q": "Hz. Muhammed'in vefatından sonra 'Dört Halife Dönemi'ne (Hulefa-i Raşidin) ne ad verilir?", "opts": ["Cumhuriyet Dönemi", "Saltanat Dönemi", "Fetret Devri", "Meşrutiyet", "Mutlakiyet"], "a": "Cumhuriyet Dönemi"},
        {"q": "Kur'an-ı Kerim'in kitap (Mushaf) haline getirilmesi hangi halife dönemindedir?", "opts": ["Hz. Ebubekir", "Hz. Ömer", "Hz. Osman", "Hz. Ali", "Hz. Muhammed"], "a": "Hz. Ebubekir"},
        {"q": "Hz. Ebubekir döneminde dinden dönenlerle ve yalancı peygamberlerle yapılan savaşlara ne ad verilir?", "opts": ["Ridde Savaşları", "Siffin Savaşı", "Cemel Vakası", "Yermük Savaşı", "Sıffin Savaşı"], "a": "Ridde Savaşları"},
        {"q": "İslam devlet teşkilatının (Divan, Adalet, Ordugah şehirleri) kurulduğu ve Hicri Takvim'in hazırlandığı dönem hangisidir?", "opts": ["Hz. Ömer", "Hz. Ebubekir", "Hz. Osman", "Hz. Ali", "Muaviye"], "a": "Hz. Ömer"},
        {"q": "Sasani İmparatorluğu'nun yıkılıp İran ve Irak'ın fethedildiği savaşlar (Kadisiye, Celula, Nihavend) hangi halife dönemindedir?", "opts": ["Hz. Ömer", "Hz. Ebubekir", "Hz. Osman", "Hz. Ali", "Muaviye"], "a": "Hz. Ömer"},
        {"q": "Kur'an-ı Kerim'in çoğaltılarak önemli merkezlere gönderilmesi hangi halife dönemindedir?", "opts": ["Hz. Osman", "Hz. Ebubekir", "Hz. Ömer", "Hz. Ali", "Ömer bin Abdülaziz"], "a": "Hz. Osman"},
        {"q": "İslam dünyasında ilk iç karışıklıkların başladığı ve ilk kez bir halifenin şehit edildiği dönem hangisidir?", "opts": ["Hz. Osman", "Hz. Ömer", "Hz. Ebubekir", "Hz. Ali", "Muaviye"], "a": "Hz. Osman"},
        {"q": "Hz. Ali ile Hz. Ayşe arasındaki mücadeleye (İlk iç savaş) ne ad verilir?", "opts": ["Cemel Vakası (Deve Olayı)", "Sıffin Savaşı", "Hakem Olayı", "Kerbela Olayı", "Harre Vakası"], "a": "Cemel Vakası (Deve Olayı)"},
        {"q": "İslam dünyasında Müslümanların; Şii, Sünni ve Harici olarak kesin gruplara ayrılmasına neden olan olay nedir?", "opts": ["Hakem Olayı (Sıffin Savaşı sonrası)", "Cemel Vakası", "Kerbela Olayı", "Mekke'nin Fethi", "Veda Haccı"], "a": "Hakem Olayı (Sıffin Savaşı sonrası)"},
        {"q": "Hz. Ali'nin başkenti Medine'den nereye taşıması, iç karışıklıkların merkezde yoğunlaştığını gösterir?", "opts": ["Küfe", "Şam", "Bağdat", "Kahire", "Mekke"], "a": "Küfe"},
        {"q": "Halifeliğin 'Saltanat'a (babadan oğula geçen sisteme) dönüşmesi hangi devlet döneminde olmuştur?", "opts": ["Emeviler", "Dört Halife", "Abbasiler", "Osmanlılar", "Selçuklular"], "a": "Emeviler"},
        {"q": "Emevilerin Arap olmayan Müslümanlara uyguladığı ve 'Azatlı köle' anlamına gelen ırkçı politika nedir?", "opts": ["Mevali", "Ümmetçilik", "İskan", "İstimalet", "Gaza"], "a": "Mevali"},
        {"q": "Emeviler döneminde İspanya'nın (Endülüs) fethini sağlayan komutan kimdir?", "opts": ["Tarık bin Ziyad", "Halid bin Velid", "Sad bin Ebi Vakkas", "Amr bin As", "Musa bin Nusayr"], "a": "Tarık bin Ziyad"},
        {"q": "Müslümanların Avrupa'daki ilerleyişinin durduğu savaş (732) hangisidir?", "opts": ["Puvatya Savaşı", "Kadiks Savaşı", "Vadikurara Savaşı", "Sıffin Savaşı", "Talas Savaşı"], "a": "Puvatya Savaşı"},
        {"q": "Hz. Hüseyin'in şehit edildiği ve İslam dünyasındaki ayrılıkların derinleştiği olay hangisidir?", "opts": ["Kerbela Olayı", "Cemel Vakası", "Sıffin Savaşı", "Harre Vakası", "Vaka-i Vakvakiye"], "a": "Kerbela Olayı"},
        {"q": "Abbasilerin Emevilerin aksine uyguladığı, Arap olmayanları da devlet kademelerine getirdiği politika nedir?", "opts": ["Hoşgörü ve Ümmetçilik", "Mevali", "Arap Milliyetçiliği", "Sömürgecilik", "Kabilecilik"], "a": "Hoşgörü ve Ümmetçilik"},
        {"q": "Türklerin kitleler halinde İslamiyet'e girmesine neden olan ve Abbasiler ile Çin arasında yapılan savaş hangisidir?", "opts": ["Talas Savaşı", "Dandanakan Savaşı", "Puvatya Savaşı", "Malazgirt Savaşı", "Yermük Savaşı"], "a": "Talas Savaşı"},
        {"q": "Abbasiler döneminde Bağdat'ta kurulan, tercüme ve bilim merkezi olan kurum hangisidir?", "opts": ["Beyt'ül Hikme", "Nizamiye Medresesi", "Darülaceze", "Enderun", "Suffe"], "a": "Beyt'ül Hikme"},
        {"q": "Abbasiler döneminde Türkler için kurulan özel ordugah şehirlere ne ad verilir?", "opts": ["Samarra", "Bağdat", "Şam", "Küfe", "Basra"], "a": "Samarra"},
        {"q": "Bizans sınırında kurulan ve Türklerin yerleştirildiği tampon bölgelere (şehirlerine) ne ad verilir?", "opts": ["Avasım", "İkta", "Vakıf", "Uç Beyliği", "Sancak"], "a": "Avasım"},
        {"q": "Avrupa'da İslam medeniyetinin ve biliminin yayılmasını sağlayan devlet hangisidir?", "opts": ["Endülüs Emevi Devleti", "Abbasiler", "Fatımiler", "Selçuklular", "Memlükler"], "a": "Endülüs Emevi Devleti"},
        {"q": "İslam dünyasında 'Muallim-i Sani' (İkinci Öğretmen) olarak bilinen ünlü filozof kimdir?", "opts": ["Farabi", "İbn-i Sina", "Biruni", "Gazali", "İbn-i Rüşd"], "a": "Farabi"},
        {"q": "Tıbbın Hükümdarı (Avicenna) olarak bilinen ve 'El Kanun fi't Tıb' eserini yazan bilgin kimdir?", "opts": ["İbn-i Sina", "Farabi", "Harezmi", "Razi", "Akşemseddin"], "a": "İbn-i Sina"},
        {"q": "Cebir ilminin kurucusu sayılan ve 'Sıfır' rakamını matematiğe kazandıran bilgin kimdir?", "opts": ["Harezmi", "Ömer Hayyam", "Biruni", "Kindî", "Battani"], "a": "Harezmi"},
        {"q": "Endülüs'te bulunan ve mimari harikası olarak kabul edilen saray hangisidir?", "opts": ["El Hamra Sarayı", "Topkapı Sarayı", "Dolmabahçe Sarayı", "Versay Sarayı", "Tac Mahal"], "a": "El Hamra Sarayı"},
        {"q": "İslam tarihinde ilk donanmayı kuran ve Kıbrıs'ı fetheden halife kimdir?", "opts": ["Hz. Osman", "Hz. Ömer", "Hz. Ebubekir", "Hz. Ali", "Muaviye"], "a": "Hz. Osman"},
        {"q": "Cahiliye döneminde haram aylarda yapılan savaşlara ne ad verilirdi?", "opts": ["Ficar Savaşları", "Gaza", "Cihat", "Ridde", "Seriyye"], "a": "Ficar Savaşları"},
        {"q": "Hz. Muhammed'in bizzat katıldığı savaşlara ne ad verilir?", "opts": ["Gazve", "Seriyye", "Cihat", "Sefer", "Akın"], "a": "Gazve"},
        {"q": "Müslümanların Habeşistan'a hicret etmesinin temel sebebi nedir?", "opts": ["Habeş Kralı'nın adaletli olması", "Mekke'de kuraklık olması", "Ticaret yapmak istemeleri", "Akrabalarının orada olması", "Habeşistan'ı fethetmek"], "a": "Habeş Kralı'nın adaletli olması"},
        {"q": "Akabe Biatları'nın İslam tarihindeki önemi nedir?", "opts": ["Medinelilerin Hz. Muhammed'i ve İslam'ı kabul etmesi", "Savaş kararının alınması", "Mekke'nin fethinin planlanması", "Ticaret antlaşması olması", "Yahudilerle anlaşma yapılması"], "a": "Medinelilerin Hz. Muhammed'i ve İslam'ı kabul etmesi"},
        {"q": "Medine Sözleşmesi'nin (Vatandaşlık Antlaşması) en önemli özelliği nedir?", "opts": ["İslam devletinin ilk anayasası olması", "Sadece Müslümanları kapsaması", "Mekkeli müşriklerle yapılması", "Savaşı sonlandırması", "Ticari bir antlaşma olması"], "a": "İslam devletinin ilk anayasası olması"},
        {"q": "Mekke'nin Fethi'nin en önemli sonucu nedir?", "opts": ["Kabe'nin putlardan temizlenmesi ve İslam'ın yayılışının hızlanması", "Mekkeli müşriklerin Medine'ye sürülmesi", "Ticaret yollarının kapanması", "Bizans'ın saldırması", "Medine'nin önemini yitirmesi"], "a": "Kabe'nin putlardan temizlenmesi ve İslam'ın yayılışının hızlanması"},
        {"q": "Veda Hutbesi'nde Hz. Muhammed'in vurguladığı evrensel mesajlardan biri nedir?", "opts": ["Kan davasının kaldırılması ve ırkçılığın yasaklanması", "Sadece Arapların üstün olduğu", "Zenginlerin daha yetkili olduğu", "Savaşın kutsal olduğu", "Krallığın gerekliliği"], "a": "Kan davasının kaldırılması ve ırkçılığın yasaklanması"},
        {"q": "Yalancı peygamberlerle mücadele eden ve 'Halifelik' kurumunu başlatan ilk halife kimdir?", "opts": ["Hz. Ebubekir", "Hz. Ömer", "Hz. Osman", "Hz. Ali", "Muaviye"], "a": "Hz. Ebubekir"},
        {"q": "İslam tarihinde 'Beytül Mal' (Devlet Hazinesi) ilk kez hangi halife döneminde sistemli hale getirilmiştir?", "opts": ["Hz. Ömer", "Hz. Ebubekir", "Hz. Osman", "Hz. Ali", "Harun Reşid"], "a": "Hz. Ömer"},
        {"q": "Emevilerin yıkılmasında etkili olan en önemli faktör nedir?", "opts": ["Mevali (Irkçılık) politikası", "Çok geniş sınırlara ulaşmaları", "Bilime önem vermeleri", "Bizans'ın saldırıları", "Tarımla uğraşmaları"], "a": "Mevali (Irkçılık) politikası"},
        {"q": "Abbasilerin en parlak dönemi hangi halife zamanındadır?", "opts": ["Harun Reşid", "Memun", "Mutasım", "Ebu'l Abbas", "Mansur"], "a": "Harun Reşid"},
        {"q": "İslam Rönesansı olarak bilinen dönemde İspanya'da kurulan ve Avrupa'yı aydınlatan medrese hangisidir?", "opts": ["Kurtuba Medresesi", "Nizamiye Medresesi", "Bağdat Medresesi", "Ezher Medresesi", "Semerkant Medresesi"], "a": "Kurtuba Medresesi"},
        {"q": "İslamiyet öncesi Mekke'de, haksızlığa uğrayanların hakkını korumak için kurulan teşkilat nedir?", "opts": ["Hılf'ul Fudul (Erdemliler İttifakı)", "Dar'un Nedve", "Kabe Hakemliği", "Mele Meclisi", "Ukaz Panayırı"], "a": "Hılf'ul Fudul (Erdemliler İttifakı)"},
        {"q": "Mute Savaşı'nın İslam tarihindeki önemi nedir?", "opts": ["Müslümanların Bizans ile yaptığı ilk savaştır", "Mekke'nin fethini sağlamıştır", "İran'ın fethini sağlamıştır", "Müslümanlar yenilmiştir", "Şam fethedilmiştir"], "a": "Müslümanların Bizans ile yaptığı ilk savaştır"},
        {"q": "Tebük Seferi'nin önemi nedir?", "opts": ["Hz. Muhammed'in son seferidir", "Bizans ile yapılan ilk savaştır", "Mekke'nin fethidir", "İran'a yapılan seferdir", "Yahudilere karşı yapılmıştır"], "a": "Hz. Muhammed'in son seferidir"}
    ],"6. Türklerin İslamiyet’i Kabulü ve İlk Türk İslam Devletleri": [
        {"q": "Türklerin kitleler halinde İslamiyet'e geçmesini sağlayan ve Abbasiler ile Çin arasında yapılan savaş hangisidir?", "opts": ["Talas Savaşı", "Dandanakan Savaşı", "Malazgirt Savaşı", "Pasinler Savaşı", "Yassıçemen Savaşı"], "a": "Talas Savaşı"},
        {"q": "Orta Asya'da kurulan ilk Türk-İslam devleti hangisidir?", "opts": ["Karahanlılar", "Gazneliler", "Tolunoğulları", "Büyük Selçuklular", "İhşidiler"], "a": "Karahanlılar"},
        {"q": "Mısır'da kurulan ilk Türk-İslam devleti hangisidir?", "opts": ["Tolunoğulları", "İhşidiler", "Eyyubiler", "Memlükler", "Fatımiler"], "a": "Tolunoğulları"},
        {"q": "Türk tarihinde 'Sultan' unvanını kullanan ilk hükümdar kimdir?", "opts": ["Gazneli Mahmut", "Tuğrul Bey", "Alparslan", "Satuk Buğra Han", "Melikşah"], "a": "Gazneli Mahmut"},
        {"q": "Karahanlı hükümdarı Satuk Buğra Han İslamiyet'i kabul ettikten sonra hangi ismi almıştır?", "opts": ["Abdülkerim", "Abdullah", "Muhammed", "Yusuf", "Ahmed"], "a": "Abdülkerim"},
        {"q": "Türk-İslam edebiyatının ilk yazılı eseri kabul edilen 'Kutadgu Bilig' kime aittir?", "opts": ["Yusuf Has Hacib", "Kaşgarlı Mahmut", "Edip Ahmet Yükneki", "Hoca Ahmet Yesevi", "Nizamülmülk"], "a": "Yusuf Has Hacib"},
        {"q": "İlk Türkçe sözlük olan ve Türkçenin Arapça kadar zengin bir dil olduğunu göstermek için yazılan eser nedir?", "opts": ["Divan-ı Lügati't-Türk", "Kutadgu Bilig", "Atabetü'l Hakayık", "Divan-ı Hikmet", "Şehname"], "a": "Divan-ı Lügati't-Türk"},
        {"q": "Büyük Selçuklu Devleti'nin resmen kurulduğu savaş hangisidir?", "opts": ["Dandanakan Savaşı", "Pasinler Savaşı", "Malazgirt Savaşı", "Katvan Savaşı", "Kösedağ Savaşı"], "a": "Dandanakan Savaşı"},
        {"q": "Büyük Selçuklu Sultanı Tuğrul Bey'e Abbasi Halifesi tarafından verilen unvan nedir?", "opts": ["Doğunun ve Batının Sultanı", "Sultan-ı İklimi Rum", "Gazi", "Hüdavendigar", "Emir"], "a": "Doğunun ve Batının Sultanı"},
        {"q": "1071 Malazgirt Savaşı'nda Bizans İmparatoru Romen Diyojen'i mağlup eden Selçuklu hükümdarı kimdir?", "opts": ["Sultan Alparslan", "Tuğrul Bey", "Melikşah", "Sencer", "Keykubat"], "a": "Sultan Alparslan"},
        {"q": "Malazgirt Savaşı'nın en önemli sonucu nedir?", "opts": ["Anadolu'nun kapılarının Türklere açılması", "Bizans'ın yıkılması", "Haçlı Seferleri'nin bitmesi", "Osmanlı'nın kurulması", "Abbasilerin yıkılması"], "a": "Anadolu'nun kapılarının Türklere açılması"},
        {"q": "Büyük Selçuklu Devleti'nin en parlak dönemi hangi hükümdar zamanındadır?", "opts": ["Sultan Melikşah", "Tuğrul Bey", "Alparslan", "Sencer", "Berkyaruk"], "a": "Sultan Melikşah"},
        {"q": "Karahanlıların Türk kültürünü korumaya önem verdiklerinin en büyük kanıtı nedir?", "opts": ["Resmi dillerinin Türkçe olması", "Arap alfabesi kullanmaları", "İslam'ı kabul etmeleri", "Medrese kurmaları", "Kervansaray yapmaları"], "a": "Resmi dillerinin Türkçe olması"},
        {"q": "Gazneli Mahmut'un Hindistan'a 17 sefer düzenlemesinin temel amacı nedir?", "opts": ["İslamiyet'i yaymak ve ganimet elde etmek", "Çin'e ulaşmak", "Haçlıları durdurmak", "Bizans'ı yıkmak", "Ticaret yollarını açmak"], "a": "İslamiyet'i yaymak ve ganimet elde etmek"},
        {"q": "Selçuklularda devlet memuru yetiştirmek için kurulan ve dünyanın ilk üniversitesi sayılan kurum nedir?", "opts": ["Nizamiye Medreseleri", "Beytül Hikme", "Enderun", "Lonca", "Rasathane"], "a": "Nizamiye Medreseleri"},
        {"q": "Nizamiye Medreseleri'ni kuran ünlü Selçuklu veziri kimdir?", "opts": ["Nizamülmülk", "Tonyukuk", "Piri Reis", "Ömer Hayyam", "İbn-i Sina"], "a": "Nizamülmülk"},
        {"q": "Büyük Selçuklu Devleti'nin yıkılmasında etkili olan sapkın tarikat hangisidir?", "opts": ["Batınilik (Haşhaşiler)", "Hariciler", "Mutezile", "Babailer", "Celaliler"], "a": "Batınilik (Haşhaşiler)"},
        {"q": "Batınilik tarikatının kurucusu ve Alamut Kalesi'nin lideri kimdir?", "opts": ["Hasan Sabbah", "Baba İshak", "Şeyh Bedrettin", "Hallac-ı Mansur", "Nesimi"], "a": "Hasan Sabbah"},
        {"q": "Türk-İslam devletlerinde hükümdarın erkek çocuklarına ne ad verilir?", "opts": ["Melik", "Şehzade", "Çelebi", "Tigin", "Atabey"], "a": "Melik"},
        {"q": "Meliklerin eğitiminden sorumlu olan tecrübeli devlet adamlarına ne ad verilir?", "opts": ["Atabey", "Lala", "Vezir", "Hacip", "Subaşı"], "a": "Atabey"},
        {"q": "Türk-İslam devletlerinde 'Gulam Sistemi' neyi ifade eder?", "opts": ["Savaş esirlerinin asker olarak yetiştirilmesi", "Vergi toplama sistemi", "Toprak sistemi", "Hukuk sistemi", "Eğitim sistemi"], "a": "Savaş esirlerinin asker olarak yetiştirilmesi"},
        {"q": "Selçuklularda askeri işlere bakan divan hangisidir?", "opts": ["Divan-ı Arz", "Divan-ı İnşa", "Divan-ı İstifa", "Divan-ı İşraf", "Divan-ı Mezalim"], "a": "Divan-ı Arz"},
        {"q": "Hicaz bölgesine (Mekke-Medine) hakim olan ilk Türk devleti hangisidir?", "opts": ["İhşidiler (Akşitler)", "Tolunoğulları", "Memlükler", "Eyyubiler", "Selçuklular"], "a": "İhşidiler (Akşitler)"},
        {"q": "Selahaddin Eyyubi'nin Kudüs'ü Haçlılardan geri aldığı savaş hangisidir?", "opts": ["Hıttin Savaşı", "Yermük Savaşı", "Ecnadin Savaşı", "Malazgirt Savaşı", "Ayn Calut Savaşı"], "a": "Hıttin Savaşı"},
        {"q": "Moğolları 'Ayn Calut Savaşı'nda durduran tek Türk devleti hangisidir?", "opts": ["Memlükler", "Eyyubiler", "Selçuklular", "Osmanlılar", "Harzemşahlar"], "a": "Memlükler"},
        {"q": "Türk-İslam mimarisinde, kervanların güvenliği ve konaklaması için yapılan yapılara ne ad verilir?", "opts": ["Ribat (Kervansaray)", "Külliye", "İmaret", "Bedesten", "Arasta"], "a": "Ribat (Kervansaray)"},
        {"q": "Büyük Selçuklu Devleti'nin Bizans ile yaptığı ilk savaş (1048) hangisidir?", "opts": ["Pasinler Savaşı", "Malazgirt Savaşı", "Miryokefalon Savaşı", "Dandanakan Savaşı", "Kösedağ Savaşı"], "a": "Pasinler Savaşı"},
        {"q": "Türk-İslam devletlerinde 'Hutbe okutmak' ve 'Para bastırmak' neyin alametidir?", "opts": ["Bağımsızlığın", "Zenginliğin", "Savaşın", "Dinin", "Eğitimin"], "a": "Bağımsızlığın"},
        {"q": "Gaznelilerin en önemli özelliği nedir?", "opts": ["Çok uluslu (imparatorluk) yapısı", "Denizci olmaları", "Anadolu'da kurulmaları", "Matbaayı kullanmaları", "Şiiliği benimsemeleri"], "a": "Çok uluslu (imparatorluk) yapısı"},
        {"q": "Karahanlılarda 'Bimarhane' ne amaçla kullanılmıştır?", "opts": ["Hastane (Akıl hastaları dahil)", "Okul", "Rasathane", "Kütüphane", "Saray"], "a": "Hastane (Akıl hastaları dahil)"},
        {"q": "Türklerin İslamiyet'i kabulüyle sosyal hayatta meydana gelen en büyük değişim nedir?", "opts": ["Göçebe yaşamdan yerleşik hayata geçişin hızlanması", "Savaşçılık özelliklerinin kaybolması", "Hayvancılığın bırakılması", "Türkçenin unutulması", "Demokrasinin gelmesi"], "a": "Göçebe yaşamdan yerleşik hayata geçişin hızlanması"},
        {"q": "Divan-ı Hikmet adlı eserin yazarı ve Türk tasavvufunun kurucusu kimdir?", "opts": ["Hoca Ahmet Yesevi", "Yunus Emre", "Mevlana", "Hacı Bektaş Veli", "Edip Ahmet Yükneki"], "a": "Hoca Ahmet Yesevi"},
        {"q": "Atabetü'l Hakayık (Gerçeklerin Eşiği) adlı eserin yazarı kimdir?", "opts": ["Edip Ahmet Yükneki", "Yusuf Has Hacib", "Kaşgarlı Mahmut", "Ali Şir Nevai", "Fuzuli"], "a": "Edip Ahmet Yükneki"},
        {"q": "Selçuklularda toprakların geliri ve idaresinin devlet memurlarına verildiği sisteme ne ad verilir?", "opts": ["İkta Sistemi", "Tımar Sistemi", "İltizam Sistemi", "Malikane Sistemi", "Vakıf Sistemi"], "a": "İkta Sistemi"},
        {"q": "Büyük Selçuklu Devleti'nin son büyük hükümdarı kimdir?", "opts": ["Sultan Sencer", "Melikşah", "Berkyaruk", "Mehmet Tapar", "Alparslan"], "a": "Sultan Sencer"},
        {"q": "Büyük Selçukluların yıkılmasının en önemli dış nedeni nedir?", "opts": ["Katvan Savaşı'nda Karahitaylara yenilmeleri", "Haçlı Seferleri", "Bizans saldırıları", "Abbasilerin güçlenmesi", "Mısır'ın kaybı"], "a": "Katvan Savaşı'nda Karahitaylara yenilmeleri"},
        {"q": "Harzemşahların kendilerini mirasçısı olarak gördükleri devlet hangisidir?", "opts": ["Büyük Selçuklu Devleti", "Gazneliler", "Karahanlılar", "Osmanlılar", "Abbasiler"], "a": "Büyük Selçuklu Devleti"},
        {"q": "Otrar Faciası olarak bilinen olayda Moğollar tarafından yıkılan devlet hangisidir?", "opts": ["Harzemşahlar", "Selçuklular", "Karahanlılar", "Memlükler", "Gazneliler"], "a": "Harzemşahlar"},
        {"q": "Memlüklerde diğer Türk devletlerinden farklı olarak uygulanan veraset sistemi nasıldır?", "opts": ["Güçlü olan komutanın başa geçmesi", "Babadan oğula geçiş", "Kardeşler arası ortaklık", "Seçimle gelme", "Halifenin ataması"], "a": "Güçlü olan komutanın başa geçmesi"},
        {"q": "Türk-İslam devletlerinde hükümdarın sarayına ne ad verilir?", "opts": ["Dergâh veya Bargâh", "Otağ", "Kervansaray", "Külliye", "Ribat"], "a": "Dergâh veya Bargâh"},
        {"q": "Selçuklularda resmi dil ve bilim dili neydi?", "opts": ["Farsça - Arapça", "Türkçe - Türkçe", "Arapça - Farsça", "Türkçe - Farsça", "Latince - Yunanca"], "a": "Farsça - Arapça"},
        {"q": "Firdevsi'nin yazdığı ve Gazneli Mahmut'a sunduğu ünlü eser hangisidir?", "opts": ["Şehname", "Kutadgu Bilig", "Siyasetname", "Mesnevi", "Bostan"], "a": "Şehname"},
        {"q": "Türk-İslam devletlerinde adaleti sağlayan, şeri mahkemelerin başındaki kişiye ne ad verilir?", "opts": ["Kadı", "Subaşı", "Muhtesib", "Atabey", "Melik"], "a": "Kadı"},
        {"q": "Çarşı ve pazarın düzenini, tartı aletlerini denetleyen görevli kimdir?", "opts": ["Muhtesib", "Kadı", "Subaşı", "Hacip", "Vezir"], "a": "Muhtesib"},
        {"q": "Sultan Alparslan'ın Malazgirt Savaşı'ndan sonra komutanlarına verdiği 'Fethedilen yer fethedenindir' emri neye yol açmıştır?", "opts": ["I. Beylikler Dönemi'nin başlamasına", "Merkezi otoritenin güçlenmesine", "Bizans'ın güçlenmesine", "Haçlı Seferleri'nin durmasına", "Selçuklu'nun yıkılmasına"], "a": "I. Beylikler Dönemi'nin başlamasına"},
        {"q": "Saltuklular, Mengücekliler, Danişmentliler ve Artuklular hangi döneme aittir?", "opts": ["I. Beylikler Dönemi", "II. Beylikler Dönemi", "Osmanlı Dönemi", "Karahanlı Dönemi", "Gazneli Dönemi"], "a": "I. Beylikler Dönemi"},
        {"q": "Anadolu'da kurulan ilk Türk beyliği hangisidir?", "opts": ["Saltuklular", "Danişmentliler", "Mengücekliler", "Artuklular", "Çaka Beyliği"], "a": "Saltuklular"},
        {"q": "İlk Türk denizcisi olan ve İzmir çevresinde beylik kuran kişi kimdir?", "opts": ["Çaka Bey", "Umur Bey", "Barbaros Hayrettin", "Piri Reis", "Karamürsel Alp"], "a": "Çaka Bey"},
        {"q": "Anadolu'daki en eski külliye olan Divriği Ulu Camii kime aittir?", "opts": ["Mengücekliler", "Saltuklular", "Danişmentliler", "Artuklular", "Selçuklular"], "a": "Mengücekliler"},
        {"q": "Batman yakınlarındaki Malabadi Köprüsü hangi beyliğe aittir?", "opts": ["Artuklular", "Saltuklular", "Danişmentliler", "Mengücekliler", "Osmanlılar"], "a": "Artuklular"}
    ],

    "7. Yerleşme ve Devletleşme Sürecinde Selçuklu Türkiyesi": [
        {"q": "Türkiye (Anadolu) Selçuklu Devleti'nin kurucusu kimdir?", "opts": ["Kutalmışoğlu Süleyman Şah", "Kılıç Arslan", "Alaaddin Keykubat", "Mesut", "Tuğrul Bey"], "a": "Kutalmışoğlu Süleyman Şah"},
        {"q": "Türkiye Selçuklu Devleti'nin ilk başkenti neresidir?", "opts": ["İznik", "Konya", "Kayseri", "Sivas", "Erzurum"], "a": "İznik"},
        {"q": "I. Haçlı Seferi sonucunda başkent İznik kaybedilince devlet merkezi nereye taşınmıştır?", "opts": ["Konya", "Ankara", "Sivas", "Kayseri", "Antalya"], "a": "Konya"},
        {"q": "Anadolu'nun kesin olarak Türk yurdu haline geldiği ve Bizans'ın Türkleri atma ümidinin sona erdiği savaş hangisidir?", "opts": ["Miryokefalon Savaşı", "Malazgirt Savaşı", "Pasinler Savaşı", "Yassıçemen Savaşı", "Kösedağ Savaşı"], "a": "Miryokefalon Savaşı"},
        {"q": "Miryokefalon Savaşı (1176) hangi Selçuklu sultanı döneminde kazanılmıştır?", "opts": ["II. Kılıç Arslan", "I. Kılıç Arslan", "Alaaddin Keykubat", "I. Gıyaseddin Keyhüsrev", "I. İzzettin Keykavus"], "a": "II. Kılıç Arslan"},
        {"q": "Türkiye Selçuklu Devleti'nin en parlak dönemi hangi hükümdar zamanındadır?", "opts": ["I. Alaaddin Keykubat", "II. Kılıç Arslan", "I. Mesut", "I. Gıyaseddin Keyhüsrev", "II. Gıyaseddin Keyhüsrev"], "a": "I. Alaaddin Keykubat"},
        {"q": "Türkiye Selçuklularında ticareti geliştirmek için yapılan uygulamalardan biri olan 'Sigorta Sistemi' neyi ifade eder?", "opts": ["Zarara uğrayan tüccarın malının devlet tarafından karşılanması", "Vergi alınmaması", "Yabancılara yasak konması", "Sadece Türklerin ticaret yapması", "Limanların kapatılması"], "a": "Zarara uğrayan tüccarın malının devlet tarafından karşılanması"},
        {"q": "Sinop'u fethederek Karadeniz ticaret yolunu açan Selçuklu sultanı kimdir?", "opts": ["I. İzzettin Keykavus", "Alaaddin Keykubat", "I. Gıyaseddin Keyhüsrev", "Kılıç Arslan", "Süleyman Şah"], "a": "I. İzzettin Keykavus"},
        {"q": "Antalya'yı fethederek Akdeniz ticaret yolunu açan Selçuklu sultanı kimdir?", "opts": ["I. Gıyaseddin Keyhüsrev", "Alaaddin Keykubat", "İzzettin Keykavus", "Kılıç Arslan", "Mesut"], "a": "I. Gıyaseddin Keyhüsrev"},
        {"q": "Kırım'ın Suğdak limanına denizaşırı sefer düzenleyerek Karadeniz hakimiyetini güçlendiren sultan kimdir?", "opts": ["I. Alaaddin Keykubat", "II. Kılıç Arslan", "I. Mesut", "II. Gıyaseddin Keyhüsrev", "Süleyman Şah"], "a": "I. Alaaddin Keykubat"},
        {"q": "Türkiye Selçuklu Devleti'nin Harzemşahları yendiği ancak Moğol komşusu olduğu savaş (1230) hangisidir?", "opts": ["Yassıçemen Savaşı", "Kösedağ Savaşı", "Katvan Savaşı", "Dandanakan Savaşı", "Malazgirt Savaşı"], "a": "Yassıçemen Savaşı"},
        {"q": "1240 yılında çıkan ve Türkiye Selçuklu Devleti'ni zayıflatarak Moğol istilasına zemin hazırlayan isyan hangisidir?", "opts": ["Baba İshak İsyanı (Babai Ayaklanması)", "Şeyh Bedrettin İsyanı", "Celali İsyanları", "Patrona Halil İsyanı", "Kalender Çelebi İsyanı"], "a": "Baba İshak İsyanı (Babai Ayaklanması)"},
        {"q": "Türkiye Selçuklu Devleti'nin Moğollara yenilerek yıkılma sürecine girdiği savaş (1243) hangisidir?", "opts": ["Kösedağ Savaşı", "Yassıçemen Savaşı", "Ankara Savaşı", "Miryokefalon Savaşı", "Katvan Savaşı"], "a": "Kösedağ Savaşı"},
        {"q": "Kösedağ Savaşı'nın en önemli siyasi sonucu nedir?", "opts": ["Anadolu Türk siyasi birliğinin bozulması ve II. Beylikler Dönemi'nin başlaması", "Bizans'ın güçlenmesi", "Haçlı Seferleri'nin başlaması", "Osmanlı'nın yıkılması", "Selçuklu'nun güçlenmesi"], "a": "Anadolu Türk siyasi birliğinin bozulması ve II. Beylikler Dönemi'nin başlaması"},
        {"q": "Ahilik Teşkilatı'nın kurucusu kimdir?", "opts": ["Ahi Evran", "Hacı Bektaş Veli", "Mevlana", "Yunus Emre", "Nasreddin Hoca"], "a": "Ahi Evran"},
        {"q": "Esnaf ve zanaatkarların dayanışma örgütü olan Ahilik Teşkilatı'nın temel prensiplerini anlatan eserlere ne ad verilir?", "opts": ["Fütüvvetname", "Siyasetname", "Seyahatname", "Vekayiname", "Menakıbname"], "a": "Fütüvvetname"},
        {"q": "Ahilik Teşkilatı'nda esnafa verilen mesleki eğitim sonunda yapılan törene ne ad verilir?", "opts": ["Şed Kuşanma", "İcazet", "Mezuniyet", "Hilat Giyme", "Biat"], "a": "Şed Kuşanma"},
        {"q": "Ahilik Teşkilatı'nın kadınlar koluna (Dünyanın ilk kadın örgütlenmesi) ne ad verilir?", "opts": ["Bacıyan-ı Rum", "Gaziyan-ı Rum", "Abdalan-ı Rum", "Alpler", "Hatunlar"], "a": "Bacıyan-ı Rum"},
        {"q": "Türkiye Selçuklularında donanma komutanına ne ad verilir?", "opts": ["Reis'ül Bahr (Melikü's Sevahil)", "Kaptan-ı Derya", "Subaşı", "Emir-i Dad", "Atabey"], "a": "Reis'ül Bahr (Melikü's Sevahil)"},
        {"q": "Selçuklularda şehirlerin güvenliğinden sorumlu olan komutan kimdir?", "opts": ["Subaşı", "Kadı", "Muhtesib", "Müstefi", "Pervaneci"], "a": "Subaşı"},
        {"q": "Türkiye Selçuklularında toprak kayıtlarını tutan ve iktaları dağıtan görevli (Pervaneci) hangi divana bağlıdır?", "opts": ["Divan-ı Pervane", "Divan-ı İstifa", "Divan-ı İşraf", "Divan-ı Arz", "Divan-ı İnşa"], "a": "Divan-ı Pervane"},
        {"q": "Mevlana Celaleddin-i Rumi'nin en önemli eseri hangisidir?", "opts": ["Mesnevi", "Makalat", "Risaletü'n Nushiyye", "Divan-ı Kebir", "Yunus Divanı"], "a": "Mesnevi"},
        {"q": "Hacı Bektaş Veli'nin öğretilerini topladığı eser hangisidir?", "opts": ["Makalat", "Mesnevi", "Fihibismillah", "Mektubat", "Garibname"], "a": "Makalat"},
        {"q": "Yunus Emre'nin Türkçe yazdığı ve tasavvufi şiirlerini topladığı eseri hangisidir?", "opts": ["Risaletü'n Nushiyye", "Mesnevi", "Makalat", "Garibname", "Kutadgu Bilig"], "a": "Risaletü'n Nushiyye"},
        {"q": "Türkiye Selçuklularında ticareti geliştirmek için Kıbrıs Krallığı ve Venedik ile ne yapılmıştır?", "opts": ["Düşük gümrük vergili ticaret antlaşmaları", "Savaş", "Sınır antlaşması", "Evlilik antlaşması", "Vergi antlaşması"], "a": "Düşük gümrük vergili ticaret antlaşmaları"},
        {"q": "Anadolu'da kurulan ilk medrese olan Yağıbasan Medresesi hangi beyliğe aittir?", "opts": ["Danişmentliler", "Saltuklular", "Mengücekliler", "Artuklular", "Selçuklular"], "a": "Danişmentliler"},
        {"q": "Kayseri'deki Gevher Nesibe Darüşşifası'nın özelliği nedir?", "opts": ["Anadolu'nun ilk tıp fakültesi ve hastanesi olması", "Rasathane olması", "Kütüphane olması", "Saray olması", "Camii olması"], "a": "Anadolu'nun ilk tıp fakültesi ve hastanesi olması"},
        {"q": "Konya'daki Karatay Medresesi ve İnce Minareli Medrese hangi devlete aittir?", "opts": ["Türkiye Selçukluları", "Osmanlılar", "Danişmentliler", "Karamanoğulları", "Artuklular"], "a": "Türkiye Selçukluları"},
        {"q": "Haçlı Seferleri'ne karşı en çok mücadele eden Türk devleti hangisidir?", "opts": ["Türkiye Selçukluları", "Gazneliler", "Karahanlılar", "Uygurlar", "Göktürkler"], "a": "Türkiye Selçukluları"},
        {"q": "II. Kılıç Arslan'ın ülkeyi 11 oğlu arasında paylaştırması neyin sonucudur?", "opts": ["Türk veraset sisteminin (Kut inancı)", "Demokrasinin", "Dış baskıların", "Ekonomik krizin", "Askeri zayıflığın"], "a": "Türk veraset sisteminin (Kut inancı)"},
        {"q": "Türkiye Selçuklularında sultanın başkentte olmadığı zamanlarda devlete vekâlet eden divan hangisidir?", "opts": ["Niyabet-i Saltanat", "Divan-ı Saltanat", "Divan-ı Mezalim", "Divan-ı Arz", "Divan-ı Pervane"], "a": "Niyabet-i Saltanat"},
        {"q": "Anadolu'da Moğol hakimiyetinin başladığı dönem hangisidir?", "opts": ["Kösedağ Savaşı sonrası", "Malazgirt sonrası", "Miryokefalon sonrası", "İstanbul'un fethi sonrası", "Haçlı Seferleri sonrası"], "a": "Kösedağ Savaşı sonrası"},
        {"q": "Moğol baskısı nedeniyle Anadolu'ya gelen Türkmenlerin batı sınırlarına yerleştirilmesi neye zemin hazırlamıştır?", "opts": ["Uç Beyliklerinin (Osmanlı vb.) kurulmasına", "Bizans'ın güçlenmesine", "Selçuklu'nun güçlenmesine", "Anadolu'da ticaretin bitmesine", "Moğolların çekilmesine"], "a": "Uç Beyliklerinin (Osmanlı vb.) kurulmasına"},
        {"q": "Karamanoğlu Mehmet Bey'in 'Bugünden sonra divanda, dergahta, bargâhta, mecliste ve meydanda Türkçeden başka dil konuşulmayacak' fermanı neyin göstergesidir?", "opts": ["Türkçeye verilen önemin ve milliyetçiliğin", "Arapça düşmanlığının", "Okuma yazma oranının düşüklüğünün", "Bizans etkisinin", "Moğol baskısının"], "a": "Türkçeye verilen önemin ve milliyetçiliğin"},
        {"q": "Kendisini Türkiye Selçuklu Devleti'nin mirasçısı olarak gören beylik hangisidir?", "opts": ["Karamanoğulları", "Osmanlılar", "Germiyanoğulları", "Karesioğulları", "Dulkadiroğulları"], "a": "Karamanoğulları"},
        {"q": "Osmanlı Devleti'ne katılan ilk beylik hangisidir?", "opts": ["Karesioğulları", "Karamanoğulları", "Germiyanoğulları", "Hamitoğulları", "Menteşeoğulları"], "a": "Karesioğulları"},
        {"q": "Karesioğulları'nın Osmanlı'ya katılmasıyla Osmanlı neye sahip olmuştur?", "opts": ["Donanmaya ve Rumeli'ye geçiş imkanına", "Güçlü bir orduya", "Anadolu'nun tamamına", "Halifeliğe", "İstanbul'a"], "a": "Donanmaya ve Rumeli'ye geçiş imkanına"},
        {"q": "Vasiyet yoluyla Osmanlı'ya katılan beylik hangisidir?", "opts": ["Germiyanoğulları", "Hamitoğulları", "Karesioğulları", "Karamanoğulları", "Aydınoğulları"], "a": "Germiyanoğulları"},
        {"q": "Para karşılığında (satın alınarak) Osmanlı'ya katılan beylik hangisidir?", "opts": ["Hamitoğulları", "Germiyanoğulları", "Menteşeoğulları", "Saruhanoğulları", "Candaroğulları"], "a": "Hamitoğulları"},
        {"q": "Anadolu Türk siyasi birliğini sağlamak için Osmanlı'yı en çok uğraştıran beylik hangisidir?", "opts": ["Karamanoğulları", "Karesioğulları", "Dulkadiroğulları", "Ramazanoğulları", "Eretna"], "a": "Karamanoğulları"},
        {"q": "Turnadağ Savaşı ile Osmanlı'ya katılan ve Anadolu Türk siyasi birliğinin kesin olarak sağlandığı beylik hangisidir?", "opts": ["Dulkadiroğulları", "Ramazanoğulları", "Karamanoğulları", "Akkoyunlular", "Karakoyunlular"], "a": "Dulkadiroğulları"},
        {"q": "Eretna Devleti'nin veziri olan Kadı Burhaneddin'in kurduğu devlet nerede hüküm sürmüştür?", "opts": ["Sivas ve Kayseri", "Konya", "İzmir", "Antalya", "Erzurum"], "a": "Sivas ve Kayseri"},
        {"q": "Akkoyunlu Devleti'nin en önemli hükümdarı olan ve Fatih Sultan Mehmet ile Otlukbeli Savaşı'nı yapan kimdir?", "opts": ["Uzun Hasan", "Kara Yülük Osman", "Cihangir", "Yakup Bey", "Ali Bey"], "a": "Uzun Hasan"},
        {"q": "Akkoyunluların Kur'an-ı Kerim'i Türkçeye çevirmeleri ve Dede Korkut Hikayeleri'ni yazılı hale getirmeleri neyi gösterir?", "opts": ["Türk kültürüne önem verdiklerini", "Araplaştıklarını", "İran etkisinde kaldıklarını", "Şii olduklarını", "Okuma bilmediklerini"], "a": "Türk kültürüne önem verdiklerini"},
        {"q": "Timur Devleti'nin kurucusu Timur'un, Altın Orda Devleti'ni yıkarak sebep olduğu olumsuz sonuç nedir?", "opts": ["Rusya'nın güneye inmesine ve güçlenmesine ortam hazırlaması", "Osmanlı'nın yıkılması", "Çin'in güçlenmesi", "Haçlı Seferleri'nin başlaması", "Anadolu'nun işgali"], "a": "Rusya'nın güneye inmesine ve güçlenmesine ortam hazırlaması"},
        {"q": "Timur döneminde yaşayan ve Semerkant'ta rasathane kuran ünlü astronomi bilgini ve hükümdar kimdir?", "opts": ["Uluğ Bey", "Ali Kuşçu", "Hüseyin Baykara", "Babür Şah", "Nizamülmülk"], "a": "Uluğ Bey"},
        {"q": "Ali Kuşçu hangi devletten Osmanlı'ya gelerek İstanbul'da müderrislik yapmıştır?", "opts": ["Akkoyunlular (ve Timur kökenli)", "Karamanoğulları", "Memlükler", "Safeviler", "Altın Orda"], "a": "Akkoyunlular (ve Timur kökenli)"},
        {"q": "Babür Devleti'nin kurucusu Babür Şah'ın yazdığı ünlü eser hangisidir?", "opts": ["Babürname", "Şehname", "Seyahatname", "Siyasetname", "Kutadgu Bilig"], "a": "Babürname"},
        {"q": "Hindistan'da bulunan ve dünyanın yedi harikasından biri sayılan Tac Mahal'i kim yaptırmıştır?", "opts": ["Şah Cihan", "Babür Şah", "Ekber Şah", "Cihangir", "Hümayun"], "a": "Şah Cihan"},
        {"q": "Safevi Devleti'nin kurucusu olan ve Şiiliği resmi mezhep ilan eden hükümdar kimdir?", "opts": ["Şah İsmail", "Şah Tahmasb", "Şah Abbas", "Nadir Şah", "Kerim Han"], "a": "Şah İsmail"}
    ],

    "8. Beylikten Devlete Osmanlı Siyaseti": [
        {"q": "Osmanlı Devleti'nin kurucusu Osman Bey'in mensup olduğu boy hangisidir?", "opts": ["Kayı Boyu", "Kınık Boyu", "Avşar Boyu", "Çepni Boyu", "Bayat Boyu"], "a": "Kayı Boyu"},
        {"q": "Osmanlı'nın kısa sürede büyüyüp gelişmesinin en önemli nedeni nedir?", "opts": ["Bizans sınırında (Uç Beyliği) kurulması ve Gaza politikası", "Moğol desteği", "Denizci olması", "Güçlü donanması", "Altın madenleri"], "a": "Bizans sınırında (Uç Beyliği) kurulması ve Gaza politikası"},
        {"q": "Osmanlı Devleti'nin Bizans ile yaptığı ilk savaş (1302) hangisidir?", "opts": ["Koyunhisar (Bafeus) Savaşı", "Maltepe (Palekanon) Savaşı", "Sazlıdere Savaşı", "Niğbolu Savaşı", "Varna Savaşı"], "a": "Koyunhisar (Bafeus) Savaşı"},
        {"q": "Osmanlı'da ilk parayı bastıran ve ilk vergiyi (Bac) koyan padişah kimdir?", "opts": ["Osman Bey", "Orhan Bey", "I. Murat", "Yıldırım Bayezid", "Fatih Sultan Mehmet"], "a": "Osman Bey"},
        {"q": "Bursa'yı fethederek başkent yapan Osmanlı padişahı kimdir?", "opts": ["Orhan Bey", "Osman Bey", "I. Murat", "Yıldırım Bayezid", "II. Murat"], "a": "Orhan Bey"},
        {"q": "Osmanlı Devleti'nin Rumeli'ye (Avrupa'ya) geçişini sağlayan ilk toprak parçası neresidir?", "opts": ["Çimpe Kalesi", "Gelibolu", "Edirne", "Tekirdağ", "Selanik"], "a": "Çimpe Kalesi"},
        {"q": "Osmanlı'da ilk düzenli orduyu (Yaya ve Müsellem) kuran padişah kimdir?", "opts": ["Orhan Bey", "Osman Bey", "I. Murat", "Yıldırım Bayezid", "II. Murat"], "a": "Orhan Bey"},
        {"q": "Osmanlı Devleti'nin Haçlılarla yaptığı ilk savaş (1364) hangisidir?", "opts": ["Sırpsındığı Savaşı", "I. Kosova Savaşı", "Niğbolu Savaşı", "Varna Savaşı", "II. Kosova Savaşı"], "a": "Sırpsındığı Savaşı"},
        {"q": "Edirne'yi fethederek başkent yapan ve 'Sultan' unvanını ilk kullanan padişah kimdir?", "opts": ["I. Murat", "Orhan Bey", "Yıldırım Bayezid", "II. Murat", "Çelebi Mehmet"], "a": "I. Murat"},
        {"q": "I. Kosova Savaşı'nın en önemli üzücü olayı nedir?", "opts": ["I. Murat'ın savaş meydanında şehit edilmesi", "Ordunun dağılması", "Timur'un saldırması", "Şehzade Mustafa'nın isyanı", "Haçlıların kazanması"], "a": "I. Murat'ın savaş meydanında şehit edilmesi"},
        {"q": "Osmanlı'da 'Devşirme Sistemi' ve 'Yeniçeri Ocağı' hangi padişah zamanında kurulmuştur?", "opts": ["I. Murat", "Orhan Bey", "Yıldırım Bayezid", "Fatih Sultan Mehmet", "II. Murat"], "a": "I. Murat"},
        {"q": "İstanbul'u kuşatan ilk Osmanlı padişahı kimdir?", "opts": ["Yıldırım Bayezid (I. Bayezid)", "Fatih Sultan Mehmet", "II. Murat", "Orhan Bey", "Çelebi Mehmet"], "a": "Yıldırım Bayezid (I. Bayezid)"},
        {"q": "Niğbolu Savaşı'nı kazanarak Halife'den 'Sultan-ı İklimi Rum' (Anadolu Diyarının Sultanı) unvanını alan padişah kimdir?", "opts": ["Yıldırım Bayezid", "I. Murat", "Fatih Sultan Mehmet", "Yavuz Sultan Selim", "Kanuni Sultan Süleyman"], "a": "Yıldırım Bayezid"},
        {"q": "1402 Ankara Savaşı'nda Osmanlı Devleti kime yenilmiştir?", "opts": ["Timur Devleti", "Bizans", "Memlükler", "Akkoyunlular", "Safeviler"], "a": "Timur Devleti"},
        {"q": "Ankara Savaşı'nın en ağır sonucu nedir?", "opts": ["Fetret Devri'nin başlaması ve devletin dağılma tehlikesi geçirmesi", "İstanbul'un fethi", "Halifeliğin alınması", "Avrupa'nın fethi", "Donanmanın yanması"], "a": "Fetret Devri'nin başlaması ve devletin dağılma tehlikesi geçirmesi"},
        {"q": "Fetret Devri'ne son vererek devleti yeniden toparlayan ve 'Osmanlı'nın İkinci Kurucusu' sayılan padişah kimdir?", "opts": ["Çelebi Mehmet (I. Mehmet)", "II. Murat", "Yıldırım Bayezid", "Fatih Sultan Mehmet", "Musa Çelebi"], "a": "Çelebi Mehmet (I. Mehmet)"},
        {"q": "Osmanlı tarihinde çıkan ilk dini ve sosyal nitelikli isyan hangisidir?", "opts": ["Şeyh Bedrettin İsyanı", "Babai İsyanı", "Celali İsyanları", "Patrona Halil İsyanı", "Kabakçı Mustafa İsyanı"], "a": "Şeyh Bedrettin İsyanı"},
        {"q": "Varna Savaşı ve II. Kosova Savaşı'nı kazanarak Balkanların kesin Türk yurdu olmasını sağlayan padişah kimdir?", "opts": ["II. Murat", "I. Murat", "Fatih Sultan Mehmet", "Yıldırım Bayezid", "Çelebi Mehmet"], "a": "II. Murat"},
        {"q": "II. Kosova Savaşı'nın (1448) Türk tarihindeki önemi nedir?", "opts": ["Avrupalıların Türkleri Balkanlardan atma ümidinin sona ermesi", "İstanbul'un fethi", "Anadolu birliğinin sağlanması", "Bizans'ın yıkılması", "Haçlı seferlerinin başlaması"], "a": "Avrupalıların Türkleri Balkanlardan atma ümidinin sona ermesi"},
        {"q": "Osmanlı'nın Balkanlarda uyguladığı 'İskan Politikası' nedir?", "opts": ["Anadolu'daki Türkmenlerin fethedilen Balkan topraklarına yerleştirilmesi", "Hristiyanların Anadolu'ya sürülmesi", "Balkanların boşaltılması", "Sadece askerlerin yerleşmesi", "Vergi affı"], "a": "Anadolu'daki Türkmenlerin fethedilen Balkan topraklarına yerleştirilmesi"},
        {"q": "Osmanlı'nın fethedilen bölgelerdeki halka hoşgörülü davranarak gönüllerini kazanma politikasına ne ad verilir?", "opts": ["İstimalet (Hoşgörü) Politikası", "İskan Politikası", "Devşirme Politikası", "Millet Sistemi", "Gaza Politikası"], "a": "İstimalet (Hoşgörü) Politikası"},
        {"q": "Osmanlı Devleti'nde yönetici ve askeri sınıfın dışında kalan, vergi veren halka ne ad verilir?", "opts": ["Reaya", "Beraya", "Seyfiye", "İlmiye", "Kalemiye"], "a": "Reaya"},
        {"q": "Tımar sisteminin en önemli askeri yararı nedir?", "opts": ["Devlet hazinesinden para çıkmadan savaşa hazır Cebelü (atlı asker) yetiştirilmesi", "Yeniçerilerin maaşının ödenmesi", "Donanmanın güçlenmesi", "Saray masraflarının azalması", "Ticaretin artması"], "a": "Devlet hazinesinden para çıkmadan savaşa hazır Cebelü (atlı asker) yetiştirilmesi"},
        {"q": "Yeniçerilerin üç ayda bir aldıkları maaşa ne ad verilir?", "opts": ["Ulufe", "Cülus", "İaşe", "Ganimet", "Arpalık"], "a": "Ulufe"},
        {"q": "Padişah değişikliğinde Kapıkulu askerlerine dağıtılan bahşişe ne ad verilir?", "opts": ["Cülus Bahşişi", "Ulufe", "Hakkı Huzur", "Diş Kirası", "Sefer Bahşişi"], "a": "Cülus Bahşişi"},
        {"q": "Osmanlı'da devlet işlerinin görüşüldüğü kurula ne ad verilir?", "opts": ["Divan-ı Hümayun", "Kurultay", "Pankuş", "Meclis-i Mebusan", "Senato"], "a": "Divan-ı Hümayun"},
        {"q": "Divan-ı Hümayun'un bugünkü karşılığı nedir?", "opts": ["Bakanlar Kurulu", "Belediye Meclisi", "Yargıtay", "Danıştay", "Sayıştay"], "a": "Bakanlar Kurulu"},
        {"q": "Osmanlı'da Padişahın mutlak vekili ve divan başkanı (Fatih'e kadar) kimdir?", "opts": ["Vezir-i Azam (Sadrazam)", "Kazasker", "Nişancı", "Defterdar", "Şeyhülislam"], "a": "Vezir-i Azam (Sadrazam)"},
        {"q": "Divanda mali işlerden sorumlu olan görevli kimdir?", "opts": ["Defterdar", "Nişancı", "Kazasker", "Reisülküttab", "Vezir"], "a": "Defterdar"},
        {"q": "Divanda yazı işlerine bakan, padişahın tuğrasını çeken ve tapu kayıtlarını tutan görevli kimdir?", "opts": ["Nişancı", "Defterdar", "Kazasker", "Sadrazam", "Şeyhülislam"], "a": "Nişancı"},
        {"q": "Divanda adalet ve eğitim işlerinden sorumlu olan, kadı ve müderris atamalarını yapan görevli kimdir?", "opts": ["Kazasker", "Şeyhülislam", "Nişancı", "Defterdar", "Sadrazam"], "a": "Kazasker"},
        {"q": "Fetret Devri'nde kardeşi Çelebi Mehmet ile taht mücadelesine giren ve 'Düzmece Mustafa' isyanını çıkaran şehzade kimdir?", "opts": ["Mustafa Çelebi", "Musa Çelebi", "İsa Çelebi", "Süleyman Çelebi", "Korkut Çelebi"], "a": "Mustafa Çelebi"},
        {"q": "Venediklilerle yapılan ilk deniz savaşı (Çalı Bey Savaşı) hangi padişah dönemindedir?", "opts": ["Çelebi Mehmet", "Fatih Sultan Mehmet", "Kanuni Sultan Süleyman", "II. Murat", "Orhan Bey"], "a": "Çelebi Mehmet"},
        {"q": "II. Murat'ın tahtı kendi isteğiyle 12 yaşındaki oğlu II. Mehmet'e (Fatih) bırakması üzerine çıkan isyan hangisidir?", "opts": ["Buçuktepe İsyanı", "Şeyh Bedrettin İsyanı", "Celali İsyanları", "Patrona Halil İsyanı", "Babai İsyanı"], "a": "Buçuktepe İsyanı"},
        {"q": "Buçuktepe İsyanı'nın Osmanlı tarihindeki özelliği nedir?", "opts": ["İlk Yeniçeri ayaklanması olması", "Rejim değişikliği olması", "Hanedanın değişmesi", "Devletin yıkılması", "Celali isyanı olması"], "a": "İlk Yeniçeri ayaklanması olması"},
        {"q": "Osmanlı Devleti'nin Rumeli'deki hakimiyetinin kesinleştiği savaş (Balkanların tapusu) hangisidir?", "opts": ["II. Kosova Savaşı", "I. Kosova Savaşı", "Varna Savaşı", "Niğbolu Savaşı", "Sırpsındığı Savaşı"], "a": "II. Kosova Savaşı"},
        {"q": "Osmanlı'nın kuruluş döneminde Ahilerin desteğini almak için Osman Bey kimin kızıyla evlenmiştir?", "opts": ["Şeyh Edebali", "Dursun Fakih", "Ahi Evran", "Hacı Bektaş Veli", "Mevlana"], "a": "Şeyh Edebali"},
        {"q": "Osmanlı'da atanan ilk kadı kimdir?", "opts": ["Dursun Fakih", "Davud-u Kayseri", "Molla Fenari", "Ebussuud Efendi", "Akşemseddin"], "a": "Dursun Fakih"},
        {"q": "İznik'te açılan ilk Osmanlı medresesinin (İznik Orhaniyesi) ilk müderrisi kimdir?", "opts": ["Davud-u Kayseri", "Dursun Fakih", "Ali Kuşçu", "Molla Gürani", "Kadızade Rumi"], "a": "Davud-u Kayseri"},
        {"q": "Osmanlı'da 'Ülke hanedanın ortak malıdır' anlayışını 'Ülke padişah ve oğullarınındır' şeklinde değiştiren padişah kimdir?", "opts": ["I. Murat", "Fatih Sultan Mehmet", "I. Ahmet", "Yavuz Sultan Selim", "Osman Bey"], "a": "I. Murat"},
        {"q": "Kuruluş döneminde Osmanlı'ya katılan ilk beylik olan Karesioğulları'nın en önemli katkısı nedir?", "opts": ["Osmanlı'nın donanma sahibi olması", "Ekonomik destek", "Kara ordusu desteği", "Haçlılarla ittifak", "Anadolu birliğini bozması"], "a": "Osmanlı'nın donanma sahibi olması"},
        {"q": "Ankara Savaşı'ndan sonra Anadolu Türk siyasi birliğinin bozulmasının temel nedeni nedir?", "opts": ["Beyliklerin yeniden kurulması", "Bizans'ın güçlenmesi", "Şehzade kavgaları", "Timur'un Anadolu'da kalması", "Halkın isyan etmesi"], "a": "Beyliklerin yeniden kurulması"},
        {"q": "Osmanlı'nın Balkanlarda ilerlemesini kolaylaştıran 'Müdarâ' politikası ne demektir?", "opts": ["Görünüşte dostluk kurma (idare etme)", "Savaş açma", "Vergi alma", "Sürgün etme", "Zorla Müslüman yapma"], "a": "Görünüşte dostluk kurma (idare etme)"},
        {"q": "Osmanlı ordusunda sınır boylarında görev yapan ve keşif hizmeti gören hafif süvari birliklerine ne ad verilir?", "opts": ["Akıncılar", "Azaplar", "Deliler", "Beşliler", "Sakalar"], "a": "Akıncılar"},
        {"q": "Kapıkulu ordusunun asker ihtiyacını karşılamak için I. Murat döneminde çıkarılan kanun nedir?", "opts": ["Pençik Kanunu", "Devşirme Kanunu", "Kanunname-i Ali Osman", "Tımar Kanunu", "Sancak Kanunu"], "a": "Pençik Kanunu"},
        {"q": "Pençik sistemi nedir?", "opts": ["Savaş esirlerinin beşte birinin asker yapılması", "Hristiyan çocukların toplanması", "Gönüllü askerlik", "Paralı askerlik", "Türkmenlerin asker yapılması"], "a": "Savaş esirlerinin beşte birinin asker yapılması"},
        {"q": "Yıldırım Bayezid'in İstanbul'u kuşatmak için yaptırdığı hisar hangisidir?", "opts": ["Güzelcehisar (Anadolu Hisarı)", "Rumeli Hisarı", "Boğazkesen", "Yedikule", "Çimenlik"], "a": "Güzelcehisar (Anadolu Hisarı)"},
        {"q": "Osmanlı'da sancaklara gönderilen şehzadelere ne ad verilir?", "opts": ["Çelebi Sultan", "Melik", "Tigin", "Atabey", "Lala"], "a": "Çelebi Sultan"},
        {"q": "Şehzadelerin sancaklarda devlet tecrübesi kazanması uygulamasına ne ad verilir?", "opts": ["Sancak Sistemi", "Kafes Sistemi", "Ekber ve Erşed", "Devşirme", "Müsadere"], "a": "Sancak Sistemi"},
        {"q": "Osmanlı Devleti'nin kuruluş yıllarında Balkanlarda feodalitenin yaygın olması ve siyasi birliğin olmaması Osmanlı'ya ne sağlamıştır?", "opts": ["Hızlı ilerleme ve fetih kolaylığı", "Savaşlarda yenilgi", "Ekonomik kriz", "İç isyan", "Nüfus kaybı"], "a": "Hızlı ilerleme ve fetih kolaylığı"}
    ],"9. Devletleşme Sürecinde Savaşçılar ve Askerler": [
        {"q": "Osmanlı Devleti'nde kurulan ilk düzenli ordu hangisidir?", "opts": ["Yaya ve Müsellem", "Yeniçeri Ocağı", "Tımarlı Sipahiler", "Akıncılar", "Azaplar"], "a": "Yaya ve Müsellem"},
        {"q": "Yaya ve Müsellem ordusu hangi padişah zamanında kurulmuştur?", "opts": ["Orhan Bey", "Osman Bey", "I. Murat", "Yıldırım Bayezid", "II. Murat"], "a": "Orhan Bey"},
        {"q": "Osmanlı ordusunda Kapıkulu Ocağı'nın asker ihtiyacını karşılamak için I. Murat döneminde uygulanan sistem nedir?", "opts": ["Pençik Sistemi", "Devşirme Sistemi", "Tımar Sistemi", "Müsadere Sistemi", "İltizam Sistemi"], "a": "Pençik Sistemi"},
        {"q": "Ankara Savaşı'ndan sonra asker ihtiyacını karşılamak için Pençik sisteminin yerine getirilen sistem nedir?", "opts": ["Devşirme Sistemi", "İskan Sistemi", "İstimalet", "Millet Sistemi", "Vakıf Sistemi"], "a": "Devşirme Sistemi"},
        {"q": "Devşirme sistemiyle toplanan çocukların ilk eğitildikleri yer neresidir?", "opts": ["Acemi Oğlanlar Ocağı", "Enderun", "Yeniçeri Ocağı", "Topçu Ocağı", "Humbaracı Ocağı"], "a": "Acemi Oğlanlar Ocağı"},
        {"q": "Kapıkulu Piyadeleri'nin en kalabalık ve en etkili grubu hangisidir?", "opts": ["Yeniçeriler", "Cebeciler", "Topçular", "Bostancılar", "Lağımcılar"], "a": "Yeniçeriler"},
        {"q": "Yeniçerilerin silahlarını yapan, tamir eden ve saklayan sınıf hangisidir?", "opts": ["Cebeciler", "Topçular", "Lağımcılar", "Humbaracılar", "Bostancılar"], "a": "Cebeciler"},
        {"q": "Kale kuşatmalarında tünel kazarak surları yıkan askeri sınıf hangisidir?", "opts": ["Lağımcılar", "Humbaracılar", "Topçular", "Sakalar", "Turnalar"], "a": "Lağımcılar"},
        {"q": "Havan topu ve el bombası yapımından sorumlu askeri sınıf hangisidir?", "opts": ["Humbaracılar", "Cebeciler", "Lağımcılar", "Topçular", "Bostancılar"], "a": "Humbaracılar"},
        {"q": "Kapıkulu Süvarileri (Atlılar) arasında yer alan ve savaşta sancağı koruyan grup hangisidir?", "opts": ["Sağ ve Sol Ulufeciler", "Silahtarlar", "Garipler", "Sipahiler", "Akıncılar"], "a": "Sağ ve Sol Ulufeciler"},
        {"q": "Savaşta hazineyi ve ganimetleri koruyan Kapıkulu Süvari birliği hangisidir?", "opts": ["Sağ ve Sol Garipler", "Ulufeciler", "Sipahiler", "Silahtarlar", "Deliler"], "a": "Sağ ve Sol Garipler"},
        {"q": "Tımarlı Sipahilerin yetiştirdiği atlı askerlere ne ad verilir?", "opts": ["Cebelü", "Yeniçeri", "Azap", "Lağımcı", "Levent"], "a": "Cebelü"},
        {"q": "Aşağıdakilerden hangisi Tımar sisteminin askeri faydalarından biridir?", "opts": ["Devlet hazinesinden para çıkmadan büyük bir ordu yetişmesi", "Donanmanın güçlenmesi", "Saray masraflarının azalması", "İstanbul'un güvenliğinin sağlanması", "Padişahın yetkilerinin artması"], "a": "Devlet hazinesinden para çıkmadan büyük bir ordu yetişmesi"},
        {"q": "Osmanlı ordusunda sınır boylarında görev yapan, keşif ve yıpratma savaşları yapan birlik hangisidir?", "opts": ["Akıncılar", "Azaplar", "Gönüllüler", "Beşliler", "Sakalar"], "a": "Akıncılar"},
        {"q": "Ordunun su ihtiyacını karşılayan yardımcı birlik hangisidir?", "opts": ["Sakalar", "Turnalar", "Derbentçiler", "Köprücüler", "Cerahorlar"], "a": "Sakalar"},
        {"q": "Ordunun haberleşmesini sağlayan yardımcı birlik hangisidir?", "opts": ["Turnalar", "Sakalar", "Yaya", "Müsellem", "Martoloslar"], "a": "Turnalar"},
        {"q": "Geçitlerin ve yolların güvenliğini sağlayan askeri grup hangisidir?", "opts": ["Derbentçiler", "Köprücüler", "Yörükler", "Turnalar", "Deliler"], "a": "Derbentçiler"},
        {"q": "Gönüllülerden oluşan, cesaretleri ve korkusuzluklarıyla bilinen, 'Tokat'ı ile meşhur birlik hangisidir?", "opts": ["Deliler", "Beşliler", "Azaplar", "Farisanlar", "Gönüllüler"], "a": "Deliler"},
        {"q": "Bekar Türk erkeklerinden oluşan ve savaşta ordunun en önünde yer alan hafif piyade birliği hangisidir?", "opts": ["Azaplar", "Akıncılar", "Yeniçeriler", "Cebeciler", "Sipahiler"], "a": "Azaplar"},
        {"q": "Osmanlı donanmasındaki askerlere ne ad verilir?", "opts": ["Levent (Bahriyeli)", "Yeniçeri", "Sipahi", "Cebelü", "Lağımcı"], "a": "Levent (Bahriyeli)"},
        {"q": "Osmanlı'da ilk tersane nerede kurulmuştur?", "opts": ["Karamürsel", "Gelibolu", "Haliç", "Sinop", "Rodos"], "a": "Karamürsel"},
        {"q": "Osmanlı'nın en büyük tersanesi (Tersane-i Amire) nerede kurulmuştur?", "opts": ["Haliç", "Gelibolu", "İzmit", "Süveyş", "Rusçuk"], "a": "Haliç"},
        {"q": "Osmanlı'da Kaptan-ı Derya'nın (Donanma Komutanı) Divan üyesi olması hangi padişah dönemindedir?", "opts": ["Kanuni Sultan Süleyman", "Fatih Sultan Mehmet", "Yavuz Sultan Selim", "II. Bayezid", "I. Süleyman"], "a": "Kanuni Sultan Süleyman"},
        {"q": "Kapıkulu askerlerinin üç ayda bir aldıkları maaşa ne ad verilir?", "opts": ["Ulufe", "Cülus", "İaşe", "Arpalık", "Gedik"], "a": "Ulufe"},
        {"q": "Her padişah değişikliğinde Kapıkulu askerlerine dağıtılan bahşişe ne ad verilir?", "opts": ["Cülus Bahşişi", "Ulufe", "Sefer Bahşişi", "Hakkı Huzur", "Aviz"], "a": "Cülus Bahşişi"},
        {"q": "Yeniçeri Ocağı'nın komutanına ne ad verilir?", "opts": ["Yeniçeri Ağası", "Kaptan-ı Derya", "Serasker", "Subaşı", "Sancak Beyi"], "a": "Yeniçeri Ağası"},
        {"q": "Osmanlı ordusunda ateşli silahların (Top) ilk kez kullanıldığı savaş hangisidir?", "opts": ["I. Kosova Savaşı", "Niğbolu Savaşı", "Sırpsındığı Savaşı", "Varna Savaşı", "Ankara Savaşı"], "a": "I. Kosova Savaşı"},
        {"q": "Osmanlı ordusunun merkezinde Padişahın yanında bulunanlar kimlerdir?", "opts": ["Kapıkulu Askerleri", "Tımarlı Sipahiler", "Eyalet Askerleri", "Akıncılar", "Azaplar"], "a": "Kapıkulu Askerleri"},
        {"q": "Tımarlı Sipahiler hangi ordunun temelini oluşturur?", "opts": ["Eyalet Ordusu", "Merkez Ordusu", "Deniz Ordusu", "Yardımcı Kuvvetler", "Saray Muhafızları"], "a": "Eyalet Ordusu"},
        {"q": "Tımar sisteminin bozulması en çok hangi askeri birliği olumsuz etkilemiştir?", "opts": ["Tımarlı Sipahiler", "Yeniçeriler", "Topçular", "Leventler", "Humbaracılar"], "a": "Tımarlı Sipahiler"},
        {"q": "Osmanlı'da gemi yapım yerlerine ne ad verilir?", "opts": ["Tersane", "Bedesten", "Kapan", "Lonca", "Zaviye"], "a": "Tersane"},
        {"q": "Barbaros Hayrettin Paşa'nın Osmanlı hizmetine girmesiyle Osmanlı donanması ne kazanmıştır?", "opts": ["Güçlü bir donanma ve Cezayir'i", "Kırım'ı", "Mısır'ı", "Girit'i", "Kıbrıs'ı"], "a": "Güçlü bir donanma ve Cezayir'i"},
        {"q": "Osmanlı ordusunun en kalabalık bölümünü hangisi oluşturur?", "opts": ["Tımarlı Sipahiler", "Yeniçeriler", "Kapıkulu Süvarileri", "Akıncılar", "Topçular"], "a": "Tımarlı Sipahiler"},
        {"q": "Yeniçeri Ocağı'na asker alımı için uygulanan 'Devşirme Kanunu' hangi padişah döneminde yasalaşmıştır?", "opts": ["II. Murat (Çelebi Mehmet dönemi uygulamalarıyla)", "I. Murat", "Fatih Sultan Mehmet", "Yavuz Sultan Selim", "Orhan Bey"], "a": "II. Murat (Çelebi Mehmet dönemi uygulamalarıyla)"},
        {"q": "Osmanlı'da 'Ocak Devlet İçindir' anlayışının 'Devlet Ocak İçindir' anlayışına dönmesi neye yol açmıştır?", "opts": ["Yeniçeri Ocağı'nın bozulmasına ve isyanlara", "Ordunun güçlenmesine", "Fetihlerin artmasına", "Ekonominin düzelmesine", "Tımar sisteminin gelişmesine"], "a": "Yeniçeri Ocağı'nın bozulmasına ve isyanlara"},
        {"q": "Tüfek icat oldu mertlik bozuldu sözüyle ateşli silahların etkisini anlatan halk ozanı kimdir?", "opts": ["Köroğlu", "Dadaloğlu", "Karacaoğlan", "Pir Sultan Abdal", "Yunus Emre"], "a": "Köroğlu"},
        {"q": "İstanbul'un fethinde kullanılan devasa toplara ne ad verilir?", "opts": ["Şahi", "Havan", "Obüs", "Mancınık", "Humabara"], "a": "Şahi"},
        {"q": "Osmanlı'da ilk topçu ocağını kim kurmuştur?", "opts": ["I. Murat", "Yıldırım Bayezid", "Fatih Sultan Mehmet", "II. Murat", "Orhan Bey"], "a": "I. Murat"},
        {"q": "Cebecilerin temel görevi nedir?", "opts": ["Silah yapımı ve bakımı", "Kale kuşatması", "Su taşıma", "Haberleşme", "Yol açma"], "a": "Silah yapımı ve bakımı"},
        {"q": "Acemi Oğlanlar Ocağı'ndan Yeniçeri Ocağı'na geçişe ne ad verilir?", "opts": ["Kapıya Çıkma (Bedergah)", "İcazet", "Şed Kuşanma", "Mülazemet", "Siftah"], "a": "Kapıya Çıkma (Bedergah)"},
        {"q": "Osmanlı kara ordusu kaç ana bölüme ayrılır?", "opts": ["3 (Kapıkulu, Eyalet, Yardımcı)", "2 (Merkez, Taşra)", "4 (Piyade, Süvari, Topçu, Deniz)", "5", "1"], "a": "3 (Kapıkulu, Eyalet, Yardımcı)"},
        {"q": "Osmanlı'da kale muhafızlarına ne ad verilir?", "opts": ["Dizdar", "Subaşı", "Kadı", "Sancakbeyi", "Beylerbeyi"], "a": "Dizdar"},
        {"q": "Sınırlarda bulunan kaleleri koruyan askerlere ne ad verilir?", "opts": ["Azaplar", "Gönüllüler", "Farisanlar", "Martoloslar", "Voynuklar"], "a": "Gönüllüler"},
        {"q": "Osmanlı ordusunda Hristiyanlardan oluşan ve ordunun atlarına bakan gruba ne ad verilir?", "opts": ["Voynuklar", "Martoloslar", "Cerahorlar", "Eflaklar", "Boğdanlar"], "a": "Voynuklar"},
        {"q": "Akıncıların en ünlü ailelerinden biri hangisidir?", "opts": ["Malkoçoğulları", "Çandarlılar", "Köprülüler", "Sokullular", "Balyanlar"], "a": "Malkoçoğulları"},
        {"q": "Yeniçerilerin sefere çıkmadan önce okudukları duaya ne ad verilir?", "opts": ["Gülbank", "Salb", "Fatiha", "Tekbir", "Fetih"], "a": "Gülbank"},
        {"q": "Osmanlı ordusunun lojistik desteğini (yiyecek, içecek, silah) sağlayan sisteme ne ad verilir?", "opts": ["Menzil Teşkilatı", "Derbent Teşkilatı", "Mekkari Taifesi", "Lonca", "Vakıf"], "a": "Menzil Teşkilatı"},
        {"q": "Ordunun yükünü taşıyan nakliye grubuna ne ad verilir?", "opts": ["Mekkari Taifesi", "Menzil", "Derbent", "Saka", "Turna"], "a": "Mekkari Taifesi"},
        {"q": "Tımarlı Sipahilerin kırsal alandaki en önemli görevi nedir?", "opts": ["Güvenliği sağlamak ve tarımsal üretimi denetlemek", "Vergi toplamak", "Yargılama yapmak", "Eğitim vermek", "Ticaret yapmak"], "a": "Güvenliği sağlamak ve tarımsal üretimi denetlemek"},
        {"q": "Kapıkulu askerlerinin evlenmesi ve başka işle uğraşması yasak mıdır?", "opts": ["Evet, yasaktır (Emekli olana kadar)", "Hayır, serbesttir", "Sadece evlenmek yasaktır", "Sadece ticaret yasaktır", "Padişah izniyle olabilir"], "a": "Evet, yasaktır (Emekli olana kadar)"}
    ],

    "10. Beylikten Devlete Osmanlı Medeniyeti": [
        {"q": "Osmanlı Devleti'nde bilinen ilk medrese hangisidir?", "opts": ["İznik Orhaniyesi", "Sahn-ı Seman", "Süleymaniye", "Fatih Medresesi", "Bursa Medresesi"], "a": "İznik Orhaniyesi"},
        {"q": "Osmanlı'nın ilk müderrisi (profesörü) olarak kabul edilen alim kimdir?", "opts": ["Davud-u Kayseri", "Molla Fenari", "Ali Kuşçu", "Akşemseddin", "Ebussuud Efendi"], "a": "Davud-u Kayseri"},
        {"q": "Osmanlı Devleti'nin ilk Şeyhülislamı kimdir?", "opts": ["Molla Fenari", "Ebussuud Efendi", "Zenbilli Ali Efendi", "İbn-i Kemal", "Akşemseddin"], "a": "Molla Fenari"},
        {"q": "Fatih Sultan Mehmet döneminde İstanbul'da açılan yükseköğretim kurumu hangisidir?", "opts": ["Sahn-ı Seman Medreseleri", "Süleymaniye Medreseleri", "İznik Medresesi", "Gök Medrese", "Çifte Minareli Medrese"], "a": "Sahn-ı Seman Medreseleri"},
        {"q": "Sahn-ı Seman Medreseleri'ne öğrenci yetiştirmek için açılan hazırlık okullarına ne ad verilir?", "opts": ["Tetimme", "Sıbyan Mektebi", "Enderun", "Rüştiye", "İdadi"], "a": "Tetimme"},
        {"q": "Fatih Sultan Mehmet'in hocası olan, İstanbul'un fethinin manevi mimarı sayılan alim kimdir?", "opts": ["Akşemseddin", "Molla Gürani", "Ali Kuşçu", "Uluğ Bey", "Hacı Bayram Veli"], "a": "Akşemseddin"},
        {"q": "Akkoyunlu Devleti'nden Osmanlı'ya gelerek İstanbul'da matematik ve astronomi dersleri veren bilgin kimdir?", "opts": ["Ali Kuşçu", "Uluğ Bey", "Kadızade Rumi", "Takiyüddin", "Matrakçı Nasuh"], "a": "Ali Kuşçu"},
        {"q": "Osmanlı'da 'Muallim-i Salis' (Üçüncü Öğretmen) olarak bilinen ünlü alim kimdir?", "opts": ["Yanyalı Esad Efendi", "Farabi", "İbn-i Sina", "Katip Çelebi", "Evliya Çelebi"], "a": "Yanyalı Esad Efendi"},
        {"q": "Kanuni Sultan Süleyman döneminin ünlü Şeyhülislamı ve hukukçusu kimdir?", "opts": ["Ebussuud Efendi", "Molla Fenari", "İbn-i Kemal", "Zembilli Ali Efendi", "Baki"], "a": "Ebussuud Efendi"},
        {"q": "Osmanlı'da 'Hace-i Evvel' (İlk Hoca) lakabıyla bilinen ünlü tarihçi ve alim kimdir?", "opts": ["Hoca Sadettin Efendi", "Naima", "Aşıkpaşazade", "Neşri", "Peçevi"], "a": "Hoca Sadettin Efendi"},
        {"q": "Osmanlı'da ilk rasathaneyi kuran bilim insanı kimdir?", "opts": ["Takiyüddin Mehmet", "Ali Kuşçu", "Uluğ Bey", "Lagari Hasan", "Hezarfen Ahmet"], "a": "Takiyüddin Mehmet"},
        {"q": "Osmanlı'da 'Seyahatname' adlı eseriyle tanınan dünyaca ünlü gezgin kimdir?", "opts": ["Evliya Çelebi", "Katip Çelebi", "Piri Reis", "Seydi Ali Reis", "Naima"], "a": "Evliya Çelebi"},
        {"q": "Katip Çelebi'nin 'Keşfü'z Zünun' adlı eseri hangi alandadır?", "opts": ["Bibliyografya", "Coğrafya", "Tarih", "Tıp", "Matematik"], "a": "Bibliyografya"},
        {"q": "Osmanlı'da 'Cihannüma' adlı coğrafya eserini yazan alim kimdir?", "opts": ["Katip Çelebi", "Evliya Çelebi", "Piri Reis", "Matrakçı Nasuh", "Seydi Ali Reis"], "a": "Katip Çelebi"},
        {"q": "Dünya haritasını çizen ve 'Kitab-ı Bahriye' adlı eseri yazan denizci kimdir?", "opts": ["Piri Reis", "Barbaros Hayrettin", "Seydi Ali Reis", "Turgut Reis", "Murat Reis"], "a": "Piri Reis"},
        {"q": "Osmanlı'da roketle ilk uçuş denemesini gerçekleştirdiği rivayet edilen kişi kimdir?", "opts": ["Lagari Hasan Çelebi", "Hezarfen Ahmet Çelebi", "Takiyüddin", "Ali Kuşçu", "Matrakçı Nasuh"], "a": "Lagari Hasan Çelebi"},
        {"q": "Galata Kulesi'nden Üsküdar'a kanat takarak uçtuğu rivayet edilen kişi kimdir?", "opts": ["Hezarfen Ahmet Çelebi", "Lagari Hasan Çelebi", "Takiyüddin", "Piri Reis", "Evliya Çelebi"], "a": "Hezarfen Ahmet Çelebi"},
        {"q": "Osmanlı'da minyatür sanatının en önemli temsilcilerinden biri olan 'Surname' eserinin çizeri kimdir?", "opts": ["Nakkaş Osman", "Matrakçı Nasuh", "Levni", "Nigari", "Sinan Bey"], "a": "Levni"},
        {"q": "Kanuni döneminde yaşayan ve minyatürleriyle şehirleri tasvir eden (Matrakçı) sanatçı kimdir?", "opts": ["Matrakçı Nasuh", "Levni", "Nakkaş Osman", "Nigari", "Sinan Bey"], "a": "Matrakçı Nasuh"},
        {"q": "Osmanlı'da 'Gül Koklayan Fatih' portresini yapan nakkaş kimdir?", "opts": ["Sinan Bey", "Levni", "Nakkaş Osman", "Matrakçı Nasuh", "Nigari"], "a": "Sinan Bey"},
        {"q": "Osmanlı'da hat sanatının en büyük ustalarından biri sayılan ve 'Kıbletü'l Küttab' denilen sanatçı kimdir?", "opts": ["Şeyh Hamdullah", "Hafız Osman", "Ahmet Karahisari", "Mustafa Rakım", "Levni"], "a": "Şeyh Hamdullah"},
        {"q": "Süleymaniye ve Selimiye camilerinin mimarı olan 'Koca Sinan' kimdir?", "opts": ["Mimar Sinan", "Mimar Hayrettin", "Sedefkar Mehmet Ağa", "Davud Ağa", "Kemaleddin"], "a": "Mimar Sinan"},
        {"q": "Mimar Sinan'ın 'Çıraklık Eserim' dediği cami hangisidir?", "opts": ["Şehzade Camii", "Süleymaniye Camii", "Selimiye Camii", "Rüstem Paşa Camii", "Mihrimah Sultan Camii"], "a": "Şehzade Camii"},
        {"q": "Mimar Sinan'ın 'Kalfalık Eserim' dediği cami hangisidir?", "opts": ["Süleymaniye Camii", "Şehzade Camii", "Selimiye Camii", "Fatih Camii", "Bayezid Camii"], "a": "Süleymaniye Camii"},
        {"q": "Mimar Sinan'ın 'Ustalık Eserim' dediği ve Edirne'de bulunan cami hangisidir?", "opts": ["Selimiye Camii", "Süleymaniye Camii", "Şehzade Camii", "Üç Şerefeli Cami", "Eski Cami"], "a": "Selimiye Camii"},
        {"q": "Sultanahmet Camii'nin (Blue Mosque) mimarı kimdir?", "opts": ["Sedefkar Mehmet Ağa", "Mimar Sinan", "Mimar Hayrettin", "Davud Ağa", "Dalgıç Ahmet"], "a": "Sedefkar Mehmet Ağa"},
        {"q": "Mostar Köprüsü'nün (Bosna-Hersek) mimarı kimdir?", "opts": ["Mimar Hayrettin", "Mimar Sinan", "Sedefkar Mehmet Ağa", "Davud Ağa", "Kemaleddin"], "a": "Mimar Hayrettin"},
        {"q": "Osmanlı'da ilk cami (Hacı Özbek Camii) hangi dönemde yapılmıştır?", "opts": ["Orhan Bey", "Osman Bey", "I. Murat", "Yıldırım Bayezid", "II. Murat"], "a": "Orhan Bey"},
        {"q": "Bursa Ulu Camii hangi padişah döneminde yapılmıştır?", "opts": ["Yıldırım Bayezid", "Orhan Bey", "I. Murat", "Çelebi Mehmet", "II. Murat"], "a": "Yıldırım Bayezid"},
        {"q": "Osmanlı'da sivil mimarinin en güzel örneklerinden olan ve ahşap işçiliğiyle ünlü evler nerede yoğunlaşmıştır?", "opts": ["Safranbolu", "İstanbul", "Bursa", "Edirne", "Konya"], "a": "Safranbolu"},
        {"q": "Osmanlı'da güzel yazı yazma sanatına ne ad verilir?", "opts": ["Hat", "Tezhip", "Minyatür", "Ebru", "Çini"], "a": "Hat"},
        {"q": "Kitap süsleme sanatına ve bu işi yapana ne ad verilir?", "opts": ["Tezhip - Müzehhip", "Hat - Hattat", "Minyatür - Nakkaş", "Ebru - Ebruzen", "Cilt - Mücellit"], "a": "Tezhip - Müzehhip"},
        {"q": "Osmanlı'da resim sanatının yerine gelişen, perspektifsiz kitap resimleme sanatına ne ad verilir?", "opts": ["Minyatür", "Hat", "Tezhip", "Ebru", "Fresk"], "a": "Minyatür"},
        {"q": "Seramik ve fayans süsleme sanatına ne ad verilir?", "opts": ["Çini", "Minyatür", "Hat", "Vitray", "Oymacılık"], "a": "Çini"},
        {"q": "Çini sanatının en önemli merkezleri nerelerdir?", "opts": ["İznik ve Kütahya", "Bursa ve Edirne", "İstanbul ve Konya", "Amasya ve Sivas", "Manisa ve Aydın"], "a": "İznik ve Kütahya"},
        {"q": "Osmanlı'da ahşap işçiliği sanatına ne ad verilir?", "opts": ["Kündekari (Oymacılık)", "Kakmacılık", "Telkari", "Malakari", "Edirnekari"], "a": "Kündekari (Oymacılık)"},
        {"q": "Osmanlı'da ciltçilik sanatıyla uğraşanlara ne ad verilir?", "opts": ["Mücellit", "Müzehhip", "Hattat", "Nakkaş", "Kazaz"], "a": "Mücellit"},
        {"q": "Osmanlı klasik döneminde şiirde en büyük temsilci sayılan, 'Sultanü'ş Şuara' (Şairler Sultanı) kimdir?", "opts": ["Baki", "Fuzuli", "Nedim", "Nefi", "Şeyh Galip"], "a": "Baki"},
        {"q": "Tasavvuf edebiyatının ve Mevleviliğin en büyük temsilcisi kimdir?", "opts": ["Mevlana", "Yunus Emre", "Hacı Bektaş Veli", "Pir Sultan Abdal", "Hacı Bayram Veli"], "a": "Mevlana"},
        {"q": "Hacı Bayram Veli hangi tarikatın kurucusudur?", "opts": ["Bayramiye", "Mevleviye", "Bektaşiye", "Nakşibendiye", "Kadiriyye"], "a": "Bayramiye"},
        {"q": "Osmanlı'da halk edebiyatının 'Pir'i sayılan şair kimdir?", "opts": ["Yunus Emre", "Karacaoğlan", "Köroğlu", "Dadaloğlu", "Aşık Veysel"], "a": "Yunus Emre"},
        {"q": "Osmanlı'da müzik alanında 'Nevakâr' makamını bulan ünlü bestekâr kimdir?", "opts": ["Itri", "Dede Efendi", "Hacı Arif Bey", "Tamburi Cemil Bey", "Sadullah Ağa"], "a": "Itri"},
        {"q": "Osmanlı'da tarih yazıcılığına ne ad verilir?", "opts": ["Vakanüvislik", "Şehnamecilik", "Tezkirecilik", "Siyer", "Hadis"], "a": "Vakanüvislik"},
        {"q": "Osmanlı'nın ilk resmi vakanüvisi (tarihçisi) kimdir?", "opts": ["Naima", "Aşıkpaşazade", "Hoca Sadettin", "Peçevi", "Neşri"], "a": "Naima"},
        {"q": "Ahilik teşkilatının kurucusu ve esnafın piri kimdir?", "opts": ["Ahi Evran", "Şeyh Edebali", "Dursun Fakih", "Hacı Bektaş Veli", "Somuncu Baba"], "a": "Ahi Evran"},
        {"q": "Osmanlı'da esnafın uyması gereken kuralları ve fiyatları belirleyen sisteme ne ad verilir?", "opts": ["Narh Sistemi", "Gedik", "Lonca", "Ahilik", "Vakıf"], "a": "Narh Sistemi"},
        {"q": "Osmanlı'da dükkan açma hakkına (ruhsatına) ne ad verilir?", "opts": ["Gedik", "Narh", "Berat", "Ferman", "İcazet"], "a": "Gedik"},
        {"q": "Osmanlı'da sosyal yardımlaşma ve dayanışmanın en önemli kurumu hangisidir?", "opts": ["Vakıf", "Lonca", "Enderun", "Darülaceze", "Külliye"], "a": "Vakıf"},
        {"q": "Süleymaniye Külliyesi'nin içinde hangisi bulunmaz?", "opts": ["Saray", "Cami", "Medrese", "Darüşşifa", "İmaret"], "a": "Saray"},
        {"q": "Osmanlı'da bayramlarda ve şenliklerde halkı eğlendiren oyunlara ne ad verilir?", "opts": ["Temaşa Sanatları (Karagöz, Ortaoyunu)", "Opera", "Bale", "Tiyatro", "Sinema"], "a": "Temaşa Sanatları (Karagöz, Ortaoyunu)"}
    ],

    "11. Dünya Gücü Osmanlı": [
        {"q": "İstanbul'un fethinin (1453) Türk tarihi açısından en önemli sonucu nedir?", "opts": ["Osmanlı Devleti'nin İmparatorluk aşamasına geçmesi ve Yükselme Dönemi'nin başlaması", "Haçlı Seferleri'nin başlaması", "Coğrafi Keşifler'in başlaması", "Rönesans'ın başlaması", "Derebeyliğin yıkılması"], "a": "Osmanlı Devleti'nin İmparatorluk aşamasına geçmesi ve Yükselme Dönemi'nin başlaması"},
        {"q": "İstanbul'un fethinin Dünya tarihi açısından en önemli sonucu nedir?", "opts": ["Orta Çağ'ın kapanıp Yeni Çağ'ın başlaması", "Osmanlı'nın başkentinin değişmesi", "Ortodoksların himaye altına alınması", "Ticaret yollarının Türklerin eline geçmesi", "Fatih'in unvan alması"], "a": "Orta Çağ'ın kapanıp Yeni Çağ'ın başlaması"},
        {"q": "Fatih Sultan Mehmet'in Karadeniz'i Türk gölü haline getirmek için fethettiği yerlerden biri değildir?", "opts": ["Mora Yarımadası", "Amasra", "Sinop", "Trabzon", "Kırım"], "a": "Mora Yarımadası"},
        {"q": "Fatih Sultan Mehmet'in 'Kayser-i Rum' (Roma İmparatoru) unvanını alması neyi gösterir?", "opts": ["Roma'nın varisi olma iddiasını", "Hristiyan olduğunu", "Anadolu birliğini kurduğunu", "Halife olduğunu", "Avrupa'dan korktuğunu"], "a": "Roma'nın varisi olma iddiasını"},
        {"q": "Akkoyunlu Hükümdarı Uzun Hasan'ın mağlup edildiği ve Doğu Anadolu güvenliğinin sağlandığı savaş (1473) hangisidir?", "opts": ["Otlukbeli Savaşı", "Çaldıran Savaşı", "Turnadağ Savaşı", "Mercidabık Savaşı", "Ridaniye Savaşı"], "a": "Otlukbeli Savaşı"},
        {"q": "Osmanlı tarihinde bir iç sorunken dış sorun haline gelen olay hangisidir?", "opts": ["Cem Sultan Olayı", "Şeyh Bedrettin İsyanı", "Düzmece Mustafa Olayı", "Kavalalı Mehmet Ali Paşa İsyanı", "Celali İsyanları"], "a": "Cem Sultan Olayı"},
        {"q": "II. Bayezid döneminin 'Sönük Dönem' olarak adlandırılmasının temel sebebi nedir?", "opts": ["Cem Sultan Olayı nedeniyle fetihlerin duraklaması", "Ekonomik kriz", "Padişahın yeteneksizliği", "Ordunun isyan etmesi", "Savaş kaybedilmesi"], "a": "Cem Sultan Olayı nedeniyle fetihlerin duraklaması"},
        {"q": "Yavuz Sultan Selim'in Safevilerle yaptığı ve Doğu Anadolu'yu güvence altına aldığı savaş (1514) hangisidir?", "opts": ["Çaldıran Savaşı", "Turnadağ Savaşı", "Mercidabık Savaşı", "Ridaniye Savaşı", "Otlukbeli Savaşı"], "a": "Çaldıran Savaşı"},
        {"q": "Yavuz Sultan Selim'in Memlükleri yenerek Mısır'ı fethettiği savaşlar hangileridir?", "opts": ["Mercidabık ve Ridaniye", "Çaldıran ve Turnadağ", "Otlukbeli ve Çaldıran", "Mohaç ve Preveze", "Varna ve Kosova"], "a": "Mercidabık ve Ridaniye"},
        {"q": "Mısır Seferi'nin en önemli dini sonucu nedir?", "opts": ["Halifeliğin Osmanlı'ya geçmesi", "Baharat Yolu'nun kontrolü", "Hazine'nin dolması", "Kutsal Emanetlerin gelmesi", "Memlüklerin yıkılması"], "a": "Halifeliğin Osmanlı'ya geçmesi"},
        {"q": "Yavuz Sultan Selim döneminde Anadolu Türk siyasi birliğinin kesin olarak sağlandığı savaş hangisidir?", "opts": ["Turnadağ Savaşı (Dulkadiroğulları'nın alınması)", "Çaldıran Savaşı", "Mercidabık Savaşı", "Otlukbeli Savaşı", "Ridaniye Savaşı"], "a": "Turnadağ Savaşı (Dulkadiroğulları'nın alınması)"},
        {"q": "Osmanlı tarihinde en uzun süre tahta kalan padişah kimdir?", "opts": ["Kanuni Sultan Süleyman (46 yıl)", "Fatih Sultan Mehmet", "Orhan Bey", "IV. Mehmet", "Abdülhamid"], "a": "Kanuni Sultan Süleyman (46 yıl)"},
        {"q": "Kanuni Sultan Süleyman'ın Belgrad'ı fethinin önemi nedir?", "opts": ["Orta Avrupa'nın kapılarının açılması", "Macaristan'ın alınması", "Viyana'nın alınması", "Almanya'nın fethi", "Rusya'ya sefer"], "a": "Orta Avrupa'nın kapılarının açılması"},
        {"q": "Dünyanın en kısa süren (2 saat) meydan savaşı hangisidir?", "opts": ["Mohaç Meydan Savaşı", "Çaldıran Savaşı", "Kosova Savaşı", "Varna Savaşı", "Niğbolu Savaşı"], "a": "Mohaç Meydan Savaşı"},
        {"q": "Osmanlı'nın ilk kez Viyana'yı kuşattığı ancak alamadığı sefer hangisidir?", "opts": ["I. Viyana Kuşatması", "II. Viyana Kuşatması", "Almanya Seferi", "Zigetvar Seferi", "Belgrad Seferi"], "a": "I. Viyana Kuşatması"},
        {"q": "Osmanlı'nın Avusturya Arşidükü'nü protokolde Osmanlı Sadrazamına denk saydığı antlaşma (1533) hangisidir?", "opts": ["İstanbul (İbrahim Paşa) Antlaşması", "Zitvatorok Antlaşması", "Karlofça Antlaşması", "Pasarofça Antlaşması", "Vasvar Antlaşması"], "a": "İstanbul (İbrahim Paşa) Antlaşması"},
        {"q": "Akdeniz'in 'Türk Gölü' haline gelmesini sağlayan deniz zaferi hangisidir?", "opts": ["Preveze Deniz Savaşı", "Cerbe Deniz Savaşı", "İnebahtı Deniz Savaşı", "Kıbrıs'ın Fethi", "Rodos'un Fethi"], "a": "Preveze Deniz Savaşı"},
        {"q": "Preveze Deniz Zaferi'ni kazanan ünlü Türk denizcisi kimdir?", "opts": ["Barbaros Hayrettin Paşa", "Turgut Reis", "Piri Reis", "Piyale Paşa", "Seydi Ali Reis"], "a": "Barbaros Hayrettin Paşa"},
        {"q": "Fransa'ya kapitülasyonların verilmesinin temel siyasi amacı nedir?", "opts": ["Avrupa Hristiyan birliğini bozmak", "Fransa'yı fethetmek", "Fransız kültürünü almak", "Ticaret yollarını değiştirmek", "Akdeniz'i korumak"], "a": "Avrupa Hristiyan birliğini bozmak"},
        {"q": "Kanuni Sultan Süleyman'ın son seferi hangisidir?", "opts": ["Zigetvar Seferi", "Viyana Kuşatması", "Almanya Seferi", "Irakeyn Seferi", "Nahçıvan Seferi"], "a": "Zigetvar Seferi"},
        {"q": "Sokullu Mehmet Paşa'nın sadrazamlığı döneminde hayata geçiremediği 'Don-Volga Kanalı Projesi'nin amacı neydi?", "opts": ["Rusya'nın güneye inmesini engellemek ve Orta Asya Türkleri ile birleşmek", "Akdeniz ticaretini canlandırmak", "Kızıldeniz'i birleştirmek", "Hindistan'a ulaşmak", "Avrupa'ya geçmek"], "a": "Rusya'nın güneye inmesini engellemek ve Orta Asya Türkleri ile birleşmek"},
        {"q": "Sokullu Mehmet Paşa'nın 'Süveyş Kanalı Projesi'nin amacı neydi?", "opts": ["Baharat Yolu'nu canlandırmak ve Portekiz'i Hint Okyanusu'ndan uzaklaştırmak", "Rusya'yı durdurmak", "İran'ı kuşatmak", "Hazar Denizi'ne ulaşmak", "Karadeniz'i korumak"], "a": "Baharat Yolu'nu canlandırmak ve Portekiz'i Hint Okyanusu'ndan uzaklaştırmak"},
        {"q": "Kıbrıs'ın fethine tepki olarak Haçlıların Osmanlı donanmasını yaktığı ilk olay hangisidir?", "opts": ["İnebahtı Deniz Savaşı", "Navarin Baskını", "Çeşme Baskını", "Sinop Baskını", "Preveze Savaşı"], "a": "İnebahtı Deniz Savaşı"},
        {"q": "Osmanlı'nın doğuda en geniş sınırlara ulaştığı antlaşma hangisidir?", "opts": ["Ferhat Paşa Antlaşması", "Amasya Antlaşması", "Kasr-ı Şirin Antlaşması", "Nasuh Paşa Antlaşması", "Serav Antlaşması"], "a": "Ferhat Paşa Antlaşması"},
        {"q": "Fatih Sultan Mehmet döneminde İtalya'nın fethi için yapılan ve Fatih'in ölümüyle yarım kalan sefer neresidir?", "opts": ["Otranto Seferi", "Roma Seferi", "Venedik Seferi", "Napoli Seferi", "Sicilya Seferi"], "a": "Otranto Seferi"},
        {"q": "Yavuz Sultan Selim'in 'Hazineyi kim benim kadar doldurursa mühür benim mührümle değil onunkiyle mühürlensin' vasiyeti neyi gösterir?", "opts": ["Ekonominin zirveye ulaştığını", "Cimri olduğunu", "Savaş sevdiğini", "İsrafı sevmediğini", "Halife olduğunu"], "a": "Ekonominin zirveye ulaştığını"},
        {"q": "Hint Deniz Seferleri'nin başarısız olmasının temel nedeni nedir?", "opts": ["Osmanlı gemilerinin okyanuslara dayanıklı olmaması ve gereken önemin verilmemesi", "Komutanların ihaneti", "Asker azlığı", "Yolun uzaklığı", "Portekiz'in güçlü olması"], "a": "Osmanlı gemilerinin okyanuslara dayanıklı olmaması ve gereken önemin verilmemesi"},
        {"q": "Rodos Adası'nı fethederek Ege Denizi güvenliğini sağlayan padişah kimdir?", "opts": ["Kanuni Sultan Süleyman", "Fatih Sultan Mehmet", "Yavuz Sultan Selim", "II. Bayezid", "II. Selim"], "a": "Kanuni Sultan Süleyman"},
        {"q": "Osmanlı Devleti'nin Safevilerle (İran) yaptığı ilk resmi antlaşma (1555) hangisidir?", "opts": ["Amasya Antlaşması", "Kasr-ı Şirin Antlaşması", "Ferhat Paşa Antlaşması", "Nasuh Paşa Antlaşması", "Kerden Antlaşması"], "a": "Amasya Antlaşması"},
        {"q": "Kırım Hanlığı'nın Osmanlı'ya bağlanması (Fatih dönemi) neyi sağlamıştır?", "opts": ["Karadeniz'in Türk gölü olmasını", "Akdeniz hakimiyetini", "Mısır'ın fethini", "Anadolu birliğini", "Rusya'nın yıkılmasını"], "a": "Karadeniz'in Türk gölü olmasını"},
        {"q": "Osmanlı'nın Kuzey Afrika hakimiyetini pekiştiren ve İspanyollara karşı kazanılan zafer hangisidir?", "opts": ["Cerbe Deniz Savaşı", "Preveze Deniz Savaşı", "İnebahtı", "Navarin", "Çeşme"], "a": "Cerbe Deniz Savaşı"},
        {"q": "Sokullu Mehmet Paşa hangi padişahlara sadrazamlık yapmıştır?", "opts": ["Kanuni, II. Selim, III. Murat", "Fatih, II. Bayezid", "Yavuz, Kanuni", "I. Ahmet, II. Osman", "IV. Murat, İbrahim"], "a": "Kanuni, II. Selim, III. Murat"},
        {"q": "Fatih döneminde 'Kanunname-i Ali Osman' ile yasalaşan ve devletin bekası için izin verilen uygulama nedir?", "opts": ["Kardeş Katli", "Devşirme", "Müsadere", "Sancak", "Ekber ve Erşed"], "a": "Kardeş Katli"},
        {"q": "Topkapı Sarayı hangi padişah döneminde inşa edilmiştir?", "opts": ["Fatih Sultan Mehmet", "Kanuni Sultan Süleyman", "Yavuz Sultan Selim", "I. Murat", "Orhan Bey"], "a": "Fatih Sultan Mehmet"},
        {"q": "Osmanlı'da 'Muhibbi' mahlasıyla şiirler yazan padişah kimdir?", "opts": ["Kanuni Sultan Süleyman", "Fatih Sultan Mehmet", "Yavuz Sultan Selim", "II. Bayezid", "II. Selim"], "a": "Kanuni Sultan Süleyman"},
        {"q": "Osmanlı'da 'Avni' mahlasıyla şiirler yazan padişah kimdir?", "opts": ["Fatih Sultan Mehmet", "Kanuni Sultan Süleyman", "Yavuz Sultan Selim", "II. Murat", "III. Selim"], "a": "Fatih Sultan Mehmet"},
        {"q": "Osmanlı'nın Memlükleri yıkarak ele geçirdiği en önemli ticaret yolu hangisidir?", "opts": ["Baharat Yolu", "İpek Yolu", "Kürk Yolu", "Kral Yolu", "Makedonya Yolu"], "a": "Baharat Yolu"},
        {"q": "II. Bayezid döneminde çıkan ve Safevilerin kışkırttığı isyan hangisidir?", "opts": ["Şahkulu İsyanı", "Şeyh Bedrettin İsyanı", "Babai İsyanı", "Celali İsyanları", "Buçuktepe İsyanı"], "a": "Şahkulu İsyanı"},
        {"q": "Yavuz Sultan Selim'in babası II. Bayezid'i tahttan indirerek başa geçmesi Osmanlı tarihinde nasıl bir ilktir?", "opts": ["Yeniçeri desteğiyle babasını tahttan indiren ilk padişah", "Savaşarak tahta geçen ilk padişah", "Seçimle gelen ilk padişah", "Halife olan ilk padişah", "Kardeşini öldürmeyen ilk padişah"], "a": "Yeniçeri desteğiyle babasını tahttan indiren ilk padişah"},
        {"q": "Turgut Reis'in şehit düştüğü kuşatma hangisidir?", "opts": ["Malta Kuşatması", "Rodos Kuşatması", "Girit Kuşatması", "Kıbrıs Kuşatması", "Viyana Kuşatması"], "a": "Malta Kuşatması"},
        {"q": "Kıbrıs'ın fethi hangi sadrazamın ısrarıyla gerçekleşmiştir?", "opts": ["Lala Mustafa Paşa (ve Sokullu dönemi)", "Pargalı İbrahim", "Lütfi Paşa", "Rüstem Paşa", "Sinan Paşa"], "a": "Lala Mustafa Paşa (ve Sokullu dönemi)"},
        {"q": "Fatih Sultan Mehmet'in Ortodoks Kilisesi'ni himaye etmesinin amacı nedir?", "opts": ["Hristiyan birliğini parçalamak", "Ortodoks olmak", "Katoliklerle savaşmak", "Ticaret yapmak", "Papa ile anlaşmak"], "a": "Hristiyan birliğini parçalamak"},
        {"q": "Belgrad ve Rodos'u fetheden, Mohaç'ı kazanan padişah kimdir?", "opts": ["Kanuni Sultan Süleyman", "Fatih Sultan Mehmet", "Yavuz Sultan Selim", "II. Bayezid", "I. Ahmet"], "a": "Kanuni Sultan Süleyman"},
        {"q": "Cezayir'in Osmanlı'ya savaşsız katılması nasıl olmuştur?", "opts": ["Barbaros Hayrettin Paşa'nın Osmanlı hizmetine girmesiyle", "Halk oylamasıyla", "Satın alınarak", "Miras yoluyla", "Antlaşma ile"], "a": "Barbaros Hayrettin Paşa'nın Osmanlı hizmetine girmesiyle"},
        {"q": "Osmanlı Devleti'nin imparatorluk karakteri kazanması ne demektir?", "opts": ["Çok uluslu ve çok dinli bir yapıya sahip olması", "Zengin olması", "Güçlü ordusu olması", "Padişahla yönetilmesi", "Halife olması"], "a": "Çok uluslu ve çok dinli bir yapıya sahip olması"},
        {"q": "Fatih'in 'Ülke hükümdarın malıdır' anlayışını getirmesinin amacı nedir?", "opts": ["Merkezi otoriteyi güçlendirmek", "Taht kavgalarını artırmak", "Demokrasiyi getirmek", "Halkı yönetime katmak", "Vergileri artırmak"], "a": "Merkezi otoriteyi güçlendirmek"},
        {"q": "Yavuz Sultan Selim'in doğu siyasetini belirleyen ve ona danışmanlık yapan Kürt alim kimdir?", "opts": ["İdris-i Bitlisi", "Ebussuud Efendi", "Molla Gürani", "Akşemseddin", "Ali Kuşçu"], "a": "İdris-i Bitlisi"},
        {"q": "Osmanlı'da '8 yılda 80 yıllık iş sığdıran padişah' olarak bilinen kimdir?", "opts": ["Yavuz Sultan Selim", "Fatih Sultan Mehmet", "Kanuni Sultan Süleyman", "IV. Murat", "Genç Osman"], "a": "Yavuz Sultan Selim"},
        {"q": "Kanuni döneminde Fransa'ya verilen kapitülasyonların süresi ne kadardı?", "opts": ["İki hükümdarın ömrüyle sınırlı", "Sonsuz", "100 yıl", "50 yıl", "10 yıl"], "a": "İki hükümdarın ömrüyle sınırlı"},
        {"q": "Osmanlı'nın Akdeniz'deki üstünlüğünü sona erdiren savaş hangisidir?", "opts": ["İnebahtı Deniz Savaşı", "Preveze", "Cerbe", "Navarin", "Çeşme"], "a": "İnebahtı Deniz Savaşı"}
    ],

    "12. Sultan ve Osmanlı Merkez Teşkilatı": [
        {"q": "Osmanlı devlet yönetiminin merkezi neresidir?", "opts": ["Topkapı Sarayı", "Dolmabahçe Sarayı", "Yıldız Sarayı", "Beylerbeyi Sarayı", "Çırağan Sarayı"], "a": "Topkapı Sarayı"},
        {"q": "Topkapı Sarayı'nın bölümleri nelerdir?", "opts": ["Birun - Enderun - Harem", "Selamlık - Mabeyn - Harem", "Divan - Adliye - Maliye", "Taşra - Merkez - Eyalet", "Kışla - Tersane - Tophane"], "a": "Birun - Enderun - Harem"},
        {"q": "Sarayın dış bölümü olan, devlet işlerinin görüşüldüğü ve törenlerin yapıldığı yer neresidir?", "opts": ["Birun", "Enderun", "Harem", "Şehzadegan", "Hasoda"], "a": "Birun"},
        {"q": "Devlet adamı yetiştirilen saray okulu ve iç saray bölümü neresidir?", "opts": ["Enderun", "Birun", "Harem", "Medrese", "Tekke"], "a": "Enderun"},
        {"q": "Padişahın ve ailesinin özel hayatını sürdürdüğü bölüme ne ad verilir?", "opts": ["Harem", "Enderun", "Birun", "Divan", "Kubbealtı"], "a": "Harem"},
        {"q": "Divan-ı Hümayun hangi padişah döneminde kurulmuştur?", "opts": ["Orhan Bey", "Osman Bey", "I. Murat", "Fatih Sultan Mehmet", "Kanuni Sultan Süleyman"], "a": "Orhan Bey"},
        {"q": "Divan-ı Hümayun'a Fatih dönemine kadar kim başkanlık etmiştir?", "opts": ["Padişah", "Sadrazam", "Şeyhülislam", "Kazasker", "Nişancı"], "a": "Padişah"},
        {"q": "Fatih'ten itibaren Divan'a kim başkanlık etmeye başlamıştır?", "opts": ["Sadrazam (Vezir-i Azam)", "Padişah", "Şeyhülislam", "Defterdar", "Kazasker"], "a": "Sadrazam (Vezir-i Azam)"},
        {"q": "Padişahın mutlak vekili olan ve padişah mührünü taşıyan divan üyesi kimdir?", "opts": ["Sadrazam", "Kazasker", "Nişancı", "Defterdar", "Kaptan-ı Derya"], "a": "Sadrazam"},
        {"q": "Divanda büyük davalara bakan, kadı ve müderrisleri atayan (Adalet ve Eğitim Bakanı) üye kimdir?", "opts": ["Kazasker", "Şeyhülislam", "Nişancı", "Defterdar", "Reisülküttab"], "a": "Kazasker"},
        {"q": "Divanda mali işlere bakan ve bütçeyi hazırlayan (Maliye Bakanı) üye kimdir?", "opts": ["Defterdar", "Nişancı", "Kazasker", "Sadrazam", "Reisülküttab"], "a": "Defterdar"},
        {"q": "Divanda fetva veren, din işlerinden sorumlu en yetkili kişi kimdir?", "opts": ["Şeyhülislam (Müftü)", "Kazasker", "Kadı", "Nişancı", "İmam"], "a": "Şeyhülislam (Müftü)"},
        {"q": "Padişah fermanlarına tuğra çeken ve tapu kadastro işlerine bakan divan üyesi kimdir?", "opts": ["Nişancı", "Defterdar", "Kazasker", "Reisülküttab", "Sadrazam"], "a": "Nişancı"},
        {"q": "17. yüzyıldan sonra dış işlerinden sorumlu olan (Dışişleri Bakanı) divan üyesi kimdir?", "opts": ["Reisülküttab", "Nişancı", "Sadrazam", "Defterdar", "Kaptan-ı Derya"], "a": "Reisülküttab"},
        {"q": "Donanma komutanı olan ve İstanbul'daysa Divan toplantılarına katılan üye kimdir?", "opts": ["Kaptan-ı Derya", "Yeniçeri Ağası", "Subaşı", "Sancakbeyi", "Levent"], "a": "Kaptan-ı Derya"},
        {"q": "İstanbul'un güvenliğinden sorumlu olan ve gerekirse Divan'a katılan komutan kimdir?", "opts": ["Yeniçeri Ağası", "Subaşı", "Böcekbaşı", "Asesbaşı", "Kaptan-ı Derya"], "a": "Yeniçeri Ağası"},
        {"q": "Osmanlı'da 'Veraset Sistemi'nde ilk değişikliği yapan (Ülke padişah ve oğullarınındır) padişah kimdir?", "opts": ["I. Murat", "Orhan Bey", "Fatih Sultan Mehmet", "I. Ahmet", "Yavuz Sultan Selim"], "a": "I. Murat"},
        {"q": "Kardeş katlini yasallaştıran (Nizam-ı Alem için) padişah kimdir?", "opts": ["Fatih Sultan Mehmet", "I. Murat", "Kanuni Sultan Süleyman", "Yavuz Sultan Selim", "II. Bayezid"], "a": "Fatih Sultan Mehmet"},
        {"q": "Veraset sisteminde son değişikliği yaparak 'Ekber ve Erşed' (En yaşlı ve en akıllı) sistemini getiren padişah kimdir?", "opts": ["I. Ahmet", "I. Murat", "Fatih Sultan Mehmet", "II. Osman", "IV. Murat"], "a": "I. Ahmet"},
        {"q": "Sancak sistemini kaldırarak 'Kafes Usulü'nü getiren padişah kimdir?", "opts": ["I. Ahmet", "III. Mehmet", "II. Osman", "IV. Murat", "I. Mustafa"], "a": "III. Mehmet"},
        {"q": "Şehzadelerin sancağa çıkma uygulamasının temel amacı nedir?", "opts": ["Devlet yönetimi ve askerlik tecrübesi kazanmaları", "İstanbul'dan uzaklaşmaları", "Halkı tanımaları", "Vergi toplamaları", "Ordu kurmaları"], "a": "Devlet yönetimi ve askerlik tecrübesi kazanmaları"},
        {"q": "Osmanlı'da padişahın yetkilerini kısıtlayan ilk belge (anayasal belge değil) nedir?", "opts": ["Sened-i İttifak", "Tanzimat Fermanı", "Islahat Fermanı", "Kanun-i Esasi", "Ferman-ı Adalet"], "a": "Sened-i İttifak"},
        {"q": "Osmanlı'da devletin yönetim birimleri büyükten küçüğe nasıldır?", "opts": ["Eyalet - Sancak - Kaza - Köy", "Köy - Kaza - Sancak - Eyalet", "Vilayet - Liva - Nahiye - Köy", "Merkez - Taşra", "Eyalet - Köy - Kaza"], "a": "Eyalet - Sancak - Kaza - Köy"},
        {"q": "Eyaletlerin başında bulunan en büyük mülki amir kimdir?", "opts": ["Beylerbeyi", "Sancakbeyi", "Kadı", "Subaşı", "Köy Kethüdası"], "a": "Beylerbeyi"},
        {"q": "Sancakların (İllerin) başında bulunan yönetici kimdir?", "opts": ["Sancakbeyi", "Beylerbeyi", "Kadı", "Subaşı", "Muhtesib"], "a": "Sancakbeyi"},
        {"q": "Kazaların (İlçelerin) hem yöneticisi hem de yargıcı olan görevli kimdir?", "opts": ["Kadı", "Subaşı", "Beylerbeyi", "Sancakbeyi", "Naib"], "a": "Kadı"},
        {"q": "Köyün yöneticisi kimdir?", "opts": ["Köy Kethüdası", "Muhtar", "İmam", "Subaşı", "Yiğitbaşı"], "a": "Köy Kethüdası"},
        {"q": "Salyaneli (Yıllıklı) eyaletlerde vergiler hangi usulle toplanır?", "opts": ["İltizam Usulü", "Tımar Sistemi", "Vakıf Sistemi", "Emanet Usulü", "Müsadere"], "a": "İltizam Usulü"},
        {"q": "Tımar sisteminin uygulandığı eyaletlere ne ad verilir?", "opts": ["Salyanesiz (Yıllıksız) Eyaletler", "Salyaneli Eyaletler", "İmtiyazlı Eyaletler", "Özel Yönetimli Eyaletler", "Yurtluk"], "a": "Salyanesiz (Yıllıksız) Eyaletler"},
        {"q": "İç işlerinde serbest, dış işlerinde Osmanlı'ya bağlı olan (Kırım, Eflak, Boğdan vb.) eyaletlere ne ad verilir?", "opts": ["İmtiyazlı Eyaletler", "Salyaneli Eyaletler", "Salyanesiz Eyaletler", "Yurtluk", "Ocaklık"], "a": "İmtiyazlı Eyaletler"},
        {"q": "Padişahın yasama (kanun yapma) yetkisini kullandığı belgelere ne ad verilir?", "opts": ["Ferman, Kanunname, Berat", "Fetva", "Hutbe", "Sikke", "Arz"], "a": "Ferman, Kanunname, Berat"},
        {"q": "Müsadere sistemi nedir?", "opts": ["Devletin haksız kazanç sağlayan memurun malına el koyması", "Toprak dağıtımı", "Vergi toplama", "Asker alma", "Maaş ödeme"], "a": "Devletin haksız kazanç sağlayan memurun malına el koyması"},
        {"q": "Osmanlı'da 'Kut' anlayışı nasıl devam etmiştir?", "opts": ["Allah'ın yeryüzündeki gölgesi (Zillullah) olarak", "Seçimle", "Soylu sınıfıyla", "Rahiplerle", "Askeri güçle"], "a": "Allah'ın yeryüzündeki gölgesi (Zillullah) olarak"},
        {"q": "Osmanlı'da şehzadelerin eğitiminden sorumlu olan hocalara ne ad verilir?", "opts": ["Lala", "Atabey", "Müderris", "Muallim", "Danişmend"], "a": "Lala"},
        {"q": "Sarayda dilsizlerin ve cücelerin hizmet ettiği, padişahın güvenliğini sağlayan bölüm hangisidir?", "opts": ["Enderun", "Harem", "Birun", "Arz Odası", "Kubbealtı"], "a": "Enderun"},
        {"q": "Osmanlı'da divan kararlarının yazıldığı defterlere ne ad verilir?", "opts": ["Mühimme Defterleri", "Tahrir Defterleri", "Şeriye Sicilleri", "Tereke Defterleri", "Ruznamçe"], "a": "Mühimme Defterleri"},
        {"q": "Toprak kayıtlarının tutulduğu defterlere ne ad verilir?", "opts": ["Tahrir Defterleri", "Mühimme Defterleri", "Şeriye Sicilleri", "Cizye Defteri", "Avarız Defteri"], "a": "Tahrir Defterleri"},
        {"q": "Osmanlı'da adalet işlerinin temeli neye dayanır?", "opts": ["Şeri ve Örfi Hukuk", "Sadece Şeri Hukuk", "Sadece Örfi Hukuk", "Roma Hukuku", "Cengiz Yasası"], "a": "Şeri ve Örfi Hukuk"},
        {"q": "Padişahın yetkilerini sınırlayan bir güç var mıdır?", "opts": ["Şeriat ve Töre (Örf)", "Yoktur, sınırsızdır", "Yeniçeriler", "Sadrazam", "Halk"], "a": "Şeriat ve Töre (Örf)"},
        {"q": "Osmanlı'da devletin dış işlerindeki yazışmalarını yürüten kalem hangisidir?", "opts": ["Divan-ı Hümayun Kalemi (Beylikçi)", "Tahvil Kalemi", "Ruus Kalemi", "Amedi Kalemi", "Maliye Kalemi"], "a": "Divan-ı Hümayun Kalemi (Beylikçi)"},
        {"q": "Kubbealtı Vezirleri kime denir?", "opts": ["Divan toplantılarına katılan vezirlere", "Sancak beylerine", "Emekli vezirlere", "Saray görevlilerine", "Taşra yöneticilerine"], "a": "Divan toplantılarına katılan vezirlere"},
        {"q": "Osmanlı'da padişahın yetkisini temsil eden sembollerden biri değildir?", "opts": ["Asa", "Hutbe", "Sikke (Para)", "Tuğra", "Çetr (Şemsiye)"], "a": "Asa"},
        {"q": "Osmanlı'da yönetici sınıfın (Askeri) vergi vermemesi neye dayanır?", "opts": ["Devlet hizmeti görmelerine", "Zengin olmalarına", "Soylu olmalarına", "Padişah akrabası olmalarına", "Türk olmalarına"], "a": "Devlet hizmeti görmelerine"},
        {"q": "Padişahın tahta çıkış törenine ne ad verilir?", "opts": ["Cülus Töreni", "Kılıç Alayı", "Biad Töreni", "Sürre Alayı", "Donanma Alayı"], "a": "Cülus Töreni"},
        {"q": "Osmanlı'da ilk kez 'Halife' unvanını kullanan padişah kimdir?", "opts": ["Yavuz Sultan Selim", "I. Murat", "Fatih Sultan Mehmet", "Kanuni Sultan Süleyman", "II. Abdülhamid"], "a": "Yavuz Sultan Selim"},
        {"q": "Devletin yönetiminde etkili olan Valide Sultan, Haseki Sultan gibi kadınların bulunduğu bölüm neresidir?", "opts": ["Harem", "Enderun", "Birun", "Şimşirlik", "Hasoda"], "a": "Harem"},
        {"q": "Osmanlı'da 'Hükümet' görevini üstlenen yapı hangisidir?", "opts": ["Divan-ı Hümayun", "Enderun", "Lonca", "Medrese", "Ocak"], "a": "Divan-ı Hümayun"},
        {"q": "Divan-ı Hümayun hangi padişah döneminde kaldırılarak yerine Nazırlıklar (Bakanlıklar) kurulmuştur?", "opts": ["II. Mahmut", "III. Selim", "Abdülmecid", "II. Abdülhamid", "I. Ahmet"], "a": "II. Mahmut"},
        {"q": "Osmanlı'da 'Sadaret Kethüdası' kimin yardımcısıdır?", "opts": ["Sadrazamın", "Padişahın", "Şeyhülislamın", "Defterdarın", "Nişancının"], "a": "Sadrazamın"},
        {"q": "Osmanlı'da İstanbul'un belediye hizmetlerini (temizlik, düzen) kim yürütür?", "opts": ["Şehremini", "Subaşı", "Muhtesib", "Mimarbaşı", "Kadı"], "a": "Şehremini"}
    ],

    "13. Klasik Çağda Osmanlı Toplum Düzeni": [
        {"q": "Osmanlı toplumunda halkın din ve mezhep esasına göre teşkilatlanmasına ne ad verilir?", "opts": ["Millet Sistemi", "Sınıf Sistemi", "Kast Sistemi", "Feodalite", "İskan Sistemi"], "a": "Millet Sistemi"},
        {"q": "Osmanlı toplumunda yönetenler sınıfına ne ad verilir?", "opts": ["Askeri (Beraya)", "Reaya", "Tebaa", "Burjuva", "Serf"], "a": "Askeri (Beraya)"},
        {"q": "Osmanlı toplumunda yönetilen (vergi veren) sınıfa ne ad verilir?", "opts": ["Reaya (Tebaa)", "Askeri", "Seyfiye", "İlmiye", "Kalemiye"], "a": "Reaya (Tebaa)"},
        {"q": "Osmanlı'da 'Seyfiye' sınıfı (Kılıç ehli) kimlerden oluşur?", "opts": ["Yönetim ve askerlik işlerine bakanlardan (Sadrazam, Beylerbeyi, Yeniçeri Ağası vb.)", "Din ve hukuk adamlarından", "Bürokratlardan", "Tüccarlardan", "Esnaftan"], "a": "Yönetim ve askerlik işlerine bakanlardan (Sadrazam, Beylerbeyi, Yeniçeri Ağası vb.)"},
        {"q": "Osmanlı'da 'İlmiye' sınıfı (İlim ehli) kimlerden oluşur?", "opts": ["Din, hukuk ve eğitim işlerine bakanlardan (Şeyhülislam, Kazasker, Kadı, Müderris)", "Askerlerden", "Bürokratlardan", "Esnaftan", "Köylülerden"], "a": "Din, hukuk ve eğitim işlerine bakanlardan (Şeyhülislam, Kazasker, Kadı, Müderris)"},
        {"q": "Osmanlı'da 'Kalemiye' sınıfı (Kalem ehli) kimlerden oluşur?", "opts": ["Bürokrasi ve maliye işlerine bakanlardan (Nişancı, Defterdar, Reisülküttab)", "Askerlerden", "Din adamlarından", "Kadılardan", "Esnaftan"], "a": "Bürokrasi ve maliye işlerine bakanlardan (Nişancı, Defterdar, Reisülküttab)"},
        {"q": "Osmanlı'da Müslüman olmayan erkeklerden askerlik yapmadıkları için alınan vergi nedir?", "opts": ["Cizye", "Öşür", "Haraç", "Avarız", "Ağnam"], "a": "Cizye"},
        {"q": "Müslüman çiftçilerden alınan ürün vergisine ne ad verilir?", "opts": ["Öşür", "Haraç", "Cizye", "İspenç", "Resm-i Çift"], "a": "Öşür"},
        {"q": "Gayrimüslim çiftçilerden alınan ürün vergisine ne ad verilir?", "opts": ["Haraç", "Öşür", "Cizye", "Avarız", "Bac"], "a": "Haraç"},
        {"q": "Olağanüstü durumlarda (savaş, afet vb.) halktan toplanan vergiye ne ad verilir?", "opts": ["Avarız", "Cizye", "Haraç", "Öşür", "Ağnam"], "a": "Avarız"},
        {"q": "Küçükbaş hayvanlardan alınan vergiye ne ad verilir?", "opts": ["Ağnam", "Öşür", "Haraç", "Cizye", "Çiftbozan"], "a": "Ağnam"},
        {"q": "Toprağını mazeretsiz olarak üç yıl üst üste ekmeyen köylüden alınan ceza vergisi nedir?", "opts": ["Çiftbozan", "Resm-i Çift", "İspenç", "Bennak", "Mücerred"], "a": "Çiftbozan"},
        {"q": "Osmanlı'da çarşı ve pazar esnafından alınan vergiye ne ad verilir?", "opts": ["Bac", "Öşür", "Haraç", "Cizye", "Avarız"], "a": "Bac"},
        {"q": "Osmanlı'da lonca teşkilatında haksız rekabeti önlemek için belirlenen fiyat sistemine ne ad verilir?", "opts": ["Narh", "Gedik", "İhtisap", "Fütüvvet", "Vakıf"], "a": "Narh"},
        {"q": "Osmanlı'da bir mesleği yapabilme yetkisi (İş yeri açma ruhsatı) nedir?", "opts": ["Gedik", "Berat", "Ferman", "İcazet", "Diploma"], "a": "Gedik"},
        {"q": "Osmanlı'da sosyal sınıflar arasında geçiş var mıdır? (Dikey Hareketlilik)", "opts": ["Vardır, liyakat ve başarıya bağlıdır", "Yoktur, yasaktır", "Sadece soylular geçebilir", "Sadece zenginler geçebilir", "Kast sistemi vardır"], "a": "Vardır, liyakat ve başarıya bağlıdır"},
        {"q": "Reayadan birinin yönetici (askeri) sınıfa geçebilmesi için gerekli temel şart nedir?", "opts": ["Müslüman olmak ve Türkçe bilmek (ve eğitim/liyakat)", "Zengin olmak", "Soylu olmak", "İstanbul'da doğmak", "Asker çocuğu olmak"], "a": "Müslüman olmak ve Türkçe bilmek (ve eğitim/liyakat)"},
        {"q": "Osmanlı'da vakıf sisteminin temel amacı nedir?", "opts": ["Sosyal ihtiyaçları karşılamak ve hayır işleri yapmak", "Orduyu beslemek", "Padişahı zengin etmek", "Toprak kazanmak", "Ticaret yapmak"], "a": "Sosyal ihtiyaçları karşılamak ve hayır işleri yapmak"},
        {"q": "Vakıf yöneticisine ne ad verilir?", "opts": ["Mütevvelli", "Kadı", "Subaşı", "İmam", "Muhtar"], "a": "Mütevvelli"},
        {"q": "Osmanlı'da devlete ait topraklara ne ad verilir?", "opts": ["Miri Arazi", "Mülk Arazi", "Vakıf Arazi", "Öşri Arazi", "Haraci Arazi"], "a": "Miri Arazi"},
        {"q": "Kişilere ait olan (özel mülkiyet) topraklara ne ad verilir?", "opts": ["Mülk Arazi", "Miri Arazi", "Vakıf Arazi", "Dirlik", "Mukataa"], "a": "Mülk Arazi"},
        {"q": "Geliri doğrudan devlet hazinesine aktarılan topraklara ne ad verilir?", "opts": ["Mukataa", "Dirlik", "Paşmaklık", "Ocaklık", "Yurtluk"], "a": "Mukataa"},
        {"q": "Geliri memur ve askerlere maaş karşılığı verilen topraklara ne ad verilir?", "opts": ["Dirlik", "Mukataa", "Vakıf", "Malikane", "Yurtluk"], "a": "Dirlik"},
        {"q": "Dirlik toprakları gelire göre kaça ayrılır?", "opts": ["Has - Zeamet - Tımar", "Öşri - Haraci", "Miri - Mülk", "Ocaklık - Yurtluk", "Mukataa - Malikane"], "a": "Has - Zeamet - Tımar"},
        {"q": "Geliri en yüksek (100.000 akçeden fazla) olan ve Padişah/Divan üyelerine verilen dirlik hangisidir?", "opts": ["Has", "Zeamet", "Tımar", "Ocaklık", "Paşmaklık"], "a": "Has"},
        {"q": "Geliri 20.000 ile 100.000 akçe arasında olan ve orta dereceli memurlara verilen dirlik hangisidir?", "opts": ["Zeamet", "Has", "Tımar", "Mukataa", "Yurtluk"], "a": "Zeamet"},
        {"q": "Geliri 3.000 ile 20.000 akçe arasında olan ve askerlere verilen dirlik hangisidir?", "opts": ["Tımar", "Has", "Zeamet", "Malikane", "Paşmaklık"], "a": "Tımar"},
        {"q": "Geliri padişahın annesi, eşi ve kızlarına ayrılan topraklara ne ad verilir?", "opts": ["Paşmaklık", "Ocaklık", "Yurtluk", "Malikane", "Mukataa"], "a": "Paşmaklık"},
        {"q": "Geliri kale muhafızlarına ve tersane giderlerine ayrılan topraklara ne ad verilir?", "opts": ["Ocaklık", "Paşmaklık", "Yurtluk", "Mukataa", "Dirlik"], "a": "Ocaklık"},
        {"q": "Sınır boylarındaki askerlere verilen topraklara ne ad verilir?", "opts": ["Yurtluk", "Ocaklık", "Paşmaklık", "Mukataa", "Has"], "a": "Yurtluk"},
        {"q": "Osmanlı'da 'Çifthane Sistemi'nin temel amacı nedir?", "opts": ["Üretimde sürekliliği sağlamak ve büyük toprak sahiplerinin oluşmasını engellemek", "Asker yetiştirmek", "Vergi toplamak", "Nüfusu artırmak", "Şehirleşmeyi sağlamak"], "a": "Üretimde sürekliliği sağlamak ve büyük toprak sahiplerinin oluşmasını engellemek"},
        {"q": "Osmanlı şehirlerinde mahallenin yöneticisi ve devletin temsilcisi kimdir?", "opts": ["İmam", "Muhtar", "Subaşı", "Kadı", "Ayan"], "a": "İmam"},
        {"q": "Lonca teşkilatında esnafın güvenliğinden sorumlu kişi kimdir?", "opts": ["Yiğitbaşı", "Kethüda", "Şeyh", "Nakib", "Ehl-i Hibre"], "a": "Yiğitbaşı"},
        {"q": "Lonca teşkilatında devlet ile esnaf arasındaki ilişkiyi sağlayan kişi kimdir?", "opts": ["Kethüda", "Yiğitbaşı", "Şeyh", "Ehl-i Hibre", "Duacı"], "a": "Kethüda"},
        {"q": "Lonca teşkilatında malların kalitesini denetleyen bilirkişi kimdir?", "opts": ["Ehl-i Hibre", "Kethüda", "Yiğitbaşı", "Şeyh", "Muhtesib"], "a": "Ehl-i Hibre"},
        {"q": "Osmanlı'da gayrimüslimlerin ibadet, eğitim ve hukuk işlerinde kendi dini kurallarına göre yönetilmesi neyin sonucudur?", "opts": ["Millet Sistemi'nin", "İstimalet politikasının", "Baskıcı yönetimin", "Zayıflığın", "Kapitülasyonların"], "a": "Millet Sistemi'nin"},
        {"q": "Osmanlı'da 'Dikey Hareketlilik' ne demektir?", "opts": ["Bir sınıftan diğerine geçiş (Reayadan Askeriye geçiş)", "Köyden şehre göç", "Şehirden köye göç", "Bir bölgeden diğerine göç", "Meslek değiştirme"], "a": "Bir sınıftan diğerine geçiş (Reayadan Askeriye geçiş)"},
        {"q": "Osmanlı'da 'Yatay Hareketlilik' ne demektir?", "opts": ["Ülke içinde yer değiştirme (Göç)", "Sınıf değiştirme", "Memur olma", "Zengin olma", "Din değiştirme"], "a": "Ülke içinde yer değiştirme (Göç)"},
        {"q": "Osmanlı'da vakıf arazileri alınıp satılabilir mi?", "opts": ["Hayır, satılamaz, devredilemez", "Evet, satılabilir", "Padişah izniyle satılır", "Sadece miras bırakılır", "Kiralanabilir"], "a": "Hayır, satılamaz, devredilemez"},
        {"q": "Osmanlı toplumunda en kalabalık grup hangisidir?", "opts": ["Köylüler", "Şehirliler", "Göçebeler", "Askerler", "Tüccarlar"], "a": "Köylüler"},
        {"q": "Göçebe (Konargöçer) halkın en önemli ekonomik faaliyeti nedir?", "opts": ["Hayvancılık", "Tarım", "Ticaret", "Sanayi", "Madencilik"], "a": "Hayvancılık"},
        {"q": "Osmanlı'da şehirlerde ticaretin yapıldığı üstü kapalı çarşılara ne ad verilir?", "opts": ["Bedesten", "Arasta", "Kapan", "Han", "Ribat"], "a": "Bedesten"},
        {"q": "Tek cins malın toptan satıldığı yerlere (Un kapanı, Yağ kapanı vb.) ne ad verilir?", "opts": ["Kapan Hanı", "Bedesten", "Arasta", "Zaviye", "İmaret"], "a": "Kapan Hanı"},
        {"q": "Aynı işi yapan esnafların bulunduğu sokak çarşılarına ne ad verilir?", "opts": ["Arasta", "Bedesten", "Kapan", "Han", "Kervansaray"], "a": "Arasta"},
        {"q": "Yolcuların konaklaması için yapılan, ticari ve sosyal yapılar hangisidir?", "opts": ["Han ve Kervansaray", "Bedesten", "Arasta", "Kapan", "Lonca"], "a": "Han ve Kervansaray"},
        {"q": "Yoksullara yemek dağıtılan hayır kurumu hangisidir?", "opts": ["İmaret (Aşevi)", "Darüşşifa", "Tabhane", "Muvakkithane", "Sebil"], "a": "İmaret (Aşevi)"},
        {"q": "Osmanlı'da 'Darülaceze' ne amaçla kurulmuştur?", "opts": ["Düşkünler ve yaşlılar evi", "Hastane", "Okul", "Misafirhane", "Kütüphane"], "a": "Düşkünler ve yaşlılar evi"},
        {"q": "Osmanlı'da kamuoyunun oluştuğu, insanların sosyalleştiği mekanlar hangileridir?", "opts": ["Kahvehaneler ve Bozahaneler", "Kütüphaneler", "Okullar", "Kişlalar", "Saraylar"], "a": "Kahvehaneler ve Bozahaneler"},
        {"q": "Osmanlı'da evlilik akdini kim gerçekleştirir ve kayıt altına alırdı?", "opts": ["Kadı (Mahkeme)", "İmam", "Muhtar", "Subaşı", "Aile büyükleri"], "a": "Kadı (Mahkeme)"},
        {"q": "Osmanlı ailesinde miras paylaşımı neye göre yapılırdı?", "opts": ["İslam Hukuku'na (Şer'i Hukuk) göre", "Örfi Hukuka göre", "Babanın isteğine göre", "Eşit olarak", "Sadece erkeklere"], "a": "İslam Hukuku'na (Şer'i Hukuk) göre"}
    ],"14. Değişen Dünya Dengeleri Karşısında Osmanlı Siyaseti": [
        {"q": "Osmanlı Devleti'nin 'Duraklama Dönemi'ne girmesine neden olan ilk antlaşma (1590) hangisidir?", "opts": ["Ferhat Paşa Antlaşması", "Nasuh Paşa Antlaşması", "Kasr-ı Şirin Antlaşması", "Zitvatorok Antlaşması", "Bucaş Antlaşması"], "a": "Ferhat Paşa Antlaşması"},
        {"q": "Osmanlı'nın batıda kazandığı son meydan savaşı (1596) hangisidir?", "opts": ["Haçova Meydan Muharebesi", "Mohaç Savaşı", "Varna Savaşı", "Niğbolu Savaşı", "Zenta Savaşı"], "a": "Haçova Meydan Muharebesi"},
        {"q": "Osmanlı'nın Avusturya karşısındaki siyasi üstünlüğünü (protokol denkliği) kaybettiği antlaşma hangisidir?", "opts": ["Zitvatorok Antlaşması", "İstanbul Antlaşması", "Karlofça Antlaşması", "Pasarofça Antlaşması", "Vasvar Antlaşması"], "a": "Zitvatorok Antlaşması"},
        {"q": "Doğuda en geniş sınırlara ulaşılan antlaşma hangisidir?", "opts": ["Ferhat Paşa Antlaşması", "Nasuh Paşa Antlaşması", "Serav Antlaşması", "Kasr-ı Şirin Antlaşması", "Amasya Antlaşması"], "a": "Ferhat Paşa Antlaşması"},
        {"q": "Bugünkü Türkiye-İran sınırını büyük ölçüde belirleyen 1639 tarihli antlaşma hangisidir?", "opts": ["Kasr-ı Şirin Antlaşması", "Ferhat Paşa Antlaşması", "Nasuh Paşa Antlaşması", "Kerden Antlaşması", "Serav Antlaşması"], "a": "Kasr-ı Şirin Antlaşması"},
        {"q": "Osmanlı'nın batıda en geniş sınırlara ulaştığı antlaşma hangisidir?", "opts": ["Bucaş Antlaşması", "Zitvatorok Antlaşması", "Vasvar Antlaşması", "Karlofça Antlaşması", "Pasarofça Antlaşması"], "a": "Bucaş Antlaşması"},
        {"q": "17. yüzyılda Osmanlı'nın Girit Adası'nı fethi kaç yıl sürmüştür?", "opts": ["24 yıl", "10 yıl", "5 yıl", "50 yıl", "1 yıl"], "a": "24 yıl"},
        {"q": "Osmanlı Devleti'nin 'Kutsal İttifak' devletlerine karşı aldığı en ağır yenilgi sonrası imzaladığı antlaşma (1699) hangisidir?", "opts": ["Karlofça Antlaşması", "İstanbul Antlaşması", "Pasarofça Antlaşması", "Belgrad Antlaşması", "Küçük Kaynarca Antlaşması"], "a": "Karlofça Antlaşması"},
        {"q": "Karlofça Antlaşması'nın en önemli özelliği nedir?", "opts": ["Osmanlı'nın batıda ilk kez büyük çapta toprak kaybetmesi", "Duraklama döneminin bitmesi", "Rusya'nın Karadeniz'e inmesi", "Gerileme döneminin bitmesi", "Yükselme döneminin başlaması"], "a": "Osmanlı'nın batıda ilk kez büyük çapta toprak kaybetmesi"},
        {"q": "Rusya'nın Karadeniz'e inme politikasının ilk adımı olan ve Azak Kalesi'nin Ruslara verildiği antlaşma (1700) hangisidir?", "opts": ["İstanbul Antlaşması", "Karlofça Antlaşması", "Prut Antlaşması", "Küçük Kaynarca Antlaşması", "Belgrad Antlaşması"], "a": "İstanbul Antlaşması"},
        {"q": "İsveç Kralı Demirbaş Şarl'ın Osmanlı'ya sığınması sonucu Rusya ile yapılan ve Azak Kalesi'nin geri alındığı savaş/antlaşma hangisidir?", "opts": ["Prut Savaşı ve Antlaşması", "Kırım Savaşı", "93 Harbi", "Petervaradin Savaşı", "Çeşme Vakası"], "a": "Prut Savaşı ve Antlaşması"},
        {"q": "Osmanlı'nın kaybettiği toprakları geri alma ümidini artıran antlaşma hangisidir?", "opts": ["Prut Antlaşması", "Pasarofça Antlaşması", "Karlofça Antlaşması", "Belgrad Antlaşması", "Küçük Kaynarca Antlaşması"], "a": "Prut Antlaşması"},
        {"q": "Osmanlı'nın batıda toprak kazanma ümidini sona erdiren ve Lale Devri'ni başlatan antlaşma (1718) hangisidir?", "opts": ["Pasarofça Antlaşması", "Karlofça Antlaşması", "Prut Antlaşması", "Belgrad Antlaşması", "Küçük Kaynarca Antlaşması"], "a": "Pasarofça Antlaşması"},
        {"q": "Pasarofça Antlaşması'ndan sonra Osmanlı'nın batıda izlediği temel politika ne olmuştur?", "opts": ["Savunma ve eldeki toprakları koruma", "Fetih politikası", "Gaza ve cihat", "İslam birliği", "Sömürgecilik"], "a": "Savunma ve eldeki toprakları koruma"},
        {"q": "Osmanlı'nın 18. yüzyılda imzaladığı son kazançlı antlaşma hangisidir?", "opts": ["Belgrad Antlaşması", "Pasarofça Antlaşması", "Karlofça Antlaşması", "Küçük Kaynarca Antlaşması", "Yaş Antlaşması"], "a": "Belgrad Antlaşması"},
        {"q": "Belgrad Antlaşması'nda arabuluculuk yaptığı için kapitülasyonları sürekli hale getirilen devlet hangisidir?", "opts": ["Fransa", "İngiltere", "Rusya", "Avusturya", "Venedik"], "a": "Fransa"},
        {"q": "1774 Küçük Kaynarca Antlaşması ile bağımsız olan ve ilk kez halkı Müslüman bir bölgenin kaybedildiği yer neresidir?", "opts": ["Kırım", "Mısır", "Mora", "Eflak", "Boğdan"], "a": "Kırım"},
        {"q": "Küçük Kaynarca Antlaşması ile Rusya'ya verilen, Osmanlı iç işlerine karışma fırsatı yaratan hak nedir?", "opts": ["Ortodoksların himayesi ve Konsolosluk açma hakkı", "Kapitülasyon", "Boğazlardan geçiş hakkı", "Donanma kurma hakkı", "Vergi muafiyeti"], "a": "Ortodoksların himayesi ve Konsolosluk açma hakkı"},
        {"q": "Osmanlı Devleti'nin tarihinde ilk kez savaş tazminatı ödediği devlet hangisidir?", "opts": ["Rusya", "Avusturya", "Venedik", "İran", "Fransa"], "a": "Rusya"},
        {"q": "Kırım'ın Rusya'ya ait olduğunun kabul edildiği antlaşma (1792) hangisidir?", "opts": ["Yaş Antlaşması", "Aynalıkavak Tenkihnamesi", "Ziştovi Antlaşması", "Küçük Kaynarca Antlaşması", "Bükreş Antlaşması"], "a": "Yaş Antlaşması"},
        {"q": "Osmanlı'da duraklamanın iç nedenlerinden biri olan 'Beşik Ulemalığı' nedir?", "opts": ["Alimin oğlu alimdir anlayışı (Liyakatsizlik)", "Eğitimin beşikta başlaması", "Medreselerin çoğalması", "Çocuk yaşta tahta çıkılması", "Yabancı dil eğitimi"], "a": "Alimin oğlu alimdir anlayışı (Liyakatsizlik)"},
        {"q": "17. yüzyıl ıslahatçılarının genel özelliği nedir?", "opts": ["Sorunların köküne inememeleri ve baskı/şiddet yoluyla çözüm aramaları", "Batı'yı örnek almaları", "Halkın isteğiyle yapılması", "Demokratik olmaları", "Kalıcı olmaları"], "a": "Sorunların köküne inememeleri ve baskı/şiddet yoluyla çözüm aramaları"},
        {"q": "İlk kez modern bütçeyi (denk bütçe) hazırlayan Osmanlı devlet adamı kimdir?", "opts": ["Tarhuncu Ahmet Paşa", "Köprülü Mehmet Paşa", "Sokullu Mehmet Paşa", "Merzifonlu Kara Mustafa Paşa", "IV. Murat"], "a": "Tarhuncu Ahmet Paşa"},
        {"q": "Saray kadınlarını devlet yönetiminden uzaklaştıran ve içki/tütün yasağı getiren padişah kimdir?", "opts": ["IV. Murat", "II. Osman (Genç Osman)", "I. Ahmet", "IV. Mehmet", "III. Selim"], "a": "IV. Murat"},
        {"q": "Yeniçeriler tarafından öldürülen ilk Osmanlı padişahı kimdir?", "opts": ["II. Osman (Genç Osman)", "III. Selim", "I. İbrahim", "IV. Mustafa", "II. Bayezid"], "a": "II. Osman (Genç Osman)"},
        {"q": "Şartlar ileri sürerek sadrazam olan ilk ve tek Osmanlı devlet adamı kimdir?", "opts": ["Köprülü Mehmet Paşa", "Tarhuncu Ahmet Paşa", "Sokullu Mehmet Paşa", "Merzifonlu Kara Mustafa Paşa", "Baltacı Mehmet Paşa"], "a": "Köprülü Mehmet Paşa"},
        {"q": "II. Viyana Kuşatması'nı gerçekleştiren ancak başarısız olup idam edilen sadrazam kimdir?", "opts": ["Merzifonlu Kara Mustafa Paşa", "Köprülü Fazıl Ahmet Paşa", "Baltacı Mehmet Paşa", "Damat İbrahim Paşa", "Alemdar Mustafa Paşa"], "a": "Merzifonlu Kara Mustafa Paşa"},
        {"q": "Kutsal İttifak devletleri arasında hangisi yoktur?", "opts": ["İngiltere", "Avusturya", "Venedik", "Rusya", "Lehistan"], "a": "İngiltere"},
        {"q": "Lale Devri (1718-1730) hangi olayla sona ermiştir?", "opts": ["Patrona Halil İsyanı", "Kabakçı Mustafa İsyanı", "Edirne Vakası", "Çınar Vakası", "31 Mart Vakası"], "a": "Patrona Halil İsyanı"},
        {"q": "Lale Devri'nin ünlü sadrazamı kimdir?", "opts": ["Nevşehirli Damat İbrahim Paşa", "Sokullu Mehmet Paşa", "Köprülü Mehmet Paşa", "Rüstem Paşa", "Pargalı İbrahim"], "a": "Nevşehirli Damat İbrahim Paşa"},
        {"q": "Lale Devri'nin ünlü şairi kimdir?", "opts": ["Nedim", "Baki", "Fuzuli", "Nefi", "Şeyh Galip"], "a": "Nedim"},
        {"q": "Osmanlı'da ilk Türk matbaasını kim kurmuştur?", "opts": ["İbrahim Müteferrika ve Said Efendi", "Ali Kuşçu", "Takiyüddin", "Evliya Çelebi", "Katip Çelebi"], "a": "İbrahim Müteferrika ve Said Efendi"},
        {"q": "Osmanlı'da Batı'nın (Avrupa'nın) üstünlüğünün ilk kez kabul edildiği dönem hangisidir?", "opts": ["Lale Devri", "Yükselme Dönemi", "Fetret Devri", "Kuruluş Dönemi", "Meşrutiyet Dönemi"], "a": "Lale Devri"},
        {"q": "Matbaada basılan ilk eser nedir?", "opts": ["Vankulu Lügati", "Cihannüma", "Seyahatname", "Kuran-ı Kerim", "Mesnevi"], "a": "Vankulu Lügati"},
        {"q": "Lale Devri'nde Avrupa'ya gönderilen geçici elçilerin raporlarına ne ad verilir?", "opts": ["Sefaretname", "Seyahatname", "Siyasetname", "Layiha", "Risale"], "a": "Sefaretname"},
        {"q": "Osmanlı'nın ilk geçici elçisi kimdir ve nereye gönderilmiştir?", "opts": ["28 Çelebi Mehmet (Paris)", "Yusuf Agah Efendi (Londra)", "İbrahim Paşa (Viyana)", "Ali Paşa (Berlin)", "Sadık Rıfat (Roma)"], "a": "28 Çelebi Mehmet (Paris)"},
        {"q": "Tulumbacılar Ocağı (İtfaiye) hangi dönemde kurulmuştur?", "opts": ["Lale Devri", "III. Selim", "II. Mahmut", "Kanuni", "Fatih"], "a": "Lale Devri"},
        {"q": "Osmanlı'da Batı tarzı ilk askeri ıslahatları yapan ve 'Humbaracı Ahmet Paşa' adını alan Fransız uzman kimdir?", "opts": ["Comte de Bonneval", "Baron de Tott", "Moltke", "Liman von Sanders", "Sebastiani"], "a": "Comte de Bonneval"},
        {"q": "III. Selim döneminde yapılan ıslahatların genel adı nedir?", "opts": ["Nizam-ı Cedit", "Sekban-ı Cedit", "Eşkinci Ocağı", "Asakir-i Mansure", "Vaka-i Hayriye"], "a": "Nizam-ı Cedit"},
        {"q": "III. Selim döneminde kurulan 'Nizam-ı Cedit' ordusunun masraflarını karşılamak için oluşturulan hazine nedir?", "opts": ["İrad-ı Cedit", "Beytül Mal", "Hazine-i Amire", "Ceb-i Hümayun", "Miri Hazine"], "a": "İrad-ı Cedit"},
        {"q": "Nizam-ı Cedit ordusunun Napolyon'u durdurduğu ilk başarı neresidir?", "opts": ["Akka Savunması", "Mısır Seferi", "Preveze", "Viyana", "Kırım"], "a": "Akka Savunması"},
        {"q": "Akka Kalesi'nde Napolyon'u yenen Osmanlı komutanı kimdir?", "opts": ["Cezzar Ahmet Paşa", "Kavalalı Mehmet Ali Paşa", "Alemdar Mustafa Paşa", "Köprülü Fazıl Ahmet", "Gazi Osman Paşa"], "a": "Cezzar Ahmet Paşa"},
        {"q": "Osmanlı'da ilk daimi (sürekli) elçilik nerede açılmıştır?", "opts": ["Londra (Yusuf Agah Efendi)", "Paris", "Viyana", "Berlin", "Moskova"], "a": "Londra (Yusuf Agah Efendi)"},
        {"q": "III. Selim'in tahttan indirilip Nizam-ı Cedit'in kaldırılmasına neden olan isyan hangisidir?", "opts": ["Kabakçı Mustafa İsyanı", "Patrona Halil İsyanı", "31 Mart Vakası", "Kuleli Vakası", "Edirne Vakası"], "a": "Kabakçı Mustafa İsyanı"},
        {"q": "Rusya'nın 'Sıcak denizlere inme' politikasını başlatan Çar kimdir?", "opts": ["I. Petro (Deli Petro)", "IV. İvan", "II. Katerina", "I. Nikola", "Aleksandr"], "a": "I. Petro (Deli Petro)"},
        {"q": "Osmanlı'da devlet adamlarının padişaha sunduğu reform önerileri raporlarına ne ad verilir?", "opts": ["Layiha", "Ferman", "Berat", "Fetva", "Risale"], "a": "Layiha"},
        {"q": "Çeşme Baskını'nda Osmanlı donanmasını yakan devlet hangisidir?", "opts": ["Rusya", "İngiltere", "Fransa", "Venedik", "Avusturya"], "a": "Rusya"},
        {"q": "Grev ve lokavt gibi kavramlar Osmanlı'da hangi dönemde ortaya çıkmıştır?", "opts": ["II. Meşrutiyet Dönemi", "Lale Devri", "Tanzimat", "Yükselme", "Fetret"], "a": "II. Meşrutiyet Dönemi"},
        {"q": "Osmanlı'da 'Vaka-i Vakvakiye' (Çınar Vakası) nedir?", "opts": ["30'a yakın devlet adamının isyancılar tarafından asılması", "Yeniçeri Ocağı'nın kaldırılması", "Padişahın öldürülmesi", "Matbaanın kurulması", "Sarayın basılması"], "a": "30'a yakın devlet adamının isyancılar tarafından asılması"},
        {"q": "Osmanlı'da ilk kağıt para (Kaime) hangi padişah döneminde basılmıştır?", "opts": ["Abdülmecid", "II. Mahmut", "III. Selim", "Abdülaziz", "V. Murat"], "a": "Abdülmecid"}
    ],

    "15. Değişim Çağında Avrupa ve Osmanlı": [
        {"q": "15. ve 16. yüzyıllarda Avrupa'da edebiyat, sanat ve bilim alanındaki yeniliklerin yaşandığı döneme ne ad verilir?", "opts": ["Rönesans", "Reform", "Aydınlanma", "Sanayi İnkılabı", "Skolastik Dönem"], "a": "Rönesans"},
        {"q": "Rönesans hareketi ilk olarak hangi ülkede başlamıştır?", "opts": ["İtalya", "Fransa", "Almanya", "İngiltere", "İspanya"], "a": "İtalya"},
        {"q": "Rönesans'ın kelime anlamı nedir?", "opts": ["Yeniden Doğuş", "Dini Yenilenme", "Sanayileşme", "Sömürgecilik", "Aydınlanma"], "a": "Yeniden Doğuş"},
        {"q": "Avrupa'da Katolik Kilisesi'nin bozulması üzerine ortaya çıkan dini düzenlemelere ne ad verilir?", "opts": ["Reform", "Rönesans", "Hümanizm", "Engizisyon", "Aforoz"], "a": "Reform"},
        {"q": "Reform hareketleri ilk olarak hangi ülkede ve kimin öncülüğünde başlamıştır?", "opts": ["Almanya - Martin Luther", "Fransa - Kalvin", "İngiltere - Kral 8. Henry", "İtalya - Da Vinci", "İspanya - Şarlken"], "a": "Almanya - Martin Luther"},
        {"q": "Martin Luther'in kilisenin uygulamalarına karşı kilise kapısına astığı bildiriye ne ad verilir?", "opts": ["95 Tez", "Magna Carta", "Nantes Fermanı", "İnsan Hakları Bildirgesi", "Augsburg Barışı"], "a": "95 Tez"},
        {"q": "Reform sonucunda Almanya'da hangi mezhep ortaya çıkmıştır?", "opts": ["Protestanlık", "Kalvinizm", "Anglikanizm", "Ortodoksluk", "Presbiteryenlik"], "a": "Protestanlık"},
        {"q": "Fransa'da Reform hareketleri sonucunda ortaya çıkan mezhep ve kurucusu kimdir?", "opts": ["Kalvinizm - Jean Calvin", "Lüteryanizm - Luther", "Anglikanizm - Henry", "Katolik - Papa", "Ortodoks - Patrik"], "a": "Kalvinizm - Jean Calvin"},
        {"q": "İngiltere'de kurulan milli kilise ve mezhep hangisidir?", "opts": ["Anglikanizm", "Kalvinizm", "Protestanlık", "Katolik", "Ortodoks"], "a": "Anglikanizm"},
        {"q": "Protestanlığın resmen tanındığı antlaşma (1555) hangisidir?", "opts": ["Augsburg Antlaşması", "Westphalia Antlaşması", "Nantes Fermanı", "Viyana Kongresi", "Verdun Antlaşması"], "a": "Augsburg Antlaşması"},
        {"q": "Fransa'da Protestanlara (Hügnolara) inanç özgürlüğünün verildiği ferman hangisidir?", "opts": ["Nantes Fermanı", "Augsburg Barışı", "Westphalia", "Magna Carta", "Reform Fermanı"], "a": "Nantes Fermanı"},
        {"q": "Avrupa'da zenginliğin kaynağını toprak yerine değerli madenler (altın, gümüş) olarak gören ekonomik anlayış nedir?", "opts": ["Merkantilizm", "Feodalite", "Liberalizm", "Sosyalizm", "Kapitalizm"], "a": "Merkantilizm"},
        {"q": "Merkantilizmin Osmanlı ekonomisine etkisi ne olmuştur?", "opts": ["Enflasyonun artması ve paranın değer kaybetmesi", "Zenginleşme", "Sanayileşme", "İhracatın artması", "Tarımın gelişmesi"], "a": "Enflasyonun artması ve paranın değer kaybetmesi"},
        {"q": "Avrupa'da 1618-1648 yılları arasında mezhep savaşları olarak bilinen savaş hangisidir?", "opts": ["30 Yıl Savaşları", "100 Yıl Savaşları", "Yedi Yıl Savaşları", "Güller Savaşı", "Haçlı Seferleri"], "a": "30 Yıl Savaşları"},
        {"q": "30 Yıl Savaşları'nı bitiren ve modern diplomasinin başlangıcı sayılan antlaşma hangisidir?", "opts": ["Westphalia Antlaşması", "Augsburg Antlaşması", "Viyana Kongresi", "Utrecht Antlaşması", "Paris Antlaşması"], "a": "Westphalia Antlaşması"},
        {"q": "Westphalia Antlaşması ile Avrupa'da neyin temelleri atılmıştır?", "opts": ["Ulus devletlerin ve laik devlet anlayışının", "Papa'nın otoritesinin", "Feodalitenin", "Kutsal Roma İmparatorluğu'nun", "Haçlı birliğinin"], "a": "Ulus devletlerin ve laik devlet anlayışının"},
        {"q": "Dünyanın güneş etrafında döndüğünü savunarak kilise dogmalarına karşı çıkan bilim insanı kimdir?", "opts": ["Kopernik", "Newton", "Aristo", "Batlamyus", "Descartes"], "a": "Kopernik"},
        {"q": "Teleskobu geliştirerek astronomide devrim yapan ve Engizisyon'da yargılanan bilim insanı kimdir?", "opts": ["Galileo", "Kopernik", "Kepler", "Bruno", "Bacon"], "a": "Galileo"},
        {"q": "Aydınlanma Çağı'nda 'Düşünüyorum, öyleyse varım' diyerek rasyonalizmi savunan filozof kimdir?", "opts": ["Descartes", "Kant", "Voltaire", "Rousseau", "Montesquieu"], "a": "Descartes"},
        {"q": "Kuvvetler ayrılığı ilkesini (Yasama, Yürütme, Yargı) savunan Aydınlanma düşünürü kimdir?", "opts": ["Montesquieu", "Rousseau", "Voltaire", "Locke", "Hobbes"], "a": "Montesquieu"},
        {"q": "Toplum Sözleşmesi adlı eseriyle demokrasi ve halk egemenliği fikrini savunan düşünür kimdir?", "opts": ["J.J. Rousseau", "Voltaire", "Montesquieu", "Diderot", "Machiavelli"], "a": "J.J. Rousseau"},
        {"q": "Makyavelizm (Amaca giden her yol mübahtır) düşüncesinin sahibi ve 'Prens' kitabının yazarı kimdir?", "opts": ["Machiavelli", "Dante", "Petrarca", "Erasmus", "More"], "a": "Machiavelli"},
        {"q": "Ütopya adlı eseriyle ideal devlet düzenini anlatan hümanist düşünür kimdir?", "opts": ["Thomas More", "Erasmus", "Shakespeare", "Cervantes", "Montaigne"], "a": "Thomas More"},
        {"q": "Osmanlı'da 17. yüzyılda Anadolu'da çıkan, ekonomik ve sosyal nedenli isyanlara ne ad verilir?", "opts": ["Celali İsyanları", "Yeniçeri İsyanları", "Suhte İsyanları", "Babai İsyanları", "Eyalet İsyanları"], "a": "Celali İsyanları"},
        {"q": "Aşağıdakilerden hangisi Celali İsyanları'nın nedenlerinden biri değildir?", "opts": ["Milliyetçilik akımı", "Vergilerin artırılması", "Tımar sisteminin bozulması", "Yerel yöneticilerin adaletsizliği", "Uzun süren savaşlar"], "a": "Milliyetçilik akımı"},
        {"q": "Medrese öğrencilerinin çıkardığı isyanlara ne ad verilir?", "opts": ["Suhte (Softa) İsyanları", "Celali İsyanları", "Kapıkulu İsyanları", "Eyalet İsyanları", "Esnaf İsyanları"], "a": "Suhte (Softa) İsyanları"},
        {"q": "Osmanlı'da merkez (İstanbul) isyanlarını genellikle kimler çıkarmıştır?", "opts": ["Yeniçeriler (Kapıkulu)", "Köylüler", "Medreseliler", "Gayrimüslimler", "Tüccarlar"], "a": "Yeniçeriler (Kapıkulu)"},
        {"q": "Osmanlı'da 'Büyük Kaçgun' nedir?", "opts": ["Celali isyanları nedeniyle köylünün toprağını terk edip şehirlere göç etmesi", "Ordunun savaştan kaçması", "Padişahın kaçması", "Hazinenin boşalması", "Vebadan kaçış"], "a": "Celali isyanları nedeniyle köylünün toprağını terk edip şehirlere göç etmesi"},
        {"q": "Osmanlı parasının değer kaybetmesine (içindeki gümüş oranının azaltılmasına) ne ad verilir?", "opts": ["Tağşiş", "Müsadere", "Narh", "Gedik", "Esham"], "a": "Tağşiş"},
        {"q": "Coğrafi Keşifler sonucunda Avrupa'ya bol miktarda gümüş ve altın girmesi Osmanlı ekonomisini nasıl etkiledi?", "opts": ["Enflasyon arttı ve Akçe değer kaybetti", "Ekonomi güçlendi", "Sanayi gelişti", "Ticaret arttı", "Vergiler azaldı"], "a": "Enflasyon arttı ve Akçe değer kaybetti"},
        {"q": "Osmanlı'da Ekber ve Erşed sisteminin getirilmesi hangi soruna yol açmıştır?", "opts": ["Şehzadelerin deneyimsiz (kafes usulü) yetişmesine", "Taht kavgalarının artmasına", "Hanedanın değişmesine", "Savaşların kaybedilmesine", "İsyanların çıkmasına"], "a": "Şehzadelerin deneyimsiz (kafes usulü) yetişmesine"},
        {"q": "Avrupa'da skolastik düşüncenin yıkılıp yerine deney ve gözleme dayalı düşüncenin gelmesine ne denir?", "opts": ["Bilim Devrimi (Aydınlanma)", "Sanayi Devrimi", "Sömürgecilik", "Feodalite", "Teokrasi"], "a": "Bilim Devrimi (Aydınlanma)"},
        {"q": "Evrensel Çekim Yasası'nı (Yerçekimi) bulan bilim insanı kimdir?", "opts": ["Isaac Newton", "Galileo", "Kopernik", "Einstein", "Kepler"], "a": "Isaac Newton"},
        {"q": "Osmanlı'da 17. yüzyılda 'Devletin kötü gidişatının nedenleri' hakkında rapor hazırlayan devlet adamı kimdir?", "opts": ["Koçi Bey", "Katip Çelebi", "Sokullu Mehmet Paşa", "Evliya Çelebi", "Naima"], "a": "Koçi Bey"},
        {"q": "Koçi Bey Risalesi hangi padişaha sunulmuştur?", "opts": ["IV. Murat", "I. Ahmet", "II. Osman", "Fatih", "Kanuni"], "a": "IV. Murat"},
        {"q": "Osmanlı'da tütün ve içki yasağı uygulayan, otoriter yönetimiyle bilinen padişah kimdir?", "opts": ["IV. Murat", "I. Ahmet", "II. Osman", "III. Murat", "I. İbrahim"], "a": "IV. Murat"},
        {"q": "Osmanlı'da 'Vaka-i Hayriye' (Hayırlı Olay) nedir?", "opts": ["Yeniçeri Ocağı'nın kaldırılması", "Tanzimat Fermanı", "Cumhuriyetin ilanı", "Matbaanın gelmesi", "Lale Devri"], "a": "Yeniçeri Ocağı'nın kaldırılması"},
        {"q": "Yeniçeri Ocağı hangi padişah tarafından kaldırılmıştır?", "opts": ["II. Mahmut", "III. Selim", "Abdülmecid", "II. Abdülhamid", "I. Mahmut"], "a": "II. Mahmut"},
        {"q": "Yeniçeri Ocağı'nın yerine kurulan ordu hangisidir?", "opts": ["Asakir-i Mansure-i Muhammediye", "Nizam-ı Cedit", "Sekban-ı Cedit", "Eşkinci Ocağı", "Hamidiye Alayları"], "a": "Asakir-i Mansure-i Muhammediye"},
        {"q": "Osmanlı'da ilk nüfus sayımı (1831) hangi padişah döneminde yapılmıştır?", "opts": ["II. Mahmut", "III. Selim", "Abdülmecid", "Abdülaziz", "Kanuni"], "a": "II. Mahmut"},
        {"q": "II. Mahmut döneminde nüfus sayımının temel amacı neydi?", "opts": ["Askeri potansiyeli ve vergi yükümlülerini belirlemek", "Kadın nüfusu saymak", "Seçmen sayısını belirlemek", "Eğitim durumunu ölçmek", "Göçleri engellemek"], "a": "Askeri potansiyeli ve vergi yükümlülerini belirlemek"},
        {"q": "Osmanlı'da 'Takvim-i Vekayi' nedir?", "opts": ["İlk resmi gazete", "İlk matbaa", "İlk anayasa", "İlk meclis", "İlk banka"], "a": "İlk resmi gazete"},
        {"q": "Kılık kıyafet devrimi yaparak memurlara fes ve pantolon giyme zorunluluğu getiren padişah kimdir?", "opts": ["II. Mahmut", "III. Selim", "Abdülmecid", "Atatürk", "Enver Paşa"], "a": "II. Mahmut"},
        {"q": "Divan-ı Hümayun'u kaldırarak yerine Nazırlıkları (Bakanlıkları) kuran padişah kimdir?", "opts": ["II. Mahmut", "III. Selim", "Abdülmecid", "Abdülaziz", "Fatih"], "a": "II. Mahmut"},
        {"q": "Köy ve mahalle muhtarlıkları ilk kez hangi dönemde kurulmuştur?", "opts": ["II. Mahmut", "Tanzimat", "Cumhuriyet", "Lale Devri", "Meşrutiyet"], "a": "II. Mahmut"},
        {"q": "Osmanlı'da ilköğretimin zorunlu hale getirilmesi (İstanbul'da) hangi padişah dönemindedir?", "opts": ["II. Mahmut", "III. Selim", "Abdülmecid", "II. Abdülhamid", "Kanuni"], "a": "II. Mahmut"},
        {"q": "Tımar sisteminin kaldırılmasıyla devlet memurlarına ne bağlanmıştır?", "opts": ["Maaş", "Toprak", "Ganimet", "Vergi hakkı", "Unvan"], "a": "Maaş"},
        {"q": "Müsadere sistemini (devletin mala el koyması) kaldıran padişah kimdir?", "opts": ["II. Mahmut", "III. Selim", "Abdülmecid", "Fatih", "Yavuz"], "a": "II. Mahmut"},
        {"q": "Osmanlı'da posta teşkilatının temelleri hangi padişah döneminde atılmıştır?", "opts": ["II. Mahmut", "Abdülmecid", "Abdülaziz", "III. Selim", "Kanuni"], "a": "II. Mahmut"},
        {"q": "Ayanlarla (yerel güçler) yapılan Sened-i İttifak (1808) hangi padişah döneminde imzalanmıştır?", "opts": ["II. Mahmut", "III. Selim", "Abdülmecid", "IV. Mustafa", "Alemdar Mustafa Paşa"], "a": "II. Mahmut"}
    ],

    "16. Devrimler Çağında Değişen Devlet-Toplum İlişkileri": [
        {"q": "1789 Fransız İhtilali'nin yaydığı en etkili fikir akımı hangisidir?", "opts": ["Milliyetçilik", "Sosyalizm", "Liberalizm", "Kapitalizm", "Feodalizm"], "a": "Milliyetçilik"},
        {"q": "Milliyetçilik akımının imparatorluklara (Osmanlı, Avusturya-Macaristan) etkisi ne olmuştur?", "opts": ["Parçalanma ve azınlık isyanları", "Güçlenme", "Birlik beraberlik", "Ekonomik kalkınma", "Sömürgecilik"], "a": "Parçalanma ve azınlık isyanları"},
        {"q": "Osmanlı Devleti'ne karşı ayaklanan ilk azınlık hangisidir?", "opts": ["Sırplar", "Yunanlılar (Rumlar)", "Bulgarlar", "Ermeniler", "Arnavutlar"], "a": "Sırplar"},
        {"q": "Osmanlı Devleti'nden ayrılarak bağımsızlığını kazanan ilk azınlık hangisidir?", "opts": ["Yunanlılar (Rumlar)", "Sırplar", "Karadağlılar", "Romenler", "Araplar"], "a": "Yunanlılar (Rumlar)"},
        {"q": "Yunanistan'ın bağımsızlığını kazandığı antlaşma (1829) hangisidir?", "opts": ["Edirne Antlaşması", "Bükreş Antlaşması", "Berlin Antlaşması", "Paris Antlaşması", "Londra Antlaşması"], "a": "Edirne Antlaşması"},
        {"q": "Osmanlı'da padişahın yetkilerini ilk kez kısıtlayan belge hangisidir?", "opts": ["Sened-i İttifak", "Tanzimat Fermanı", "Islahat Fermanı", "Kanun-i Esasi", "1. Meşrutiyet"], "a": "Sened-i İttifak"},
        {"q": "Sened-i İttifak (1808) kimler arasında imzalanmıştır?", "opts": ["II. Mahmut ve Ayanlar", "Padişah ve Yeniçeriler", "Padişah ve Halk", "Osmanlı ve Rusya", "Padişah ve Ulema"], "a": "II. Mahmut ve Ayanlar"},
        {"q": "Sened-i İttifak'ın önemi nedir?", "opts": ["Padişahın mutlak otoritesinin ilk kez sınırlandırılması", "Anayasal düzene geçilmesi", "Rejimin değişmesi", "Demokrasinin ilanı", "Halkın yönetime katılması"], "a": "Padişahın mutlak otoritesinin ilk kez sınırlandırılması"},
        {"q": "1839 Tanzimat Fermanı'nın (Gülhane Hatt-ı Hümayunu) temel amacı nedir?", "opts": ["Devleti dağılmaktan kurtarmak ve hukukun üstünlüğünü sağlamak", "Padişahı devirmek", "Şeriatı kaldırmak", "Cumhuriyeti ilan etmek", "Ekonomiyi düzeltmek"], "a": "Devleti dağılmaktan kurtarmak ve hukukun üstünlüğünü sağlamak"},
        {"q": "Tanzimat Fermanı'nı ilan eden padişah kimdir?", "opts": ["Sultan Abdülmecid", "II. Mahmut", "Abdülaziz", "II. Abdülhamid", "III. Selim"], "a": "Sultan Abdülmecid"},
        {"q": "Tanzimat Fermanı'nın getirdiği en önemli yenilik nedir?", "opts": ["Padişahın kanun gücünün üstünlüğünü kabul etmesi", "Seçimlerin yapılması", "Anayasa ilanı", "Meclis açılması", "Laiklik"], "a": "Padişahın kanun gücünün üstünlüğünü kabul etmesi"},
        {"q": "1856 Islahat Fermanı'nın temel amacı nedir?", "opts": ["Gayrimüslimlere geniş haklar vererek Avrupalıların iç işlerine karışmasını engellemek", "Müslüman halkı memnun etmek", "Orduda ıslahat yapmak", "Vergileri artırmak", "Toprak reformu"], "a": "Gayrimüslimlere geniş haklar vererek Avrupalıların iç işlerine karışmasını engellemek"},
        {"q": "Tanzimat ve Islahat fermanlarının ortak fikir akımı nedir?", "opts": ["Osmanlıcılık", "Türkçülük", "İslamcılık", "Batıcılık", "Turancılık"], "a": "Osmanlıcılık"},
        {"q": "Gayrimüslimlere devlet memuru olma, il genel meclisine üye olma gibi siyasi haklar hangi belgeyle verilmiştir?", "opts": ["Islahat Fermanı", "Tanzimat Fermanı", "Sened-i İttifak", "Kanun-i Esasi", "Muharrem Kararnamesi"], "a": "Islahat Fermanı"},
        {"q": "Osmanlı'da halkın ilk kez yönetime katıldığı olay nedir?", "opts": ["I. Meşrutiyet'in ilanı", "Tanzimat Fermanı", "Sened-i İttifak", "Vaka-i Hayriye", "31 Mart Vakası"], "a": "I. Meşrutiyet'in ilanı"},
        {"q": "I. Meşrutiyet'i (1876) ilan eden padişah kimdir?", "opts": ["II. Abdülhamid", "Abdülaziz", "V. Murat", "Abdülmecid", "Mehmet Reşat"], "a": "II. Abdülhamid"},
        {"q": "Türk tarihinin ilk yazılı anayasası hangisidir?", "opts": ["Kanun-i Esasi", "Teşkilat-ı Esasiye", "1921 Anayasası", "Sened-i İttifak", "Mecelle"], "a": "Kanun-i Esasi"},
        {"q": "I. Meşrutiyet döneminde açılan meclisin adı nedir?", "opts": ["Meclis-i Mebusan (ve Ayan)", "TBMM", "Kurultay", "Divan", "Senato"], "a": "Meclis-i Mebusan (ve Ayan)"},
        {"q": "Kanun-i Esasi'yi hazırlayan komisyonun başkanı kimdir?", "opts": ["Mithat Paşa", "Ahmet Cevdet Paşa", "Mustafa Reşit Paşa", "Enver Paşa", "Talat Paşa"], "a": "Mithat Paşa"},
        {"q": "Meşrutiyet'in ilanında etkili olan aydın grubu hangisidir?", "opts": ["Jön Türkler (Genç Osmanlılar)", "İttihat ve Terakki", "Hürriyet ve İtilaf", "Ayanlar", "Ulema"], "a": "Jön Türkler (Genç Osmanlılar)"},
        {"q": "II. Abdülhamid, I. Meşrutiyet'i ve Meclis'i hangi olayı gerekçe göstererek tatil etmiştir?", "opts": ["93 Harbi (1877-78 Osmanlı-Rus Savaşı)", "Kırım Savaşı", "Balkan Savaşları", "31 Mart Vakası", "Dömeke Savaşı"], "a": "93 Harbi (1877-78 Osmanlı-Rus Savaşı)"},
        {"q": "II. Meşrutiyet'in (1908) ilanında etkili olan cemiyet hangisidir?", "opts": ["İttihat ve Terakki Cemiyeti", "Jön Türkler", "Hürriyet ve İtilaf", "Ahrar Fırkası", "Müdafaa-i Hukuk"], "a": "İttihat ve Terakki Cemiyeti"},
        {"q": "Osmanlı tarihinde rejime (yönetim şekline) karşı çıkan ilk isyan hangisidir?", "opts": ["31 Mart Vakası", "Şeyh Sait İsyanı", "Menemen Olayı", "Patrona Halil", "Kabakçı Mustafa"], "a": "31 Mart Vakası"},
        {"q": "31 Mart İsyanı'nı bastıran ordunun adı ve komutanı (kurmay başkanı) kimdir?", "opts": ["Hareket Ordusu - Mustafa Kemal", "Nizam-ı Cedit - III. Selim", "Asakir-i Mansure - II. Mahmut", "Kuvayi Milliye - Çerkez Ethem", "Hamidiye - Abdülhamid"], "a": "Hareket Ordusu - Mustafa Kemal"},
        {"q": "II. Abdülhamid'in tahttan indirilip yerine V. Mehmet Reşat'ın getirilmesi hangi olay sonucunda olmuştur?", "opts": ["31 Mart Vakası", "Bab-ı Ali Baskını", "Edirne Vakası", "Kuleli Vakası", "Çırağan Vakası"], "a": "31 Mart Vakası"},
        {"q": "1909 Anayasa değişikliği ile padişahın hangi yetkisi sınırlandırılmıştır?", "opts": ["Meclisi feshetme ve sürgün yetkisi", "Halifelik yetkisi", "Para basma yetkisi", "Ordu komutanlığı", "Hutbe okutma"], "a": "Meclisi feshetme ve sürgün yetkisi"},
        {"q": "Osmanlı'da çok partili hayata ilk kez hangi dönemde geçilmiştir?", "opts": ["II. Meşrutiyet Dönemi", "I. Meşrutiyet Dönemi", "Tanzimat Dönemi", "Cumhuriyet Dönemi", "Lale Devri"], "a": "II. Meşrutiyet Dönemi"},
        {"q": "İttihat ve Terakki'nin yönetimi tamamen ele geçirdiği olay (1913) hangisidir?", "opts": ["Bab-ı Ali Baskını", "31 Mart Vakası", "Vaka-i Hayriye", "Çınar Vakası", "Edirne Vakası"], "a": "Bab-ı Ali Baskını"},
        {"q": "Osmanlı'da 'Mecelle' (Medeni Kanun) kime hazırlatılmıştır?", "opts": ["Ahmet Cevdet Paşa", "Mithat Paşa", "Mustafa Reşit Paşa", "Ziya Paşa", "Namık Kemal"], "a": "Ahmet Cevdet Paşa"},
        {"q": "Mecelle'nin kaynağı nedir?", "opts": ["İslam Hukuku (Hanefi Fıkhı)", "Roma Hukuku", "İsviçre Medeni Kanunu", "Fransız Hukuku", "Türk Töresi"], "a": "İslam Hukuku (Hanefi Fıkhı)"},
        {"q": "Osmanlı'da ilk kağıt para olan 'Kaime' hangi dönemde basılmıştır?", "opts": ["Abdülmecid (Tanzimat)", "II. Mahmut", "II. Abdülhamid", "III. Selim", "Fatih"], "a": "Abdülmecid (Tanzimat)"},
        {"q": "İlk Osmanlı Bankası olan 'Bank-ı Dersaadet' ne zaman kuruldu?", "opts": ["Tanzimat Dönemi", "Lale Devri", "Meşrutiyet", "Yükselme", "Cumhuriyet"], "a": "Tanzimat Dönemi"},
        {"q": "Yabancı sermayeli olan ve para basma yetkisine sahip 'Bank-ı Osmani' (Osmanlı Bankası) hangi ülkenin sermayesiyle kuruldu?", "opts": ["İngiltere", "Fransa", "Almanya", "Rusya", "ABD"], "a": "İngiltere"},
        {"q": "Osmanlı'da modern anlamda ilk üniversite sayılan kurum hangisidir?", "opts": ["Darülfünun", "Sahn-ı Seman", "Nizamiye", "Mülkiye", "Hendesehane"], "a": "Darülfünun"},
        {"q": "Kız rüştiyeleri (ortaokul) ve Kız Öğretmen Okulu hangi dönemde açılmıştır?", "opts": ["Tanzimat Dönemi", "Lale Devri", "Meşrutiyet", "Yükselme", "Kuruluş"], "a": "Tanzimat Dönemi"},
        {"q": "Osmanlı'da 'Encümen-i Daniş' (Bilim Kurulu) ne amaçla kurulmuştur?", "opts": ["Ders kitaplarını hazırlamak ve bilimi geliştirmek", "Orduyu eğitmek", "Vergi toplamak", "Kanun yapmak", "Diplomasi yürütmek"], "a": "Ders kitaplarını hazırlamak ve bilimi geliştirmek"},
        {"q": "Osmanlı'da 'Sanayi-i Nefise Mektebi' (Güzel Sanatlar Fakültesi) kim tarafından kurulmuştur?", "opts": ["Osman Hamdi Bey", "Şeker Ahmet Paşa", "İbrahim Çallı", "Mimar Kemalettin", "Halil Paşa"], "a": "Osman Hamdi Bey"},
        {"q": "Osmanlı'da müzeciliğin kurucusu sayılan kişi kimdir?", "opts": ["Osman Hamdi Bey", "Ahmet Vefik Paşa", "Halit Ziya", "Recaizade Mahmut Ekrem", "Namık Kemal"], "a": "Osman Hamdi Bey"},
        {"q": "İlk yerli tiyatro eseri 'Şair Evlenmesi'ni kim yazmıştır?", "opts": ["Şinasi", "Namık Kemal", "Ahmet Vefik Paşa", "Ziya Paşa", "Abdülhak Hamit"], "a": "Şinasi"},
        {"q": "Vatan Şairi olarak bilinen ve 'Vatan Yahut Silistre' oyununu yazan aydın kimdir?", "opts": ["Namık Kemal", "Ziya Paşa", "Tevfik Fikret", "Mehmet Akif", "Ömer Seyfettin"], "a": "Namık Kemal"},
        {"q": "Osmanlı'da çıkan ilk özel gazete hangisidir?", "opts": ["Tercüman-ı Ahval", "Takvim-i Vekayi", "Ceride-i Havadis", "Tasvir-i Efkar", "Tanin"], "a": "Tercüman-ı Ahval"},
        {"q": "Osmanlı'da kadınların çıkardığı ilk dergi hangisidir?", "opts": ["Şükufezar", "Demet", "Kadın", "Terakki", "Hanımlar"], "a": "Şükufezar"},
        {"q": "Fatma Aliye Hanım'ın öncülüğünde çıkan kadın dergisi hangisidir?", "opts": ["Hanımlara Mahsus Gazete", "Demet", "Mehasin", "Süs", "Kadın Yolu"], "a": "Hanımlara Mahsus Gazete"},
        {"q": "Türkçülük akımının en önemli savunucusu ve ideologu kimdir?", "opts": ["Ziya Gökalp", "Namık Kemal", "Tevfik Fikret", "Şinasi", "Ali Suavi"], "a": "Ziya Gökalp"},
        {"q": "İslamcılık (Ümmetçilik) politikasını devlet politikası haline getiren padişah kimdir?", "opts": ["II. Abdülhamid", "V. Mehmet Reşat", "Abdülmecid", "II. Mahmut", "III. Selim"], "a": "II. Abdülhamid"},
        {"q": "Batıcılık akımının en önemli savunucularından biri kimdir?", "opts": ["Tevfik Fikret", "Mehmet Akif", "Ziya Gökalp", "Ömer Seyfettin", "Yusuf Akçura"], "a": "Tevfik Fikret"},
        {"q": "Osmanlı'yı oluşturan tüm milletleri 'Osmanlı Vatandaşı' sayarak birliği sağlamayı amaçlayan fikir akımı nedir?", "opts": ["Osmanlıcılık", "İslamcılık", "Türkçülük", "Batıcılık", "Adem-i Merkeziyetçilik"], "a": "Osmanlıcılık"},
        {"q": "Osmanlıcılık fikri hangi olayla geçerliliğini yitirmiştir?", "opts": ["Balkan Savaşları (Azınlıkların isyan edip ayrılmasıyla)", "93 Harbi", "Kırım Savaşı", "Trablusgarp Savaşı", "I. Dünya Savaşı"], "a": "Balkan Savaşları (Azınlıkların isyan edip ayrılmasıyla)"},
        {"q": "İslamcılık fikri hangi olayla geçerliliğini yitirmiştir?", "opts": ["I. Dünya Savaşı'nda Arapların İngilizlerle işbirliği yapması", "Balkan Savaşları", "Trablusgarp Savaşı", "Kurtuluş Savaşı", "31 Mart Vakası"], "a": "I. Dünya Savaşı'nda Arapların İngilizlerle işbirliği yapması"},
        {"q": "Kurtuluş Savaşı'nın ve Türkiye Cumhuriyeti'nin temel ideolojisi hangi fikir akımı olmuştur?", "opts": ["Türkçülük", "Osmanlıcılık", "İslamcılık", "Batıcılık", "Turancılık"], "a": "Türkçülük"}
    ],

    "18. Uluslararası İlişkilerde Denge Stratejisi (1774-1914)": [
        {"q": "Osmanlı Devleti'nin 19. yüzyılda varlığını sürdürmek için izlediği, büyük devletlerin çıkar çatışmalarından yararlanma politikasına ne ad verilir?", "opts": ["Denge Politikası", "Gaza Politikası", "İstimalet", "İskan", "Panislamizm"], "a": "Denge Politikası"},
        {"q": "Denge politikasının ilk kez uygulandığı olay (1798) hangisidir?", "opts": ["Napolyon'un Mısır'ı İşgali", "Kırım Savaşı", "93 Harbi", "Yunan İsyanı", "Mısır Sorunu"], "a": "Napolyon'un Mısır'ı İşgali"},
        {"q": "Napolyon'un Mısır'dan çıkarılmasında Osmanlı'ya yardım eden devletler hangileridir?", "opts": ["İngiltere ve Rusya", "Fransa ve Almanya", "Avusturya ve Prusya", "İtalya ve İspanya", "ABD ve Hollanda"], "a": "İngiltere ve Rusya"},
        {"q": "Sırpların Osmanlı'dan ayrıcalık kazandığı ilk antlaşma hangisidir?", "opts": ["Bükreş Antlaşması", "Edirne Antlaşması", "Berlin Antlaşması", "Paris Antlaşması", "Londra Antlaşması"], "a": "Bükreş Antlaşması"},
        {"q": "Yunan İsyanı sırasında Osmanlı donanmasının yakıldığı olay (1827) hangisidir?", "opts": ["Navarin Olayı", "Çeşme Baskını", "Sinop Baskını", "İnebahtı", "Preveze"], "a": "Navarin Olayı"},
        {"q": "Mısır Valisi Kavalalı Mehmet Ali Paşa'nın isyanı Osmanlı için neye dönüşmüştür?", "opts": ["Uluslararası bir soruna (Mısır Sorunu)", "İç savaşa", "Din savaşına", "Mezhep çatışmasına", "Rejim değişikliğine"], "a": "Uluslararası bir soruna (Mısır Sorunu)"},
        {"q": "Osmanlı'nın Mısır sorunu karşısında Rusya'dan yardım istemesi üzerine imzalanan antlaşma (1833) hangisidir?", "opts": ["Hünkar İskelesi Antlaşması", "Kütahya Antlaşması", "Balta Limanı Antlaşması", "Londra Antlaşması", "Paris Antlaşması"], "a": "Hünkar İskelesi Antlaşması"},
        {"q": "Hünkar İskelesi Antlaşması ile hangi sorun ortaya çıkmıştır?", "opts": ["Boğazlar Sorunu", "Mısır Sorunu", "Musul Sorunu", "Kırım Sorunu", "Balkan Sorunu"], "a": "Boğazlar Sorunu"},
        {"q": "Boğazların uluslararası statü kazandığı ilk sözleşme (1841) hangisidir?", "opts": ["Londra Boğazlar Sözleşmesi", "Hünkar İskelesi", "Montrö", "Sevr", "Lozan"], "a": "Londra Boğazlar Sözleşmesi"},
        {"q": "Kırım Savaşı'nda (1853-1856) Osmanlı'nın yanında yer alan devletler hangileridir?", "opts": ["İngiltere, Fransa, Piyemonte", "Rusya, Almanya", "Avusturya, Prusya", "İtalya, İspanya", "ABD, Hollanda"], "a": "İngiltere, Fransa, Piyemonte"},
        {"q": "Osmanlı Devleti'nin ilk kez dış borç aldığı savaş hangisidir?", "opts": ["Kırım Savaşı", "93 Harbi", "Trablusgarp Savaşı", "Balkan Savaşları", "I. Dünya Savaşı"], "a": "Kırım Savaşı"},
        {"q": "Osmanlı'nın ilk dış borcu hangi ülkeden alınmıştır?", "opts": ["İngiltere", "Fransa", "Almanya", "Rusya", "ABD"], "a": "İngiltere"},
        {"q": "Osmanlı Devleti'nin 'Avrupalı Devlet' sayıldığı ve toprak bütünlüğünün Avrupa garantisine alındığı antlaşma hangisidir?", "opts": ["1856 Paris Antlaşması", "1878 Berlin Antlaşması", "1923 Lozan Antlaşması", "1833 Hünkar İskelesi", "1829 Edirne Antlaşması"], "a": "1856 Paris Antlaşması"},
        {"q": "Paris Antlaşması'nda Osmanlı'nın galip devlet olmasına rağmen yenik sayılmasına neden olan madde nedir?", "opts": ["Osmanlı ve Rusya'nın Karadeniz'de donanma bulunduramaması", "Boğazların kapatılması", "Sınırların değişmemesi", "Tazminat ödenmemesi", "Borçların ertelenmesi"], "a": "Osmanlı ve Rusya'nın Karadeniz'de donanma bulunduramaması"},
        {"q": "1877-1878 Osmanlı-Rus Savaşı'nın (93 Harbi) en önemli komutanlarından olup 'Plevne Kahramanı' olarak bilinen kişi kimdir?", "opts": ["Gazi Osman Paşa", "Ahmet Muhtar Paşa", "Nene Hatun", "Süleyman Paşa", "Enver Paşa"], "a": "Gazi Osman Paşa"},
        {"q": "93 Harbi'nin doğu cephesinde Aziziye Tabyası savunmasıyla simgeleşen kadın kahramanımız kimdir?", "opts": ["Nene Hatun", "Kara Fatma", "Şerife Bacı", "Halide Edip", "Tayyar Rahmiye"], "a": "Nene Hatun"},
        {"q": "93 Harbi sonunda imzalanan ancak yürürlüğe girmeyen (ölü doğan) antlaşma hangisidir?", "opts": ["Ayastefanos (Yeşilköy) Antlaşması", "Berlin Antlaşması", "Paris Antlaşması", "Edirne Antlaşması", "Bükreş Antlaşması"], "a": "Ayastefanos (Yeşilköy) Antlaşması"},
        {"q": "Ayastefanos yerine imzalanan 1878 Berlin Antlaşması'nın en önemli siyasi sonucu nedir?", "opts": ["Sırbistan, Karadağ ve Romanya'nın bağımsız olması", "Yunanistan'ın bağımsız olması", "Bulgaristan'ın bağımsız olması", "Mısır'ın kaybedilmesi", "Kırım'ın kaybedilmesi"], "a": "Sırbistan, Karadağ ve Romanya'nın bağımsız olması"},
        {"q": "Berlin Antlaşması ile Rusya'ya bırakılan 'Elviye-i Selase' (Üç İl) hangisidir?", "opts": ["Kars, Ardahan, Batum", "Erzurum, Van, Bitlis", "Musul, Kerkük, Süleymaniye", "Edirne, Tekirdağ, Kırklareli", "Selanik, Manastır, Üsküp"], "a": "Kars, Ardahan, Batum"},
        {"q": "Berlin Antlaşması'ndan sonra İngiltere'nin Osmanlı politikasındaki değişikliği nedir?", "opts": ["Osmanlı toprak bütünlüğünü korumaktan vazgeçmesi", "Osmanlı'yı desteklemesi", "Rusya'ya savaş açması", "Almanya ile düşman olması", "Mısır'ı geri vermesi"], "a": "Osmanlı toprak bütünlüğünü korumaktan vazgeçmesi"},
        {"q": "İngiltere, Berlin Antlaşması'nda Osmanlı'yı savunma karşılığında hangi adayı üs olarak almıştır?", "opts": ["Kıbrıs", "Girit", "Rodos", "Sakız", "Midilli"], "a": "Kıbrıs"},
        {"q": "Berlin Antlaşması'nda ilk kez gündeme gelen ve 'Ermeni Sorunu'nun başlangıcı sayılan madde nedir?", "opts": ["Ermenilerin yaşadığı yerlerde ıslahat yapılması", "Ermenilere bağımsızlık verilmesi", "Ermenilerin sürgün edilmesi", "Ermenilerin vergi vermemesi", "Ermenilerin silahlanması"], "a": "Ermenilerin yaşadığı yerlerde ıslahat yapılması"},
        {"q": "II. Abdülhamid döneminde Osmanlı'nın yakınlaştığı yeni müttefik devlet hangisidir?", "opts": ["Almanya", "Fransa", "İngiltere", "Rusya", "İtalya"], "a": "Almanya"},
        {"q": "Kuzey Afrika'da kaybettiğimiz ilk toprak parçası neresidir?", "opts": ["Cezayir (Fransa işgali)", "Tunus", "Mısır", "Trablusgarp", "Fas"], "a": "Cezayir (Fransa işgali)"},
        {"q": "Kuzey Afrika'da kaybettiğimiz son toprak parçası neresidir?", "opts": ["Trablusgarp (İtalya işgali)", "Mısır", "Tunus", "Cezayir", "Fas"], "a": "Trablusgarp (İtalya işgali)"},
        {"q": "İngiltere 1882 yılında hangi Osmanlı toprağını işgal etmiştir?", "opts": ["Mısır", "Kıbrıs", "Irak", "Filistin", "Suriye"], "a": "Mısır"},
        {"q": "Mustafa Kemal'in tarih sahnesine çıktığı ilk savaş hangisidir?", "opts": ["31 Mart Vakası (Hareket Ordusu)", "Trablusgarp Savaşı", "Balkan Savaşları", "Çanakkale Savaşı", "Sakarya Savaşı"], "a": "31 Mart Vakası (Hareket Ordusu)"},
        {"q": "Mustafa Kemal'in sömürgeciliğe karşı savaştığı ilk cephe hangisidir?", "opts": ["Trablusgarp", "Çanakkale", "Suriye", "Kafkas", "Makedonya"], "a": "Trablusgarp"},
        {"q": "Trablusgarp Savaşı sonunda İtalya ile imzalanan antlaşma hangisidir?", "opts": ["Uşi Antlaşması", "Lozan Antlaşması", "Paris Antlaşması", "Londra Antlaşması", "İstanbul Antlaşması"], "a": "Uşi Antlaşması"},
        {"q": "Uşi Antlaşması ile İtalya'ya geçici olarak bırakılan adalar hangisidir?", "opts": ["On İki Ada", "Kıbrıs", "Girit", "Sakız", "Midilli"], "a": "On İki Ada"},
        {"q": "I. Balkan Savaşı'nın çıkma nedeni nedir?", "opts": ["Balkan devletlerinin Osmanlı'yı Balkanlardan atmak istemesi", "Rusya'nın kışkırtması (Panslavizm)", "Osmanlı'nın zayıflığı", "Trablusgarp Savaşı", "Hepsi"], "a": "Hepsi"},
        {"q": "I. Balkan Savaşı'na katılan devletler hangileridir?", "opts": ["Bulgaristan, Yunanistan, Sırbistan, Karadağ", "Romanya, Bulgaristan, Sırbistan", "Rusya, Avusturya, İtalya", "Arnavutluk, Makedonya, Bosna", "İngiltere, Fransa, Rusya"], "a": "Bulgaristan, Yunanistan, Sırbistan, Karadağ"},
        {"q": "Osmanlı'nın I. Balkan Savaşı'nı kaybetmesinin en önemli nedeni nedir?", "opts": ["Ordunun siyasete karışması", "Silah eksikliği", "Asker azlığı", "Dış destek olmaması", "Ekonomik kriz"], "a": "Ordunun siyasete karışması"},
        {"q": "I. Balkan Savaşı sonucunda Osmanlı'dan ayrılan son Balkan devleti hangisidir?", "opts": ["Arnavutluk", "Bulgaristan", "Yunanistan", "Sırbistan", "Karadağ"], "a": "Arnavutluk"},
        {"q": "II. Balkan Savaşı'nın çıkma nedeni nedir?", "opts": ["Bulgaristan'ın I. Balkan Savaşı'nda en çok payı alması", "Osmanlı'nın saldırması", "Rusya'nın isteği", "Arnavutluk'un bağımsızlığı", "Sınır anlaşmazlığı"], "a": "Bulgaristan'ın I. Balkan Savaşı'nda en çok payı alması"},
        {"q": "II. Balkan Savaşı'na I. Balkan'da olmayıp sonradan katılan devlet hangisidir?", "opts": ["Romanya", "Osmanlı", "Yunanistan", "Sırbistan", "Karadağ"], "a": "Romanya"},
        {"q": "Osmanlı Devleti II. Balkan Savaşı'nı fırsat bilerek nereyi geri almıştır?", "opts": ["Edirne ve Kırklareli (Doğu Trakya)", "Selanik", "Manastır", "Üsküp", "Yanya"], "a": "Edirne ve Kırklareli (Doğu Trakya)"},
        {"q": "Edirne Fatihi olarak bilinen komutan kimdir?", "opts": ["Enver Paşa", "Mustafa Kemal", "Talat Paşa", "Cemal Paşa", "Kazım Karabekir"], "a": "Enver Paşa"},
        {"q": "Balkan Savaşları sonunda kaybedilen topraklardan Anadolu'ya yapılan göçlerin en önemli sonucu nedir?", "opts": ["Anadolu'da Türk nüfus yoğunluğunun artması", "Ekonominin düzelmesi", "İşsizliğin azalması", "Ordunun güçlenmesi", "Kültürel çatışma"], "a": "Anadolu'da Türk nüfus yoğunluğunun artması"},
        {"q": "Reval Görüşmeleri'nde (1908) İngiltere ve Rusya'nın Osmanlı'yı paylaşma planı yapması neyi hızlandırmıştır?", "opts": ["II. Meşrutiyet'in ilanını", "Tanzimat'ı", "Lale Devri'ni", "Sened-i İttifak'ı", "Islahat Fermanı'nı"], "a": "II. Meşrutiyet'in ilanını"},
        {"q": "Hamidiye Alayları kim tarafından ve ne amaçla kurulmuştur?", "opts": ["II. Abdülhamid - Doğudaki Ermeni isyanlarına karşı", "II. Mahmut - Yeniçerilere karşı", "III. Selim - Ruslara karşı", "Abdülmecid - Mısır'a karşı", "Enver Paşa - Araplara karşı"], "a": "II. Abdülhamid - Doğudaki Ermeni isyanlarına karşı"},
        {"q": "Dünya Savaşı öncesi oluşan 'Üçlü İtilaf' grubu hangi devletlerden oluşur?", "opts": ["İngiltere, Fransa, Rusya", "Almanya, Avusturya, İtalya", "ABD, Japonya, Çin", "Osmanlı, Almanya, Bulgaristan", "İspanya, Portekiz, Hollanda"], "a": "İngiltere, Fransa, Rusya"},
        {"q": "Dünya Savaşı öncesi oluşan 'Üçlü İttifak' grubu hangi devletlerden oluşur?", "opts": ["Almanya, Avusturya-Macaristan, İtalya", "İngiltere, Fransa, Rusya", "Osmanlı, Bulgaristan, Romanya", "ABD, İngiltere, Fransa", "Sırbistan, Yunanistan, Karadağ"], "a": "Almanya, Avusturya-Macaristan, İtalya"},
        {"q": "Almanya'nın Osmanlı ile yakınlaşmasının temel ekonomik sebebi nedir?", "opts": ["Berlin-Bağdat Demiryolu Projesi ve hammadde ihtiyacı", "Silah satmak", "Askeri eğitim vermek", "Kültürel değişim", "Din birliği"], "a": "Berlin-Bağdat Demiryolu Projesi ve hammadde ihtiyacı"},
        {"q": "Ermeni Sorunu uluslararası alanda ilk kez hangi antlaşma ile yer almıştır?", "opts": ["Berlin Antlaşması", "Paris Antlaşması", "Ayastefanos Antlaşması", "Lozan Antlaşması", "Uşi Antlaşması"], "a": "Berlin Antlaşması"},
        {"q": "Girit Adası'nın Yunanistan'a bağlanması hangi olayla kesinleşmiştir?", "opts": ["Balkan Savaşları (Atina Antlaşması)", "Trablusgarp Savaşı", "93 Harbi", "Kırım Savaşı", "I. Dünya Savaşı"], "a": "Balkan Savaşları (Atina Antlaşması)"},
        {"q": "Mustafa Kemal'in 'Ordular! İlk hedefiniz Akdeniz'dir, ileri!' emrini verdiği savaş hangisidir?", "opts": ["Başkomutanlık Meydan Muharebesi", "Sakarya Savaşı", "I. İnönü", "II. İnönü", "Çanakkale"], "a": "Başkomutanlık Meydan Muharebesi"},
        {"q": "Rusya'nın Balkanlardaki Slavları birleştirme politikasına ne ad verilir?", "opts": ["Panslavizm", "Panislamizm", "Pantürkizm", "Sömürgecilik", "Faşizm"], "a": "Panslavizm"},
        {"q": "Hasta Adam tabirini Osmanlı için kullanan ilk devlet hangisidir?", "opts": ["Rusya", "İngiltere", "Fransa", "Almanya", "Avusturya"], "a": "Rusya"},
        {"q": "Mecelle hangi yıl yürürlükten kaldırılmıştır?", "opts": ["1926 (Türk Medeni Kanunu ile)", "1908", "1876", "1923", "1920"], "a": "1926 (Türk Medeni Kanunu ile)"}
    ],

    "19. Sermaye ve Emek": [
        {"q": "İnsan ve hayvan gücünden makine gücüne geçişi ifade eden Sanayi İnkılabı ilk nerede başlamıştır?", "opts": ["İngiltere", "Fransa", "Almanya", "İtalya", "ABD"], "a": "İngiltere"},
        {"q": "Sanayi İnkılabı'nın başlamasında etkili olan enerji kaynağı nedir?", "opts": ["Buhar Gücü (Kömür)", "Elektrik", "Petrol", "Güneş", "Rüzgar"], "a": "Buhar Gücü (Kömür)"},
        {"q": "Sanayi İnkılabı sonucunda ortaya çıkan hammadde ve pazar arayışı neye neden olmuştur?", "opts": ["Sömürgecilik yarışına ve I. Dünya Savaşı'na", "Barışa", "Ticaretin azalmasına", "Tarımın gelişmesine", "Nüfusun azalmasına"], "a": "Sömürgecilik yarışına ve I. Dünya Savaşı'na"},
        {"q": "Sanayi İnkılabı ile ortaya çıkan yeni sosyal sınıf hangisidir?", "opts": ["İşçi Sınıfı (Proletarya)", "Burjuva", "Soylular", "Ruhban", "Serf"], "a": "İşçi Sınıfı (Proletarya)"},
        {"q": "Osmanlı Devleti'nin Avrupa mallarının açık pazarı haline gelmesine neden olan antlaşma (1838) hangisidir?", "opts": ["Balta Limanı Ticaret Antlaşması", "Hünkar İskelesi", "Kütahya Antlaşması", "Paris Antlaşması", "Londra Antlaşması"], "a": "Balta Limanı Ticaret Antlaşması"},
        {"q": "Balta Limanı Antlaşması hangi devletle imzalanmıştır?", "opts": ["İngiltere", "Fransa", "Rusya", "Almanya", "Avusturya"], "a": "İngiltere"},
        {"q": "Balta Limanı Antlaşması'nın Osmanlı ekonomisine en büyük zararı nedir?", "opts": ["Yerli sanayinin (Lonca) çökmesi", "İhracatın artması", "Gümrük gelirlerinin artması", "Yabancı sermayenin gelmesi", "Tarımın gelişmesi"], "a": "Yerli sanayinin (Lonca) çökmesi"},
        {"q": "Osmanlı Devleti'nin dış borçlarını ödeyememesi üzerine iflasını açıkladığı belge (1881) nedir?", "opts": ["Muharrem Kararnamesi", "Ramazan Kararnamesi", "Tanzimat Fermanı", "Islahat Fermanı", "Kanun-i Esasi"], "a": "Muharrem Kararnamesi"},
        {"q": "Muharrem Kararnamesi ile alacaklı devletlerin kurduğu ve Osmanlı gelirlerine el koyan teşkilat hangisidir?", "opts": ["Duyun-u Umumiye (Genel Borçlar İdaresi)", "Bank-ı Osmani", "Ziraat Bankası", "Reji İdaresi", "Kapitülasyonlar"], "a": "Duyun-u Umumiye (Genel Borçlar İdaresi)"},
        {"q": "Duyun-u Umumiye'nin kurulması Osmanlı için ne anlama gelir?", "opts": ["Ekonomik bağımsızlığın kaybedilmesi", "Borçların bitmesi", "Zenginleşme", "Sanayileşme", "Kalkınma"], "a": "Ekonomik bağımsızlığın kaybedilmesi"},
        {"q": "Osmanlı'da milli bankacılığın temeli sayılan ve çiftçiye kredi vermek için kurulan sandıklar nedir?", "opts": ["Memleket Sandıkları", "Emniyet Sandığı", "Duyun-u Umumiye", "İtibar-ı Milli", "İş Bankası"], "a": "Memleket Sandıkları"},
        {"q": "Memleket Sandıkları daha sonra (1888) hangi bankaya dönüşmüştür?", "opts": ["Ziraat Bankası", "Osmanlı Bankası", "İş Bankası", "Halk Bankası", "Vakıfbank"], "a": "Ziraat Bankası"},
        {"q": "Osmanlı'da ilk demiryolu hattı nereye yapılmıştır (1856-1866)?", "opts": ["İzmir - Aydın", "İstanbul - Edirne", "İstanbul - Ankara", "Bağdat - Basra", "Selanik - Manastır"], "a": "İzmir - Aydın"},
        {"q": "Sanayi İnkılabı'na tepki olarak doğan ve işçi haklarını savunan fikir akımı nedir?", "opts": ["Sosyalizm", "Liberalizm", "Kapitalizm", "Merkantilizm", "Faşizm"], "a": "Sosyalizm"},
        {"q": "Kapitalizmin savunduğu 'Bırakınız yapsınlar, bırakınız geçsinler' ilkesi kime aittir?", "opts": ["Adam Smith", "Karl Marx", "Engels", "Keynes", "Ricardo"], "a": "Adam Smith"},
        {"q": "Osmanlı'da sanayileşme hamlesi olarak kurulan fabrikalar (Feshane, Çuha Fabrikası vb.) neden başarılı olamamıştır?", "opts": ["Bilgi ve sermaye eksikliği ile kapitülasyonlar", "Hammadde yokluğu", "İşçi bulunamaması", "Savaşlar", "Padişahın istememesi"], "a": "Bilgi ve sermaye eksikliği ile kapitülasyonlar"},
        {"q": "Yedi Yıl Savaşları'nın (1756-1763) temel nedeni nedir?", "opts": ["İngiltere ve Fransa arasındaki sömürge rekabeti", "Din savaşları", "Osmanlı mirası", "Alman birliği", "İtalyan birliği"], "a": "İngiltere ve Fransa arasındaki sömürge rekabeti"},
        {"q": "Osmanlı'da yerli malı kullanımını teşvik eden ilk padişah kimdir?", "opts": ["III. Selim", "II. Mahmut", "Abdülmecid", "II. Abdülhamid", "Kanuni"], "a": "III. Selim"},
        {"q": "İttihat ve Terakki'nin I. Dünya Savaşı yıllarında uygulamaya çalıştığı ekonomi politikası nedir?", "opts": ["Milli İktisat", "Liberalizm", "Kapitalizm", "Sosyalizm", "Merkantilizm"], "a": "Milli İktisat"},
        {"q": "1914'te tek taraflı olarak kaldırılan kapitülasyonlar kesin olarak ne zaman kaldırılmıştır?", "opts": ["Lozan Antlaşması (1923)", "Sevr Antlaşması", "Mondros Ateşkesi", "Mudanya Ateşkesi", "Ankara Antlaşması"], "a": "Lozan Antlaşması (1923)"}
    ],"17. XIX. ve XX. Yüzyılda Değişen Gündelik Hayat": [
        {"q": "Osmanlı'da modern anlamda ilk nüfus sayımı (sadece erkeklerin sayıldığı) hangi padişah döneminde yapılmıştır?", "opts": ["II. Mahmut", "III. Selim", "Abdülmecid", "Abdülaziz", "Kanuni"], "a": "II. Mahmut"},
        {"q": "Osmanlı Devleti'nde çıkan ilk Türkçe resmi gazete hangisidir?", "opts": ["Takvim-i Vekayi", "Ceride-i Havadis", "Tercüman-ı Ahval", "Tasvir-i Efkar", "Tanin"], "a": "Takvim-i Vekayi"},
        {"q": "Osmanlı'da özel teşebbüsle (Şinasi ve Agah Efendi) çıkarılan ilk özel gazete hangisidir?", "opts": ["Tercüman-ı Ahval", "Takvim-i Vekayi", "İkdam", "Sabah", "Hürriyet"], "a": "Tercüman-ı Ahval"},
        {"q": "19. yüzyılda İstanbul'da deniz ulaşımını sağlamak amacıyla kurulan şirket hangisidir?", "opts": ["Şirket-i Hayriye", "Seyr-i Sefain", "Denizbank", "Liman İşletmesi", "Haliç Vapurları"], "a": "Şirket-i Hayriye"},
        {"q": "Osmanlı'da ilk tramvay hatları ve tünel (metro) hangi şehirde kurulmuştur?", "opts": ["İstanbul", "İzmir", "Selanik", "Beyrut", "Şam"], "a": "İstanbul"},
        {"q": "Osmanlı'da modern tiyatronun (Darülbedayi) temelleri hangi dönemde atılmıştır?", "opts": ["II. Meşrutiyet / 1914", "Lale Devri", "Tanzimat", "Cumhuriyet", "Yükselme"], "a": "II. Meşrutiyet / 1914"},
        {"q": "Osmanlı'da Batı müziği eğitimi vermek amacıyla kurulan askeri bando okulu hangisidir?", "opts": ["Mızıka-i Hümayun", "Darülelhan", "Mehterhane", "Enderun", "Hendesehane"], "a": "Mızıka-i Hümayun"},
        {"q": "Mızıka-i Hümayun'u kuran İtalyan müzisyen kimdir?", "opts": ["Donizetti Paşa", "Guatelli Paşa", "Mozart", "Verdi", "Vivaldi"], "a": "Donizetti Paşa"},
        {"q": "Osmanlı'da ilk konservatuvar sayılan kurum hangisidir?", "opts": ["Darülelhan", "Darülbedayi", "Darülfünun", "Sanayi-i Nefise", "Encümen-i Daniş"], "a": "Darülelhan"},
        {"q": "Osmanlı'da kadınların sosyal hayata katılımını artırmak için kurulan derneklerden biri hangisidir?", "opts": ["Teali-i Nisvan Cemiyeti", "Müdafaa-i Hukuk", "İttihat ve Terakki", "Ahrar", "Hilal-i Ahmer"], "a": "Teali-i Nisvan Cemiyeti"},
        {"q": "19. yüzyılda Osmanlı'da 'Alafranga' neyi ifade eder?", "opts": ["Batı (Avrupa) tarzı yaşam biçimini", "Geleneksel yaşamı", "Doğu kültürünü", "Dini yaşamı", "Askeri düzeni"], "a": "Batı (Avrupa) tarzı yaşam biçimini"},
        {"q": "Osmanlı'da kaybedilen topraklardan (Kırım, Kafkasya, Balkanlar) Anadolu'ya yapılan göçlerin en önemli sonucu nedir?", "opts": ["Anadolu'da Müslüman-Türk nüfus yoğunluğunun artması", "Ekonominin çökmesi", "Ordunun zayıflaması", "Dilin değişmesi", "Rejimin değişmesi"], "a": "Anadolu'da Müslüman-Türk nüfus yoğunluğunun artması"},
        {"q": "Osmanlı'da 'Mahalle' kavramının değişime uğrayıp 'Apartmanlaşma'nın başladığı semt neresidir?", "opts": ["Pera (Beyoğlu) - Galata", "Fatih", "Üsküdar", "Eyüp", "Sultanahmet"], "a": "Pera (Beyoğlu) - Galata"},
        {"q": "19. yüzyılda Osmanlı saraylarında hangi müzik türü ilgi görmeye başlamıştır?", "opts": ["Opera ve Batı Müziği", "Sadece Halk Müziği", "Arabesk", "Caz", "Rock"], "a": "Opera ve Batı Müziği"},
        {"q": "Osmanlı'da ilk telefon, elektrik ve otomobil kullanımı hangi dönemde yaygınlaşmaya başlamıştır?", "opts": ["II. Abdülhamid ve Meşrutiyet dönemi", "Fatih dönemi", "Lale Devri", "Kuruluş dönemi", "Fetret devri"], "a": "II. Abdülhamid ve Meşrutiyet dönemi"},
        {"q": "Osmanlı'da halkın haber alma özgürlüğünün kısıtlandığı (Sansür) dönem hangisidir?", "opts": ["II. Abdülhamid (İstibdat Dönemi)", "Tanzimat", "Lale Devri", "III. Selim", "Kanuni"], "a": "II. Abdülhamid (İstibdat Dönemi)"},
        {"q": "Osmanlı'da 'Kanton' adı verilen eğlence türü (Müzikli tiyatro) hangi semtte gelişmiştir?", "opts": ["Direklerarası (Şehzadebaşı)", "Üsküdar", "Kadıköy", "Adalar", "Bebek"], "a": "Direklerarası (Şehzadebaşı)"},
        {"q": "Şeker Ahmet Paşa ve Osman Hamdi Bey hangi sanat dalının öncüleridir?", "opts": ["Resim", "Müzik", "Tiyatro", "Heykel", "Mimari"], "a": "Resim"},
        {"q": "Osmanlı'da ilk arkeoloji müzesini kuran ve 'Kaplumbağa Terbiyecisi' tablosunun ressamı kimdir?", "opts": ["Osman Hamdi Bey", "Şeker Ahmet Paşa", "Hoca Ali Rıza", "İbrahim Çallı", "Abidin Dino"], "a": "Osman Hamdi Bey"},
        {"q": "Osmanlı mutfağına domates, patates, kakao gibi ürünlerin girmesi neyin sonucudur?", "opts": ["Coğrafi Keşifler ve Amerika'nın keşfi", "Haçlı Seferleri", "İpek Yolu", "Sanayi İnkılabı", "Rönesans"], "a": "Coğrafi Keşifler ve Amerika'nın keşfi"},
        {"q": "19. yüzyılda Osmanlı erkek giyiminde kavuk ve cübbenin yerini ne almıştır?", "opts": ["Fes, Pantolon ve Setre", "Şapka", "Sarık", "Kaftan", "Şalvar"], "a": "Fes, Pantolon ve Setre"},
        {"q": "Osmanlı'da ilk kadın romancı ve 50 TL banknotlarının üzerindeki kişi kimdir?", "opts": ["Fatma Aliye Hanım", "Halide Edip", "Nezihe Muhiddin", "Afife Jale", "Sabiha Gökçen"], "a": "Fatma Aliye Hanım"},
        {"q": "Osmanlı'da sahneye çıkan ilk Müslüman Türk kadın tiyatrocu kimdir?", "opts": ["Afife Jale", "Bedia Muvahhit", "Cahide Sonku", "Neyyire Neyir", "Halide Pişkin"], "a": "Afife Jale"},
        {"q": "Osmanlı'da 'Hilal-i Ahmer' cemiyetinin bugünkü adı nedir?", "opts": ["Kızılay", "Yeşilay", "Çocuk Esirgeme Kurumu", "Mehmetçik Vakfı", "Darülaceze"], "a": "Kızılay"},
        {"q": "Osmanlı'da 'Himaye-i Etfal' cemiyetinin bugünkü adı nedir?", "opts": ["Çocuk Esirgeme Kurumu", "Kızılay", "Yeşilay", "Darüşşafaka", "Lösev"], "a": "Çocuk Esirgeme Kurumu"},
        {"q": "Osmanlı'da yetim ve öksüz Müslüman çocukların eğitimi için kurulan okul hangisidir?", "opts": ["Darüşşafaka", "Galatasaray Sultanisi", "Robert Koleji", "Mülkiye", "Harbiye"], "a": "Darüşşafaka"},
        {"q": "19. yüzyılda İstanbul'un siluetini değiştiren, Batı tarzı mimari eserlerden biri değildir?", "opts": ["Sultanahmet Camii (Klasik Dönem)", "Dolmabahçe Sarayı", "Çırağan Sarayı", "Yıldız Sarayı", "Beylerbeyi Sarayı"], "a": "Sultanahmet Camii (Klasik Dönem)"},
        {"q": "Osmanlı'da spor alanında kurulan ilk kulüpler (Beşiktaş, Galatasaray, Fenerbahçe) hangi dönemde ortaya çıkmıştır?", "opts": ["XX. Yüzyıl başları (II. Meşrutiyet)", "Lale Devri", "Yükselme", "Duraklama", "Cumhuriyet"], "a": "XX. Yüzyıl başları (II. Meşrutiyet)"},
        {"q": "Osmanlı'da 'Düyun-u Umumiye' binası (Bugünkü İstanbul Erkek Lisesi) hangi mimari üslubu yansıtır?", "opts": ["Birinci Ulusal Mimarlık Akımı (Neoklasik)", "Barok", "Gotik", "Rokoko", "Selçuklu"], "a": "Birinci Ulusal Mimarlık Akımı (Neoklasik)"},
        {"q": "Osmanlı'da modern anlamda ilk hemşirelik faaliyetleri hangi savaş sırasında başlamıştır?", "opts": ["Kırım Savaşı (Florence Nightingale)", "93 Harbi", "Balkan Savaşları", "I. Dünya Savaşı", "Trablusgarp Savaşı"], "a": "Kırım Savaşı (Florence Nightingale)"},
        {"q": "Osmanlı'da ilk mizah dergisi hangisidir?", "opts": ["Diyojen (Teodor Kasap)", "Kalem", "Davul", "Karagöz", "Markopaşa"], "a": "Diyojen (Teodor Kasap)"},
        {"q": "Osmanlı'da tüketim alışkanlıklarının değişmesiyle hangi ürünlerin kullanımı artmıştır?", "opts": ["Kahve ve Tütün", "Kımız", "Pastırma", "Bulgur", "Ayran"], "a": "Kahve ve Tütün"},
        {"q": "Osmanlı şehirlerinde gece hayatının ve aydınlatmanın başlaması neyle sağlanmıştır?", "opts": ["Hagazı (Gaz lambaları) ve sonrasında elektrik", "Mum", "Meşale", "Ateş", "Ay ışığı"], "a": "Hagazı (Gaz lambaları) ve sonrasında elektrik"},
        {"q": "Osmanlı'da 'Selamlık Sohbetleri'nin yerini zamanla ne almıştır?", "opts": ["Kıraathaneler ve Kulüpler", "Camiler", "Medreseler", "Saraylar", "Hamamlar"], "a": "Kıraathaneler ve Kulüpler"},
        {"q": "Osmanlı'da ilk grev (iş bırakma) eylemini kimler yapmıştır?", "opts": ["Telgraf ve Tersane işçileri", "Memurlar", "Askerler", "Köylüler", "Öğrenciler"], "a": "Telgraf ve Tersane işçileri"},
        {"q": "Osmanlı'da 'Mesire Yerleri' (Kağıthane, Göksu) ne amaçla kullanılırdı?", "opts": ["Halkın sosyalleşmesi ve eğlenmesi (Piknik)", "Askeri eğitim", "Pazar yeri", "İbadet", "Tarım"], "a": "Halkın sosyalleşmesi ve eğlenmesi (Piknik)"},
        {"q": "19. yüzyılda Osmanlı'da 'Frenk' kime denirdi?", "opts": ["Avrupalılara ve Batı tarzı giyinenlere", "Türklere", "Araplara", "Köylülere", "Askerlere"], "a": "Avrupalılara ve Batı tarzı giyinenlere"},
        {"q": "Osmanlı'da 'Ramazan Eğlenceleri' (Direklerarası) hangi sanat dallarını içerirdi?", "opts": ["Karagöz, Hacivat, Ortaoyunu, Meddah", "Opera", "Bale", "Sinema", "Futbol"], "a": "Karagöz, Hacivat, Ortaoyunu, Meddah"},
        {"q": "Osmanlı'da ilk sinema gösterimi nerede yapılmıştır?", "opts": ["İstanbul (Beyoğlu)", "İzmir", "Selanik", "Bursa", "Ankara"], "a": "İstanbul (Beyoğlu)"},
        {"q": "Osmanlı'da 'Saat Kuleleri'nin yaygınlaşması (II. Abdülhamid dönemi) neyin göstergesidir?", "opts": ["Zaman kavramının modernleşmesinin ve devlet otoritesinin", "Dini yaşamın", "Savaşın", "Eğitimin", "Sanatın"], "a": "Zaman kavramının modernleşmesinin ve devlet otoritesinin"},
        {"q": "Osmanlı'da 'Pera Palas' oteli neden yapılmıştır?", "opts": ["Orient Express (Şark Ekspresi) yolcularını ağırlamak için", "Padişah için", "Askerler için", "Halk için", "Okul olması için"], "a": "Orient Express (Şark Ekspresi) yolcularını ağırlamak için"},
        {"q": "Osmanlı'da 'Bonmarşe' ne demektir?", "opts": ["Çok katlı büyük mağaza (AVM'nin atası)", "Banka", "Okul", "Hastane", "Park"], "a": "Çok katlı büyük mağaza (AVM'nin atası)"},
        {"q": "Osmanlı'da fotoğrafçılığın yaygınlaşması hangi padişah döneminde zirveye ulaşmıştır?", "opts": ["II. Abdülhamid", "III. Selim", "Fatih", "Kanuni", "Orhan Bey"], "a": "II. Abdülhamid"},
        {"q": "Osmanlı'da 'Hamidiye Suları' projesi neyi amaçlamıştır?", "opts": ["İstanbul'a temiz içme suyu sağlamayı", "Tarımı sulamayı", "Yangın söndürmeyi", "Hamamları beslemeyi", "Gemileri yüzdürmeyi"], "a": "İstanbul'a temiz içme suyu sağlamayı"},
        {"q": "Osmanlı'da 'Milli Mimari Rönesansı'nı başlatan mimarlar kimlerdir?", "opts": ["Mimar Kemalettin ve Vedat Tek", "Mimar Sinan", "Sedefkar Mehmet", "Balyan Ailesi", "Sarkis Balyan"], "a": "Mimar Kemalettin ve Vedat Tek"},
        {"q": "19. yüzyılda Osmanlı'da gayrimüslimlerin ve yabancıların yoğun yaşadığı, Batılı yaşam tarzının merkezi olan semt neresidir?", "opts": ["Beyoğlu (Pera)", "Fatih", "Eyüp", "Üsküdar", "Kasımpaşa"], "a": "Beyoğlu (Pera)"},
        {"q": "Osmanlı'da 'Karantina' uygulaması ilk kez hangi padişah döneminde başlamıştır?", "opts": ["II. Mahmut", "Fatih", "Kanuni", "III. Selim", "Abdülaziz"], "a": "II. Mahmut"},
        {"q": "Osmanlı'da ilk modern nüfus cüzdanı (Kafa Kağıdı) ne zaman verilmiştir?", "opts": ["II. Mahmut (1830'lar)", "Cumhuriyet", "Lale Devri", "Meşrutiyet", "Yükselme"], "a": "II. Mahmut (1830'lar)"},
        {"q": "Osmanlı'da 'Araba Sevdası' romanında eleştirilen sosyal tip hangisidir?", "opts": ["Bihruz Bey (Yanlış Batılılaşan züppe)", "Köylü", "Asker", "Hoca", "Tüccar"], "a": "Bihruz Bey (Yanlış Batılılaşan züppe)"},
        {"q": "Osmanlı'da gündelik hayatta 'fes'in yerine 'şapka'nın geçmesi ne zaman olmuştur?", "opts": ["Cumhuriyet Dönemi (Şapka İnkılabı)", "Tanzimat", "Meşrutiyet", "Lale Devri", "I. Dünya Savaşı"], "a": "Cumhuriyet Dönemi (Şapka İnkılabı)"}
    ],

    "20. XX. Yüzyıl Başlarında Osmanlı Devleti ve Dünya": [
        {"q": "Osmanlı Devleti'nin Kuzey Afrika'daki son toprak parçasını kaybettiği savaş hangisidir?", "opts": ["Trablusgarp Savaşı", "Balkan Savaşları", "I. Dünya Savaşı", "93 Harbi", "Kırım Savaşı"], "a": "Trablusgarp Savaşı"},
        {"q": "Mustafa Kemal'in 'Gazeteci Şerif Bey' takma adıyla gönüllü olarak katıldığı savaş hangisidir?", "opts": ["Trablusgarp Savaşı", "Çanakkale Savaşı", "Balkan Savaşları", "Sakarya Savaşı", "Kurtuluş Savaşı"], "a": "Trablusgarp Savaşı"},
        {"q": "Trablusgarp Savaşı'nı bitiren ve On İki Ada'nın geçici olarak İtalya'ya bırakıldığı antlaşma hangisidir?", "opts": ["Uşi Antlaşması", "Lozan Antlaşması", "Londra Antlaşması", "Atina Antlaşması", "İstanbul Antlaşması"], "a": "Uşi Antlaşması"},
        {"q": "I. Balkan Savaşı'nda Osmanlı'ya saldıran devletler hangileridir?", "opts": ["Bulgaristan, Yunanistan, Sırbistan, Karadağ", "Romanya, Rusya, İngiltere", "Almanya, Avusturya", "İtalya, Fransa", "Mısır, Suriye"], "a": "Bulgaristan, Yunanistan, Sırbistan, Karadağ"},
        {"q": "Arnavutluk'un bağımsızlığını ilan etmesi hangi savaş sırasında olmuştur?", "opts": ["I. Balkan Savaşı", "Trablusgarp Savaşı", "I. Dünya Savaşı", "II. Balkan Savaşı", "Kurtuluş Savaşı"], "a": "I. Balkan Savaşı"},
        {"q": "I. Balkan Savaşı'nın kaybedilmesinin en önemli nedeni nedir?", "opts": ["Ordunun siyasete karışması", "Silah eksikliği", "Dış destek", "Ekonomi", "Halkın isyanı"], "a": "Ordunun siyasete karışması"},
        {"q": "II. Balkan Savaşı'nın çıkma nedeni nedir?", "opts": ["Bulgaristan'ın I. Balkan Savaşı'nda en büyük payı alması", "Osmanlı'nın saldırması", "Rusya'nın isteği", "Arnavutluk sorunu", "Makedonya sorunu"], "a": "Bulgaristan'ın I. Balkan Savaşı'nda en büyük payı alması"},
        {"q": "Mustafa Kemal'in 'Edirne'yi geri aldığı' ve Enver Paşa'nın kahramanlaştığı savaş hangisidir?", "opts": ["II. Balkan Savaşı", "I. Balkan Savaşı", "Trablusgarp", "Çanakkale", "Kafkas"], "a": "II. Balkan Savaşı"},
        {"q": "I. Dünya Savaşı'nın genel nedeni nedir?", "opts": ["Sömürgecilik, Hammadde ve Pazar arayışı (Sanayi İnkılabı)", "Din savaşları", "Mezhep çatışmaları", "Kral kavgaları", "Kadın hakları"], "a": "Sömürgecilik, Hammadde ve Pazar arayışı (Sanayi İnkılabı)"},
        {"q": "I. Dünya Savaşı'nı başlatan kıvılcım (özel neden) nedir?", "opts": ["Avusturya-Macaristan veliahtının Saraybosna'da bir Sırp milliyetçisi tarafından öldürülmesi", "Almanya'nın Polonya'ya girmesi", "Rusya'nın sıcak denizlere inmesi", "Fransız İhtilali", "Süveyş Kanalı'nın açılması"], "a": "Avusturya-Macaristan veliahtının Saraybosna'da bir Sırp milliyetçisi tarafından öldürülmesi"},
        {"q": "Osmanlı Devleti'nin I. Dünya Savaşı'nda Almanya'nın yanında yer alma nedenlerinden biri değildir?", "opts": ["Kaybedilen toprakları geri alma isteği", "Siyasi yalnızlıktan kurtulma", "Almanya'nın savaşı kazanacağına inanılması", "İngiltere'nin toprak vermesi", "İttihat ve Terakki'nin Alman hayranlığı"], "a": "İngiltere'nin toprak vermesi"},
        {"q": "Osmanlı'nın I. Dünya Savaşı'na girmesine neden olan gemiler hangileridir?", "opts": ["Goben ve Breslau (Yavuz ve Midilli)", "Nusret ve Muavenet", "Hamidiye ve Mecidiye", "Sultan Osman ve Reşadiye", "Mayflower ve Titanic"], "a": "Goben ve Breslau (Yavuz ve Midilli)"},
        {"q": "Osmanlı'nın I. Dünya Savaşı'nda savaştığı 'Taarruz' (Saldırı) cepheleri hangileridir?", "opts": ["Kafkas ve Kanal", "Çanakkale ve Irak", "Suriye ve Filistin", "Galiçya ve Makedonya", "Hicaz ve Yemen"], "a": "Kafkas ve Kanal"},
        {"q": "Kafkas Cephesi'nde Sarıkamış Harekatı'nın başarısız olmasının nedeni nedir?", "opts": ["Ağır kış şartları ve teçhizat eksikliği", "Düşmanın çok güçlü olması", "Cephane bitmesi", "İhanet", "Salgın hastalık"], "a": "Ağır kış şartları ve teçhizat eksikliği"},
        {"q": "Mustafa Kemal'in Kafkas Cephesi'nde geri aldığı iller hangileridir?", "opts": ["Muş ve Bitlis", "Kars ve Ardahan", "Erzurum ve Erzincan", "Van ve Hakkari", "Trabzon ve Rize"], "a": "Muş ve Bitlis"},
        {"q": "Osmanlı Devleti'nin 1915'te Ermenilere yönelik çıkardığı zorunlu göç kanunu nedir?", "opts": ["Tehcir Kanunu (Sevk ve İskan)", "Tanzimat", "Islahat", "Varlık Vergisi", "İskan Kanunu"], "a": "Tehcir Kanunu (Sevk ve İskan)"},
        {"q": "Çanakkale Cephesi'nin açılma nedenlerinden biri değildir?", "opts": ["Osmanlı'yı savaş dışı bırakmak", "Rusya'ya yardım götürmek", "İstanbul'u almak", "Yeni cepheler açılmasını engellemek", "Almanya'yı işgal etmek"], "a": "Almanya'yı işgal etmek"},
        {"q": "Mustafa Kemal'in 'Ben size taarruzu değil, ölmeyi emrediyorum' dediği cephe hangisidir?", "opts": ["Çanakkale Cephesi", "Kafkas Cephesi", "Suriye Cephesi", "Trablusgarp", "Sakarya"], "a": "Çanakkale Cephesi"},
        {"q": "I. Dünya Savaşı'nda Osmanlı'nın kazandığı tek cephe hangisidir?", "opts": ["Çanakkale Cephesi", "Kafkas Cephesi", "Kanal Cephesi", "Irak Cephesi", "Yemen Cephesi"], "a": "Çanakkale Cephesi"},
        {"q": "Çanakkale Zaferi'nin Dünya tarihi açısından en önemli sonucu nedir?", "opts": ["I. Dünya Savaşı'nın süresinin uzaması ve Rusya'da Bolşevik İhtilali'nin çıkması", "Osmanlı'nın savaşı kazanması", "ABD'nin savaşa girmesi", "Almanya'nın yenilmesi", "İtalya'nın taraf değiştirmesi"], "a": "I. Dünya Savaşı'nın süresinin uzaması ve Rusya'da Bolşevik İhtilali'nin çıkması"},
        {"q": "Irak Cephesi'nde Halil (Kut) Paşa'nın İngiliz ordusunu esir aldığı zafer hangisidir?", "opts": ["Kut'ül Amare Zaferi", "Çanakkale Zaferi", "Plevne Zaferi", "Dumlupınar Zaferi", "Sakarya Zaferi"], "a": "Kut'ül Amare Zaferi"},
        {"q": "Kanal Cephesi'nin açılma amacı nedir?", "opts": ["Mısır'ı geri almak ve İngiltere'nin sömürge yollarını kesmek", "Rusya'ya yardım etmek", "Petrol bölgelerini korumak", "Kutsal toprakları korumak", "İstanbul'u korumak"], "a": "Mısır'ı geri almak ve İngiltere'nin sömürge yollarını kesmek"},
        {"q": "Hicaz-Yemen Cephesi'nde 'Medine Müdafii' olarak bilinen komutan kimdir?", "opts": ["Fahrettin Paşa", "Enver Paşa", "Cemal Paşa", "Talat Paşa", "Mustafa Kemal"], "a": "Fahrettin Paşa"},
        {"q": "I. Dünya Savaşı sırasında Arapların İngilizlerle işbirliği yapması hangi fikir akımının çöktüğünü gösterir?", "opts": ["İslamcılık (Ümmetçilik)", "Türkçülük", "Osmanlıcılık", "Batıcılık", "Turancılık"], "a": "İslamcılık (Ümmetçilik)"},
        {"q": "I. Dünya Savaşı sırasında imzalanan gizli antlaşmaların amacı nedir?", "opts": ["Osmanlı topraklarını kendi aralarında paylaşmak", "Barışı sağlamak", "Almanya'yı bölmek", "Ticaret yapmak", "Silah satmak"], "a": "Osmanlı topraklarını kendi aralarında paylaşmak"},
        {"q": "Gizli antlaşmaları Dünya kamuoyuna duyuran devlet hangisidir?", "opts": ["Sovyet Rusya (Bolşevikler)", "ABD", "Osmanlı", "Almanya", "İtalya"], "a": "Sovyet Rusya (Bolşevikler)"},
        {"q": "ABD'nin savaşa girmesi ve savaşın bitişini hızlandıran gelişme nedir?", "opts": ["Alman denizaltılarının ABD ticaret gemilerini batırması", "Çanakkale Savaşı", "Rusya'nın çekilmesi", "Osmanlı'nın yenilmesi", "İtalya'nın taraf değiştirmesi"], "a": "Alman denizaltılarının ABD ticaret gemilerini batırması"},
        {"q": "Wilson İlkeleri'nin en önemli maddesi nedir?", "opts": ["Her milletin kendi geleceğini belirleme hakkı (Self-determinasyon)", "Sömürgeciliğin devam etmesi", "Savaş tazminatı alınması", "Gizli antlaşmaların yapılması", "Silahlanmanın artması"], "a": "Her milletin kendi geleceğini belirleme hakkı (Self-determinasyon)"},
        {"q": "I. Dünya Savaşı'nı Osmanlı adına bitiren ateşkes antlaşması hangisidir?", "opts": ["Mondros Ateşkes Antlaşması", "Mudanya Ateşkesi", "Sevr Antlaşması", "Lozan Antlaşması", "Paris Antlaşması"], "a": "Mondros Ateşkes Antlaşması"},
        {"q": "Mondros'un 'Anadolu'nun işgaline zemin hazırlayan' en tehlikeli maddesi hangisidir?", "opts": ["7. Madde (İtilaf devletleri güvenliklerini tehdit eden herhangi bir stratejik noktayı işgal edebilecek)", "24. Madde", "Ordunun terhisi", "Toros tünellerinin işgali", "Donanmanın teslimi"], "a": "7. Madde (İtilaf devletleri güvenliklerini tehdit eden herhangi bir stratejik noktayı işgal edebilecek)"},
        {"q": "Mondros'un 24. maddesi ('Vilayet-i Sitte'de karışıklık çıkarsa işgal edilecek') neyi amaçlamaktadır?", "opts": ["Doğu Anadolu'da bir Ermeni devleti kurmayı", "Kürt devleti kurmayı", "Rum devleti kurmayı", "Petrolü almayı", "Rusya'yı engellemeyi"], "a": "Doğu Anadolu'da bir Ermeni devleti kurmayı"},
        {"q": "Mondros'tan sonra işgal edilen ilk Osmanlı toprağı neresidir?", "opts": ["Musul (İngiltere)", "İzmir", "İstanbul", "Antalya", "Adana"], "a": "Musul (İngiltere)"},
        {"q": "Mondros'tan sonra Anadolu'da işgal edilen ilk yer (Hatay-Dörtyol) kime karşı direniş başlatmıştır?", "opts": ["Fransa", "İngiltere", "Yunanistan", "İtalya", "Ermeniler"], "a": "Fransa"},
        {"q": "Paris Barış Konferansı'nda (1919) İzmir ve çevresinin İtalya yerine Yunanistan'a verilmesinin nedeni nedir?", "opts": ["İngiltere'nin Akdeniz'de güçlü bir İtalya istememesi", "Yunanistan'ın daha güçlü olması", "Tarihi haklar", "Nüfus yoğunluğu", "İtalya'nın savaştan çekilmesi"], "a": "İngiltere'nin Akdeniz'de güçlü bir İtalya istememesi"},
        {"q": "İzmir'in Yunanlılar tarafından işgali (15 Mayıs 1919) Türk halkında neye yol açmıştır?", "opts": ["Milli bilincin uyanmasına ve Kuva-yi Milliye'nin doğuşuna", "Teslimiyete", "Padişaha bağlılığa", "Göçe", "İç savaşa"], "a": "Milli bilincin uyanmasına ve Kuva-yi Milliye'nin doğuşuna"},
        {"q": "İzmir'in işgalinde ilk kurşunu atarak şehit olan gazeteci kimdir?", "opts": ["Hasan Tahsin", "Sütçü İmam", "Şahin Bey", "Ali Saip Bey", "Yörük Ali Efe"], "a": "Hasan Tahsin"},
        {"q": "Osmanlı Devleti'nin I. Dünya Savaşı sonunda imzaladığı barış antlaşması (1920) hangisidir?", "opts": ["Sevr Barış Antlaşması", "Lozan Antlaşması", "Versay Antlaşması", "Saint Germain Antlaşması", "Trianon Antlaşması"], "a": "Sevr Barış Antlaşması"},
        {"q": "Sevr Antlaşması'nın hukuken geçersiz olmasının nedeni nedir?", "opts": ["Mebusan Meclisi tarafından onaylanmaması", "Padişahın imzalamaması", "Süresinin dolması", "Halkın istememesi", "Savaşın devam etmesi"], "a": "Mebusan Meclisi tarafından onaylanmaması"},
        {"q": "Kuva-yi Milliye nedir?", "opts": ["Halkın işgallere karşı kurduğu düzensiz silahlı direniş birlikleri", "Düzenli ordu", "Padişahın ordusu", "İtilaf devletleri birliği", "Polis teşkilatı"], "a": "Halkın işgallere karşı kurduğu düzensiz silahlı direniş birlikleri"},
        {"q": "Yararlı (Milli) Cemiyetlerin ortak amacı nedir?", "opts": ["Bölgesel kurtuluşu sağlamak ve işgalleri önlemek", "Padişahı korumak", "Halifeyi korumak", "İngiliz mandasını istemek", "Devlet kurmak"], "a": "Bölgesel kurtuluşu sağlamak ve işgalleri önlemek"},
        {"q": "Doğu Anadolu Müdafaa-i Hukuk Cemiyeti'nin amacı nedir?", "opts": ["Doğu Anadolu'da Ermeni devleti kurulmasını engellemek", "Pontus Rum devleti kurmak", "Fransızları atmak", "İngilizleri atmak", "Petrolü korumak"], "a": "Doğu Anadolu'da Ermeni devleti kurulmasını engellemek"},
        {"q": "Kilikyalılar Cemiyeti hangi bölgeyi savunmak için kurulmuştur?", "opts": ["Adana ve Çukurova", "Trabzon", "İzmir", "Trakya", "Erzurum"], "a": "Adana ve Çukurova"},
        {"q": "Zararlı (Milli Varlığa Düşman) cemiyetlerden 'Mavri Mira'nın amacı nedir?", "opts": ["Büyük Yunanistan'ı (Megali İdea) kurmak", "Pontus devleti kurmak", "Kürt devleti kurmak", "Ermeni devleti kurmak", "Hilafeti korumak"], "a": "Büyük Yunanistan'ı (Megali İdea) kurmak"},
        {"q": "Manda ve himayeyi savunan zararlı cemiyet hangisidir?", "opts": ["İngiliz Muhipleri Cemiyeti (ve Wilson Prensipleri)", "Kilikyalılar", "Milli Kongre", "Trakya Paşaeli", "Redd-i İlhak"], "a": "İngiliz Muhipleri Cemiyeti (ve Wilson Prensipleri)"},
        {"q": "Basın-yayın yoluyla mücadele eden ve Kuva-yi Milliye tabirini ilk kullanan yararlı cemiyet hangisidir?", "opts": ["Milli Kongre Cemiyeti", "Redd-i İlhak", "Kilikyalılar", "Şark Vilayetleri", "Trabzon Muhafaza"], "a": "Milli Kongre Cemiyeti"},
        {"q": "I. Dünya Savaşı'nda Almanya'nın imzaladığı barış antlaşması hangisidir?", "opts": ["Versay", "Sevr", "Saint Germain", "Neuilly", "Trianon"], "a": "Versay"},
        {"q": "Brest-Litovsk Antlaşması ile savaştan çekilen ve Kars, Ardahan, Batum'u Osmanlı'ya geri veren devlet hangisidir?", "opts": ["Sovyet Rusya", "Almanya", "İngiltere", "Fransa", "Bulgaristan"], "a": "Sovyet Rusya"},
        {"q": "Tehcir Kanunu ile Ermeniler nereye göç ettirilmiştir?", "opts": ["Suriye ve Lübnan", "Avrupa", "Rusya", "İran", "Mısır"], "a": "Suriye ve Lübnan"},
        {"q": "Mustafa Kemal'in I. Dünya Savaşı'ndaki son görevi nedir?", "opts": ["Suriye-Filistin Cephesi (Yıldırım Orduları Grup Komutanı)", "Kafkas Cephesi Komutanı", "Çanakkale Komutanı", "Hareket Ordusu Komutanı", "Sofya Ataşemiliteri"], "a": "Suriye-Filistin Cephesi (Yıldırım Orduları Grup Komutanı)"},
        {"q": "İzmir'in işgalinin haksız olduğunu belirten ilk uluslararası rapor hangisidir?", "opts": ["Amiral Bristol Raporu", "General Harbord Raporu", "Sandler Raporu", "Milne Hattı", "Hrisantos Raporu"], "a": "Amiral Bristol Raporu"}
    ],

    "21. Milli Mücadele": [
        {"q": "Milli Mücadele'nin fiilen başladığı kabul edilen olay nedir?", "opts": ["Mustafa Kemal'in Samsun'a çıkışı (19 Mayıs 1919)", "İzmir'in işgali", "Mondros Ateşkesi", "TBMM'nin açılması", "Sivas Kongresi"], "a": "Mustafa Kemal'in Samsun'a çıkışı (19 Mayıs 1919)"},
        {"q": "Mustafa Kemal'in Samsun'a çıkarkenki resmi görevi nedir?", "opts": ["9. Ordu Müfettişi", "Yıldırım Orduları Komutanı", "Harbiye Nazırı", "Genelkurmay Başkanı", "Sivil Vatandaş"], "a": "9. Ordu Müfettişi"},
        {"q": "Milli Mücadele'de ulusal bilinci uyandırmak için yayımlanan ilk belge hangisidir?", "opts": ["Havza Genelgesi", "Amasya Genelgesi", "Erzurum Kongresi", "Sivas Kongresi", "Misak-ı Milli"], "a": "Havza Genelgesi"},
        {"q": "Milli Mücadele'nin amacı, gerekçesi ve yönteminin belirlendiği belge hangisidir?", "opts": ["Amasya Genelgesi", "Havza Genelgesi", "Erzurum Kongresi", "Sivas Kongresi", "Misak-ı Milli"], "a": "Amasya Genelgesi"},
        {"q": "'Milletin bağımsızlığını yine milletin azim ve kararı kurtaracaktır' maddesi nerede yer alır?", "opts": ["Amasya Genelgesi", "Erzurum Kongresi", "Sivas Kongresi", "Misak-ı Milli", "Teşkilat-ı Esasiye"], "a": "Amasya Genelgesi"},
        {"q": "Mustafa Kemal'in 'Artık İstanbul Anadolu'ya hakim değil, tabi olmak zorundadır' sözünü nerede söylemiştir?", "opts": ["Amasya Genelgesi sonrasında", "Samsun'a çıkınca", "TBMM açılınca", "Erzurum Kongresi'nde", "Sakarya Savaşı'nda"], "a": "Amasya Genelgesi sonrasında"},
        {"q": "Mustafa Kemal askerlik mesleğinden ne zaman istifa etmiştir?", "opts": ["Amasya Genelgesi'nden sonra, Erzurum Kongresi'nden önce", "Samsun'a çıkmadan önce", "Sivas Kongresi'nden sonra", "TBMM açılınca", "Sakarya Savaşı'ndan önce"], "a": "Amasya Genelgesi'nden sonra, Erzurum Kongresi'nden önce"},
        {"q": "Toplanış şekli bakımından bölgesel, aldığı kararlar bakımından ulusal olan kongre hangisidir?", "opts": ["Erzurum Kongresi", "Sivas Kongresi", "Amasya Görüşmeleri", "Balıkesir Kongresi", "Alaşehir Kongresi"], "a": "Erzurum Kongresi"},
        {"q": "'Milli sınırlar içinde vatan bir bütündür, bölünemez' kararı ilk kez nerede alınmıştır?", "opts": ["Erzurum Kongresi", "Sivas Kongresi", "Amasya Genelgesi", "Misak-ı Milli", "TBMM"], "a": "Erzurum Kongresi"},
        {"q": "Manda ve himaye fikri ilk kez nerede reddedilmiştir?", "opts": ["Erzurum Kongresi", "Sivas Kongresi", "Amasya Genelgesi", "Misak-ı Milli", "TBMM"], "a": "Erzurum Kongresi"},
        {"q": "Manda ve himaye fikri kesin olarak nerede reddedilmiştir?", "opts": ["Sivas Kongresi", "Erzurum Kongresi", "Amasya Genelgesi", "Misak-ı Milli", "Lozan"], "a": "Sivas Kongresi"},
        {"q": "Her yönüyle (toplanış ve kararlar) ulusal olan tek kongre hangisidir?", "opts": ["Sivas Kongresi", "Erzurum Kongresi", "Amasya Kongresi", "Balıkesir Kongresi", "Nazilli Kongresi"], "a": "Sivas Kongresi"},
        {"q": "Temsil Heyeti'nin (Heyet-i Temsiliye) yürütme yetkisini kullandığının (Hükümet gibi davrandığının) kanıtı nedir?", "opts": ["Ali Fuat Paşa'yı Batı Cephesi Komutanlığına ataması", "Gazete çıkarması", "Kongre toplaması", "İstanbul ile haberleşmeyi kesmesi", "Telgraf çekmesi"], "a": "Ali Fuat Paşa'yı Batı Cephesi Komutanlığına ataması"},
        {"q": "Tüm yararlı cemiyetler nerede 'Anadolu ve Rumeli Müdafaa-i Hukuk Cemiyeti' adı altında birleştirilmiştir?", "opts": ["Sivas Kongresi", "Erzurum Kongresi", "Amasya Görüşmeleri", "TBMM", "Son Osmanlı Mebusan Meclisi"], "a": "Sivas Kongresi"},
        {"q": "Milli Mücadele'nin yayın organı olan 'İrade-i Milliye' gazetesi nerede çıkarılmıştır?", "opts": ["Sivas", "Ankara", "Erzurum", "İstanbul", "İzmir"], "a": "Sivas"},
        {"q": "İstanbul Hükümeti'nin (Ali Rıza Paşa) Temsil Heyeti'ni resmen tanıdığı olay hangisidir?", "opts": ["Amasya Görüşmeleri (Protokolü)", "Bilecik Görüşmesi", "Sivas Kongresi", "Erzurum Kongresi", "Havza Genelgesi"], "a": "Amasya Görüşmeleri (Protokolü)"},
        {"q": "Son Osmanlı Mebusan Meclisi'nde kabul edilen ve Milli Mücadele'nin siyasi programı olan belge nedir?", "opts": ["Misak-ı Milli", "Takrir-i Sükun", "Teşkilat-ı Esasiye", "Sened-i İttifak", "Tanzimat Fermanı"], "a": "Misak-ı Milli"},
        {"q": "İstanbul'un İtilaf Devletleri tarafından resmen işgal edilmesinin (16 Mart 1920) temel nedeni nedir?", "opts": ["Misak-ı Milli'nin kabul edilmesi", "Mustafa Kemal'in Samsun'a çıkması", "TBMM'nin açılması", "Sivas Kongresi", "Damat Ferit'in istifası"], "a": "Misak-ı Milli'nin kabul edilmesi"},
        {"q": "TBMM'nin (Büyük Millet Meclisi) açılış tarihi nedir?", "opts": ["23 Nisan 1920", "19 Mayıs 1919", "29 Ekim 1923", "30 Ağustos 1922", "9 Eylül 1922"], "a": "23 Nisan 1920"},
        {"q": "I. TBMM'nin en önemli özelliği nedir?", "opts": ["Kurucu, İhtilalci ve Güçler Birliği ilkesine sahip olması", "Laik olması", "Partili olması", "Atanmış olması", "Saltanatı savunması"], "a": "Kurucu, İhtilalci ve Güçler Birliği ilkesine sahip olması"},
        {"q": "TBMM'ye karşı çıkan ayaklanmaları bastırmak için çıkarılan kanun nedir?", "opts": ["Hıyanet-i Vataniye Kanunu", "Takrir-i Sükun", "Teşkilat-ı Esasiye", "Tekalif-i Milliye", "Firariler Kanunu"], "a": "Hıyanet-i Vataniye Kanunu"},
        {"q": "İstiklal Mahkemeleri ilk kez hangi olay için kurulmuştur?", "opts": ["TBMM'ye karşı çıkan isyanları bastırmak için", "Menemen Olayı", "Şeyh Sait İsyanı", "İzmir Suikastı", "Çerkez Ethem İsyanı"], "a": "TBMM'ye karşı çıkan isyanları bastırmak için"},
        {"q": "Sevr Antlaşması'nı imzalayan heyete TBMM'nin tepkisi ne olmuştur?", "opts": ["Vatan haini ilan edip vatandaşlıktan çıkarmıştır", "Onaylamıştır", "Sürgüne göndermiştir", "Hapse atmıştır", "Ödüllendirmiştir"], "a": "Vatan haini ilan edip vatandaşlıktan çıkarmıştır"},
        {"q": "Doğu Cephesi'nde kimlere karşı savaşılmıştır?", "opts": ["Ermeniler", "Ruslar", "İngilizler", "Fransızlar", "Yunanlılar"], "a": "Ermeniler"},
        {"q": "Doğu Cephesi Komutanı ve 'Şark Fatihi' kimdir?", "opts": ["Kazım Karabekir", "Ali Fuat Cebesoy", "İsmet İnönü", "Fevzi Çakmak", "Refet Bele"], "a": "Kazım Karabekir"},
        {"q": "TBMM'nin uluslararası alanda imzaladığı ilk antlaşma ve ilk siyasi zafer hangisidir?", "opts": ["Gümrü Antlaşması", "Moskova Antlaşması", "Kars Antlaşması", "Ankara Antlaşması", "Lozan Antlaşması"], "a": "Gümrü Antlaşması"},
        {"q": "Güney Cephesi'nde kimlere karşı savaşılmıştır?", "opts": ["Fransızlar ve Ermeniler", "İngilizler", "İtalyanlar", "Yunanlılar", "Ruslar"], "a": "Fransızlar ve Ermeniler"},
        {"q": "Güney Cephesi'nde düzenli ordu var mıydı?", "opts": ["Hayır, Kuva-yi Milliye birlikleri savaştı", "Evet, vardı", "Kısmen vardı", "Yabancı askerler vardı", "Padişah ordusu vardı"], "a": "Hayır, Kuva-yi Milliye birlikleri savaştı"},
        {"q": "Maraş savunmasının simge ismi kimdir?", "opts": ["Sütçü İmam", "Şahin Bey", "Ali Saip Bey", "Yörük Ali Efe", "Demirci Mehmet Efe"], "a": "Sütçü İmam"},
        {"q": "Antep savunmasının simge ismi kimdir?", "opts": ["Şahin Bey", "Sütçü İmam", "Karayılan", "Gördesli Makbule", "Nezahat Onbaşı"], "a": "Şahin Bey"},
        {"q": "Batı Cephesi'nde düzenli ordunun Yunanlılara karşı kazandığı ilk zafer hangisidir?", "opts": ["I. İnönü Savaşı", "II. İnönü Savaşı", "Sakarya Savaşı", "Büyük Taarruz", "Kütahya-Eskişehir"], "a": "I. İnönü Savaşı"},
        {"q": "I. İnönü Savaşı'nın uluslararası sonuçları nelerdir (Milat)?", "opts": ["Moskova Antlaşması, İstiklal Marşı, Londra Konferansı, Afganistan Dostluk, Teşkilat-ı Esasiye", "Lozan Antlaşması", "Mudanya Ateşkesi", "Sevr Antlaşması", "Gümrü Antlaşması"], "a": "Moskova Antlaşması, İstiklal Marşı, Londra Konferansı, Afganistan Dostluk, Teşkilat-ı Esasiye"},
        {"q": "TBMM'yi tanıyan ilk Avrupa devleti hangisidir?", "opts": ["Sovyet Rusya (Moskova Antlaşması)", "Fransa", "İtalya", "İngiltere", "Almanya"], "a": "Sovyet Rusya (Moskova Antlaşması)"},
        {"q": "Misak-ı Milli'den verilen ilk taviz (Batum) hangi antlaşma ile olmuştur?", "opts": ["Moskova Antlaşması", "Gümrü Antlaşması", "Kars Antlaşması", "Ankara Antlaşması", "Lozan Antlaşması"], "a": "Moskova Antlaşması"},
        {"q": "İtilaf Devletleri'nin TBMM'yi resmen tanıdığı olay hangisidir?", "opts": ["Londra Konferansı", "Paris Konferansı", "San Remo Konferansı", "Sevr Konferansı", "Lozan Konferansı"], "a": "Londra Konferansı"},
        {"q": "Düzenli ordunun aldığı tek yenilgi hangisidir?", "opts": ["Kütahya-Eskişehir Savaşları", "I. İnönü", "II. İnönü", "Sakarya", "Büyük Taarruz"], "a": "Kütahya-Eskişehir Savaşları"},
        {"q": "Mustafa Kemal'e 'Başkomutanlık' yetkisi hangi olaydan sonra verilmiştir?", "opts": ["Kütahya-Eskişehir Savaşları'ndan sonra", "Sakarya'dan sonra", "Büyük Taarruz'dan sonra", "I. İnönü'den sonra", "Samsun'a çıkınca"], "a": "Kütahya-Eskişehir Savaşları'ndan sonra"},
        {"q": "Ordunun ihtiyaçlarını karşılamak için Mustafa Kemal'in çıkardığı emirler nedir?", "opts": ["Tekalif-i Milliye Emirleri", "Tehcir Kanunu", "Takrir-i Sükun", "Hıyanet-i Vataniye", "Tanzimat"], "a": "Tekalif-i Milliye Emirleri"},
        {"q": "Türk ordusunun son savunma savaşı ve Milli Mücadele'nin dönüm noktası hangisidir?", "opts": ["Sakarya Meydan Muharebesi", "I. İnönü", "II. İnönü", "Büyük Taarruz", "Dumlupınar"], "a": "Sakarya Meydan Muharebesi"},
        {"q": "Mustafa Kemal'e 'Mareşal' rütbesi ve 'Gazi' unvanı hangi savaştan sonra verilmiştir?", "opts": ["Sakarya Meydan Muharebesi", "Büyük Taarruz", "Çanakkale Savaşı", "I. İnönü", "Trablusgarp"], "a": "Sakarya Meydan Muharebesi"},
        {"q": "Fransa'nın TBMM'yi tanıdığı ve Güney Cephesi'nin kapandığı antlaşma hangisidir?", "opts": ["1921 Ankara Antlaşması", "Gümrü Antlaşması", "Kars Antlaşması", "Moskova Antlaşması", "Lozan Antlaşması"], "a": "1921 Ankara Antlaşması"},
        {"q": "Doğu sınırımızın kesinlik kazandığı antlaşma hangisidir?", "opts": ["Kars Antlaşması", "Moskova Antlaşması", "Gümrü Antlaşması", "Ankara Antlaşması", "Lozan Antlaşması"], "a": "Kars Antlaşması"},
        {"q": "'Ordular! İlk hedefiniz Akdeniz'dir, ileri!' emri hangi savaşta verilmiştir?", "opts": ["Büyük Taarruz (Başkomutanlık Meydan Muharebesi)", "Sakarya Savaşı", "I. İnönü", "Çanakkale", "Kütahya-Eskişehir"], "a": "Büyük Taarruz (Başkomutanlık Meydan Muharebesi)"},
        {"q": "Kurtuluş Savaşı'nın askeri safhasını bitiren ateşkes antlaşması hangisidir?", "opts": ["Mudanya Ateşkes Antlaşması", "Mondros Ateşkesi", "Sevr Antlaşması", "Lozan Antlaşması", "Gümrü Antlaşması"], "a": "Mudanya Ateşkes Antlaşması"},
        {"q": "Mudanya Ateşkesi ile savaş yapılmadan kurtarılan yerler nerelerdir?", "opts": ["Doğu Trakya, İstanbul ve Boğazlar", "İzmir ve Aydın", "Antalya ve Konya", "Adana ve Mersin", "Kars ve Ardahan"], "a": "Doğu Trakya, İstanbul ve Boğazlar"},
        {"q": "Osmanlı Devleti'nin hukuken sona ermesi hangi olayla olmuştur?", "opts": ["Mudanya Ateşkes Antlaşması (İstanbul'un TBMM'ye bırakılmasıyla)", "Saltanatın kaldırılması", "Cumhuriyetin ilanı", "Lozan Antlaşması", "Mondros Ateşkesi"], "a": "Mudanya Ateşkes Antlaşması (İstanbul'un TBMM'ye bırakılmasıyla)"},
        {"q": "Lozan Barış Konferansı'na gönderilen heyetin başkanı kimdir?", "opts": ["İsmet İnönü", "Rauf Orbay", "Kazım Karabekir", "Ali Fuat Cebesoy", "Refet Bele"], "a": "İsmet İnönü"},
        {"q": "Lozan'da taviz verilmemesi istenen iki konu nedir?", "opts": ["Ermeni Yurdu ve Kapitülasyonlar", "Boğazlar ve Borçlar", "Musul ve Hatay", "Sınırlar ve Tazminat", "Adalar ve Patrikhan"], "a": "Ermeni Yurdu ve Kapitülasyonlar"},
        {"q": "Türkiye'nin bağımsızlığının ve sınırlarının (Misak-ı Milli'ye büyük ölçüde uygun) tanındığı antlaşma hangisidir?", "opts": ["Lozan Barış Antlaşması", "Sevr Antlaşması", "Mudanya Ateşkesi", "Paris Antlaşması", "Gümrü Antlaşması"], "a": "Lozan Barış Antlaşması"},
        {"q": "Lozan'da çözülemeyen tek konu hangisidir?", "opts": ["Musul Sorunu (Irak Sınırı)", "Boğazlar", "Kapitülasyonlar", "Savaş Tazminatı", "Nüfus Mübadelesi"], "a": "Musul Sorunu (Irak Sınırı)"}
    ],

    "22. Atatürkçülük ve Türk İnkılabı": [
        {"q": "Atatürk ilkeleri ve inkılaplarının temel amacı nedir?", "opts": ["Türkiye'yi çağdaş uygarlık düzeyine çıkarmak", "Sınırları genişletmek", "Geçmişi canlandırmak", "Dini devlet kurmak", "Avrupa'yı taklit etmek"], "a": "Türkiye'yi çağdaş uygarlık düzeyine çıkarmak"},
        {"q": "Saltanatın kaldırılması (1 Kasım 1922) hangi ilke ile doğrudan ilgilidir?", "opts": ["Cumhuriyetçilik ve Laiklik", "Devletçilik", "Halkçılık", "İnkılapçılık", "Milliyetçilik"], "a": "Cumhuriyetçilik ve Laiklik"},
        {"q": "Osmanlı Devleti'nin resmen sona ermesi hangi olayla gerçekleşmiştir?", "opts": ["Saltanatın kaldırılması", "Cumhuriyetin ilanı", "Lozan Antlaşması", "Mudanya Ateşkesi", "Halifeliğin kaldırılması"], "a": "Saltanatın kaldırılması"},
        {"q": "Cumhuriyetin ilanı (29 Ekim 1923) ile çözülen sorunlar nelerdir?", "opts": ["Devletin adı, rejimi ve başkanlığı sorunu", "Sınır sorunu", "Kapitülasyon sorunu", "Borçlar sorunu", "Eğitim sorunu"], "a": "Devletin adı, rejimi ve başkanlığı sorunu"},
        {"q": "Türkiye Cumhuriyeti'nin ilk Cumhurbaşkanı ve ilk Başbakanı kimlerdir?", "opts": ["Mustafa Kemal Atatürk - İsmet İnönü", "Mustafa Kemal - Fevzi Çakmak", "İsmet İnönü - Celal Bayar", "Kazım Karabekir - Rauf Orbay", "Ali Fethi Okyar - Adnan Menderes"], "a": "Mustafa Kemal Atatürk - İsmet İnönü"},
        {"q": "Halifeliğin kaldırılması (3 Mart 1924) en çok hangi ilkenin güçlenmesini sağlamıştır?", "opts": ["Laiklik", "Devletçilik", "Halkçılık", "İnkılapçılık", "Milliyetçilik"], "a": "Laiklik"},
        {"q": "Eğitim ve öğretimin birleştirildiği kanun hangisidir?", "opts": ["Tevhid-i Tedrisat Kanunu", "Maarif Teşkilatı Kanunu", "Harf İnkılabı", "Tekke ve Zaviyelerin Kapatılması", "Medeni Kanun"], "a": "Tevhid-i Tedrisat Kanunu"},
        {"q": "Hukuk alanında yapılan en köklü inkılap hangisidir?", "opts": ["Türk Medeni Kanunu'nun kabulü", "Anayasanın ilanı", "Şeriatın kaldırılması", "Mecelle'nin yazılması", "Baroların kurulması"], "a": "Türk Medeni Kanunu'nun kabulü"},
        {"q": "Türk Medeni Kanunu hangi ülkeden örnek alınarak hazırlanmıştır?", "opts": ["İsviçre", "Almanya", "İtalya", "Fransa", "İngiltere"], "a": "İsviçre"},
        {"q": "Türk Medeni Kanunu ile kadınlara verilen haklardan biri değildir?", "opts": ["Seçme ve seçilme hakkı (Siyasi hak)", "Mirasta eşitlik", "Resmi nikah", "Boşanma hakkı", "Şahitlikte eşitlik"], "a": "Seçme ve seçilme hakkı (Siyasi hak)"},
        {"q": "Türk kadınlarına siyasi haklar (BMV - Belediye, Muhtar, Vekil) hangi yıllarda verilmiştir?", "opts": ["1930, 1933, 1934", "1923, 1924, 1925", "1926, 1928, 1930", "1940, 1945, 1950", "1908, 1912, 1914"], "a": "1930, 1933, 1934"},
        {"q": "Yeni Türk Harflerinin (Latin alfabesi) kabul edilmesinin temel amacı nedir?", "opts": ["Okuma yazmayı kolaylaştırmak ve çağdaşlaşmak", "Avrupa'ya yaranmak", "Geçmişi unutturmak", "Dini değiştirmek", "Nüfusu azaltmak"], "a": "Okuma yazmayı kolaylaştırmak ve çağdaşlaşmak"},
        {"q": "Yeni harfleri halka öğretmek için açılan kurumlar hangisidir?", "opts": ["Millet Mektepleri", "Halkevleri", "Köy Enstitüleri", "Medreseler", "Darülfünun"], "a": "Millet Mektepleri"},
        {"q": "Atatürk'e 'Başöğretmen' unvanı ne zaman verilmiştir?", "opts": ["Harf İnkılabı ve Millet Mektepleri'nin açılmasıyla", "Cumhuriyetin ilanıyla", "Kurtuluş Savaşı'ndan sonra", "Sakarya Savaşı'ndan sonra", "Nutuk'u okuyunca"], "a": "Harf İnkılabı ve Millet Mektepleri'nin açılmasıyla"},
        {"q": "Türk tarihini bilimsel olarak araştırmak ve milli bilinci geliştirmek için kurulan kurum nedir?", "opts": ["Türk Tarih Kurumu (TTK)", "Türk Dil Kurumu", "Halkevleri", "Anadolu Ajansı", "Maden Tetkik Arama"], "a": "Türk Tarih Kurumu (TTK)"},
        {"q": "Türkçeyi yabancı kelimelerin boyunduruğundan kurtarmak ve zenginleştirmek için kurulan kurum nedir?", "opts": ["Türk Dil Kurumu (TDK)", "Türk Tarih Kurumu", "Maarif Vekaleti", "Darülfünun", "Milli Kütüphane"], "a": "Türk Dil Kurumu (TDK)"},
        {"q": "Kılık kıyafet kanunu ve şapka inkılabı hangi ilke ile ilgilidir?", "opts": ["İnkılapçılık", "Devletçilik", "Cumhuriyetçilik", "Milliyetçilik", "Halkçılık"], "a": "İnkılapçılık"},
        {"q": "Tekke, zaviye ve türbelerin kapatılması hangi ilkeyi güçlendirmiştir?", "opts": ["Laiklik", "Devletçilik", "Cumhuriyetçilik", "Milliyetçilik", "Halkçılık"], "a": "Laiklik"},
        {"q": "Soyadı Kanunu'nun çıkarılma amacı nedir?", "opts": ["Resmi işlerdeki karışıklığı önlemek ve toplumsal eşitliği sağlamak", "Aileleri ayırmak", "Nüfus sayımı yapmak", "Vergi toplamak", "Askerlik çağırmak"], "a": "Resmi işlerdeki karışıklığı önlemek ve toplumsal eşitliği sağlamak"},
        {"q": "Mustafa Kemal'e 'Atatürk' soyadını kim vermiştir?", "opts": ["TBMM", "Halk", "Kendisi", "İsmet İnönü", "Fevzi Çakmak"], "a": "TBMM"},
        {"q": "Ekonomi alanında bağımsızlığı sağlamak için kapitülasyonların kaldırılmasından sonra atılan önemli adım nedir?", "opts": ["İzmir İktisat Kongresi ve Misak-ı İktisadi", "Tekalif-i Milliye", "Aşar vergisinin kaldırılması", "Varlık vergisi", "Duyun-u Umumiye"], "a": "İzmir İktisat Kongresi ve Misak-ı İktisadi"},
        {"q": "Türk denizlerinde gemi işletme hakkının (Kabotaj hakkı) Türklere verilmesi hangi kanunla olmuştur?", "opts": ["Kabotaj Kanunu", "Teşvik-i Sanayi Kanunu", "Medeni Kanun", "Soyadı Kanunu", "Ticaret Kanunu"], "a": "Kabotaj Kanunu"},
        {"q": "Kabotaj Kanunu hangi ilke ile doğrudan ilgilidir?", "opts": ["Milliyetçilik", "Laiklik", "İnkılapçılık", "Cumhuriyetçilik", "Halkçılık"], "a": "Milliyetçilik"},
        {"q": "Özel sektörün yetersiz kaldığı alanlarda devletin ekonomiye müdahale etmesini öngören ilke hangisidir?", "opts": ["Devletçilik", "Halkçılık", "Milliyetçilik", "Cumhuriyetçilik", "Laiklik"], "a": "Devletçilik"},
        {"q": "Halkın yönetime katılması, seçme ve seçilme hakkı hangi ilkenin gereğidir?", "opts": ["Cumhuriyetçilik", "Devletçilik", "Laiklik", "İnkılapçılık", "Milliyetçilik"], "a": "Cumhuriyetçilik"},
        {"q": "Din ve devlet işlerinin ayrılması, akıl ve bilimin rehber alınması hangi ilkedir?", "opts": ["Laiklik", "Cumhuriyetçilik", "Halkçılık", "Devletçilik", "İnkılapçılık"], "a": "Laiklik"},
        {"q": "Hiçbir sınıf veya zümreye ayrıcalık tanınmaması, kanun önünde eşitlik hangi ilkedir?", "opts": ["Halkçılık", "Laiklik", "Devletçilik", "Milliyetçilik", "İnkılapçılık"], "a": "Halkçılık"},
        {"q": "Türk milletini sevmek, yüceltmek ve bağımsızlığını korumak hangi ilkedir?", "opts": ["Milliyetçilik", "Halkçılık", "Devletçilik", "Cumhuriyetçilik", "Laiklik"], "a": "Milliyetçilik"},
        {"q": "Sürekli yenileşmeyi, çağdaşlaşmayı ve dinamizmi savunan ilke hangisidir?", "opts": ["İnkılapçılık", "Cumhuriyetçilik", "Milliyetçilik", "Halkçılık", "Devletçilik"], "a": "İnkılapçılık"},
        {"q": "Köylünün üzerindeki ağır vergi yükünü kaldırmak için ne yapılmıştır?", "opts": ["Aşar (Öşür) Vergisi kaldırılmıştır", "Toprak dağıtılmıştır", "Kredi verilmiştir", "Traktör alınmıştır", "Kooperatif kurulmuştur"], "a": "Aşar (Öşür) Vergisi kaldırılmıştır"},
        {"q": "Sanayiyi geliştirmek için 1927'de çıkarılan ancak sermaye yetersizliğinden tam uygulanamayan kanun nedir?", "opts": ["Teşvik-i Sanayi Kanunu", "Kabotaj Kanunu", "İş Kanunu", "Maden Kanunu", "Gümrük Kanunu"], "a": "Teşvik-i Sanayi Kanunu"},
        {"q": "Türkiye'nin ilk kalkınma planı olan 'I. Beş Yıllık Sanayi Planı' hangi yıllarda uygulanmıştır?", "opts": ["1933-1938", "1923-1928", "1940-1945", "1950-1955", "1960-1965"], "a": "1933-1938"},
        {"q": "Maden kaynaklarını işletmek ve finanse etmek için kurulan banka hangisidir?", "opts": ["Etibank", "Sümerbank", "İş Bankası", "Ziraat Bankası", "Halk Bankası"], "a": "Etibank"},
        {"q": "Tekstil ve sanayi yatırımlarını finanse etmek için kurulan banka hangisidir?", "opts": ["Sümerbank", "Etibank", "İş Bankası", "Denizbank", "Yapı Kredi"], "a": "Sümerbank"},
        {"q": "Cumhuriyet döneminin ilk özel bankası hangisidir?", "opts": ["Türkiye İş Bankası", "Sanayi ve Maadin Bankası", "Ziraat Bankası", "Osmanlı Bankası", "Merkez Bankası"], "a": "Türkiye İş Bankası"},
        {"q": "Çok partili hayata geçiş denemelerinin ilki olan parti hangisidir?", "opts": ["Terakkiperver Cumhuriyet Fırkası", "Serbest Cumhuriyet Fırkası", "Demokrat Parti", "Milli Kalkınma Partisi", "Ahali Fırkası"], "a": "Terakkiperver Cumhuriyet Fırkası"},
        {"q": "Terakkiperver Cumhuriyet Fırkası hangi olay gerekçe gösterilerek kapatılmıştır?", "opts": ["Şeyh Sait İsyanı", "Menemen Olayı", "İzmir Suikastı", "Çerkez Ethem İsyanı", "31 Mart Vakası"], "a": "Şeyh Sait İsyanı"},
        {"q": "Türkiye Cumhuriyeti'ne yönelik ilk irticai ayaklanma hangisidir?", "opts": ["Şeyh Sait İsyanı", "Menemen Olayı", "Anzavur İsyanı", "Koçgiri İsyanı", "Dersim İsyanı"], "a": "Şeyh Sait İsyanı"},
        {"q": "Şeyh Sait İsyanı'nın en önemli dış sonucu nedir?", "opts": ["Musul'un kaybedilmesi (Irak sınırının aleyhimize çizilmesi)", "Hatay'ın alınması", "Boğazlar sorunu", "NATO'ya giriş", "Kıbrıs sorunu"], "a": "Musul'un kaybedilmesi (Irak sınırının aleyhimize çizilmesi)"},
        {"q": "Mustafa Kemal'e yönelik düzenlenen İzmir Suikastı girişimi neyi hedeflemiştir?", "opts": ["Cumhuriyet rejimini ve inkılapları", "Sadece Mustafa Kemal'i", "İzmir'i", "Meclisi", "Orduyu"], "a": "Cumhuriyet rejimini ve inkılapları"},
        {"q": "1930'da Fethi Okyar tarafından kurulan ikinci muhalefet partisi hangisidir?", "opts": ["Serbest Cumhuriyet Fırkası", "Terakkiperver Cumhuriyet Fırkası", "Demokrat Parti", "Millet Partisi", "Hürriyet Partisi"], "a": "Serbest Cumhuriyet Fırkası"},
        {"q": "Serbest Cumhuriyet Fırkası'nın kapanmasından sonra çıkan rejim karşıtı olay nedir?", "opts": ["Menemen Olayı (Kubilay Olayı)", "Şeyh Sait İsyanı", "Dersim Olayı", "Varto İsyanı", "31 Mart"], "a": "Menemen Olayı (Kubilay Olayı)"},
        {"q": "Türk kadınına milletvekili seçme ve seçilme hakkı ne zaman verilmiştir?", "opts": ["1934", "1930", "1933", "1923", "1926"], "a": "1934"},
        {"q": "Atatürk ilkeleri anayasaya ne zaman girmiştir?", "opts": ["1937", "1924", "1928", "1961", "1982"], "a": "1937"},
        {"q": "Halkevleri'nin yayın organı olan dergi hangisidir?", "opts": ["Ülkü", "Kadro", "Varlık", "Türk Yurdu", "Dergâh"], "a": "Ülkü"},
        {"q": "Darülfünun reformu sonucunda kurulan üniversite hangisidir?", "opts": ["İstanbul Üniversitesi", "Ankara Üniversitesi", "İTÜ", "ODTÜ", "Boğaziçi"], "a": "İstanbul Üniversitesi"},
        {"q": "Musiki Muallim Mektebi'nin yerine kurulan sanat kurumu hangisidir?", "opts": ["Ankara Devlet Konservatuvarı", "Sanayi-i Nefise", "Gazi Eğitim", "Köy Enstitüsü", "Halkevi"], "a": "Ankara Devlet Konservatuvarı"},
        {"q": "Atatürk Dönemi'nin son Başbakanı kimdir?", "opts": ["Celal Bayar", "İsmet İnönü", "Fethi Okyar", "Refik Saydam", "Şükrü Saraçoğlu"], "a": "Celal Bayar"},
        {"q": "Nutuk adlı eser hangi yılları kapsar?", "opts": ["1919-1927", "1914-1923", "1920-1938", "1923-1938", "1881-1938"], "a": "1919-1927"},
        {"q": "Atatürk'ün 'Benim naçiz vücudum elbet bir gün toprak olacaktır...' sözünü hangi olay üzerine söylemiştir?", "opts": ["İzmir Suikastı", "Cumhuriyetin ilanı", "Menemen Olayı", "Hastalığı sırasında", "Bursa Nutku"], "a": "İzmir Suikastı"}
    ],

    "23. İki Savaş Arasındaki Dönemde Türkiye ve Dünya": [
        {"q": "1929 Dünya Ekonomik Buhranı (Kara Perşembe) hangi ülkede başlamıştır?", "opts": ["ABD", "Almanya", "İngiltere", "Fransa", "İtalya"], "a": "ABD"},
        {"q": "1929 Krizinin Türkiye'ye etkisi ne olmuştur?", "opts": ["Devletçilik ilkesinin uygulanması ve yerli malının teşvik edilmesi", "İhracatın artması", "Zenginleşme", "Dış borç alınması", "Sanayinin durması"], "a": "Devletçilik ilkesinin uygulanması ve yerli malının teşvik edilmesi"},
        {"q": "İki savaş arası dönemde İtalya'da ortaya çıkan totaliter rejim ve lideri kimdir?", "opts": ["Faşizm - Mussolini", "Nazizm - Hitler", "Komünizm - Stalin", "Sosyalizm - Lenin", "Liberalizm - Roosevelt"], "a": "Faşizm - Mussolini"},
        {"q": "Almanya'da Hitler'in iktidara gelmesiyle uyguladığı yayılmacı politika nedir?", "opts": ["Hayat Sahası (Lebensraum)", "Bizim Deniz (Mare Nostrum)", "Sömürgecilik", "Panslavizm", "Demokrasi"], "a": "Hayat Sahası (Lebensraum)"},
        {"q": "İtalya'nın Akdeniz'e yayılma politikasına ne ad verilir?", "opts": ["Bizim Deniz (Mare Nostrum)", "Hayat Sahası", "Roma İmparatorluğu", "Büyük İtalya", "Faşizm"], "a": "Bizim Deniz (Mare Nostrum)"},
        {"q": "Japonya'nın Uzak Doğu'da batılıları istememesi politikasına ne ad verilir?", "opts": ["Asya Asyalılarındır (Ortak Refah Alanı)", "Hayat Sahası", "Bizim Deniz", "Mandarincilik", "Samurai"], "a": "Asya Asyalılarındır (Ortak Refah Alanı)"},
        {"q": "Sovyet Rusya'nın Türkistan'daki milli mücadeleleri bastırma politikasına karşı çıkan Türk direnişi nedir?", "opts": ["Basmacı Hareketi", "Kuvayi Milliye", "Mücahitler", "Türkçülük", "Cedidizm"], "a": "Basmacı Hareketi"},
        {"q": "Basmacı Hareketi'ne katılan ünlü Osmanlı komutanı kimdir?", "opts": ["Enver Paşa", "Talat Paşa", "Cemal Paşa", "Kazım Karabekir", "Rauf Orbay"], "a": "Enver Paşa"},
        {"q": "Türkiye'nin 1932 yılında üye olduğu uluslararası kuruluş hangisidir?", "opts": ["Milletler Cemiyeti", "Birleşmiş Milletler", "NATO", "Balkan Antantı", "Sadabat Paktı"], "a": "Milletler Cemiyeti"},
        {"q": "Türkiye'nin batı sınırını güvence altına almak için 1934'te imzaladığı antlaşma nedir?", "opts": ["Balkan Antantı", "Sadabat Paktı", "Montrö", "Locarno", "Kellogg Paktı"], "a": "Balkan Antantı"},
        {"q": "Balkan Antantı'na üye devletler hangileridir? (TAYYAR)", "opts": ["Türkiye, Yunanistan, Yugoslavya, Romanya", "Türkiye, Bulgaristan, Arnavutluk", "Yunanistan, İtalya, Türkiye", "Romanya, Rusya, Türkiye", "Sırbistan, Bosna, Türkiye"], "a": "Türkiye, Yunanistan, Yugoslavya, Romanya"},
        {"q": "Türkiye'nin doğu sınırını güvence altına almak için 1937'de imzaladığı antlaşma nedir?", "opts": ["Sadabat Paktı", "Balkan Antantı", "Bağdat Paktı", "CENTO", "Kasr-ı Şirin"], "a": "Sadabat Paktı"},
        {"q": "Sadabat Paktı'na üye devletler hangileridir? (İran-Atı)", "opts": ["İran, Irak, Afganistan, Türkiye", "Suriye, Mısır, Türkiye", "İran, Rusya, Türkiye", "Irak, Ürdün, Türkiye", "Pakistan, Hindistan, Türkiye"], "a": "İran, Irak, Afganistan, Türkiye"},
        {"q": "Boğazların Türk hakimiyetine girdiği ve askerlendirilebildiği antlaşma (1936) hangisidir?", "opts": ["Montrö Boğazlar Sözleşmesi", "Lozan Antlaşması", "Sevr Antlaşması", "Londra Sözleşmesi", "Paris Sözleşmesi"], "a": "Montrö Boğazlar Sözleşmesi"},
        {"q": "Hatay Sorunu ilk olarak hangi antlaşma ile gündeme gelmiştir?", "opts": ["1921 Ankara Antlaşması (Fransa ile)", "Lozan Antlaşması", "Kars Antlaşması", "Gümrü Antlaşması", "Moskova Antlaşması"], "a": "1921 Ankara Antlaşması (Fransa ile)"},
        {"q": "Milletler Cemiyeti'nin Hatay için hazırladığı rapor hangisidir?", "opts": ["Sandler Raporu", "Amiral Bristol Raporu", "General Harbord Raporu", "Milne Raporu", "Hrisantos Raporu"], "a": "Sandler Raporu"},
        {"q": "Hatay Cumhuriyeti'nin ilk ve tek Cumhurbaşkanı kimdir?", "opts": ["Tayfur Sökmen", "Abdurrahman Melek", "Şükrü Saraçoğlu", "Rauf Orbay", "İsmet İnönü"], "a": "Tayfur Sökmen"},
        {"q": "Hatay Türkiye'ye ne zaman katılmıştır?", "opts": ["1939", "1938", "1936", "1923", "1940"], "a": "1939"},
        {"q": "Atatürk'ün 'Kırk asırlık Türk yurdu düşman eline bırakılamaz' dediği yer neresidir?", "opts": ["Hatay", "Musul", "Selanik", "Kıbrıs", "Batum"], "a": "Hatay"},
        {"q": "İspanya İç Savaşı'nda (1936-1939) iktidarı ele geçiren faşist lider kimdir?", "opts": ["Franco", "Mussolini", "Hitler", "Salazar", "Lenin"], "a": "Franco"},
        {"q": "Dünya barışını korumak için 1928'de imzalanan ve 'Savaş ulusal politika aracı olamaz' diyen pakt nedir?", "opts": ["Briand-Kellogg Paktı", "Locarno Antlaşması", "Litvinov Protokolü", "Balkan Antantı", "Sadabat Paktı"], "a": "Briand-Kellogg Paktı"},
        {"q": "Almanya'nın uluslararası sisteme geri döndüğü antlaşma (1925) nedir?", "opts": ["Locarno Antlaşması", "Versay Antlaşması", "Rapallo Antlaşması", "Nöyyi Antlaşması", "Trianon Antlaşması"], "a": "Locarno Antlaşması"},
        {"q": "SSCB'de Stalin'in uyguladığı ekonomik kalkınma planlarına ne ad verilir?", "opts": ["Beş Yıllık Kalkınma Planları (Kollektivizasyon)", "NEP", "Perestroyka", "Glasnost", "Liberalizm"], "a": "Beş Yıllık Kalkınma Planları (Kollektivizasyon)"},
        {"q": "Rusya'da Çarlık rejimini yıkan ihtilal hangisidir?", "opts": ["Bolşevik İhtilali (Ekim Devrimi 1917)", "Fransız İhtilali", "Sanayi Devrimi", "1905 Devrimi", "Şubat Devrimi"], "a": "Bolşevik İhtilali (Ekim Devrimi 1917)"},
        {"q": "Milletler Cemiyeti'ne Türkiye'yi davet eden ülke hangisidir?", "opts": ["İspanya (ve Yunanistan)", "İngiltere", "Fransa", "Almanya", "Rusya"], "a": "İspanya (ve Yunanistan)"},
        {"q": "Musul Sorunu'nun Türkiye aleyhine çözülmesine neden olan antlaşma (1926) hangisidir?", "opts": ["Ankara Antlaşması (İngiltere ile)", "Lozan Antlaşması", "Kars Antlaşması", "Moskova Antlaşması", "Gümrü Antlaşması"], "a": "Ankara Antlaşması (İngiltere ile)"},
        {"q": "Türkiye ile Yunanistan arasındaki Nüfus Mübadelesi sorunu ne zaman çözülmüştür?", "opts": ["1930 (Ahali Antlaşması)", "1923", "1924", "1934", "1950"], "a": "1930 (Ahali Antlaşması)"},
        {"q": "Atatürk döneminde 'Yurtta Sulh, Cihanda Sulh' ilkesi gereği Türkiye'nin izlediği politika nedir?", "opts": ["Barışçı ve Denge Politikası", "Yayılmacı", "Saldırgan", "İçe kapalı", "Sömürgeci"], "a": "Barışçı ve Denge Politikası"},
        {"q": "Picasso'nun İspanya İç Savaşı'nı anlattığı ünlü tablosu hangisidir?", "opts": ["Guernica", "Çığlık", "Yıldızlı Gece", "Son Akşam Yemeği", "Mona Lisa"], "a": "Guernica"},
        {"q": "Steinbeck'in 1929 krizini anlattığı ünlü romanı hangisidir?", "opts": ["Gazap Üzümleri", "Sefiller", "Suç ve Ceza", "Savaş ve Barış", "Çanlar Kimin İçin Çalıyor"], "a": "Gazap Üzümleri"},
        {"q": "Türkiye'de kadro hareketini başlatan dergi hangisidir?", "opts": ["Kadro Dergisi", "Ülkü", "Varlık", "Akbaba", "Markopaşa"], "a": "Kadro Dergisi"},
        {"q": "Atatürk döneminde açılan ilk baraj hangisidir?", "opts": ["Çubuk Barajı", "Atatürk Barajı", "Keban Barajı", "Hirfanlı Barajı", "Sarıyar Barajı"], "a": "Çubuk Barajı"},
        {"q": "Türkiye'de ilk demiryolu fabrikası nerede kurulmuştur?", "opts": ["Eskişehir", "Ankara", "Sivas", "İzmir", "İstanbul"], "a": "Eskişehir"},
        {"q": "Nuri Demirağ'ın kurduğu fabrika ne üretmiştir?", "opts": ["Uçak", "Araba", "Silah", "Kağıt", "Cam"], "a": "Uçak"},
        {"q": "Vecihi Hürkuş kimdir?", "opts": ["İlk Türk sivil havacısı ve uçak tasarımcısı", "İlk doktor", "İlk mühendis", "İlk başbakan", "İlk öğretmen"], "a": "İlk Türk sivil havacısı ve uçak tasarımcısı"},
        {"q": "Albert Einstein'ın Türkiye'ye gelmesi için mektup yazdığı olay nedir?", "opts": ["Nazi Almanyası'ndan kaçan bilim insanlarının Türkiye'ye kabulü", "Atom bombası yapımı", "Üniversite reformu", "Barış ödülü", "Nobel ödülü"], "a": "Nazi Almanyası'ndan kaçan bilim insanlarının Türkiye'ye kabulü"},
        {"q": "Türkiye'de üniversite reformunu hazırlayan İsviçreli profesör kimdir?", "opts": ["Albert Malche", "John Dewey", "Einstein", "Von Papen", "Heisenberg"], "a": "Albert Malche"},
        {"q": "Atatürk'ün vasiyetiyle mal varlığını bıraktığı kurumlar hangileridir?", "opts": ["TTK ve TDK (İş Bankası hisseleri)", "Kızılay", "Yeşilay", "THK", "Çocuk Esirgeme"], "a": "TTK ve TDK (İş Bankası hisseleri)"},
        {"q": "Atatürk'ün naaşı Anıtkabir yapılana kadar nerede kalmıştır?", "opts": ["Etnografya Müzesi", "TBMM", "Dolmabahçe Sarayı", "Çankaya Köşkü", "İstanbul Üniversitesi"], "a": "Etnografya Müzesi"},
        {"q": "Atatürk'ün hastalığına (Siroz) ilk teşhisi koyan doktor kimdir?", "opts": ["Dr. Nihat Reşat Belger", "Dr. Mim Kemal Öke", "Dr. Adnan Adıvar", "Dr. Refik Saydam", "Dr. Tevfik Rüştü Aras"], "a": "Dr. Nihat Reşat Belger"},
        {"q": "Türkiye'nin Montrö'deki başarısında etkili olan Dışişleri Bakanı kimdir?", "opts": ["Tevfik Rüştü Aras", "İsmet İnönü", "Fatin Rüştü Zorlu", "Hasan Saka", "Necmettin Sadak"], "a": "Tevfik Rüştü Aras"},
        {"q": "İki savaş arası dönemde dünyada radyonun kullanımı nasıldı?", "opts": ["Propaganda ve kitle iletişim aracı olarak yaygınlaştı", "Sadece askeri amaçlıydı", "Yasaklandı", "Bilinmiyordu", "Önemsizdi"], "a": "Propaganda ve kitle iletişim aracı olarak yaygınlaştı"},
        {"q": "Sürrealizm (Gerçeküstücülük) akımının en ünlü temsilcisi kimdir?", "opts": ["Salvador Dali", "Picasso", "Van Gogh", "Monet", "Rembrandt"], "a": "Salvador Dali"},
        {"q": "1936 Berlin Olimpiyatları'nda 4 altın madalya alarak Hitler'i kızdıran siyahi atlet kimdir?", "opts": ["Jesse Owens", "Usain Bolt", "Carl Lewis", "Muhammed Ali", "Michael Jordan"], "a": "Jesse Owens"},
        {"q": "Charlie Chaplin'in sanayi toplumunu eleştirdiği filmi hangisidir?", "opts": ["Modern Zamanlar", "Büyük Diktatör", "Altına Hücum", "Sirk", "Şehir Işıkları"], "a": "Modern Zamanlar"},
        {"q": "Türkiye'de ilk kadın doğum uzmanı kimdir?", "opts": ["Pakize İzzet Tarzi", "Safiye Ali", "Türkan Saylan", "Sabiha Gökçen", "Afet İnan"], "a": "Pakize İzzet Tarzi"},
        {"q": "Türkiye'nin ilk kadın pilotu kimdir?", "opts": ["Bedriye Tahir Gökmen", "Sabiha Gökçen", "Leman Bozkurt", "Yıldız Uçman", "Edibe Subaşı"], "a": "Bedriye Tahir Gökmen"},
        {"q": "Türkiye'nin (ve dünyanın) ilk kadın savaş pilotu kimdir?", "opts": ["Sabiha Gökçen", "Bedriye Tahir", "Leman Altınçekiç", "Keriman Halis", "Afet İnan"], "a": "Sabiha Gökçen"},
        {"q": "Türkiye güzeli seçilerek Dünya Güzeli (1932) olan Türk kadını kimdir?", "opts": ["Keriman Halis Ece", "Feriha Tevfik", "Leyla Gencer", "İdil Biret", "Suna Kan"], "a": "Keriman Halis Ece"},
        {"q": "Atatürk'ün manevi kızı ve tarihçi olan, Türk Tarih Tezi çalışmalarına katılan kişi kimdir?", "opts": ["Afet İnan", "Sabiha Gökçen", "Ülkü Adatepe", "Zübeyde Hanım", "Latife Hanım"], "a": "Afet İnan"}
    ],

    "24. II. Dünya Savaşı Sürecinde Türkiye ve Dünya": [
        {"q": "II. Dünya Savaşı'nı başlatan olay (1 Eylül 1939) nedir?", "opts": ["Almanya'nın Polonya'yı işgali", "Pearl Harbor Baskını", "Fransa'nın işgali", "İtalya'nın Habeşistan'a saldırması", "Japonya'nın Çin'e girmesi"], "a": "Almanya'nın Polonya'yı işgali"},
        {"q": "II. Dünya Savaşı'nda 'Mihver Devletler' hangileridir?", "opts": ["Almanya, İtalya, Japonya", "İngiltere, Fransa, SSCB, ABD", "Türkiye, İspanya, İsveç", "Polonya, Çekoslovakya", "Çin, Hindistan"], "a": "Almanya, İtalya, Japonya"},
        {"q": "Almanya'nın savaşın başında uyguladığı hızlı saldırı taktiğine ne ad verilir?", "opts": ["Yıldırım Savaşı (Blitzkrieg)", "Siper Savaşı", "Gerilla Savaşı", "Soğuk Savaş", "Nükleer Savaş"], "a": "Yıldırım Savaşı (Blitzkrieg)"},
        {"q": "Fransa'nın Alman işgaline karşı kurduğu savunma hattı nedir?", "opts": ["Maginot Hattı", "Siegfried Hattı", "Çakmak Hattı", "Berlin Duvarı", "Demir Perde"], "a": "Maginot Hattı"},
        {"q": "Almanya'nın SSCB'ye (Rusya) saldırdığı harekatın adı nedir?", "opts": ["Barbarossa Harekatı", "Kartal Hücumu", "Deniz Aslanı", "Normandiya", "Pearl Harbor"], "a": "Barbarossa Harekatı"},
        {"q": "ABD'nin savaşa girmesine neden olan olay nedir?", "opts": ["Japonya'nın Pearl Harbor Baskını", "Almanya'nın saldırması", "İngiltere'nin isteği", "Atom bombası", "Normandiya"], "a": "Japonya'nın Pearl Harbor Baskını"},
        {"q": "Savaşın seyrini değiştiren ve Almanların ilk büyük yenilgisi olan savaş (Rusya'da) hangisidir?", "opts": ["Stalingrad Savaşı", "Berlin Savaşı", "Moskova Savaşı", "Kursk Savaşı", "Leningrad Kuşatması"], "a": "Stalingrad Savaşı"},
        {"q": "Müttefiklerin Avrupa'yı kurtarmak için Fransa kıyılarına yaptığı çıkarma (1944) hangisidir?", "opts": ["Normandiya Çıkarması", "Sicilya Çıkarması", "Gelibolu", "Dunkerque", "Anzio"], "a": "Normandiya Çıkarması"},
        {"q": "Japonya'nın teslim olmasını sağlayan olay nedir?", "opts": ["Hiroşima ve Nagazaki'ye atom bombası atılması", "Berlin'in düşmesi", "Mussolini'nin ölümü", "Hitler'in intiharı", "Sovyetlerin saldırması"], "a": "Hiroşima ve Nagazaki'ye atom bombası atılması"},
        {"q": "Atom bombalarını atan ABD başkanı kimdir?", "opts": ["Harry Truman", "Roosevelt", "Eisenhower", "Kennedy", "Wilson"], "a": "Harry Truman"},
        {"q": "II. Dünya Savaşı sırasında Türkiye'nin izlediği politika nedir?", "opts": ["Aktif Tarafsızlık (Denge)", "Mihver yanlısı", "Müttefik yanlısı", "Savaşa girmek", "İşgalci"], "a": "Aktif Tarafsızlık (Denge)"},
        {"q": "Savaş yıllarında Türkiye'nin Cumhurbaşkanı kimdir?", "opts": ["İsmet İnönü", "Atatürk", "Celal Bayar", "Fevzi Çakmak", "Adnan Menderes"], "a": "İsmet İnönü"},
        {"q": "Türkiye'nin olası bir Alman saldırısına karşı İstanbul'da kurduğu savunma hattı nedir?", "opts": ["Çakmak Hattı", "Maginot Hattı", "Edirne Hattı", "Çatalca Hattı", "Gelibolu Hattı"], "a": "Çakmak Hattı"},
        {"q": "İsmet İnönü ile Churchill'in Türkiye'nin savaşa girmesi için görüştüğü konferans (1943) hangisidir?", "opts": ["Adana Görüşmeleri", "Yalta Konferansı", "Tahran Konferansı", "Kahire Konferansı", "Potsdam Konferansı"], "a": "Adana Görüşmeleri"},
        {"q": "Türkiye savaşın sonuna doğru (1945) neden Almanya ve Japonya'ya savaş ilan etmiştir?", "opts": ["Birleşmiş Milletler'e (BM) kurucu üye olabilmek için", "Toprak kazanmak için", "Savaşı sevdikleri için", "Almanya saldırdığı için", "Rusya istediği için"], "a": "Birleşmiş Milletler'e (BM) kurucu üye olabilmek için"},
        {"q": "Savaş yıllarında Türkiye'de karaborsayı önlemek ve fiyatları denetlemek için çıkarılan kanun nedir?", "opts": ["Milli Korunma Kanunu", "Varlık Vergisi", "Toprak Mahsulleri Vergisi", "Takrir-i Sükun", "Teşvik-i Sanayi"], "a": "Milli Korunma Kanunu"},
        {"q": "Savaş zenginlerinden alınan olağanüstü vergi hangisidir?", "opts": ["Varlık Vergisi", "Toprak Mahsulleri Vergisi", "Aşar", "Ağnam", "Gelir Vergisi"], "a": "Varlık Vergisi"},
        {"q": "Köylüyü kalkındırmak ve eğitimci yetiştirmek için kurulan (1940) eğitim kurumları nedir?", "opts": ["Köy Enstitüleri", "Halkevleri", "Millet Mektepleri", "İmam Hatip", "Darülfünun"], "a": "Köy Enstitüleri"},
        {"q": "Köy Enstitüleri'nin kurucusu olan Milli Eğitim Bakanı kimdir?", "opts": ["Hasan Ali Yücel (ve İsmail Hakkı Tonguç)", "Tevfik İleri", "Reşit Galip", "Hamdullah Suphi", "Mümtaz Turhan"], "a": "Hasan Ali Yücel (ve İsmail Hakkı Tonguç)"},
        {"q": "II. Dünya Savaşı'ndan sonra kurulan ve dünya barışını korumayı amaçlayan örgüt hangisidir?", "opts": ["Birleşmiş Milletler (BM)", "Milletler Cemiyeti", "NATO", "Varşova Paktı", "Avrupa Birliği"], "a": "Birleşmiş Milletler (BM)"},
        {"q": "Birleşmiş Milletler'in kuruluş antlaşmasının imzalandığı konferans hangisidir?", "opts": ["San Francisco Konferansı", "Yalta Konferansı", "Potsdam Konferansı", "Paris Konferansı", "Londra Konferansı"], "a": "San Francisco Konferansı"},
        {"q": "BM Güvenlik Konseyi'nin 5 daimi üyesi (Veto yetkisi olanlar) kimlerdir? (FİRÇA)", "opts": ["Fransa, İngiltere, Rusya, Çin, ABD", "Almanya, İtalya, Japonya, Türkiye, Brezilya", "ABD, Kanada, Meksika, İngiltere, İspanya", "Rusya, Çin, Hindistan, Pakistan, İran", "Mısır, Suudi Arabistan, Türkiye, İran, Irak"], "a": "Fransa, İngiltere, Rusya, Çin, ABD"},
        {"q": "II. Dünya Savaşı'ndan sonra dünya hangi iki bloğa ayrılmıştır?", "opts": ["Doğu (SSCB) ve Batı (ABD) Bloku (Soğuk Savaş)", "Kuzey ve Güney", "Müslüman ve Hristiyan", "Zengin ve Fakir", "Asya ve Avrupa"], "a": "Doğu (SSCB) ve Batı (ABD) Bloku (Soğuk Savaş)"},
        {"q": "Uluslararası Para Fonu (IMF) ve Dünya Bankası'nın kurulduğu konferans hangisidir?", "opts": ["Bretton Woods Konferansı", "San Francisco", "Yalta", "Potsdam", "Paris"], "a": "Bretton Woods Konferansı"},
        {"q": "Almanya'nın savaş suçlularının yargılandığı mahkeme hangisidir?", "opts": ["Nürnberg Mahkemeleri", "Tokyo Mahkemeleri", "Lahey Adalet Divanı", "İstiklal Mahkemeleri", "Divan-ı Harp"], "a": "Nürnberg Mahkemeleri"},
        {"q": "Japonya'nın savaş suçlularının yargılandığı mahkeme hangisidir?", "opts": ["Tokyo Mahkemeleri", "Nürnberg Mahkemeleri", "Lahey", "Washington", "Pekin"], "a": "Tokyo Mahkemeleri"},
        {"q": "Savaş sırasında soykırıma uğrayan Yahudiler için kullanılan terim nedir?", "opts": ["Holokost", "Tehcir", "Apartheid", "Sürgün", "Pogrom"], "a": "Holokost"},
        {"q": "İnsan Hakları Evrensel Bildirgesi hangi kurum tarafından kabul edilmiştir?", "opts": ["Birleşmiş Milletler (1948)", "Milletler Cemiyeti", "Avrupa Konseyi", "NATO", "UNESCO"], "a": "Birleşmiş Milletler (1948)"},
        {"q": "Türkiye'de çok partili hayata geçişin ilk adımı olan ve Nuri Demirağ tarafından kurulan parti (1945) hangisidir?", "opts": ["Milli Kalkınma Partisi", "Demokrat Parti", "Millet Partisi", "Hürriyet Partisi", "Adalet Partisi"], "a": "Milli Kalkınma Partisi"},
        {"q": "CHP'den ayrılarak Demokrat Parti'yi (DP) kuran 'Dörtlü Takrir' grubu kimlerdir?", "opts": ["Celal Bayar, Adnan Menderes, Fuat Köprülü, Refik Koraltan", "İsmet İnönü, Fevzi Çakmak", "Süleyman Demirel, Bülent Ecevit", "Necmettin Erbakan, Alparslan Türkeş", "Turgut Özal, Mesut Yılmaz"], "a": "Celal Bayar, Adnan Menderes, Fuat Köprülü, Refik Koraltan"},
        {"q": "Türkiye'de ilk tek dereceli ve çok partili seçim ne zaman yapılmıştır?", "opts": ["1946 Seçimleri", "1950 Seçimleri", "1923 Seçimleri", "1960 Seçimleri", "1980 Seçimleri"], "a": "1946 Seçimleri"},
        {"q": "1946 seçimlerinin özelliği nedir?", "opts": ["Açık oy, gizli sayım (Şaibeli seçim)", "Gizli oy, açık sayım", "Tek parti seçimi", "Sadece erkekler oy kullandı", "Atamalı seçim"], "a": "Açık oy, gizli sayım (Şaibeli seçim)"},
        {"q": "Demokrat Parti'nin iktidara geldiği ve CHP'nin 27 yıllık iktidarının bittiği seçim (Beyaz Devrim) hangisidir?", "opts": ["1950 Seçimleri", "1946 Seçimleri", "1954 Seçimleri", "1960 Seçimleri", "1965 Seçimleri"], "a": "1950 Seçimleri"},
        {"q": "1950 seçimlerinde uygulanan demokratik yöntem nedir?", "opts": ["Gizli oy, açık sayım", "Açık oy, gizli sayım", "Tek dereceli", "Çift dereceli", "Atama"], "a": "Gizli oy, açık sayım"},
        {"q": "Türkiye'nin Truman Doktrini ve Marshall Planı'ndan yardım almasının sebebi nedir?", "opts": ["Sovyet Rusya (SSCB) tehdidi ve Batı Bloku'na yakınlaşma isteği", "Savaş tazminatı", "Borç ödeme", "Sanayileşme", "Tarım"], "a": "Sovyet Rusya (SSCB) tehdidi ve Batı Bloku'na yakınlaşma isteği"},
        {"q": "Avrupa'nın ekonomik kalkınması için ABD'nin yaptığı yardım planı nedir?", "opts": ["Marshall Planı", "Truman Doktrini", "Molotov Planı", "Schuman Planı", "Monroe Doktrini"], "a": "Marshall Planı"},
        {"q": "SSCB'nin ABD'nin çevreleme politikasına karşı kurduğu ekonomik örgüt nedir?", "opts": ["COMECON", "COMINFORM", "Varşova Paktı", "NATO", "AET"], "a": "COMECON"},
        {"q": "Soğuk Savaş döneminde Batı savunma paktı hangisidir?", "opts": ["NATO", "Varşova Paktı", "CENTO", "SEATO", "ANZUS"], "a": "NATO"},
        {"q": "Soğuk Savaş döneminde Doğu (Komünist) savunma paktı hangisidir?", "opts": ["Varşova Paktı", "NATO", "COMECON", "Sadabat Paktı", "Balkan Paktı"], "a": "Varşova Paktı"},
        {"q": "İsrail Devleti ne zaman kurulmuştur?", "opts": ["1948", "1945", "1950", "1960", "1917"], "a": "1948"},
        {"q": "II. Dünya Savaşı'ndan sonra bağımsızlığını kazanan Asya ülkelerinden Hindistan'ın lideri kimdir?", "opts": ["Mahatma Gandhi", "Cinnah", "Nehru", "Mao", "Ho Chi Minh"], "a": "Mahatma Gandhi"},
        {"q": "Pakistan'ın kurucusu kimdir?", "opts": ["Muhammed Ali Cinnah", "Gandhi", "Nehru", "Müşerref", "Butto"], "a": "Muhammed Ali Cinnah"},
        {"q": "Bilgisayarın atası sayılan ENIAC ve ilk füzeler (V2) hangi dönemde geliştirilmiştir?", "opts": ["II. Dünya Savaşı yılları", "I. Dünya Savaşı", "Soğuk Savaş", "Sanayi İnkılabı", "2000'ler"], "a": "II. Dünya Savaşı yılları"},
        {"q": "Savaş yıllarında Türkiye'de ekmek karnesi uygulamasının nedeni nedir?", "opts": ["Tahıl stoklarını korumak ve kıtlığı önlemek", "Halkı cezalandırmak", "Savaşa girmek", "Almanya'ya yardım etmek", "İhracat yapmak"], "a": "Tahıl stoklarını korumak ve kıtlığı önlemek"},
        {"q": "II. Dünya Savaşı'nda 'En Büyük Savaş' olarak bilinen ve milyonlarca kişinin öldüğü cephe hangisidir?", "opts": ["Doğu Cephesi (Almanya - SSCB)", "Batı Cephesi", "Pasifik Cephesi", "Kuzey Afrika", "İtalya"], "a": "Doğu Cephesi (Almanya - SSCB)"},
        {"q": "Atlantik Bildirisi'ni (BM'nin temeli) kimler yayınlamıştır?", "opts": ["Roosevelt (ABD) ve Churchill (İngiltere)", "Stalin ve Hitler", "İnönü ve Truman", "Mussolini ve Franco", "Lenin ve Wilson"], "a": "Roosevelt (ABD) ve Churchill (İngiltere)"},
        {"q": "Savaş sonrasında Almanya kaç bölgeye ayrılmıştır?", "opts": ["4 (ABD, İngiltere, Fransa, SSCB)", "2", "3", "5", "Bölünmedi"], "a": "4 (ABD, İngiltere, Fransa, SSCB)"},
        {"q": "Berlin Duvarı ne zaman inşa edilmiştir?", "opts": ["1961 (Soğuk Savaş)", "1945", "1989", "1990", "1950"], "a": "1961 (Soğuk Savaş)"},
        {"q": "II. Dünya Savaşı'nda Türkiye'nin nüfus artış hızı nasıl etkilenmiştir?", "opts": ["Düşmüştür (Seferberlik nedeniyle)", "Artmıştır", "Değişmemiştir", "Sıfırlanmıştır", "Bilinmiyor"], "a": "Düşmüştür (Seferberlik nedeniyle)"},
        {"q": "Türkiye'nin NATO'ya girmesini hızlandıran olay nedir?", "opts": ["Kore Savaşı'na asker göndermesi", "II. Dünya Savaşı'na girmesi", "Marshall yardımı alması", "Demokrasiye geçmesi", "İsrail'i tanıması"], "a": "Kore Savaşı'na asker göndermesi"}
    ],"25. II. Dünya Savaşı Sonrasında Türkiye ve Dünya": [
        {"q": "II. Dünya Savaşı'ndan sonra dünya siyasetine yön veren iki süper güç hangisidir?", "opts": ["ABD ve SSCB", "İngiltere ve Fransa", "Almanya ve Japonya", "Çin ve ABD", "Rusya ve Çin"], "a": "ABD ve SSCB"},
        {"q": "Batı Bloku (ABD) ve Doğu Bloku (SSCB) arasındaki gerginlik dönemine ne ad verilir?", "opts": ["Soğuk Savaş", "Yumuşama", "Sıcak Çatışma", "Barış Dönemi", "Fetret Devri"], "a": "Soğuk Savaş"},
        {"q": "ABD'nin Sovyet yayılmacılığına karşı Türkiye ve Yunanistan'a askeri yardım yapmasını öngören belge hangisidir?", "opts": ["Truman Doktrini", "Marshall Planı", "Monroe Doktrini", "Eisenhower Doktrini", "Balfour Deklarasyonu"], "a": "Truman Doktrini"},
        {"q": "ABD'nin Avrupa ülkelerini ekonomik olarak kalkındırmak için hazırladığı yardım paketi nedir?", "opts": ["Marshall Planı", "Truman Doktrini", "Molotov Planı", "Schuman Planı", "Dawes Planı"], "a": "Marshall Planı"},
        {"q": "SSCB'nin ABD'nin Marshall Planı'na karşı Doğu Bloku ülkeleriyle kurduğu ekonomik örgüt hangisidir?", "opts": ["COMECON", "COMINFORM", "Varşova Paktı", "NATO", "AET"], "a": "COMECON"},
        {"q": "Batı Bloku'nun (ABD ve müttefikleri) askeri savunma örgütü hangisidir?", "opts": ["NATO (Kuzey Atlantik Paktı)", "Varşova Paktı", "Birleşmiş Milletler", "Avrupa Konseyi", "CENTO"], "a": "NATO (Kuzey Atlantik Paktı)"},
        {"q": "Doğu Bloku'nun (SSCB ve müttefikleri) NATO'ya karşı kurduğu askeri örgüt hangisidir?", "opts": ["Varşova Paktı", "COMECON", "Kominform", "Sadabat Paktı", "Balkan Paktı"], "a": "Varşova Paktı"},
        {"q": "Demir Perde kavramını ilk kez kullanan İngiliz devlet adamı kimdir?", "opts": ["Winston Churchill", "Roosevelt", "Chamberlain", "Truman", "Stalin"], "a": "Winston Churchill"},
        {"q": "Berlin Buhranı sonucunda Almanya nasıl bölünmüştür?", "opts": ["Doğu (Demokratik Alman) ve Batı (Federal Alman) Almanya olarak", "Kuzey ve Güney olarak", "Prusya ve Bavyera olarak", "Berlin ve Münih olarak", "Bölünmemiştir"], "a": "Doğu (Demokratik Alman) ve Batı (Federal Alman) Almanya olarak"},
        {"q": "1948'de kurulan İsrail Devleti'ni tanıyan ilk Müslüman ülke hangisidir?", "opts": ["Türkiye", "Mısır", "İran", "Pakistan", "Endonezya"], "a": "Türkiye"},
        {"q": "Türkiye'nin Kore Savaşı'na asker göndermesinin temel siyasi amacı neydi?", "opts": ["NATO'ya üye olabilmek", "Güney Kore'yi sömürge yapmak", "Japonya ile savaşmak", "BM Güvenlik Konseyi'ne girmek", "Çin ile dost olmak"], "a": "NATO'ya üye olabilmek"},
        {"q": "Türkiye NATO'ya hangi yıl üye olmuştur?", "opts": ["1952", "1949", "1950", "1960", "1945"], "a": "1952"},
        {"q": "Türkiye ile birlikte NATO'ya aynı anda üye olan diğer ülke hangisidir?", "opts": ["Yunanistan", "İspanya", "İtalya", "Almanya", "Fransa"], "a": "Yunanistan"},
        {"q": "Çok partili hayata geçişin ilk genel seçimi olan 1946 seçimlerinin özelliği nedir?", "opts": ["Açık oy, gizli sayım (Şaibeli)", "Gizli oy, açık sayım", "Tek dereceli", "İki turlu", "Elektronik"], "a": "Açık oy, gizli sayım (Şaibeli)"},
        {"q": "14 Mayıs 1950 seçimlerinde iktidara gelerek 27 yıllık CHP iktidarını sonlandıran parti hangisidir?", "opts": ["Demokrat Parti", "Milli Kalkınma Partisi", "Millet Partisi", "Adalet Partisi", "Hürriyet Partisi"], "a": "Demokrat Parti"},
        {"q": "Demokrat Parti'nin iktidara gelmesine siyasi tarihte ne ad verilir?", "opts": ["Beyaz Devrim", "Kadife Devrim", "Halk Devrimi", "Sessiz Devrim", "Demokrasi Bayramı"], "a": "Beyaz Devrim"},
        {"q": "1950-1960 yılları arasında Cumhurbaşkanlığı yapan isim kimdir?", "opts": ["Celal Bayar", "Adnan Menderes", "İsmet İnönü", "Cemal Gürsel", "Fevzi Çakmak"], "a": "Celal Bayar"},
        {"q": "1950-1960 yılları arasında Başbakanlık yapan isim kimdir?", "opts": ["Adnan Menderes", "Celal Bayar", "Fuat Köprülü", "Refik Koraltan", "Hasan Polatkan"], "a": "Adnan Menderes"},
        {"q": "Demokrat Parti döneminde ezanın diliyle ilgili yapılan değişiklik nedir?", "opts": ["Ezanın tekrar Arapça okunması serbest bırakıldı", "Türkçe okunması zorunlu oldu", "Ezan yasaklandı", "Sadece cami içinde okunması", "Latince okunması"], "a": "Ezanın tekrar Arapça okunması serbest bırakıldı"},
        {"q": "Köy Enstitüleri hangi yıl tamamen kapatılarak İlköğretmen Okullarına dönüştürülmüştür?", "opts": ["1954", "1940", "1950", "1960", "1946"], "a": "1954"},
        {"q": "Türkiye'nin 1955'te İran, Irak, Pakistan ve İngiltere ile kurduğu savunma örgütü hangisidir?", "opts": ["Bağdat Paktı (Sonraki adı CENTO)", "Sadabat Paktı", "Balkan Paktı", "NATO", "Varşova Paktı"], "a": "Bağdat Paktı (Sonraki adı CENTO)"},
        {"q": "1955'te Atatürk'ün evinin bombalandığı yalan haberi üzerine çıkan olaylar hangisidir?", "opts": ["6-7 Eylül Olayları", "Menemen Olayı", "31 Mart Vakası", "Şeyh Sait İsyanı", "Kanlı Pazar"], "a": "6-7 Eylül Olayları"},
        {"q": "Türkiye'de ilk askeri darbe ne zaman gerçekleşmiştir?", "opts": ["27 Mayıs 1960", "12 Eylül 1980", "12 Mart 1971", "28 Şubat 1997", "15 Temmuz 2016"], "a": "27 Mayıs 1960"},
        {"q": "27 Mayıs 1960 darbesini yapan komita hangisidir?", "opts": ["Milli Birlik Komitesi", "Yurtta Sulh Konseyi", "Milli Güvenlik Konseyi", "İttihat ve Terakki", "Hürriyet ve İtilaf"], "a": "Milli Birlik Komitesi"},
        {"q": "Yassıada yargılamaları sonucunda idam edilen Başbakan kimdir?", "opts": ["Adnan Menderes", "Celal Bayar", "Fatin Rüştü Zorlu", "Hasan Polatkan", "Refik Koraltan"], "a": "Adnan Menderes"},
        {"q": "Soğuk Savaş döneminde Orta Doğu'da etkili olmak isteyen ABD'nin yayınladığı doktrin nedir?", "opts": ["Eisenhower Doktrini", "Truman Doktrini", "Monroe Doktrini", "Nixon Doktrini", "Kennedy Doktrini"], "a": "Eisenhower Doktrini"},
        {"q": "Hindistan ve Çin'in öncülüğünde kurulan, bloklara dahil olmayan ülkelerin hareketi nedir?", "opts": ["Bağlantısızlar Hareketi (3. Dünya Ülkeleri)", "Mihver Devletler", "Müttefik Devletler", "Doğu Bloku", "Batı Bloku"], "a": "Bağlantısızlar Hareketi (3. Dünya Ülkeleri)"},
        {"q": "Bağlantısızlar Hareketi'nin temellerinin atıldığı konferans hangisidir?", "opts": ["Bandung Konferansı", "Yalta Konferansı", "Potsdam Konferansı", "Kahire Konferansı", "San Francisco Konferansı"], "a": "Bandung Konferansı"},
        {"q": "Fransa'ya karşı bağımsızlık savaşı vererek 1962'de bağımsız olan Kuzey Afrika ülkesi hangisidir?", "opts": ["Cezayir", "Mısır", "Tunus", "Fas", "Libya"], "a": "Cezayir"},
        {"q": "Küba'da sosyalist devrimi gerçekleştiren lider kimdir?", "opts": ["Fidel Castro", "Che Guevara", "Batista", "Allende", "Peron"], "a": "Fidel Castro"},
        {"q": "Soğuk Savaş'ın en gergin anlarından biri olan 'Füze Krizi' (1962) hangi iki ülke arasında yaşanmıştır?", "opts": ["ABD ve SSCB (Küba ve Türkiye füzeleri)", "ABD ve Çin", "SSCB ve İngiltere", "Almanya ve Fransa", "Kore ve Japonya"], "a": "ABD ve SSCB (Küba ve Türkiye füzeleri)"},
        {"q": "Sputnik 1 uydusunu uzaya göndererek uzay çağını başlatan devlet hangisidir?", "opts": ["SSCB (Sovyetler Birliği)", "ABD", "Çin", "Almanya", "Japonya"], "a": "SSCB (Sovyetler Birliği)"},
        {"q": "Ay'a ilk insanı (Neil Armstrong) gönderen ülke hangisidir?", "opts": ["ABD (Apollo 11)", "SSCB", "Çin", "Fransa", "İngiltere"], "a": "ABD (Apollo 11)"},
        {"q": "Berlin Duvarı (Utanç Duvarı) hangi yıl inşa edilmiştir?", "opts": ["1961", "1945", "1950", "1989", "1990"], "a": "1961"},
        {"q": "Türkiye'de televizyon yayınları (TRT) ilk kez hangi yıl başlamıştır?", "opts": ["1968", "1950", "1980", "1990", "1940"], "a": "1968"},
        {"q": "Avrupa Ekonomik Topluluğu'nun (AB'nin temeli) kurulduğu antlaşma hangisidir?", "opts": ["Roma Antlaşması", "Maastricht Antlaşması", "Paris Antlaşması", "Ankara Antlaşması", "Lizbon Antlaşması"], "a": "Roma Antlaşması"},
        {"q": "Türkiye'nin AET (AB) ile imzaladığı ortaklık antlaşması (1963) hangisidir?", "opts": ["Ankara Antlaşması", "Roma Antlaşması", "Katma Protokol", "Gümrük Birliği", "Lozan"], "a": "Ankara Antlaşması"},
        {"q": "Kore Savaşı'ndaki başarısıyla bilinen Türk birliğinin adı nedir?", "opts": ["Şimal Yıldızı (Kutup Yıldızı)", "Mehmetçik", "Barış Gücü", "Çelik Kuvvet", "Akıncılar"], "a": "Şimal Yıldızı (Kutup Yıldızı)"},
        {"q": "1960 Darbesi'nden sonra hazırlanan ve Türkiye'nin en özgürlükçü anayasası sayılan anayasa hangisidir?", "opts": ["1961 Anayasası", "1924 Anayasası", "1982 Anayasası", "1921 Anayasası", "Kanun-i Esasi"], "a": "1961 Anayasası"},
        {"q": "Anayasa Mahkemesi hangi anayasa ile kurulmuştur?", "opts": ["1961 Anayasası", "1982 Anayasası", "1924 Anayasası", "2010 Değişikliği", "1921 Anayasası"], "a": "1961 Anayasası"},
        {"q": "Devlet Planlama Teşkilatı (DPT) hangi dönemde kurulmuştur?", "opts": ["1960 Sonrası (1961 Anayasası ile)", "Atatürk Dönemi", "Demokrat Parti Dönemi", "1980 Sonrası", "2000'ler"], "a": "1960 Sonrası (1961 Anayasası ile)"},
        {"q": "1961 Anayasası'na göre TBMM kaç meclisten oluşuyordu?", "opts": ["İki (Millet Meclisi ve Cumhuriyet Senatosu)", "Tek", "Üç", "Dört", "Beş"], "a": "İki (Millet Meclisi ve Cumhuriyet Senatosu)"},
        {"q": "Türkiye'de otomobil üretimi (Devrim Arabaları) hangi yıl denenmiştir?", "opts": ["1961", "1950", "1970", "1980", "1940"], "a": "1961"},
        {"q": "Demokrat Parti'nin devamı niteliğinde olan ve Süleyman Demirel'in liderliğini yaptığı parti hangisidir?", "opts": ["Adalet Partisi (AP)", "Anavatan Partisi", "Refah Partisi", "Cumhuriyet Halk Partisi", "Milli Selamet Partisi"], "a": "Adalet Partisi (AP)"},
        {"q": "1958'de Irak'ta darbe olması üzerine Bağdat Paktı'nın merkezi Ankara'ya taşınmış ve adı ne olmuştur?", "opts": ["CENTO", "NATO", "SEATO", "Sadabat Paktı", "KEİ"], "a": "CENTO"},
        {"q": "Vietnam Savaşı'nda ABD'yi protesto eden ünlü boksör kimdir?", "opts": ["Muhammed Ali Clay", "Mike Tyson", "Joe Frazier", "George Foreman", "Rocky Marciano"], "a": "Muhammed Ali Clay"},
        {"q": "Gandhi'nin Hindistan'ın bağımsızlığı için başlattığı pasif direniş eylemi nedir?", "opts": ["Tuz Yürüyüşü", "Uzun Yürüyüş", "Sivil İtaatsizlik", "Açlık Grevi", "Boykot"], "a": "Tuz Yürüyüşü"},
        {"q": "Keşmir Sorunu hangi iki ülke arasındadır?", "opts": ["Hindistan ve Pakistan", "Çin ve Hindistan", "Pakistan ve Afganistan", "İran ve Irak", "Rusya ve Ukrayna"], "a": "Hindistan ve Pakistan"},
        {"q": "Filistin Sorunu nedeniyle İsrail ile Arap ülkeleri arasında yapılan savaşlar nelerdir?", "opts": ["1948, 1956, 1967 (6 Gün), 1973 (Yom Kippur)", "Körfez Savaşları", "İran-Irak Savaşı", "Balkan Savaşları", "Kore Savaşı"], "a": "1948, 1956, 1967 (6 Gün), 1973 (Yom Kippur)"},
        {"q": "Süveyş Krizi (1956) hangi ülkenin kanalı millileştirmesiyle çıkmıştır?", "opts": ["Mısır (Cemal Abdünnasır)", "İsrail", "İngiltere", "Fransa", "ABD"], "a": "Mısır (Cemal Abdünnasır)"}
    ],

    "26. Toplumsal Devrim Çağında Dünya ve Türkiye": [
        {"q": "Soğuk Savaş döneminde bloklar arasındaki gerginliğin azalmasına ne ad verilir?", "opts": ["Yumuşama (Detant) Dönemi", "Soğuk Savaş", "Barış Pınarı", "Küreselleşme", "Demir Perde"], "a": "Yumuşama (Detant) Dönemi"},
        {"q": "Yumuşama dönemini başlatan ABD Başkanı ve SSCB Lideri kimlerdir?", "opts": ["Nixon ve Brejnev (öncesinde Kennedy-Kruşçev)", "Reagan ve Gorbaçov", "Truman ve Stalin", "Bush ve Putin", "Wilson ve Lenin"], "a": "Nixon ve Brejnev (öncesinde Kennedy-Kruşçev)"},
        {"q": "Nükleer silahların sınırlandırılması için ABD ve SSCB arasında imzalanan antlaşmalar hangileridir?", "opts": ["SALT-1 ve SALT-2", "START", "INF", "NATO", "Varşova"], "a": "SALT-1 ve SALT-2"},
        {"q": "ABD ve Çin arasındaki ilişkilerin düzelmesini sağlayan 'Pinpon Diplomasisi' hangi sporu içerir?", "opts": ["Masa Tenisi", "Tenis", "Golf", "Futbol", "Basketbol"], "a": "Masa Tenisi"},
        {"q": "Avrupa'da güvenlik ve işbirliğini sağlamak amacıyla 1975'te imzalanan belge nedir?", "opts": ["Helsinki Nihai Senedi", "Paris Şartı", "Roma Antlaşması", "Maastricht Kriterleri", "Kopenhag Kriterleri"], "a": "Helsinki Nihai Senedi"},
        {"q": "1960'ta Kıbrıs Cumhuriyeti'nin kurulduğu antlaşmalar hangileridir?", "opts": ["Zürih ve Londra Antlaşmaları", "Ankara Antlaşması", "Lozan Antlaşması", "Atina Antlaşması", "Paris Antlaşması"], "a": "Zürih ve Londra Antlaşmaları"},
        {"q": "Kıbrıs Cumhuriyeti'nin ilk Cumhurbaşkanı ve Cumhurbaşkanı Yardımcısı kimlerdir?", "opts": ["Makarios ve Dr. Fazıl Küçük", "Rauf Denktaş ve Sampson", "Klerides ve Eroğlu", "Grivas ve Denktaş", "Papadopulos ve Talat"], "a": "Makarios ve Dr. Fazıl Küçük"},
        {"q": "Kıbrıslı Rumların Kıbrıs'ı Yunanistan'a bağlama hedefine ne ad verilir?", "opts": ["Enosis", "Megali İdea", "EOKA", "Akritas", "Helenizm"], "a": "Enosis"},
        {"q": "Rumların Kıbrıs Türklerini yok etmek için kurduğu terör örgütü hangisidir?", "opts": ["EOKA", "ASALA", "PKK", "FETÖ", "DHKP-C"], "a": "EOKA"},
        {"q": "EOKA'ya karşı Kıbrıs Türklerinin savunma amacıyla kurduğu teşkilat hangisidir?", "opts": ["TMT (Türk Mukavemet Teşkilatı)", "Volkan", "Mücahitler", "Kuvayi Milliye", "Akıncılar"], "a": "TMT (Türk Mukavemet Teşkilatı)"},
        {"q": "Rumların 1963'te Türklere karşı başlattığı ve 'Kanlı Noel' olarak bilinen saldırı planı nedir?", "opts": ["Akritas Planı", "Enosis Planı", "Megali İdea", "Yıldırım Planı", "Barış Planı"], "a": "Akritas Planı"},
        {"q": "ABD Başkanı Johnson'ın Türkiye'nin Kıbrıs'a müdahalesini engellemek için yazdığı mektuba ne ad verilir?", "opts": ["Johnson Mektubu", "Truman Mektubu", "Kennedy Mektubu", "Nixon Mektubu", "Carter Mektubu"], "a": "Johnson Mektubu"},
        {"q": "Türkiye'nin 1974'te gerçekleştirdiği 'Kıbrıs Barış Harekatı'nın dönemin Başbakanı kimdir?", "opts": ["Bülent Ecevit", "Süleyman Demirel", "Necmettin Erbakan", "Alparslan Türkeş", "Turgut Özal"], "a": "Bülent Ecevit"},
        {"q": "Kıbrıs Barış Harekatı'nın parolası nedir?", "opts": ["Ayşe tatile çıksın", "Ordular ilk hedefiniz Akdeniz", "Vatan sana canım feda", "Barış hemen şimdi", "Zafer bizimdir"], "a": "Ayşe tatile çıksın"},
        {"q": "Kıbrıs Barış Harekatı sonucunda kurulan ilk Türk devleti (1975) hangisidir?", "opts": ["Kıbrıs Türk Federe Devleti", "KKTC", "Hatay Cumhuriyeti", "Batı Trakya Cumhuriyeti", "Azerbaycan"], "a": "Kıbrıs Türk Federe Devleti"},
        {"q": "Kuzey Kıbrıs Türk Cumhuriyeti (KKTC) hangi yıl kurulmuştur?", "opts": ["1983", "1974", "1975", "1990", "1960"], "a": "1983"},
        {"q": "KKTC'nin kurucu Cumhurbaşkanı kimdir?", "opts": ["Rauf Denktaş", "Dr. Fazıl Küçük", "Derviş Eroğlu", "Mehmet Ali Talat", "Mustafa Akıncı"], "a": "Rauf Denktaş"},
        {"q": "1970'li yıllarda Türk diplomatlarına suikastlar düzenleyen Ermeni terör örgütü hangisidir?", "opts": ["ASALA", "EOKA", "PKK", "Taşnak", "Hınçak"], "a": "ASALA"},
        {"q": "Türkiye'de 12 Mart 1971 Muhtırası kime karşı verilmiştir?", "opts": ["Süleyman Demirel Hükümeti'ne", "Bülent Ecevit'e", "Adnan Menderes'e", "Turgut Özal'a", "Kenan Evren'e"], "a": "Süleyman Demirel Hükümeti'ne"},
        {"q": "1973 Arap-İsrail Savaşı (Yom Kippur) sonrasında yaşanan küresel kriz nedir?", "opts": ["1973 Petrol Krizi (OPEC Ambargosu)", "1929 Ekonomik Buhranı", "Küresel Isınma", "Mülteci Krizi", "Nükleer Kriz"], "a": "1973 Petrol Krizi (OPEC Ambargosu)"},
        {"q": "Mısır ve İsrail arasında barışı sağlayan ve Mısır'ın İsrail'i tanıdığı ilk antlaşma (1978) hangisidir?", "opts": ["Camp David Antlaşması", "Oslo Görüşmeleri", "Madrid Konferansı", "Kahire Antlaşması", "Kudüs Antlaşması"], "a": "Camp David Antlaşması"},
        {"q": "İran'da 1979'da Şah rejimini devirerek İslam Cumhuriyeti'ni kuran lider kimdir?", "opts": ["Ayetullah Humeyni", "Muhammed Rıza Pehlevi", "Musaddık", "Rafsancani", "Ahmedinejad"], "a": "Ayetullah Humeyni"},
        {"q": "Sovyetler Birliği (SSCB) 1979'da hangi ülkeyi işgal etmiştir?", "opts": ["Afganistan", "İran", "Türkiye", "Polonya", "Macaristan"], "a": "Afganistan"},
        {"q": "Türkiye'de 12 Eylül 1980 askeri darbesini yapan Genelkurmay Başkanı kimdir?", "opts": ["Kenan Evren", "Cemal Gürsel", "Memduh Tağmaç", "Çevik Bir", "Hilmi Özkök"], "a": "Kenan Evren"},
        {"q": "1980 darbesinden sonra hazırlanan ve halkoylamasıyla kabul edilen anayasa hangisidir?", "opts": ["1982 Anayasası", "1961 Anayasası", "1924 Anayasası", "2010 Anayasası", "1921 Anayasası"], "a": "1982 Anayasası"},
        {"q": "1980 sonrası Türk ekonomisinde serbest piyasa ekonomisine geçişi sağlayan kararlar nedir?", "opts": ["24 Ocak Kararları", "12 Temmuz Beyannamesi", "İzmir İktisat Kongresi", "Varlık Vergisi", "Milli Korunma"], "a": "24 Ocak Kararları"},
        {"q": "24 Ocak Kararları'nın mimarı ve 1983 seçimlerini kazanan lider kimdir?", "opts": ["Turgut Özal (ANAP)", "Süleyman Demirel", "Bülent Ecevit", "Necmettin Erbakan", "Alparslan Türkeş"], "a": "Turgut Özal (ANAP)"},
        {"q": "İran-Irak Savaşı (1980-1988) sırasında Irak'ın Halepçe'de yaptığı katliamın niteliği nedir?", "opts": ["Kimyasal Silah Saldırısı (Halepçe Katliamı)", "Nükleer Saldırı", "Hava Saldırısı", "Tank Saldırısı", "Deniz Saldırısı"], "a": "Kimyasal Silah Saldırısı (Halepçe Katliamı)"},
        {"q": "Filistin Kurtuluş Örgütü'nün (FKÖ) efsanevi lideri kimdir?", "opts": ["Yaser Arafat", "Mahmud Abbas", "Şeyh Yasin", "Haniye", "Meşal"], "a": "Yaser Arafat"},
        {"q": "Filistinlilerin İsrail işgaline karşı başlattığı halk ayaklanmasına ne ad verilir?", "opts": ["İntifada", "Cihad", "Hicret", "Direniş", "Kıyam"], "a": "İntifada"},
        {"q": "Yumuşama döneminde uzaya gönderilen ilk kadın kozmonot kimdir?", "opts": ["Valentina Tereşkova", "Sabiha Gökçen", "Marie Curie", "Sally Ride", "Amelia Earhart"], "a": "Valentina Tereşkova"},
        {"q": "Türkiye'nin Eurovision Şarkı Yarışması'na ilk kez katıldığı yıl ve sanatçı kimdir?", "opts": ["1975 - Semiha Yankı (Seninle Bir Dakika)", "1980 - Ajda Pekkan", "1997 - Şebnem Paker", "2003 - Sertab Erener", "1970 - Erol Büyükburç"], "a": "1975 - Semiha Yankı (Seninle Bir Dakika)"},
        {"q": "Türkiye'de renkli televizyon yayınına ne zaman geçilmiştir?", "opts": ["1984 (Özal Dönemi)", "1974", "1990", "1968", "2000"], "a": "1984 (Özal Dönemi)"},
        {"q": "1960'larda dünyada gençlik hareketlerinin sembolü olan '68 Kuşağı' olayları nerede başlamıştır?", "opts": ["Fransa (Paris)", "ABD", "İngiltere", "Türkiye", "Almanya"], "a": "Fransa (Paris)"},
        {"q": "ABD'de ırkçılığa karşı mücadele eden ve 'Bir hayalim var' konuşmasını yapan lider kimdir?", "opts": ["Martin Luther King", "Malcolm X", "Obama", "Rosa Parks", "Mandela"], "a": "Martin Luther King"},
        {"q": "Güney Afrika'da ırk ayrımcılığına (Apartheid) karşı mücadele eden efsanevi lider kimdir?", "opts": ["Nelson Mandela", "Gandhi", "Kofi Annan", "Desmond Tutu", "Zuma"], "a": "Nelson Mandela"},
        {"q": "1970'lerde ortaya çıkan ve çevre bilincini savunan sivil toplum kuruluşu hangisidir?", "opts": ["Greenpeace", "NATO", "BM", "UNESCO", "UNICEF"], "a": "Greenpeace"},
        {"q": "Kıbrıs Barış Harekatı nedeniyle Türkiye'ye ambargo uygulayan ülke hangisidir?", "opts": ["ABD", "SSCB", "Çin", "Almanya", "İtalya"], "a": "ABD"},
        {"q": "Türkiye'nin ilk yerli otomobili 'Devrim'den sonra seri üretime geçen ilk otomobil markası nedir?", "opts": ["Anadol", "Tofaş", "Renault", "Murat 124", "TOGG"], "a": "Anadol"},
        {"q": "1970'li yıllarda Türkiye'de yaşanan siyasi ve ekonomik istikrarsızlığın en belirgin özelliği nedir?", "opts": ["Koalisyon hükümetleri, sokak çatışmaları (Sağ-Sol) ve kuyruklar", "Tek parti iktidarı", "Ekonomik refah", "Barış ortamı", "AB üyeliği"], "a": "Koalisyon hükümetleri, sokak çatışmaları (Sağ-Sol) ve kuyruklar"},
        {"q": "12 Eylül 1980 darbesinden sonra siyasi yasaklı hale gelen liderler kimlerdir?", "opts": ["Demirel, Ecevit, Erbakan, Türkeş", "Özal, İnönü", "Menderes, Bayar", "Evren, Özal", "Çiller, Yılmaz"], "a": "Demirel, Ecevit, Erbakan, Türkeş"},
        {"q": "1987'de siyasi yasakların kalkmasıyla Süleyman Demirel'in başına geçtiği parti hangisidir?", "opts": ["Doğru Yol Partisi (DYP)", "Adalet Partisi", "Anavatan Partisi", "Demokrat Parti", "MHP"], "a": "Doğru Yol Partisi (DYP)"},
        {"q": "Türkiye'nin AB'ye (o zamanki AET) tam üyelik başvurusunu yapan Başbakan kimdir?", "opts": ["Turgut Özal (1987)", "Bülent Ecevit", "Süleyman Demirel", "Mesut Yılmaz", "Tansu Çiller"], "a": "Turgut Özal (1987)"},
        {"q": "1988'de açılan ve Asya ile Avrupa'yı ikinci kez birleştiren köprü hangisidir?", "opts": ["Fatih Sultan Mehmet Köprüsü", "Boğaziçi Köprüsü", "Yavuz Sultan Selim Köprüsü", "Galata Köprüsü", "Osmangazi Köprüsü"], "a": "Fatih Sultan Mehmet Köprüsü"},
        {"q": "Naim Süleymanoğlu hangi alanda dünya rekorları kırarak 'Cep Herkülü' unvanını almıştır?", "opts": ["Halter", "Güreş", "Boks", "Atletizm", "Yüzme"], "a": "Halter"},
        {"q": "SSCB'nin Afganistan'ı işgaline tepki olarak hangi olimpiyatlar boykot edilmiştir?", "opts": ["1980 Moskova Olimpiyatları", "1984 Los Angeles", "1972 Münih", "1988 Seul", "1968 Meksika"], "a": "1980 Moskova Olimpiyatları"},
        {"q": "Chernobyl (Çernobil) Nükleer Santral kazası (1986) hangi ülkede meydana gelmiştir?", "opts": ["Ukrayna (SSCB)", "Rusya", "Belarus", "Polonya", "Almanya"], "a": "Ukrayna (SSCB)"},
        {"q": "1989'da Berlin Duvarı'nın yıkılması neyin habercisi olmuştur?", "opts": ["Soğuk Savaş'ın sonunun ve Almanya'nın birleşmesinin", "Savaşın başladığının", "Duvarın yenileneceğinin", "AB'nin dağılacağının", "Hitler'in döneceğinin"], "a": "Soğuk Savaş'ın sonunun ve Almanya'nın birleşmesinin"},
        {"q": "İran-Irak savaşını sona erdiren ateşkesi sağlayan uluslararası kurum hangisidir?", "opts": ["Birleşmiş Milletler", "NATO", "İslam İşbirliği Teşkilatı", "Varşova Paktı", "AB"], "a": "Birleşmiş Milletler"},
        {"q": "Türkiye'de turizmin gelişmesi ve 'Turizm Patlaması' hangi dönemde başlamıştır?", "opts": ["Özal Dönemi (1980'ler)", "1960'lar", "1950'ler", "1990'lar", "2000'ler"], "a": "Özal Dönemi (1980'ler)"}
    ],

    "27. XXI. Yüzyılın Eşiğinde Türkiye ve Dünya": [
        {"q": "Soğuk Savaş'ı resmen bitiren ve SSCB'nin dağılmasına yol açan lider kimdir?", "opts": ["Mihail Gorbaçov", "Boris Yeltsin", "Vladimir Putin", "Stalin", "Brejnev"], "a": "Mihail Gorbaçov"},
        {"q": "Gorbaçov'un uyguladığı 'Açıklık' ve 'Yeniden Yapılanma' politikalarının adları nelerdir?", "opts": ["Glasnost ve Perestroyka", "Demir Perde", "Kızıl Meydan", "Bolşevizm", "Komintern"], "a": "Glasnost ve Perestroyka"},
        {"q": "SSCB'nin dağılmasıyla (1991) bağımsızlığını kazanan Türk Cumhuriyetleri hangileridir?", "opts": ["Azerbaycan, Kazakistan, Kırgızistan, Özbekistan, Türkmenistan", "Tataristan, Yakutistan", "Kırım, Çeçenistan", "Macaristan, Polonya", "Gürcistan, Ermenistan"], "a": "Azerbaycan, Kazakistan, Kırgızistan, Özbekistan, Türkmenistan"},
        {"q": "Azerbaycan'ın bağımsızlık lideri kimdir?", "opts": ["Ebulfez Elçibey", "Haydar Aliyev", "İlham Aliyev", "Resulzade", "Nazarbayev"], "a": "Ebulfez Elçibey"},
        {"q": "Türk dili konuşan ülkeler arasında kültürel işbirliğini sağlamak amacıyla kurulan teşkilat nedir?", "opts": ["TÜRKSOY", "TİKA", "TDT", "KEİ", "D-8"], "a": "TÜRKSOY"},
        {"q": "Türkiye'nin Orta Asya ve Balkanlardaki ülkelere kalkınma yardımı yapmak için kurduğu kuruluş nedir?", "opts": ["TİKA (Türk İşbirliği ve Koordinasyon Ajansı)", "TÜRKSOY", "Yunus Emre Enstitüsü", "Maarif Vakfı", "Kızılay"], "a": "TİKA (Türk İşbirliği ve Koordinasyon Ajansı)"},
        {"q": "Yugoslavya'nın dağılmasıyla ortaya çıkan devletlerden biri değildir?", "opts": ["Arnavutluk (Zaten bağımsızdı)", "Bosna-Hersek", "Hırvatistan", "Sırbistan", "Makedonya"], "a": "Arnavutluk (Zaten bağımsızdı)"},
        {"q": "Bosna Savaşı'nda Sırpların Boşnaklara karşı uyguladığı soykırımın (Srebrenitsa) simge ismi, 'Bilge Kral' kimdir?", "opts": ["Aliya İzzetbegoviç", "Tito", "Mladiç", "Karaciç", "Miloseviç"], "a": "Aliya İzzetbegoviç"},
        {"q": "Bosna Savaşı'nı sona erdiren antlaşma (1995) hangisidir?", "opts": ["Dayton Antlaşması", "Paris Antlaşması", "Roma Antlaşması", "Helsinki Nihai Senedi", "Lizbon Antlaşması"], "a": "Dayton Antlaşması"},
        {"q": "Körfez Savaşı (1990-1991) hangi ülkenin Kuveyt'i işgaliyle başlamıştır?", "opts": ["Irak (Saddam Hüseyin)", "İran", "ABD", "Suriye", "İsrail"], "a": "Irak (Saddam Hüseyin)"},
        {"q": "Avrupa Ekonomik Topluluğu'nun (AET) adını Avrupa Birliği (AB) olarak değiştiren antlaşma (1992) hangisidir?", "opts": ["Maastricht Antlaşması", "Roma Antlaşması", "Kopenhag Kriterleri", "Lizbon Antlaşması", "Amsterdam Antlaşması"], "a": "Maastricht Antlaşması"},
        {"q": "Türkiye'nin AB ile Gümrük Birliği'ne girdiği tarih nedir?", "opts": ["1 Ocak 1996", "1999", "2005", "1963", "1987"], "a": "1 Ocak 1996"},
        {"q": "Türkiye'nin AB'ye 'Aday Ülke' statüsü kazandığı zirve (1999) hangisidir?", "opts": ["Helsinki Zirvesi", "Lüksemburg Zirvesi", "Kopenhag Zirvesi", "Brüksel Zirvesi", "Ankara Zirvesi"], "a": "Helsinki Zirvesi"},
        {"q": "28 Şubat 1997'de Milli Güvenlik Kurulu kararlarıyla yapılan müdahaleye ne ad verilir?", "opts": ["Post-Modern Darbe", "Muhtıra", "İhtilal", "E-Muhtıra", "Devrim"], "a": "Post-Modern Darbe"},
        {"q": "Türkiye'nin ilk kadın Başbakanı kimdir?", "opts": ["Tansu Çiller", "Benazir Butto", "Meral Akşener", "İmren Aykut", "Lale Aytaman"], "a": "Tansu Çiller"},
        {"q": "17 Ağustos 1999'da meydana gelen ve büyük yıkıma yol açan deprem hangisidir?", "opts": ["Marmara (Gölcük) Depremi", "Erzincan Depremi", "Van Depremi", "Düzce Depremi", "İzmir Depremi"], "a": "Marmara (Gölcük) Depremi"},
        {"q": "11 Eylül 2001'de ABD'de İkiz Kuleler'e yapılan terör saldırısını kim üstlenmiştir?", "opts": ["El-Kaide (Usame bin Ladin)", "IŞİD", "Taliban", "Boko Haram", "PKK"], "a": "El-Kaide (Usame bin Ladin)"},
        {"q": "ABD'nin 11 Eylül saldırıları sonrası işgal ettiği ülkeler hangileridir?", "opts": ["Afganistan ve Irak", "İran ve Suriye", "Libya ve Mısır", "Pakistan ve Hindistan", "Kuveyt ve Yemen"], "a": "Afganistan ve Irak"},
        {"q": "2002 yılından itibaren Türkiye'de tek başına iktidar olan parti hangisidir?", "opts": ["AK Parti (Adalet ve Kalkınma Partisi)", "CHP", "MHP", "DSP", "ANAP"], "a": "AK Parti (Adalet ve Kalkınma Partisi)"},
        {"q": "Türk Lirası'ndan 6 sıfırın atılması ve YTL'ye geçiş hangi yıl olmuştur?", "opts": ["2005", "2001", "2010", "2002", "1999"], "a": "2005"},
        {"q": "Türkiye'nin AB ile katılım müzakerelerine resmen başladığı tarih nedir?", "opts": ["3 Ekim 2005", "1999", "1996", "2010", "1963"], "a": "3 Ekim 2005"},
        {"q": "Kıbrıs'ta çözümü öngören ancak Rumların reddettiği plan (2004) nedir?", "opts": ["Annan Planı", "Dayton Planı", "Ahtisaari Planı", "Rogers Planı", "B planı"], "a": "Annan Planı"},
        {"q": "Arap Baharı (2010) ilk olarak hangi ülkede başlamıştır?", "opts": ["Tunus", "Mısır", "Libya", "Suriye", "Yemen"], "a": "Tunus"},
        {"q": "Suriye İç Savaşı ne zaman başlamıştır?", "opts": ["2011", "2010", "2015", "2003", "2001"], "a": "2011"},
        {"q": "15 Temmuz 2016'da Türkiye'de gerçekleşen olay nedir?", "opts": ["FETÖ Darbe Girişimi", "Gezi Olayları", "28 Şubat", "12 Eylül", "27 Nisan"], "a": "FETÖ Darbe Girişimi"},
        {"q": "Azerbaycan'ın Ermenistan işgalindeki Karabağ'ı kurtardığı savaş (2020) hangisidir?", "opts": ["II. Karabağ Savaşı (44 Gün Savaşı)", "Hocalı Savaşı", "Nahçıvan Savaşı", "Bakü Savaşı", "Şuşa Savaşı"], "a": "II. Karabağ Savaşı (44 Gün Savaşı)"},
        {"q": "Türkiye'nin yerli ve milli otomobili hangisidir?", "opts": ["TOGG", "Devrim", "Anadol", "Tofaş", "Murat"], "a": "TOGG"},
        {"q": "Türkiye'nin Karadeniz'den Rus doğalgazını aldığı boru hattı projesi nedir?", "opts": ["Mavi Akım", "TANAP", "TAP", "Bakü-Tiflis-Ceyhan", "Nabucco"], "a": "Mavi Akım"},
        {"q": "Azerbaycan petrolünü Türkiye üzerinden dünyaya taşıyan boru hattı hangisidir?", "opts": ["Bakü-Tiflis-Ceyhan (BTC)", "Mavi Akım", "Türk Akımı", "Kerkük-Yumurtalık", "TANAP"], "a": "Bakü-Tiflis-Ceyhan (BTC)"},
        {"q": "Küresel ısınmaya karşı sera gazı emisyonlarını azaltmayı hedefleyen uluslararası antlaşma nedir?", "opts": ["Kyoto Protokolü (ve Paris Anlaşması)", "Montreal Protokolü", "Viyana Sözleşmesi", "Cenevre Sözleşmesi", "Rio Sözleşmesi"], "a": "Kyoto Protokolü (ve Paris Anlaşması)"},
        {"q": "Dünyada internetin yaygınlaşması ve 'Bilgi Çağı'na geçiş hangi döneme denk gelir?", "opts": ["1990'lar ve sonrası", "1980'ler", "1970'ler", "2010'lar", "1960'lar"], "a": "1990'lar ve sonrası"},
        {"q": "Klonlanan ilk memeli hayvanın adı nedir?", "opts": ["Dolly (Koyun)", "Laika", "Garip", "Boncuk", "Pamuk"], "a": "Dolly (Koyun)"},
        {"q": "Nanoteknoloji nedir?", "opts": ["Maddenin atomik ve moleküler seviyede (çok küçük boyutta) kontrol edilmesi", "Uzay teknolojisi", "Robot teknolojisi", "Tarım teknolojisi", "Büyük makineler"], "a": "Maddenin atomik ve moleküler seviyede (çok küçük boyutta) kontrol edilmesi"},
        {"q": "2019'da Çin'de ortaya çıkan ve dünyayı etkileyen salgın hastalık nedir?", "opts": ["COVID-19 (Koronavirüs)", "SARS", "MERS", "Ebola", "İspanyol Gribi"], "a": "COVID-19 (Koronavirüs)"},
        {"q": "Türkiye'nin Nobel Ödülü alan ilk bilim insanı kimdir?", "opts": ["Aziz Sancar (Kimya)", "Orhan Pamuk (Edebiyat)", "Cahit Arf", "Gazi Yaşargil", "Oktay Sinanoğlu"], "a": "Aziz Sancar (Kimya)"},
        {"q": "Türkiye'nin Nobel Edebiyat Ödülü alan yazarı kimdir?", "opts": ["Orhan Pamuk", "Yaşar Kemal", "Elif Şafak", "Nazım Hikmet", "Ahmet Hamdi Tanpınar"], "a": "Orhan Pamuk"},
        {"q": "Avrupa Birliği'nin ortak para birimi nedir?", "opts": ["Euro", "Dolar", "Sterlin", "Mark", "Frank"], "a": "Euro"},
        {"q": "Birleşik Krallık'ın (İngiltere) AB'den ayrılması sürecine ne ad verilir?", "opts": ["Brexit", "Grexit", "Eurozone", "Schengen", "Maastricht"], "a": "Brexit"},
        {"q": "Dünya Ticaret Örgütü'nün (WTO) amacı nedir?", "opts": ["Uluslararası ticaretin serbestleşmesini sağlamak", "Petrol fiyatlarını belirlemek", "Savaşları önlemek", "Sağlığı korumak", "Eğitimi desteklemek"], "a": "Uluslararası ticaretin serbestleşmesini sağlamak"},
        {"q": "G-20 nedir?", "opts": ["Dünyanın en büyük 20 ekonomisinin oluşturduğu grup", "En fakir 20 ülke", "Savaşan 20 ülke", "AB ülkeleri", "NATO ülkeleri"], "a": "Dünyanın en büyük 20 ekonomisinin oluşturduğu grup"},
        {"q": "Şanghay İşbirliği Örgütü'nün (ŞİÖ) kurucuları kimlerdir?", "opts": ["Çin, Rusya, Kazakistan, Kırgızistan, Tacikistan", "ABD, İngiltere", "AB ülkeleri", "Türkiye, Azerbaycan", "Japonya, Kore"], "a": "Çin, Rusya, Kazakistan, Kırgızistan, Tacikistan"},
        {"q": "Türkiye'nin Somali, Katar gibi ülkelerde askeri üs kurması neyin göstergesidir?", "opts": ["Bölgesel ve küresel güç olma vizyonunun", "Sömürgeciliğin", "Savaş isteğinin", "NATO'nun zorlamasının", "Ekonomik krizin"], "a": "Bölgesel ve küresel güç olma vizyonunun"},
        {"q": "Mavi Vatan doktrini neyi savunur?", "opts": ["Türkiye'nin denizlerdeki hak ve menfaatlerini", "Uzay çalışmalarını", "Kara sınırlarını", "Hava sahasını", "Ormanları"], "a": "Türkiye'nin denizlerdeki hak ve menfaatlerini"},
        {"q": "Türkiye'nin ilk yerli sondaj gemisinin adı nedir?", "opts": ["Fatih", "Yavuz", "Kanuni", "Abdülhamid Han", "Barbaros"], "a": "Fatih"},
        {"q": "Türk savunma sanayisinin ürettiği İHA ve SİHA'ların (Bayraktar, ANKA) başarısı neyi değiştirmiştir?", "opts": ["Savaş konseptini ve Türkiye'nin askeri gücünü", "Sadece ticareti", "Tarımı", "Eğitimi", "Turizmi"], "a": "Savaş konseptini ve Türkiye'nin askeri gücünü"},
        {"q": "2023 yılında yaşanan Kahramanmaraş merkezli depremlere ne ad verilmiştir?", "opts": ["Asrın Felaketi", "Büyük Marmara Depremi", "Van Depremi", "Elazığ Depremi", "Ege Depremi"], "a": "Asrın Felaketi"},
        {"q": "Türkiye'nin uzaya gönderdiği ilk astronot kimdir?", "opts": ["Alper Gezeravcı", "Vecihi Hürkuş", "Nuri Demirağ", "Sabiha Gökçen", "Hezarfen Ahmet"], "a": "Alper Gezeravcı"},
        {"q": "Dünyada yapay zeka (AI) teknolojisinin gelişmesi hangi çağı başlatmıştır?", "opts": ["Dijital Çağ (Endüstri 4.0 / 5.0)", "Uzay Çağı", "Atom Çağı", "Cilalı Taş Devri", "Demir Çağı"], "a": "Dijital Çağ (Endüstri 4.0 / 5.0)"},
        {"q": "Yenilenebilir enerji kaynakları (Güneş, Rüzgar) neden önem kazanmıştır?", "opts": ["İklim değişikliğiyle mücadele ve sürdürülebilirlik için", "Daha pahalı olduğu için", "Kömür bittiği için", "Moda olduğu için", "Zorunlu olduğu için"], "a": "İklim değişikliğiyle mücadele ve sürdürülebilirlik için"},
        {"q": "Medeniyetler İttifakı projesinin eş başkanları hangi ülkelerdir?", "opts": ["Türkiye ve İspanya", "ABD ve İngiltere", "Rusya ve Çin", "Almanya ve Fransa", "İtalya ve Yunanistan"], "a": "Türkiye ve İspanya"}
    ]
}

THEME = get_theme()

# --- 4. CSS DÜZENLEMELERİ ---
if st.session_state.get('page') == 'quiz':
    bg_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Vienna_Battle_1683.jpg/1280px-Vienna_Battle_1683.jpg"
    opacity = "0.2"
else:
    bg_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Reprise_ch%C3%A2teau_Buda_1686.jpg/2560px-Reprise_ch%C3%A2teau_Buda_1686.jpg"
    opacity = "0.5"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Montserrat:wght@600;800&family=Brush+Script+MT&display=swap');

    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,{opacity}), rgba(0,0,0,{opacity})), url("{bg_url}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    .block-container {{ padding-top: 3rem !important; max-width: 98% !important; }}
    .stDeployButton {{ display: none; }}

    div.stButton > button:not([kind="primary"]) {{
        width: 100% !important; height: auto !important; min-height: 50px !important;
        border-radius: 10px !important; font-size: 18px !important;
        background: linear-gradient(135deg, #800000 0%, #4a0000 100%) !important;
        color: #FFD700 !important; border: 2px solid #FFD700 !important;
        font-family: 'Montserrat', sans-serif !important; font-weight: 800 !important;
        margin: 5px 0 !important; box-shadow: 0 5px 15px rgba(0,0,0,0.5);
    }}
    div.stButton > button:not([kind="primary"]):hover {{ transform: scale(1.02); filter: brightness(1.2); border-color: white !important; }}

    .profile-img {{ width: 130px; height: 130px; border-radius: 15px; border: 3px solid {THEME.get('gold_color')}; object-fit: cover; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }}
    .header-box {{ background: linear-gradient(90deg, #1a2e22, #2F4F2F); border: 2px solid {THEME.get('gold_color')}; border-radius: 15px; padding: 15px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }}
    .crown-title {{ color: {THEME.get('gold_color')}; font-weight: bold; font-size: 24px; }}
    .main-title {{ font-family: 'Cinzel'; color: white; margin: 0; font-size: 48px; text-shadow: 2px 2px 5px black; }}
    .admin-stat-box {{ background-color: #2e1a1a; padding: 15px; border-radius: 10px; border: 1px solid #FFD700; text-align: center; }}
    .admin-stat-value {{ font-size: 24px; font-weight: bold; color: white; }}
    .admin-stat-label {{ font-size: 14px; color: #ccc; }}
    
    /* GÜNCELLENEN LEADERBOARD CSS (YARI OPAK) */
    .leaderboard-container {{ 
        background-color: rgba(30, 60, 47, 0.9); 
        border: 2px solid #DAA520; 
        border-radius: 10px; 
        padding: 8px 15px; 
        margin-bottom: 15px; 
        display: flex; 
        justify-content: center; 
        gap: 15px; 
        align-items: center; 
        box-shadow: 0 5px 10px rgba(0,0,0,0.5); 
    }}
    .leader-badge {{ color: white; font-size: 14px; font-weight: bold; display: flex; align-items: center; gap: 5px; }}
    .leader-xp {{ color: #FFD700; margin-left: 3px; font-size: 12px; }}
    .announcement-solid {{ background-color: #800000; color: white; padding: 10px; border-radius: 8px; border: 2px solid gold; text-align: center; font-weight: bold; margin-bottom: 15px; }}

    /* YENİ EKLENEN CSS: İMZA VE BRE GAFİL ANIMASYONU (DÜZELTİLMİŞ) */
    .bre-gafil {{
        font-size: 60px; color: #B22222; text-align: center; font-weight: 900; animation: shake 0.6s; margin: 30px 0; font-family: 'Cinzel', serif; text-shadow: 2px 2px 0px #000;
    }}
    @keyframes shake {{
        0% {{ transform: translate(1px, 1px) rotate(0deg); }}
        10% {{ transform: translate(-1px, -2px) rotate(-1deg); }}
        20% {{ transform: translate(-3px, 0px) rotate(1deg); }}
        30% {{ transform: translate(3px, 2px) rotate(0deg); }}
        40% {{ transform: translate(1px, -1px) rotate(1deg); }}
        50% {{ transform: translate(-1px, 2px) rotate(-1deg); }}
        60% {{ transform: translate(-3px, 1px) rotate(0deg); }}
        70% {{ transform: translate(3px, 1px) rotate(-1deg); }}
        80% {{ transform: translate(-1px, -1px) rotate(1deg); }}
        90% {{ transform: translate(1px, 2px) rotate(0deg); }}
        100% {{ transform: translate(1px, -2px) rotate(-1deg); }}
    }}
</style>
""", unsafe_allow_html=True)

# --- STATE ---
if 'user' not in st.session_state: st.session_state.user = None
if 'xp' not in st.session_state: st.session_state.xp = 0
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'current_ogm_page' not in st.session_state: st.session_state.current_ogm_page = None
if 'show_bre_gafil' not in st.session_state: st.session_state.show_bre_gafil = False

if st.session_state.user: update_user_activity(st.session_state.user)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 👤 KİMLİK")
    if st.session_state.user and st.session_state.user != "ADMIN": 
        st.success(f"Hoşgeldin, {st.session_state.user}")
    
    with st.expander("👑 YÖNETİCİ", expanded=(st.session_state.user == "ADMIN")):
        if st.session_state.user != "ADMIN":
            with st.form("admin_form"):
                p = st.text_input("Şifre", type="password"); 
                if st.form_submit_button("GİRİŞ"):
                    if p == "admin123": st.session_state.user = "ADMIN"; st.rerun()
                    else: st.error("Hatalı!")
        else:
            if st.button("Çıkış"): st.session_state.user=None; st.rerun()
            st.markdown("---")
            if st.button("📊 ANALİZ PANELİNE GİT"): st.session_state.page = 'admin_panel'; st.rerun()
    
    st.markdown("### 👥 AKTİF LİSTE")
    ud = get_all_users_status()
    now_t = datetime.now()
    for _, r in ud.iterrows():
        on = False
        if r['last_seen']:
            try:
                last = datetime.strptime(r['last_seen'], "%Y-%m-%d %H:%M:%S")
                if (now_t - last).total_seconds() < 600: on = True
            except: pass
        if r['username'] == st.session_state.user: on = True
        st.markdown(f"{'🟢' if on else '⚪'} **{r['username']}**")

# --- LOGIN ---
if st.session_state.page == 'login':
    c1,c2,c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center; color:#FFD700; text-shadow: 2px 2px 4px black;'>TARİH LİGİ</h1>", unsafe_allow_html=True)
        u = st.text_input("Adın:", label_visibility="collapsed", placeholder="Adınızı giriniz...")
        if st.button("GİRİŞ YAP", type="primary", use_container_width=True): 
            conn=get_db();c=conn.cursor();
            c.execute("INSERT OR IGNORE INTO users (username,xp,total_questions,last_seen, active_seconds) VALUES (?,0,0,?, 0)",(u,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit();conn.close()
            st.session_state.user=u; st.session_state.page='home'; st.rerun()

# --- ADMIN PANEL ---
elif st.session_state.page == 'admin_panel' and st.session_state.user == "ADMIN":
    st.markdown("<h2 style='color:#FFD700; text-align:center;'>👑 YÖNETİCİ KOÇLUK PANELİ</h2>", unsafe_allow_html=True)
    if st.button("🏠 Ana Sayfaya Dön"): st.session_state.page = 'home'; st.rerun()
    
    users_df = get_all_users_status()
    user_list = users_df['username'].tolist()
    selected_student = st.selectbox("Analiz Edilecek Öğrenciyi Seç:", user_list)
    
    if selected_student:
        mistakes, stats = get_detailed_user_report(selected_student)
        if not stats.empty:
            xp = stats.iloc[0]['xp']
            total_q = stats.iloc[0]['total_questions']
            seconds = stats.iloc[0]['active_seconds']
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            time_str = f"{hours} Saat {minutes} Dk"
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='admin-stat-box'><div class='admin-stat-value'>{xp}</div><div class='admin-stat-label'>Toplam XP</div></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='admin-stat-box'><div class='admin-stat-value'>{total_q}</div><div class='admin-stat-label'>Çözülen Soru</div></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='admin-stat-box'><div class='admin-stat-value'>{time_str}</div><div class='admin-stat-label'>Aktif Çalışma Süresi</div></div>", unsafe_allow_html=True)
            
            st.write("")
            st.markdown("### ⚠️ Son 60 Hatalı Cevap Analizi")
            if not mistakes.empty: st.dataframe(mistakes, use_container_width=True)
            else: st.info("Bu öğrencinin kayıtlı hatası bulunmamaktadır.")
            
            st.write("")
            with st.form("admin_msg"):
                msg_txt = st.text_area("Öğrenciye Özel Tavsiye/Mesaj Gönder:")
                if st.form_submit_button("Gönder"):
                    send_message(selected_student, msg_txt)
                    st.success("Mesaj iletildi.")

# --- HOME ---
elif st.session_state.page == 'home':
    for i, m in get_unread_messages(st.session_state.user): st.toast(f"📜 {m}", icon="👑"); mark_message_read(i)
    
    c_p, c_h = st.columns([0.8, 5])
    with c_p:
        img_src = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        if os.path.exists("profil.jpg"):
            with open("profil.jpg", "rb") as f: img_src = f"data:image/jpg;base64,{base64.b64encode(f.read()).decode()}"
        st.markdown(f'<img src="{img_src}" class="profile-img">', unsafe_allow_html=True)
    with c_h:
        # İMZA BURAYA EKLENDİ
        st.markdown(f"""<div class="header-box">
        <div style="font-family: 'Brush Script MT', cursive; font-size: 32px; color: #DAA520; margin-bottom:-15px; text-shadow: 1px 1px 2px black;">Alperen Süngü</div>
        <div class="crown-title">{THEME.get('crown_text')}</div><h1 class="main-title">{THEME.get('app_title')}</h1></div>""", unsafe_allow_html=True)

    if st.session_state.user != "ADMIN":
        with st.expander("📨 Yöneticiye Mesaj Gönder"):
            with st.form("quick_msg", clear_on_submit=True):
                um = st.text_input("Mesajınız:"); 
                if st.form_submit_button("Gönder"): send_message(st.session_state.user, "ADMIN", um); st.success("İletildi!")

    top5 = get_all_users_status().head(5)
    medals = ["🥇", "🥈", "🥉", "4.", "5."]
    lh = '<div class="leaderboard-container">'
    if top5.empty: lh += "<span style='color:white'>Veri yok</span>"
    else:
        for i, row in enumerate(top5.itertuples(), 0):
            if i < 5: lh += f'<div class="leader-badge">{medals[i]} {row.username} <span class="leader-xp">({row.xp} XP)</span></div>'
    lh += '</div>'
    st.markdown(lh, unsafe_allow_html=True)

    d_msg = get_sys_val("duyuru", "Hoşgeldiniz!")
    if st.session_state.user == "ADMIN":
        nm = st.text_input("Duyuru:", value=d_msg)
        if st.button("Kaydet (Duyuru)"): set_sys_val("duyuru", nm); st.rerun()
        d_msg = nm
    st.markdown(f"<div class='announcement-solid'>📢 {d_msg}</div>", unsafe_allow_html=True)

    if st.button("📚 KONU ÇALIŞMA ODASI", type="primary", use_container_width=True): st.session_state.page='study'; st.rerun()

    st.write("") 
    modules = get_modules()
    with st.container():
        st.markdown('<div style="max-width: 900px; margin: 0 auto;">', unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="small")
        cols = [col1, col2]
        for i, m in enumerate(modules):
            with cols[i % 2]:
                if st.button(f"{m['icon']} {m['title']}", key=m['module_key']):
                    st.session_state.quiz_topic = m['module_key']
                    raw_questions = SORU_HAVUZU.get(m['module_key'], [])
                    if not raw_questions: st.warning("Bu konu için henüz soru eklenmedi!")
                    else:
                        st.session_state.quiz_q = raw_questions[:]
                        random.shuffle(st.session_state.quiz_q)
                        st.session_state.q_idx=0; st.session_state.score=0; st.session_state.page='quiz'; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    c_out1, c_out2, c_out3 = st.columns([2, 1, 2])
    with c_out2:
        if st.button("ÇIKIŞ YAP", use_container_width=True): st.session_state.user=None; st.session_state.page='login'; st.rerun()

# --- STUDY ---
elif st.session_state.page == 'study':
    st.markdown("<div class='announcement-solid'>📚 TARİH ARAŞTIRMA MERKEZİ</div>", unsafe_allow_html=True)
    if st.button("⬅ ANA MENÜYE DÖN"): st.session_state.page='home'; st.session_state.current_ogm_page = None; st.rerun()
    
    secilen_konu = st.selectbox("Çalışmak istediğin konuyu seç:", list(KONU_AYARLARI.keys()))
    
    if secilen_konu:
        data = KONU_AYARLARI[secilen_konu]
        view_mode = st.radio("Görünüm Seçiniz:", ["📖 DERS KİTABI (MEB)", "🌍 DİJİTAL ANSİKLOPEDİ (KAPSAMLI)"], horizontal=True, label_visibility="collapsed")
        st.write("")

        if view_mode == "📖 DERS KİTABI (MEB)":
            components.html("""<script>window.onload = function(){try{window.frameElement.scrollIntoView({behavior:'smooth',block:'center'});}catch(e){}};</script>""", height=0)
            if data["ogm_pages"]:
                page_range = data["ogm_pages"]
                min_p, max_p = page_range.start, page_range.stop - 1
                if st.session_state.current_ogm_page is None or st.session_state.current_ogm_page not in page_range:
                    st.session_state.current_ogm_page = min_p
                page_left = st.session_state.current_ogm_page
                page_right = page_left + 1
                
                col1, col2 = st.columns(2)
                with col1: st.image(f"{OGM_IMG_BASE}{page_left}.jpg", caption=f"Sayfa {page_left}", use_container_width=True)
                with col2:
                    if page_right <= max_p: st.image(f"{OGM_IMG_BASE}{page_right}.jpg", caption=f"Sayfa {page_right}", use_container_width=True)
                
                c_prev, c_mid, c_next = st.columns([1, 2, 1])
                with c_prev:
                    if page_left > min_p:
                        if st.button("⬅ Önceki"): st.session_state.current_ogm_page -= 2; st.rerun()
                with c_next:
                    if page_right < max_p:
                        if st.button("Sonraki ➡"): st.session_state.current_ogm_page += 2; st.rerun()
            else: st.warning("Bu konu için OGM Kitap içeriği tanımlanmadı.")
        else:
            if data["wiki"]:
                with st.spinner("Kaynaklar derleniyor..."):
                    content_html = get_wiki_content_by_url(data["wiki"])
                    components.html(content_html, height=600, scrolling=True)
            else: st.info("Ansiklopedi kaynağı bulunamadı.")

# --- QUIZ ---
elif st.session_state.page == 'quiz':
    idx=st.session_state.q_idx; qs=st.session_state.quiz_q
    
    # 1. DURUM: BRE GAFİL EKRANI
    if st.session_state.show_bre_gafil:
        st.markdown('<div class="bre-gafil">BRE GAFİL! 😡</div>', unsafe_allow_html=True)
        st.error(f"Hocan öğretmedi mi?! Diğer soruya geç!")
        if st.button("Sıradaki Soruya Geç ➡️", type="primary"):
            st.session_state.show_bre_gafil = False
            st.session_state.q_idx += 1
            st.rerun()

    # 2. DURUM: NORMAL SORU EKRANI
    elif idx < len(qs):
        st.markdown(f"<div class='announcement-solid' style='background:#1e3c2f'>SORU {idx+1}/{len(qs)} | PUAN: {st.session_state.score}</div>", unsafe_allow_html=True)
        q = qs[idx]
        st.markdown(f"<div style='background:rgba(255,255,255,0.9);padding:20px;border-radius:10px;border:3px solid #8B0000;text-align:center;color:black;margin-bottom:10px'><h3>{q['q']}</h3></div>", unsafe_allow_html=True)
        ch = st.radio("Cevap:", q['opts'], key=f"q_{idx}", label_visibility="collapsed")
        st.write("")
        if st.button("YANITLA 🚀", type="primary", use_container_width=True):
            corr = (ch == q['a'])
            log_attempt(st.session_state.user, st.session_state.quiz_topic, q['q'], ch, corr)
            if corr:
                st.balloons(); st.session_state.score+=10; st.session_state.xp+=10
                update_user_xp(st.session_state.user, st.session_state.xp)
                st.success("DOĞRU! +10 XP")
                time.sleep(1); st.session_state.q_idx+=1; st.rerun()
            else:
                # BRE GAFİL MODUNA GEÇİŞ
                st.session_state.show_bre_gafil = True
                st.rerun()
    
    # 3. DURUM: OYUN BİTTİ
    else:
        st.balloons()
        st.markdown(f"<div class='announcement-solid'>BİTTİ! Toplam Puan: {st.session_state.score}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("🏠 ANA MENÜYE DÖN", use_container_width=True):
        st.session_state.page = 'home'; st.session_state.show_bre_gafil = False; st.rerun()