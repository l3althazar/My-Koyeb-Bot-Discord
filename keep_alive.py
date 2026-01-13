import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import json
import os
import random
import logging
import google.generativeai as genai

# ==========================================
# 📝 1. ตั้งค่าระบบ Log
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)
logger = logging.getLogger("DevilsBot")

# --- Permission ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='-', intents=intents)

# ==========================================
# ⚙️ 2. ตั้งค่า
# ==========================================
PUBLIC_CHANNEL = "ห้องแนะนำตัว"
CHANNEL_LEAVE = "ห้องแจ้งลา"       
ALLOWED_CHANNEL_FORTUNE = "ห้องเช็คดวง"

ROLE_VERIFIED = "‹ แนะนำตัวแล้ว ›"
ROLE_WWM = "ข้าคือจอมยุทธ์เด๊ะ"

ROLE_DPS = "DPS ⚔️"
ROLE_HEALER = "หมอ💉🩺"
ROLE_TANK = "แทงค์ 🛡️"
ROLE_HYBRID = "ไฮบริด 🧬"

LEAVE_FILE = "leaves.json"

# ==========================================
# 🧠 3. AI Setup
# ==========================================
GENAI_VERSION = genai.__version__
BOT_PERSONA = """
คุณคือ "Devils DenBot" AI ผู้ช่วยอัจฉริยะประจำกิลด์
ตัวตนของคุณ: เป็นปัญญาประดิษฐ์ที่มีความรอบรู้ แต่มีจิตวิญญาณของจอมยุทธ์แฝงอยู่
สไตล์การตอบ:
1. วิชาการ: จริงจัง ชัดเจน ถูกต้อง
2. คุยเล่น: กวนนิดๆ สไตล์หนังจีนกำลังภายใน เรียกผู้ใช้ว่า "สหาย"
"""

model = None
AI_STATUS = "Unknown"
KEY_DEBUG_INFO = "No Key"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

try:
    if not GEMINI_API_KEY:
        AI_STATUS = "❌ ไม่พบ Key"
        logger.error("API Key not found!")
    else:
        k_len = len(GEMINI_API_KEY)
        KEY_DEBUG_INFO = f"{GEMINI_API_KEY[:5]}...{GEMINI_API_KEY[-4:]} (ยาว: {k_len})"
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        AI_STATUS = "✅ พร้อมใช้งาน"
        logger.info("✅ Gemini Model loaded successfully.")
except Exception as e:
    AI_STATUS = f"💥 Error: {str(e)}"
    logger.critical(f"🔥 Critical Error loading AI: {e}")

# ==========================================
# 4. ระบบจัดการไฟล์
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
# 5. ระบบ GUI (ใบลา & แนะนำตัว)
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

class LeaveModal(discord.ui.Modal, title="📜 แบบฟอร์มขอลา (Leave Form)"):
    char_name = discord.ui.TextInput(label="ชื่อตัวละครในเกม", placeholder="ระบุชื่อตัวละครของท่าน...", required=True)
    leave_type = discord.ui.TextInput(label="หัวข้อการลา", placeholder="เช่น ลากิจ, ลาป่วย, ขาด War", required=True)
    leave_date = discord.ui.TextInput(label="วันที่/เวลา", placeholder="เช่น 12-14 ม.ค. หรือ วันนี้ 2 ทุ่ม", required=True)
    reason = discord.ui.TextInput(label="เหตุผล (ถ้ามี)", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True) 
        tz_thai = datetime.timezone(datetime.timedelta(hours=7))
        timestamp = datetime.datetime.now(tz_thai).strftime("%d/%m/%Y %H:%M")

        entry = {
            "user": interaction.user.display_name,
            "char_name": self.char_name.value,
            "id": interaction.user.id,
            "type": self.leave_type.value,
            "date": self.leave_date.value,
            "reason": self.reason.value or "-",
            "timestamp": timestamp
        }
        leave_data.append(entry)
        save_json(LEAVE_FILE, leave_data)

        embed = discord.Embed(title="📩 มีสาส์นขอลาหยุด!", color=0xff9900)
        # ✅ ส่วนนี้ยังมีรูปโปรไฟล์อยู่ (ตามที่ท่านต้องการ)
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        embed.add_field(name="👤 จอมยุทธ์", value=f"ชื่อ : {self.char_name.value}", inline=False)
        embed.add_field(name="📌 ประเภท", value=self.leave_type.value, inline=False)
        embed.add_field(name="📅 วันที่/เวลา", value=self.leave_date.value, inline=False)
        embed.add_field(name="📝 เหตุผล", value=self.reason.value or "-", inline=False)
        embed.set_footer(text=f"ยื่นเรื่องเมื่อ: {timestamp}")

        await interaction.channel.send(content=f"**ผู้ยื่นเรื่อง:** {interaction.user.mention}", embed=embed)
        msg = await interaction.followup.send(f"✅ ส่งใบลาเรียบร้อยแล้วครับ!", ephemeral=True)
        await refresh_leave_msg(interaction.guild)
        await asyncio.sleep(3) 
        try: await msg.delete()
        except: pass

class LeaveButtonView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 เขียนใบลา", style=discord.ButtonStyle.danger, custom_id="open_leave_modal", emoji="📜")
    async def open_leave(self, interaction, button):
        await interaction.response.send_modal(LeaveModal())

# ==========================================
# 🆕 ระบบแนะนำตัว (Super Smooth Flow)
# ==========================================

class IntroModal(discord.ui.Modal, title="📝 ข้อมูลแนะนำตัว"):
    name = discord.ui.TextInput(label="ชื่อเล่น", placeholder="ชื่อเล่นของท่าน...", required=True)
    age = discord.ui.TextInput(label="อายุ", placeholder="ระบุอายุ...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        data = {
            "name": self.name.value,
            "age": self.age.value,
            "char_name": "-", 
            "class": "-"      
        }
        view = GameSelectView(data)
        await interaction.response.send_message("🎮 **โปรดเลือกเกมที่คุณเล่น:**", view=view, ephemeral=True)

class GameSelect(discord.ui.Select):
    def __init__(self, data):
        self.data = data
        options = [discord.SelectOption(label="Where Winds Meet", emoji="⚔️"), discord.SelectOption(label="อื่นๆ", emoji="🎮")]
        super().__init__(placeholder="เลือกเกมที่คุณเล่น...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction):
        game = self.values[0]
        self.data["game"] = game
        
        if game == "Where Winds Meet":
            await interaction.response.send_modal(WWMCharModal(self.data))
        else:
            await finalize_intro(interaction, self.data)

class GameSelectView(discord.ui.View):
    def __init__(self, data):
        super().__init__()
        self.add_item(GameSelect(data))

class WWMCharModal(discord.ui.Modal, title="⚔️ ข้อมูลตัวละคร WWM"):
    char_name = discord.ui.TextInput(label="ชื่อตัวละคร (IGN)", placeholder="ชื่อในเกม WWM...", required=True)

    def __init__(self, data):
        super().__init__()
        self.data = data

    async def on_submit(self, interaction: discord.Interaction):
        self.data['char_name'] = self.char_name.value
        view = ClassSelectView(self.data)
        await interaction.response.edit_message(content=f"✅ บันทึกชื่อ: **{self.char_name.value}**\n\n🛡️ **โปรดเลือกสายอาชีพ:**", view=view)

class ClassSelect(discord.ui.Select):
    def __init__(self, data):
        self.data = data
        options = [
            discord.SelectOption(label="ดาเมจ", emoji="⚔️"),
            discord.SelectOption(label="หมอ", emoji="🩺"),
            discord.SelectOption(label="แทงค์", emoji="🛡️"),
            discord.SelectOption(label="ไฮบริด", emoji="🧬")
        ]
        super().__init__(placeholder="เลือกสายอาชีพหลัก...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction):
        self.data["class"] = self.values[0]
        await finalize_intro(interaction, self.data)

class ClassSelectView(discord.ui.View):
    def __init__(self, data):
        super().__init__()
        self.add_item(ClassSelect(data))

async def finalize_intro(interaction, data):
    embed_loading = discord.Embed(description="⏳ กำลังบันทึกข้อมูล...", color=0xf1c40f)
    await interaction.response.edit_message(content=None, embed=embed_loading, view=None)

    user = interaction.user
    guild = interaction.guild

    roles_to_add = []
    
    all_class_roles = []
    for r_name in [ROLE_DPS, ROLE_HEALER, ROLE_TANK, ROLE_HYBRID]:
        r = discord.utils.get(guild.roles, name=r_name)
        if r: all_class_roles.append(r)

    roles_to_remove = [r for r in all_class_roles if r in user.roles]
    if roles_to_remove:
        try: await user.remove_roles(*roles_to_remove)
        except: pass

    role_ver = discord.utils.get(guild.roles, name=ROLE_VERIFIED)
    if role_ver: roles_to_add.append(role_ver)

    icon_prefix = ""
    if data["game"] == "Where Winds Meet":
        role_wwm = discord.utils.get(guild.roles, name=ROLE_WWM)
        if role_wwm: roles_to_add.append(role_wwm)
        
        cls = data.get("class")
        target_role = None
        if cls == "ดาเมจ":
            target_role = discord.utils.get(guild.roles, name=ROLE_DPS)
            icon_prefix = "⚔️"
        elif cls == "หมอ":
            target_role = discord.utils.get(guild.roles, name=ROLE_HEALER)
            icon_prefix = "💉"
        elif cls == "แทงค์":
            target_role = discord.utils.get(guild.roles, name=ROLE_TANK)
            icon_prefix = "🛡️"
        elif cls == "ไฮบริด":
            target_role = discord.utils.get(guild.roles, name=ROLE_HYBRID)
            icon_prefix = "🧬"
        
        if target_role: roles_to_add.append(target_role)

    if roles_to_add:
        try: await user.add_roles(*roles_to_add)
        except: pass

    try:
        new_nick = f"{icon_prefix} {user.name} ({data['name']})" if icon_prefix else f"{user.name} ({data['name']})"
        await user.edit(nick=new_nick)
    except: pass

    embed = discord.Embed(title="✅ สมาชิกใหม่รายงานตัว!", color=0xffd700)
    desc = f"**ชื่อเล่น :** {data['name']}\n\n**อายุ :** {data['age']}\n\n**เกมที่เล่น :** {data['game']}"
    
    if data["game"] == "Where Winds Meet":
        desc += f"\n\n**ชื่อในเกม :** {data['char_name']}"
        desc += f"\n\n**สายอาชีพ :** {data['class']}"
    
    embed.description = desc
    
    # ✅ ส่วนนี้ยังมีรูปโปรไฟล์อยู่ (ตามที่ท่านต้องการ)
    if user.avatar: embed.set_thumbnail(url=user.avatar.url)
    
    embed.set_footer(text=f"แนะนำตัวโดย {user.name}")

    pub_ch = discord.utils.get(guild.text_channels, name=PUBLIC_CHANNEL)
    if pub_ch:
        async for msg in pub_ch.history(limit=50):
            if msg.author == bot.user and msg.embeds and msg.embeds[0].footer.text == f"แนะนำตัวโดย {user.name}":
                try: await msg.delete()
                except: pass
                break
        await pub_ch.send(embed=embed)
        await refresh_setup_msg(pub_ch)

    embed_success = discord.Embed(title="✅ เรียบร้อย!", description="บันทึกข้อมูลเสร็จสิ้น", color=0x00ff00)
    try: await interaction.edit_original_response(embed=embed_success)
    except: pass

    await asyncio.sleep(3)
    try: await interaction.delete_original_response()
    except: pass

class TicketButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 กดเพื่อเริ่มแนะนำตัว", style=discord.ButtonStyle.green, custom_id="start_intro_main")
    async def start_intro(self, interaction, button):
        await interaction.response.send_modal(IntroModal())

async def refresh_setup_msg(channel):
    try:
        async for message in channel.history(limit=20):
            if message.author == bot.user and message.embeds and message.embeds[0].title == "📢 ยืนยันตัวตน / แนะนำตัว":
                await message.delete()
    except: pass
    
    embed = discord.Embed(title="📢 ยืนยันตัวตน / แนะนำตัว", description="กดปุ่มด้านล่างเพื่อเปิดแบบฟอร์มลงทะเบียนครับ 👇", color=0x00ff00)
    await channel.send(embed=embed, view=TicketButton())

@bot.command()
async def sync(ctx):
    bot.tree.clear_commands(guild=ctx.guild)
    await bot.tree.sync(guild=ctx.guild)
    synced = await bot.tree.sync() 
    await ctx.send(f"✅ **Global Sync เรียบร้อย!** เจอทั้งหมด {len(synced)} คำสั่ง")

@bot.command()
async def setup(ctx):
    await ctx.message.delete()
    pub_ch = discord.utils.get(ctx.guild.text_channels, name=PUBLIC_CHANNEL)
    leave_ch = discord.utils.get(ctx.guild.text_channels, name=CHANNEL_LEAVE)
    if pub_ch: await refresh_setup_msg(pub_ch)
    if leave_ch: await refresh_leave_msg(ctx.guild)
    await ctx.send("✅ รีเฟรชปุ่มทั้ง 2 ห้องเรียบร้อย!")

# Commands อื่นๆ
@bot.tree.command(name="เช็คคนลา", description="📋 ดูรายชื่อคนที่ลาอยู่")
async def check_leaves(interaction: discord.Interaction):
    if not leave_data: return await interaction.response.send_message("✅ ไม่มีใครลาเลยครับ!", ephemeral=True)
    embed = discord.Embed(title="📋 รายชื่อจอมยุทธ์ที่ขอลาพัก", color=0xff9900)
    desc = ""
    for i, entry in enumerate(leave_data, 1):
        char_name = entry.get('char_name', '-')
        desc += f"**{i}. {entry['user']} (IGN: {char_name})**\n📌 {entry['type']} | 📅 {entry['date']}\n📝 {entry['reason']}\n\n"
    embed.description = desc
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ล้างโพยลา", description="🧹 ล้างรายชื่อคนลาทั้งหมด")
@app_commands.checks.has_permissions(administrator=True)
async def clear_leaves(interaction: discord.Interaction):
    leave_data.clear()
    save_json(LEAVE_FILE, leave_data)
    await interaction.response.send_message("🧹 ล้างบัญชีคนลาเรียบร้อย!", ephemeral=False)

@bot.tree.command(name="เช็คระบบ", description="🔧 ดูสถานะบอท")
async def check_status(interaction: discord.Interaction):
    color = 0x00ff00 if "✅" in AI_STATUS else 0xff0000
    embed = discord.Embed(title="🔧 ข้อมูลระบบ AI", color=color)
    embed.add_field(name="สถานะ", value=AI_STATUS, inline=False)
    embed.add_field(name="📦 Version", value=f"`v{GENAI_VERSION}`", inline=True)
    embed.add_field(name="🔑 Key", value=f"`{KEY_DEBUG_INFO}`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ถาม", description="🤖 คุยกับ AI")
async def ask_ai(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    if model is None: return await interaction.followup.send(f"⚠️ AI ไม่พร้อม", ephemeral=True)
    try:
        tz_thai = datetime.timezone(datetime.timedelta(hours=7))
        now = datetime.datetime.now(tz_thai).strftime("%d/%m/%Y %H:%M:%S")
        response = model.generate_content(f"{BOT_PERSONA}\n(เวลาไทย: {now})\n\nQ: {question}\nA:")
        text = response.text[:1900] + "..." if len(response.text) > 1900 else response.text
        embed = discord.Embed(title="🗣️ ท่านจอมยุทธ์กล่าว...", description=text, color=0x00ffcc)
        embed.set_footer(text=f"Q: {question} | โดย {interaction.user.name}")
        await interaction.followup.send(embed=embed)
    except Exception as e: await interaction.followup.send(f"😵 Error: {e}", ephemeral=True)

# ==========================================
# 🔮 6. ดูดวง (No User Pic, Big Text Only)
# ==========================================
@bot.tree.command(name="ดูดวง", description="🔮 เช็คดวงกาชา/Tune ประจำวัน")
async def fortune(interaction: discord.Interaction):
    if interaction.channel.name != ALLOWED_CHANNEL_FORTUNE:
        return await interaction.response.send_message(f"❌ ผิดห้อง! ไป `{ALLOWED_CHANNEL_FORTUNE}` ครับ", ephemeral=True)
    
    fortunes_data = [
        {"text": "🌟 เทพเจ้า RNG ประทับร่าง! ออฟชั่นทองมาแน่!", "color": 0xffd700, "img": "https://media.giphy.com/media/l0Ex6kAKAoFRsFh6M/giphy.gif"},
        {"text": "🔥 มือร้อน(เงิน)! ระวังหมดตัวนะเพื่อน (แต่ได้ของดี)", "color": 0xff4500, "img": "https://media.giphy.com/media/Lopx9eUi34rbq/giphy.gif"},
        {"text": "✨ แสงสีทองรออยู่! (ในฝันนะ... ล้อเล่น ของจริง!)", "color": 0xffff00, "img": "https://media.giphy.com/media/3o7TKSjRrfIPjeiVyM/giphy.gif"},
        {"text": "🟢 สีเขียวเหนี่ยวทรัพย์ วันนี้ได้แต่ของพอถูไถ", "color": 0x2ecc71, "img": "https://media.giphy.com/media/13HgwGsXF0aiGY/giphy.gif"},
        {"text": "📈 ดวงกลางๆ พอไหว แต่อย่าหวังของแรร์มาก", "color": 0x3498db, "img": "https://media.giphy.com/media/l2Je66zG6mAAZxgqI/giphy.gif"},
        {"text": "🧘 ไปทำบุญ 9 วัดก่อน ดวงยังไม่พุ่ง แต่ไม่แย่", "color": 0x9b59b6, "img": "https://media.giphy.com/media/xT5LMHxhOfscxPfIfm/giphy.gif"},
        {"text": "💀 ดวงของคุณจะได้ All Bamboocut", "color": 0x000000, "img": "https://media.giphy.com/media/26tP3M3iA3EBIfXy0/giphy.gif"},
        {"text": "💎 มีแววเสียตังค์ฟรี 99% = เกลือล้วนๆ", "color": 0x95a5a6, "img": "https://media.giphy.com/media/3o6UB5RrlQuMfZp82Y/giphy.gif"},
        {"text": "⚔️ จอมยุทธ์ถังแตก เก็บตังค์กินข้าวเถอะเชื่อข้า", "color": 0x7f8c8d, "img": "https://media.giphy.com/media/l2JdZOv5901Q6Q7Ek/giphy.gif"},
        {"text": "🧧 GM รักคุณ (รักที่จะกินตังค์คุณจนหมดตัว)", "color": 0xe74c3c, "img": "https://media.giphy.com/media/3o7TKRBB3E7IdVNLm8/giphy.gif"}
    ]

    selection = random.choice(fortunes_data)

    # ❌ ส่วนนี้ไม่มี set_thumbnail (เอาออกแล้วตามคำสั่ง)
    embed = discord.Embed(
        title="🔮 เสี่ยงเซียมซีวัดดวง",
        description=f"# {selection['text']}", 
        color=selection["color"]
    )
    
    # รูป GIF ใหญ่
    embed.set_image(url=selection["img"])
    
    # ชื่อผู้เสี่ยงทายอยู่ที่ Footer เท่านั้น (ไม่มีรูป)
    embed.set_footer(text=f"ผู้เสี่ยงทาย: {interaction.user.display_name} • Devils DenBot")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ล้าง", description="🧹 ลบข้อความ")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_chat(interaction: discord.Interaction, amount: int):
    if amount > 100: return await interaction.response.send_message("❌ สูงสุด 100", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send("🧹 เรียบร้อย!", ephemeral=True)

@bot.tree.command(name="ล้างห้อง", description="⚠️ Nuke Channel")
@app_commands.checks.has_permissions(administrator=True)
async def nuke_channel(interaction: discord.Interaction):
    view = discord.ui.View()
    async def confirm(i):
        if i.user != interaction.user: return
        await i.response.send_message("💣 บึ้ม...", ephemeral=True)
        new_ch = await interaction.channel.clone(reason="Nuke")
        await interaction.channel.delete()
        await new_ch.send("✨ ห้องใหม่!")
    btn = discord.ui.Button(label="ยืนยัน?", style=discord.ButtonStyle.danger, emoji="💣")
    btn.callback = confirm
    view.add_item(btn)
    await interaction.response.send_message("⚠️ ยืนยัน?", view=view, ephemeral=True)

@bot.event
async def on_ready():
    logger.info(f"🚀 Logged in as {bot.user}")
    bot.add_view(TicketButton())
    bot.add_view(LeaveButtonView())
    for guild in bot.guilds:
        await refresh_leave_msg(guild)

bot.run(os.getenv("DISCORD_TOKEN"))
