import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import json
import os
import random
import logging
import google.generativeai as genai # กลับมาใช้ SDK เดิมที่เสถียร
from flask import Flask
from threading import Thread

# ==========================================
# 🌐 Web Server สำหรับ Uptime
# ==========================================
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# ⚙️ การตั้งค่าหลัก
# ==========================================
logging.basicConfig(level=logging.INFO)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='-', intents=intents)

# ชื่อยศและห้อง (ตามที่ระบุ)
PUBLIC_CHANNEL = "ห้องแนะนำตัว"
CHANNEL_LEAVE = "ห้องแจ้งลา"        
ALLOWED_CHANNEL_FORTUNE = "ห้องเช็คดวง"
ROLE_ADMIN_CHECK = "‹ 𝑆𝑦𝑠𝑡𝑒𝑚 𝐴𝑑𝑚𝑖𝑛 ⚖️ ›" 
ROLE_VERIFIED = "‹ แนะนำตัวแล้ว ›"
ROLE_WWM = "ข้าคือจอมยุทธ์เด๊ะ"
ROLE_DPS = "DPS ⚔️"
ROLE_HEALER = "หมอ💉🩺"
ROLE_TANK = "แทงค์ 🛡️"
ROLE_HYBRID = "ไฮบริด 🧬"

# AI Setup (รุ่นเดิมที่เสถียร)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 📜 ระบบจัดการใบลา (แก้ไขลบข้อความอัตโนมัติ)
# ==========================================
class LeaveApprovalView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    async def interaction_check(self, interaction):
        if discord.utils.get(interaction.user.roles, name=ROLE_ADMIN_CHECK): return True
        await interaction.response.send_message("⛔ เฉพาะ Admin เท่านั้น", ephemeral=True)
        return False

    @discord.ui.button(label="อนุมัติ", style=discord.ButtonStyle.success, custom_id="approve")
    async def approve(self, interaction, button):
        emb = interaction.message.embeds[0].copy()
        emb.color = 0x2ecc71
        emb.set_field_at(3, name="📋 สถานะ", value=f"✅ อนุมัติโดย {interaction.user.mention}", inline=False)
        await interaction.response.edit_message(embed=emb, view=None)

    @discord.ui.button(label="ไม่อนุมัติ", style=discord.ButtonStyle.danger, custom_id="deny")
    async def deny(self, interaction, button):
        emb = interaction.message.embeds[0].copy()
        emb.color = 0xe74c3c
        emb.set_field_at(3, name="📋 สถานะ", value=f"❌ ไม่อนุมัติโดย {interaction.user.mention}", inline=False)
        await interaction.response.edit_message(embed=emb, view=None)

class LeaveModal(discord.ui.Modal, title="📜 แบบฟอร์มขอลา"):
    char = discord.ui.TextInput(label="ชื่อตัวละคร", required=True)
    l_type = discord.ui.TextInput(label="ประเภทการลา", required=True)
    l_date = discord.ui.TextInput(label="วันที่", required=True)
    reason = discord.ui.TextInput(label="เหตุผล", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction):
        embed = discord.Embed(title="📩 มีสาส์นขอลาหยุด!", color=0xf1c40f)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 จอมยุทธ์", value=self.char.value, inline=False)
        embed.add_field(name="📌 ประเภท", value=self.l_type.value, inline=False)
        embed.add_field(name="📅 วันที่/เวลา", value=self.l_date.value, inline=False)
        embed.add_field(name="📋 สถานะ", value="⏳ รอตรวจสอบ", inline=False)
        embed.set_footer(text=f"ยื่นเรื่องเมื่อ: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        await interaction.channel.send(content=f"**ผู้ยื่นเรื่อง:** {interaction.user.mention}", embed=embed, view=LeaveApprovalView())
        # ลบข้อความตอบกลับอัตโนมัติใน 5 วินาที
        await interaction.response.send_message("✅ ส่งใบลาแล้ว ข้อความนี้จะถูกลบอัตโนมัติ", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.delete_original_response()

class LeaveButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 เขียนใบลา", style=discord.ButtonStyle.danger, custom_id="write_leave")
    async def write(self, interaction, button): await interaction.response.send_modal(LeaveModal())

# ==========================================
# 🆕 ระบบแนะนำตัว (แก้ไขรูปภาพและปุ่ม)
# ==========================================
class IntroModal(discord.ui.Modal, title="📝 แนะนำตัว"):
    name = discord.ui.TextInput(label="ชื่อเล่น", required=True)
    age = discord.ui.TextInput(label="อายุ", required=True)
    async def on_submit(self, interaction):
        await interaction.response.send_message("🎮 เลือกเกมที่ท่านเล่น:", view=GameSelect({"n": self.name.value, "a": self.age.value}), ephemeral=True)

class GameSelect(discord.ui.View):
    def __init__(self, data): super().__init__(); self.data = data
    @discord.ui.select(options=[discord.SelectOption(label="Where Winds Meet", emoji="⚔️"), discord.SelectOption(label="อื่นๆ", emoji="🎮")])
    async def select(self, interaction, select):
        self.data["g"] = select.values[0]
        if self.data["g"] == "Where Winds Meet":
            modal = discord.ui.Modal(title="⚔️ ข้อมูล WWM")
            ign = discord.ui.TextInput(label="ชื่อในเกม")
            modal.add_item(ign)
            async def wwm_submit(it):
                self.data["ign"] = ign.value
                await it.response.send_message("🛡️ เลือกอาชีพ:", view=ClassSelect(self.data), ephemeral=True)
            modal.on_submit = wwm_submit
            await interaction.response.send_modal(modal)
        else: await finalize_intro(interaction, self.data)

class ClassSelect(discord.ui.View):
    def __init__(self, data): super().__init__(); self.data = data
    @discord.ui.select(options=[discord.SelectOption(label="ดาเมจ"), discord.SelectOption(label="หมอ"), discord.SelectOption(label="แทงค์"), discord.SelectOption(label="ไฮบริด")])
    async def callback(self, interaction, select):
        self.data["c"] = select.values[0]
        await finalize_intro(interaction, self.data)

async def finalize_intro(interaction, data):
    user, guild = interaction.user, interaction.guild
    pub_ch = discord.utils.get(guild.text_channels, name=PUBLIC_CHANNEL)
    
    # ลบข้อความเก่าและปุ่มเก่า
    if pub_ch:
        async for m in pub_ch.history(limit=50):
            if m.author == bot.user and (user.name in str(m.embeds[0].footer.text if m.embeds else "") or "ยืนยันตัวตน" in str(m.embeds[0].title if m.embeds else "")):
                await m.delete()

    # ยศและชื่อ
    roles = [discord.utils.get(guild.roles, name=ROLE_VERIFIED)]
    icon = ""
    if data.get("g") == "Where Winds Meet":
        roles.append(discord.utils.get(guild.roles, name=ROLE_WWM))
        cls_map = {"ดาเมจ": (ROLE_DPS, "⚔️"), "หมอ": (ROLE_HEALER, "💉"), "แทงค์": (ROLE_TANK, "🛡️"), "ไฮบริด": (ROLE_HYBRID, "🧬")}
        rn, icon = cls_map.get(data.get("c"), (None, ""))
        roles.append(discord.utils.get(guild.roles, name=rn))
    
    await user.add_roles(*[r for r in roles if r])
    try: await user.edit(nick=f"{icon} {user.name} ({data['n']})")
    except: pass

    # ส่ง Embed และปุ่มใหม่ลงล่างสุด
    embed = discord.Embed(title="✅ สมาชิกใหม่รายงานตัว!", color=0xffd700)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.description = f"**ชื่อ :** {data['n']}\n**อายุ :** {data['a']}\n**เกม :** {data['g']}"
    if "ign" in data: embed.description += f"\n**IGN :** {data['ign']}\n**อาชีพ :** {data['c']}"
    embed.set_footer(text=f"แนะนำตัวโดย {user.name}")
    
    await pub_ch.send(embed=embed)
    await pub_ch.send(embed=discord.Embed(title="📢 ยืนยันตัวตน / แนะนำตัว", description="กดปุ่มด้านล่างเพื่อลงทะเบียน 👇", color=0x00ff00), view=IntroButton())
    await interaction.response.edit_message(content="✅ สำเร็จ!", view=None)

class IntroButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 กดเพื่อเริ่มแนะนำตัว", style=discord.ButtonStyle.green, custom_id="start_intro")
    async def start(self, interaction, button): await interaction.response.send_modal(IntroModal())

# ==========================================
# 🛠️ คำสั่งระบบ
# ==========================================
@bot.command()
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("✅ Sync All Commands Success!")

@bot.tree.command(name="ถาม", description="🤖 คุยกับ AI")
async def ask(interaction, question: str):
    await interaction.response.defer()
    try:
        response = ai_model.generate_content(question)
        await interaction.followup.send(embed=discord.Embed(title="🗣️ AI ตอบว่า:", description=response.text[:1900], color=0x00ffcc))
    except Exception as e: await interaction.followup.send(f"❌ Error: {e}")

@bot.tree.command(name="เช็ครุ่นไอเอ", description="🔍 ดูรุ่น AI")
async def check_ai(interaction):
    txt = "- gemini-1.5-flash 🟢 (Active)\n- gemini-1.5-pro ⚪\n- gemini-2.0-flash-exp ⚪"
    await interaction.response.send_message(embed=discord.Embed(title="🤖 AI Support", description=txt), ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(IntroButton())
    bot.add_view(LeaveButton())
    bot.add_view(LeaveApprovalView())
    await bot.tree.sync()
    print(f"🚀 {bot.user} พร้อม!")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
