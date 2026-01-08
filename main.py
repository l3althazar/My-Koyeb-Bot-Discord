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
from keep_alive import keep_alive

# ==========================================
# 📝 ตั้งค่าระบบ Log
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
# ⚙️ ตั้งค่า
# ==========================================
PUBLIC_CHANNEL = "ห้องแนะนำตัว"
ROLE_VERIFIED = "‹ แนะนำตัวแล้ว ›"
ROLE_WWM = "ข้าคือจอมยุทธ์เด๊ะ"
HISTORY_FILE = "history.json"
ALLOWED_CHANNEL_FORTUNE = "ห้องเช็คดวง"

# ==========================================
# 🧠 AI Setup
# ==========================================
GENAI_VERSION = genai.__version__
BOT_PERSONA = """
คุณคือ "Devils DenBot" AI ผู้ช่วยอัจฉริยะที่มีความรู้กว้างขวาง
ตัวตนของคุณ: เป็นปัญญาประดิษฐ์ที่มีความรอบรู้ระดับสูง แต่มีจิตวิญญาณของจอมยุทธ์แฝงอยู่
สไตล์การตอบ: ตอบแบบผู้รู้จริง แม่นยำ แต่มีลูกเล่นสไตล์จอมยุทธ์
"""

model = None
AI_STATUS = "Unknown"
KEY_DEBUG_INFO = "No Key"

try:
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        AI_STATUS = "❌ ไม่พบ Key"
        logger.error("API Key not found!")
    else:
        k_len = len(api_key)
        KEY_DEBUG_INFO = f"{api_key[:5]}...{api_key[-4:]} (Length: {k_len})"
        genai.configure(api_key=api_key)
        
        # ✅ แก้กลับเป็นแบบธรรมดา (ไม่มี Google Search) เพื่อความเสถียร
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        AI_STATUS = "✅ พร้อมใช้งาน (Basic Mode)"
        logger.info("✅ Gemini Model loaded successfully (Basic Mode).")
except Exception as e:
    AI_STATUS = f"💥 Error: {str(e)}"
    logger.critical(f"🔥 Critical Error loading AI: {e}")

# ==========================================
# Functions
# ==========================================
def load_history():
    if not os.path.exists(HISTORY_FILE): return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

user_history = load_history()

async def refresh_setup_msg(channel):
    try:
        async for message in channel.history(limit=30):
            if message.author == bot.user and message.embeds and message.embeds[0].title == "📢 ยืนยันตัวตน / แนะนำตัว":
                await message.delete()
    except: pass
    embed = discord.Embed(title="📢 ยืนยันตัวตน / แนะนำตัว", description="กดปุ่มด้านล่างเพื่อเปิดห้องส่วนตัวสำหรับแนะนำตัวครับ 👇", color=0x00ff00)
    await channel.send(embed=embed, view=TicketButton())

# --- Classes ---
class GameSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label="Where Winds Meet", emoji="⚔️"), discord.SelectOption(label="อื่นๆ", emoji="🎮")]
        super().__init__(placeholder="เลือกเกม...", min_values=1, max_values=1, options=options)
    async def callback(self, interaction):
        self.view.selected_value = self.values[0]
        await interaction.response.defer()
        self.view.stop()

class GameView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.selected_value = None
        self.add_item(GameSelect())

class TicketButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 กดเพื่อเริ่มแนะนำตัว", style=discord.ButtonStyle.green, custom_id="start_intro")
    async def create_ticket(self, interaction, button):
        user = interaction.user
        guild = interaction.guild
        await interaction.response.send_message("⏳ กำลังเตรียมห้อง...", ephemeral=True)
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), user: discord.PermissionOverwrite(read_messages=True, send_messages=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        try:
            ch = await guild.create_text_channel(f"verify-{user.name}", overwrites=overwrites)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="👉 เข้าห้องส่วนตัว 👈", style=discord.ButtonStyle.link, url=ch.jump_url))
            await interaction.edit_original_response(content=f"✅ สร้างห้องแล้ว! {user.mention}", view=view)
            await self.start_interview(ch, user, guild)
        except Exception as e: print(e)

    async def start_interview(self, channel, user, guild):
        data = {"name": "", "age": "", "game": "", "char_name": "-"}
        def check(m): return m.author == user and m.channel == channel
        try:
            await channel.send(f"{user.mention} ยินดีต้อนรับครับ!")
            await channel.send(embed=discord.Embed(title="1. ชื่อเล่น?", color=0x3498db))
            data["name"] = (await bot.wait_for("message", check=check, timeout=300)).content
            await channel.send(embed=discord.Embed(title="2. อายุ?", color=0x3498db))
            data["age"] = (await bot.wait_for("message", check=check, timeout=300)).content
            
            view = GameView()
            await channel.send(embed=discord.Embed(title="3. เลือกเกม", color=0x3498db), view=view)
            await view.wait()
            if not view.selected_value: return
            data["game"] = view.selected_value
            
            if data["game"] == "Where Winds Meet":
                await channel.send(embed=discord.Embed(title="⚔️ ชื่อตัวละคร?", color=0xe74c3c))
                data["char_name"] = (await bot.wait_for("message", check=check, timeout=300)).content
                role = discord.utils.get(guild.roles, name=ROLE_WWM)
                if role: await user.add_roles(role)

            embed = discord.Embed(title="✅ ข้อมูลบันทึกแล้ว", description=f"ชื่อ: {data['name']}\nเกม: {data['game']}", color=0xffd700)
            if user.avatar: embed.set_thumbnail(url=user.avatar.url)
            
            pub_ch = discord.utils.get(guild.text_channels, name=PUBLIC_CHANNEL)
            sent_msg = None
            if pub_ch:
                if str(user.id) in user_history:
                    try: (await pub_ch.fetch_message(user_history[str(user.id)])).delete()
                    except: pass
                sent_msg = await pub_ch.send(embed=embed)
                user_history[str(user.id)] = sent_msg.id
                save_history(user_history)
                await refresh_setup_msg(pub_ch)

            role_ver = discord.utils.get(guild.roles, name=ROLE_VERIFIED)
            if role_ver: await user.add_roles(role_ver)
            try: await user.edit(nick=f"{user.display_name} ({data['name']})")
            except: pass

            if sent_msg:
                view_back = discord.ui.View()
                view_back.add_item(discord.ui.Button(label="🔙 ไปดูผลลัพธ์", style=discord.ButtonStyle.link, url=sent_msg.jump_url))
                await channel.send(embed=discord.Embed(title="✅ เรียบร้อย!", description="ห้องจะลบใน 10 วิ", color=0x00ff00), view=view_back)
            
            await asyncio.sleep(10)
            await channel.delete()
        except: await channel.delete()

@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"✅ Synced {len(synced)} commands.")

# --- Commands ---
@bot.tree.command(name="เช็คระบบ", description="🔧 ดูสถานะ")
async def check_status(interaction: discord.Interaction):
    color = 0x00ff00 if "✅" in AI_STATUS else 0xff0000
    embed = discord.Embed(title="🔧 ข้อมูลระบบ AI", color=color)
    embed.add_field(name="สถานะ", value=AI_STATUS, inline=False)
    embed.add_field(name="📦 GenAI Version", value=f"`v{GENAI_VERSION}`", inline=True)
    embed.add_field(name="🔑 Key Info", value=f"`{KEY_DEBUG_INFO}`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ถาม", description="🤖 คุยกับ AI")
async def ask_ai(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    if model is None:
        return await interaction.followup.send(f"⚠️ AI ไม่พร้อม: {AI_STATUS}", ephemeral=True)
    try:
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        response = model.generate_content(f"{BOT_PERSONA}\n(เวลา: {now})\n\nQ: {question}\nA:")
        text = response.text[:1900] + "..." if len(response.text) > 1900 else response.text
        embed = discord.Embed(title="🗣️ คำตอบ:", description=text, color=0x00ffcc)
        embed.set_footer(text=f"Q: {question}")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"😵 Error: {e}", ephemeral=True)

@bot.tree.command(name="ดูดวง", description="🔮 เช็คดวง")
async def fortune(interaction: discord.Interaction):
    if interaction.channel.name != ALLOWED_CHANNEL_FORTUNE:
        return await interaction.response.send_message(f"❌ ผิดห้อง! ไปห้อง `{ALLOWED_CHANNEL_FORTUNE}`", ephemeral=True)
    results = ["เกลือ 🧂", "ดวงดี ✨", "ปานกลาง 😐", "เฮงๆ 🔥", "ระวังตัว 💀"]
    await interaction.response.send_message(f"🔮 {interaction.user.mention}: {random.choice(results)}")

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
        await new_ch.send("✨ ห้องใหม่มาแล้ว!")
    btn = discord.ui.Button(label="ยืนยัน?", style=discord.ButtonStyle.danger, emoji="💣")
    btn.callback = confirm
    view.add_item(btn)
    await interaction.response.send_message("⚠️ ยืนยันล้างห้อง?", view=view, ephemeral=True)

@bot.tree.command(name="เช็คโมเดล", description="📂 ดูโมเดล")
async def list_models(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        msg = "**Models:**\n" + "\n".join([f"- `{m.name}`" for m in genai.list_models() if 'generateContent' in m.supported_generation_methods])
        await interaction.followup.send(msg[:1900])
    except Exception as e: await interaction.followup.send(f"❌ Error: {e}")

@bot.event
async def on_ready():
    logger.info(f"🚀 Online as {bot.user}")
    bot.add_view(TicketButton())

@bot.command()
async def setup(ctx):
    await ctx.message.delete()
    await refresh_setup_msg(ctx.channel)

keep_alive()
bot.run(os.environ['TOKEN'])
