import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import json
import os
import random
import logging
from google import genai
from google.genai import types
from keep_alive import keep_alive

# ==========================================
# 📝 ตั้งค่าระบบ Log
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("DevilsBot")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='-', intents=intents)

# ==========================================
# ⚙️ ตั้งค่า (Config) - แก้ไขยศตามสั่ง
# ==========================================
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

LEAVE_FILE = "leaves.json"

# ==========================================
# 🧠 AI Setup - แก้ไข Path Model
# ==========================================
AI_STATUS = "Unknown"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client_ai = None
# แก้ไขจากชื่อรุ่นเฉยๆ เป็น path เต็มเพื่อแก้ Error 404
AI_MODEL_NAME = "models/gemini-1.5-flash" 

try:
    if not GEMINI_API_KEY:
        AI_STATUS = "❌ ไม่พบ Key"
    else:
        client_ai = genai.Client(api_key=GEMINI_API_KEY)
        AI_STATUS = "✅ พร้อมใช้งาน"
except Exception as e:
    AI_STATUS = f"💥 Error: {str(e)}"

# ==========================================
# ระบบจัดการไฟล์
# ==========================================
def load_json(filename):
    if not os.path.exists(filename): return []
    try:
        with open(filename, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

leave_data = load_json(LEAVE_FILE)

# ==========================================
# 📜 ระบบจัดการใบลา - แก้ไขรูปโปรไฟล์
# ==========================================
async def refresh_leave_msg(guild):
    channel = discord.utils.get(guild.text_channels, name=CHANNEL_LEAVE)
    if not channel: return
    try:
        async for message in channel.history(limit=20):
            if message.author == bot.user and message.embeds and message.embeds[0].title == "📢 แจ้งลาหยุด / ลากิจกรรม":
                await message.delete()
    except: pass
    embed = discord.Embed(title="📢 แจ้งลาหยุด / ลากิจกรรม", description="กดปุ่มด้านล่างเพื่อกรอกแบบฟอร์มใบลาครับ 👇", color=0xe74c3c)
    await channel.send(embed=embed, view=LeaveButtonView())

class LeaveApprovalView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None) 
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        has_role = discord.utils.get(interaction.user.roles, name=ROLE_ADMIN_CHECK)
        if has_role: return True
        await interaction.response.send_message(f"⛔ เฉพาะ **{ROLE_ADMIN_CHECK}** เท่านั้น", ephemeral=True)
        return False

    @discord.ui.button(label="อนุมัติ", style=discord.ButtonStyle.success, custom_id="leave_approve", emoji="✅")
    async def approve_button(self, interaction, button): await self.process_leave(interaction, "✅ อนุมัติแล้ว", 0x2ecc71)

    @discord.ui.button(label="ไม่อนุมัติ", style=discord.ButtonStyle.danger, custom_id="leave_deny", emoji="❌")
    async def deny_button(self, interaction, button): await self.process_leave(interaction, "❌ ไม่อนุมัติ", 0xe74c3c)

    async def process_leave(self, interaction, status_text, color_code):
        new_embed = interaction.message.embeds[0].copy()
        new_embed.color = color_code
        new_embed.set_field_at(index=3, name="📋 สถานะ", value=f"**{status_text}** โดย {interaction.user.mention}", inline=False)
        await interaction.response.edit_message(embed=new_embed, view=None)

class LeaveModal(discord.ui.Modal, title="📜 แบบฟอร์มขอลา (Leave Form)"):
    char_name = discord.ui.TextInput(label="ชื่อตัวละครในเกม", required=True)
    leave_type = discord.ui.TextInput(label="หัวข้อการลา", required=True)
    leave_date = discord.ui.TextInput(label="วันที่/เวลา", required=True)
    reason = discord.ui.TextInput(label="เหตุผล (ถ้ามี)", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        tz_thai = datetime.timezone(datetime.timedelta(hours=7))
        timestamp = datetime.datetime.now(tz_thai).strftime("%d/%m/%Y %H:%M")
        
        embed = discord.Embed(title="📩 มีสาส์นขอลาหยุด!", color=0xf1c40f)
        # แก้ไข: เพิ่มรูปโปรไฟล์กลับมา
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 จอมยุทธ์", value=f"{self.char_name.value}", inline=False)
        embed.add_field(name="📌 ประเภท", value=self.leave_type.value, inline=False)
        embed.add_field(name="📅 วันที่/เวลา", value=self.leave_date.value, inline=False)
        embed.add_field(name="📋 สถานะ", value="⏳ **รอการตรวจสอบ**", inline=False)
        embed.set_footer(text=f"ยื่นเรื่องเมื่อ: {timestamp}")
        
        await interaction.channel.send(content=f"**ผู้ยื่นเรื่อง:** {interaction.user.mention}", embed=embed, view=LeaveApprovalView())
        await interaction.followup.send("✅ ส่งใบลาเรียบร้อย!", ephemeral=True)
        await refresh_leave_msg(interaction.guild)

class LeaveButtonView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 เขียนใบลา", style=discord.ButtonStyle.danger, custom_id="open_leave_modal", emoji="📜")
    async def open_leave(self, interaction, button): await interaction.response.send_modal(LeaveModal())

# ==========================================
# 🆕 ระบบแนะนำตัว - แก้ไขลบข้อความเก่า/รูป/ปุ่มย้ายลงล่าง
# ==========================================
class IntroModal(discord.ui.Modal, title="📝 ข้อมูลแนะนำตัว"):
    name = discord.ui.TextInput(label="ชื่อเล่น", required=True)
    age = discord.ui.TextInput(label="อายุ", required=True)
    async def on_submit(self, interaction):
        data = {"name": self.name.value, "age": self.age.value}
        await interaction.response.send_message("🎮 **เลือกเกมที่ท่านเล่น:**", view=GameSelectView(data), ephemeral=True)

class GameSelectView(discord.ui.View):
    def __init__(self, data): super().__init__(); self.data = data
    @discord.ui.select(placeholder="เลือกเกม...", options=[discord.SelectOption(label="Where Winds Meet", emoji="⚔️"), discord.SelectOption(label="อื่นๆ", emoji="🎮")])
    async def callback(self, interaction, select):
        self.data["game"] = select.values[0]
        if self.data["game"] == "Where Winds Meet": await interaction.response.send_modal(WWMCharModal(self.data))
        else: await finalize_intro(interaction, self.data)

class WWMCharModal(discord.ui.Modal, title="⚔️ ข้อมูลตัวละคร WWM"):
    char_name = discord.ui.TextInput(label="ชื่อในเกม WWM", required=True)
    def __init__(self, data): super().__init__(); self.data = data
    async def on_submit(self, interaction):
        self.data['char_name'] = self.char_name.value
        await interaction.response.edit_message(content="🛡️ **เลือกสายอาชีพ:**", view=ClassSelectView(self.data))

class ClassSelectView(discord.ui.View):
    def __init__(self, data): super().__init__(); self.data = data
    @discord.ui.select(placeholder="เลือกอาชีพ...", options=[discord.SelectOption(label="ดาเมจ", emoji="⚔️"), discord.SelectOption(label="หมอ", emoji="🩺"), discord.SelectOption(label="แทงค์", emoji="🛡️"), discord.SelectOption(label="ไฮบริด", emoji="🧬")])
    async def callback(self, interaction, select):
        self.data["class"] = select.values[0]
        await finalize_intro(interaction, self.data)

async def finalize_intro(interaction, data):
    user, guild = interaction.user, interaction.guild
    pub_ch = discord.utils.get(guild.text_channels, name=PUBLIC_CHANNEL)
    
    # แก้ไข: ลบข้อความแนะนำตัวเก่าของผู้ใช้รายนี้ในช่อง
    if pub_ch:
        async for m in pub_ch.history(limit=50):
            if m.author == bot.user and m.embeds and f"แนะนำตัวโดย {user.name}" in (m.embeds[0].footer.text if m.embeds[0].footer else ""):
                await m.delete()

    # จัดการยศ (คงเดิม)
    roles_to_add = []
    role_ver = discord.utils.get(guild.roles, name=ROLE_VERIFIED)
    if role_ver: roles_to_add.append(role_ver)
    icon = ""
    if data.get("game") == "Where Winds Meet":
        role_wwm = discord.utils.get(guild.roles, name=ROLE_WWM)
        if role_wwm: roles_to_add.append(role_wwm)
        cls_map = {"ดาเมจ": (ROLE_DPS, "⚔️"), "หมอ": (ROLE_HEALER, "💉"), "แทงค์": (ROLE_TANK, "🛡️"), "ไฮบริด": (ROLE_HYBRID, "🧬")}
        role_n, icon = cls_map.get(data["class"], (None, ""))
        tr = discord.utils.get(guild.roles, name=role_n)
        if tr: roles_to_add.append(tr)

    if roles_to_add: await user.add_roles(*roles_to_add)
    try: await user.edit(nick=f"{icon} {user.name} ({data['name']})")
    except: pass

    # แก้ไข: เพิ่มรูปโปรไฟล์ใน Embed รายงานตัว
    embed = discord.Embed(title="✅ สมาชิกใหม่รายงานตัว!", color=0xffd700)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.description = f"**ชื่อเล่น :** {data['name']}\n**อายุ :** {data['age']}\n**เกมที่เล่น :** {data['game']}"
    if data.get("game") == "Where Winds Meet":
        embed.description += f"\n**ชื่อในเกม :** {data['char_name']}\n**สายอาชีพ :** {data['class']}"
    embed.set_footer(text=f"แนะนำตัวโดย {user.name}")

    if pub_ch:
        # ส่ง Embed รายงานตัว
        await pub_ch.send(embed=embed)
        # แก้ไข: ย้ายปุ่มแนะนำตัวลงมาล่างสุดเสมอ
        async for m in pub_ch.history(limit=10):
            if m.author == bot.user and m.embeds and "ยืนยันตัวตน" in m.embeds[0].title:
                await m.delete()
        await pub_ch.send(embed=discord.Embed(title="📢 ยืนยันตัวตน / แนะนำตัว", description="กดปุ่มด้านล่างเพื่อเปิดแบบฟอร์มลงทะเบียนครับ 👇", color=0x00ff00), view=TicketButton())

    await interaction.response.edit_message(content="✅ บันทึกเรียบร้อย!", view=None)

class TicketButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 กดเพื่อเริ่มแนะนำตัว", style=discord.ButtonStyle.green, custom_id="start_intro")
    async def start(self, interaction, button): await interaction.response.send_modal(IntroModal())

# ==========================================
# 🔮 ฟังก์ชันบันเทิง & จัดการ (คงเดิม)
# ==========================================
@bot.tree.command(name="ดูดวง", description="🔮 เช็คดวงประจำวัน")
async def fortune(interaction: discord.Interaction):
    if interaction.channel.name != ALLOWED_CHANNEL_FORTUNE:
        return await interaction.response.send_message(f"❌ ไปใช้ในห้อง `{ALLOWED_CHANNEL_FORTUNE}`", ephemeral=True)
    fortunes_data = [
        {"text": "🌟 เทพเจ้า RNG ประทับร่าง! ออฟชั่นทองมาแน่!", "color": 0xffd700, "img": "https://media.giphy.com/media/l0Ex6kAKAoFRsFh6M/giphy.gif"},
        {"text": "🔥 มือร้อน(เงิน)! ระวังหมดตัวนะเพื่อน (แต่ได้ของดี)", "color": 0xff4500, "img": "https://media.giphy.com/media/Lopx9eUi34rbq/giphy.gif"},
        {"text": "✨ แสงสีทองรออยู่!", "color": 0xffff00, "img": "https://media.giphy.com/media/3o7TKSjRrfIPjeiVyM/giphy.gif"},
        {"text": "🟢 สีเขียวเหนี่ยวทรัพย์ วันนี้ได้แต่ของพอถูไถ", "color": 0x2ecc71, "img": "https://media.giphy.com/media/13HgwGsXF0aiGY/giphy.gif"},
        {"text": "📈 ดวงกลางๆ พอไหว", "color": 0x3498db, "img": "https://media.giphy.com/media/l2Je66zG6mAAZxgqI/giphy.gif"},
        {"text": "🧘 ไปทำบุญ 9 วัดก่อน", "color": 0x9b59b6, "img": "https://media.giphy.com/media/xT5LMHxhOfscxPfIfm/giphy.gif"},
        {"text": "💀 ดวง All Bamboocut", "color": 0x000000, "img": "https://media.giphy.com/media/26tP3M3iA3EBIfXy0/giphy.gif"},
        {"text": "💎 เกลือล้วนๆ", "color": 0x95a5a6, "img": "https://media.giphy.com/media/3o6UB5RrlQuMfZp82Y/giphy.gif"},
        {"text": "⚔️ จอมยุทธ์ถังแตก", "color": 0x7f8c8d, "img": "https://media.giphy.com/media/l2JdZOv5901Q6Q7Ek/giphy.gif"},
        {"text": "🧧 GM รักคุณ (รักที่จะกินตังค์คุณ)", "color": 0xe74c3c, "img": "https://media.giphy.com/media/3o7TKRBB3E7IdVNLm8/giphy.gif"}
    ]
    selection = random.choice(fortunes_data)
    embed = discord.Embed(title="🔮 เสี่ยงเซียมซีวัดดวง", description=f"# {selection['text']}", color=selection["color"])
    embed.set_image(url=selection["img"])
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ล้าง", description="🧹 ลบข้อความ")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_chat(interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 ลบแล้ว {len(deleted)} ข้อความ", ephemeral=True)

@bot.tree.command(name="ถาม", description="🤖 คุยกับ AI")
async def ask_ai(interaction, question: str):
    await interaction.response.defer()
    if not client_ai: return await interaction.followup.send("⚠️ AI ไม่พร้อม")
    try:
        # แก้ไข Path ของ Model
        response = client_ai.models.generate_content(model=AI_MODEL_NAME, contents=question)
        embed = discord.Embed(title="🗣️ ท่านจอมยุทธ์กล่าว...", description=response.text[:1900], color=0x00ffcc)
        await interaction.followup.send(embed=embed)
    except Exception as e: await interaction.followup.send(f"😵 Error: {e}")

@bot.tree.command(name="เช็ครุ่นไอเอ", description="🔍 ตรวจสอบ Ver.AI")
async def check_ai_ver(interaction):
    # แก้ไข: ปรับให้แสดงรุ่นทั้งหมดที่ระบุในลิสต์
    models = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-2.0-flash-exp"]
    txt = ""
    for m in models:
        status = "🟢 (ใช้อยู่)" if m == AI_MODEL_NAME else "⚪ (รองรับ)"
        txt += f"- **{m.replace('models/', '')}** {status}\n"
    
    embed = discord.Embed(title="🤖 AI Model Support:", description=txt, color=0x3498db)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="เช็คระบบ", description="🔧 ดูสถานะบอท")
async def check_status(interaction):
    embed = discord.Embed(title="🔧 สถานะระบบ", color=0x00ff00 if "✅" in AI_STATUS else 0xff0000)
    embed.add_field(name="AI Status", value=AI_STATUS, inline=False)
    embed.add_field(name="Latency", value=f"`{round(bot.latency * 1000)}ms`", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==========================================
# 🚀 เริ่มระบบ
# ==========================================
@bot.event
async def on_ready():
    logger.info(f"🚀 {bot.user} Online!")
    bot.add_view(TicketButton())
    bot.add_view(LeaveButtonView())
    bot.add_view(LeaveApprovalView())
    await bot.tree.sync()
    keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN: bot.run(TOKEN)
