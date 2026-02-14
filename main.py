import discord
import os
import asyncio
import datetime
import aiohttp
from flask import Flask
from threading import Thread

# --- RENDER İÇİN WEB SUNUCU ---
app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# Environment Variables
TOKEN = os.getenv("TOKEN")
TARGET_ID = os.getenv("TARGET_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BEKLEME_SURESI = int(os.getenv("BEKLEME_SURESI", 1))

class MyBot(discord.Client):
    def __init__(self):
        # Hata veren Intents kısmını kaldırdık, self-bot için böyle daha stabil
        super().__init__()
        self.son_mesaj_vakti = None
        self.son_mesaj_icerik = "Mesaj bulunamadı"
        self.son_mesaj_linki = ""
        self.bildirim_gonderildi = False

    async def on_ready(self):
        print(f"------------------------------------")
        print(f"Giriş Başarılı: {self.user}")
        print(f"Hedef ID: {TARGET_ID}")
        print(f"Süre: {BEKLEME_SURESI} dakika")
        print(f"------------------------------------")
        self.loop.create_task(self.takip_dongusu())

    async def on_message(self, message):
        if str(message.author.id) == str(TARGET_ID):
            self.son_mesaj_vakti = discord.utils.utcnow()
            self.son_mesaj_icerik = message.content if message.content else "(Görsel/Dosya)"
            
            if message.guild:
                self.son_mesaj_linki = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
            else:
                self.son_mesaj_linki = "DM Mesajı"
                
            self.bildirim_gonderildi = False
            print(f"Yeni mesaj yakalandı, sayaç sıfırlandı.")

    async def takip_dongusu(self):
        await self.wait_until_ready()
        while not self.is_closed():
            if self.son_mesaj_vakti and not self.bildirim_gonderildi:
                simdi = discord.utils.utcnow()
                gecen_saniye = (simdi - self.son_mesaj_vakti).total_seconds()
                
                if gecen_saniye >= (BEKLEME_SURESI * 60):
                    vakit_str = self.son_mesaj_vakti.strftime('%H:%M:%S')
                    bildirim = (
                        f"⚠️ **SESSİZLİK TESPİT EDİLDİ**\n"
                        f"👤 **Kullanıcı:** <@{TARGET_ID}>\n"
                        f"⏳ **Süre:** {BEKLEME_SURESI} dakikadır mesaj yok.\n"
                        f"🕒 **Son Mesaj Saati:** {vakit_str}\n"
                        f"📝 **Son Mesaj:** {self.son_mesaj_icerik}\n"
                        f"🔗 **Git:** [Mesaja Git]({self.son_mesaj_linki})"
                    )
                    await self.webhook_gonder(bildirim)
                    self.bildirim_gonderildi = True
                    print(f"Bildirim gönderildi.")
            
            await asyncio.sleep(15)

    async def webhook_gonder(self, icerik):
        async with aiohttp.ClientSession() as session:
            payload = {"content": icerik}
            try:
                async with session.post(WEBHOOK_URL, json=payload) as resp:
                    return resp.status == 204
            except Exception as e:
                print(f"Webhook Hatası: {e}")

if __name__ == "__main__":
    if TOKEN:
        keep_alive()
        client = MyBot()
        client.run(TOKEN)
    else:
        print("TOKEN bulunamadı!")
