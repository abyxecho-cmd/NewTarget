import discord
import os
import asyncio
import datetime
import aiohttp
from flask import Flask
from threading import Thread

# --- RENDER WEB SUNUCU ---
app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# Environment Variables
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BEKLEME_SURESI = int(os.getenv("BEKLEME_SURESI", 1))
TARGET_IDS = os.getenv("TARGET_ID", "").split(",")

# Etiketlenecek senin hesapların
HESAP_1 = "1416866481018241044"
HESAP_2 = "1411681601846378599"

class MyBot(discord.Client):
    def __init__(self):
        super().__init__()
        self.takip_verisi = {}
        for uid in TARGET_IDS:
            uid = uid.strip()
            if uid:
                self.takip_verisi[uid] = {
                    "vakit": None,
                    "icerik": "Mesaj bulunamadı",
                    "link": "",
                    "bildirildi": False
                }

    async def on_ready(self):
        print(f"------------------------------------")
        print(f"Giriş Başarılı: {self.user}")
        print(f"Takip Edilen Sayısı: {len(self.takip_verisi)}")
        print(f"------------------------------------")
        self.loop.create_task(self.takip_dongusu())

    async def on_message(self, message):
        uid = str(message.author.id)
        if uid in self.takip_verisi:
            self.takip_verisi[uid]["vakit"] = discord.utils.utcnow()
            self.takip_verisi[uid]["icerik"] = message.content if message.content else "(Görsel/Dosya)"
            
            if message.guild:
                self.takip_verisi[uid]["link"] = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
            else:
                self.takip_verisi[uid]["link"] = "DM Mesajı"
                
            self.takip_verisi[uid]["bildirildi"] = False

    async def takip_dongusu(self):
        await self.wait_until_ready()
        while not self.is_closed():
            simdi = discord.utils.utcnow()
            for uid, data in self.takip_verisi.items():
                if data["vakit"] and not data["bildirildi"]:
                    gecen_saniye = (simdi - data["vakit"]).total_seconds()
                    
                    if gecen_saniye >= (BEKLEME_SURESI * 60):
                        vakit_str = data["vakit"].strftime('%H:%M:%S')
                        # Bildirim metni: Hedef ID sadece yazı olarak kalır, senin hesapların etiketlenir.
                        bildirim = (
                            f"🔔 <@{HESAP_1}> <@{HESAP_2}>\n"
                            f"⚠️ **SESSİZLİK TESPİT EDİLDİ**\n"
                            f"👤 **Kullanıcı ID:** `{uid}`\n"
                            f"⏳ **Süre:** {BEKLEME_SURESI} dakikadır mesaj yok.\n"
                            f"🕒 **Son Mesaj Saati:** {vakit_str}\n"
                            f"📝 **Son Mesaj:** {data['icerik']}\n"
                            f"🔗 **Git:** [Mesaja Git]({data['link']})"
                        )
                        await self.webhook_gonder(bildirim)
                        data["bildirildi"] = True
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
