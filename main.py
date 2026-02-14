import discord
import os
import asyncio
import datetime
import aiohttp
from flask import Flask
from threading import Thread

# --- RENDER İÇİN WEB SUNUCU (KAPANMAYI ÖNLER) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot Calisiyor!"

def run():
    # Render varsayılan olarak 8080 portunu kullanır
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# -----------------------------------------------

# Render Environment Variables (Ortam Değişkenleri)
TOKEN = os.getenv("TOKEN")
TARGET_ID = os.getenv("TARGET_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

class MyBot(discord.Client):
    def __init__(self):
        # discord.py-self için gerekli izinler
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.son_mesaj_vakti = None
        self.bildirim_gonderildi = False

    async def on_ready(self):
        print(f"------------------------------------")
        print(f"Giris Yapildi: {self.user}")
        print(f"Takip Edilen ID: {TARGET_ID}")
        print(f"------------------------------------")
        # Arka planda çalışan kontrol döngüsünü başlat
        self.loop.create_task(self.takip_dongusu())

    async def on_message(self, message):
        # Eğer mesajı atan kişi hedef kullanıcı ise
        if str(message.author.id) == str(TARGET_ID):
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Hedef mesaj atti.")
            self.son_mesaj_vakti = discord.utils.utcnow()
            self.bildirim_gonderildi = False

    async def takip_dongusu(self):
        await self.wait_until_ready()
        while not self.is_closed():
            if self.son_mesaj_vakti and not self.bildirim_gonderildi:
                gecen_sure = (discord.utils.utcnow() - self.son_mesaj_vakti).total_seconds()
                
                # Örnek: 60 saniye (1 dakika) boyunca mesaj atmazsa bildirim gönder
                if gecen_sure >= 60:
                    await self.webhook_gonder(f"🔴 **DURDU** - <@{TARGET_ID}> 1 dakikadir mesaj atmiyor.")
                    self.bildirim_gonderildi = True
                    print("Sessizlik bildirimi webhook ile gonderildi.")
            
            # Her 15 saniyede bir kontrol et
            await asyncio.sleep(15)

    async def webhook_gonder(self, icerik):
        async with aiohttp.ClientSession() as session:
            payload = {"content": icerik}
            try:
                async with session.post(WEBHOOK_URL, json=payload) as resp:
                    return resp.status == 204
            except Exception as e:
                print(f"Webhook Hatasi: {e}")

if __name__ == "__main__":
    if not TOKEN or not WEBHOOK_URL:
        print("HATA: TOKEN veya WEBHOOK_URL bulunamadi! Render Environment ayarlarini kontrol edin.")
    else:
        keep_alive() # Flask sunucusunu baslat
        client = MyBot()
        try:
            client.run(TOKEN)
        except Exception as e:
            print(f"Bot Calistirma Hatasi: {e}")
