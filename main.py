import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import json
import os
import random
import google.generativeai as genai # เรียกใช้สมอง AI
from keep_alive import keep_alive

# --- ตั้งค่า Permission ---
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
# 🧠 ตั้งค่า AI (Gemini) - ย้ายออกมากันบั๊ก
# ==========================================

# 1. กำหนดนิสัยบอท (เอาไว้นอก Try เพื่อให้ตัวแปรนี้มีอยู่เสมอ)
BOT_PERSONA = """
คุณคือ "Devils DenBot" บอทประจำกิลด์เกม "Where Winds Meet" 
นิสัยของคุณคือ: เป็นจอมยุทธ์ผู้เก่งกาจในยุทธภพ, กวนประสาทนิดๆ, เฮฮา, รักพวกพ้อง
คำพูดติดปาก: "ข้าคือจอมยุทธ์เด๊ะ", "ประเสริฐ", "นับถือๆ"
เวลาตอบคำถาม: ให้ตอบสั้นๆ กระชับ ได้ใจความ และลงท้ายด้วยคำพูดสไตล์หนังจีนกำลังภายใน
"""

model = None # ประกาศตัวแปร model ไว้ก่อน

try:
    # 2. พยายามเชื่อมต่อสมอง AI
    if 'GEMINI_API_KEY' in os.environ:
        GENAI_KEY = os.environ['GEMINI_API_KEY']
        genai.configure(api_key=GENAI_KEY)
        model = genai.GenerativeModel('gemini-pro')
        print("✅ AI System: Ready (สมองพร้อมใช้งาน)")
    else:
        print("⚠️ AI Warning: ไม่พบ GEMINI_API_KEY ใน Secrets")
except Exception as e:
    print(f"⚠️ AI Error: {e}")

# ==========================================
# ระบบจัดการไฟล์ประวัติ
# ==========================================
def load_history():
    if not os.path.exists(HISTORY_FILE): return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

user_history = load_history()

def log(message):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}")

async def refresh_setup_msg(channel):
    try:
        async for message in channel.history(limit=30):
            if message.author == bot.user and message.embeds:
                if message.embeds[0].title == "📢 ยืนยันตัวตน / แนะนำตัว":
                    await message.delete()
    except: pass
    
    embed = discord.Embed(
        title="📢 ยืนยันตัวตน / แนะนำตัว",
        description="กดปุ่มด้านล่างเพื่อเปิดห้องส่วนตัวสำหรับแนะนำตัวครับ 👇",
        color=0x00ff00
    )
    await channel.send(embed=embed, view=TicketButton())

# --- Dropdown & Views ---
class GameSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Where Winds Meet", emoji="⚔️", description="จอมยุทธ์"),
            discord.SelectOption(label="อื่นๆ", emoji="🎮", description="เกมทั่วไป")
        ]
        super().__init__(placeholder="เลือกเกมที่คุณเล่น...", min_values=1, max_values=1, options=options)

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
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 กดเพื่อเริ่มแนะนำตัว", style=discord.ButtonStyle.green, custom_id="start_intro")
    async def create_ticket(self, interaction, button):
        user = interaction.user
        guild = interaction.guild
        await interaction.response.send_message("⏳ กำลังเตรียมห้องส่วนตัว...", ephemeral=True)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        try:
            ch = await guild.create_text_channel(f"verify-{user.name}", overwrites=overwrites)
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="👉 เข้าห้องส่วนตัว 👈", style=discord.ButtonStyle.link, url=ch.jump_url))
            await interaction.edit_original_response(content=f"✅ สร้างห้องเรียบร้อย! {user.mention}", view=view)
            await self.start_interview(ch, user, guild)
        except Exception as e:
            log(f"Error: {e}")

    async def start_interview(self, channel, user, guild):
        data = {"name": "", "age": "", "game": "", "char_name": "-"}
        def check(m): return m.author == user and m.channel == channel
        try:
            await channel.send(f"{user.mention} **ยินดีต้อนรับครับ!** (ตอบคำถามในห้องนี้ได้เลย)")
            
            await channel.send(embed=discord.Embed(title="1. ชื่อเล่นของคุณคือ?", color=0x3498db))
            data["name"] = (await bot.wait_for("message", check=check, timeout=300)).content

            await channel.send(embed=discord.Embed(title="2. อายุเท่าไหร่?", color=0x3498db))
            data["age"] = (await bot.wait_for("message", check=check, timeout=300)).content

            view = GameView()
            await channel.send(embed=discord.Embed(title="3. เลือกเกมที่คุณเล่น", color=0x3498db), view=view)
            await view.wait()
            if not view.selected_value: return
            data["game"] = view.selected_value

            if data["game"] == "Where Winds Meet":
                await channel.send(embed=discord.Embed(title="⚔️ ชื่อตัวละครของคุณคือ?", color=0xe74c3c))
                data["char_name"] = (await bot.wait_for("message", check=check, timeout=300)).content
                role_wwm = discord.utils.get(guild.roles, name=ROLE_WWM)
                if role_wwm: await user.add_roles(role_wwm)

            await channel.send("⏳ **กำลังบันทึกข้อมูล...**")
            embed = discord.Embed(title="✅ สมาชิกใหม่รายงานตัว!", color=0xffd700)
            desc = f"**ชื่อเล่น :** {data['name']}\n**อายุ :** {data['age']}\n**เกมที่เล่น :** {data['game']}"
            if data["char_name"] != "-": desc += f"\n**ชื่อในเกม :** {data['char_name']}"
            embed.description = desc
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
                btn_back = discord.ui.Button(label="🔙 กดเพื่อไปดูผลลัพธ์", style=discord.ButtonStyle.link, url=sent_msg.jump_url, emoji="✨")
                view_back.add_item(btn_back)
                await channel.send(embed=discord.Embed(title="✅ เรียบร้อย!", description="ห้องจะลบใน 10 วินาที", color=0x00ff00), view=view_back)
            
            await asyncio.sleep(10)
            await channel.delete()
        except: await channel.delete()

# ==========================================
# ⚡ Slash Commands
# ==========================================

@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"✅ Synced {len(synced)} commands.")

# 1. ระบบถาม AI (แก้บั๊กแล้ว)
@bot.tree.command(name="ถาม", description="🤖 คุยกับท่านจอมยุทธ์ (AI)")
@app_commands.describe(question="เรื่องที่อยากถาม")
async def ask_ai(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    
    # เช็คว่า AI พร้อมไหม
    if model is None:
        await interaction.followup.send("⚠️ **ลมปราณติดขัด!** (ระบบ AI ยังไม่พร้อม หรือ API Key ผิดพลาด)", ephemeral=True)
        return

    try:
        full_prompt = f"{BOT_PERSONA}\n\nคำถาม: {question}\nคำตอบ:"
        response = model.generate_content(full_prompt)
        text = response.text[:1900] + "..." if len(response.text) > 1900 else response.text
        
        embed = discord.Embed(title="🗣️ ท่านจอมยุทธ์กล่าว...", description=text, color=0x00ffcc)
        embed.set_footer(text=f"Q: {question} | โดย {interaction.user.name}")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"😵 **ธาตุไฟเข้าแทรก!** (Error: {e})", ephemeral=True)

# 2. ระบบดูดวง (ฉบับ Tune/เกลือ)
@bot.tree.command(name="ดูดวง", description="🔮 เช็คดวงกาชา/ตีบวก ประจำวัน")
async def fortune(interaction: discord.Interaction):
    if interaction.channel.name != ALLOWED_CHANNEL_FORTUNE:
        await interaction.response.send_message(f"❌ **ผิดห้องครับ!**\nเล่นได้เฉพาะห้อง `{ALLOWED_CHANNEL_FORTUNE}` เท่านั้นครับ", ephemeral=True)
        return

    fortunes = [
        "🌟 **เทพเจ้า RNG ประทับร่าง!** วันนี้กดอะไรก็ติด ออฟชั่นทองมาแน่!",
        "💀 **เกลือเค็มปี๋...** อย่าหาทำ Tune ออฟชั่นกาก พักก่อนโยม",
        "🔥 **มือร้อน(เงิน)!** ระวังหมดตัวนะเพื่อน เรท 0.98% มันไม่มีจริงหรอก",
        "🟢 **สีเขียวเหนี่ยวทรัพย์** วันนี้ได้แต่ของกากๆ แน่นอน ทำใจซะ",
        "📈 **ดวงกลางๆ** พอถูไถ แต่อย่าหวังของแรร์เลย แค่ได้ของปลอบใจก็ดีแล้ว",
        "💎 **มีแววเสียตังค์ฟรี** เปอร์เซ็นต์สำเร็จ 99% = เกลือ (ตามสูตรเกม)",
        "✨ **แสงสีทองรออยู่!** (ในฝันนะ) ของจริงน่าจะได้แค่เกลือ",
        "🧘 **ไปทำบุญ 9 วัดก่อน** ค่อยมาสุ่ม ดวงมืดมนมากวันนี้ ราหูอมกาชา",
        "⚔️ **จอมยุทธ์ถังแตก** วันนี้ดวงการเงินรั่วไหล อย่าเสี่ยงดวงเลย เก็บตังค์กินข้าวเถอะ",
        "🧧 **GM รักคุณ** (รักที่จะกินตังค์คุณ) กดกาชาทีไร น้ำตาไหลพรากทุกที"
    ]
    result = random.choice(fortunes)
    
    if "เทพเจ้า" in result or "แสง" in result: color = 0xffd700
    elif "เกลือ" in result or "ถังแตก" in result: color = 0x000000
    else: color = 0x3498db

    embed = discord.Embed(title="🎲 ผลการเสี่ยงทายดวงชะตา", description=f"ผลลัพธ์ของ {interaction.user.mention} คือ...\n\n{result}", color=color)
    await interaction.response.send_message(embed=embed)

# 3. ล้างแชท
@bot.tree.command(name="ล้าง", description="🧹 ลบข้อความล่าสุด")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_chat(interaction: discord.Interaction, amount: int):
    if amount > 100: return await interaction.response.send_message("❌ สูงสุด 100 ครับ", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send("🧹 เรียบร้อย!", ephemeral=True)

# 4. ล้างห้อง (Nuke)
@bot.tree.command(name="ล้างห้อง", description="⚠️ ลบห้องนี้ทิ้งแล้วสร้างใหม่ (Nuke)")
@app_commands.checks.has_permissions(administrator=True)
async def nuke_channel(interaction: discord.Interaction):
    view = discord.ui.View()
    async def confirm(i):
        if i.user != interaction.user: return
        await i.response.send_message("💣 บึ้มมมม...", ephemeral=True)
        new_ch = await interaction.channel.clone(reason="Nuke by Bot")
        await interaction.channel.delete()
        await new_ch.send(f"✨ **ห้องใหม่ไฉไลกว่าเดิม!** (ล้างโดย {interaction.user.mention})")
    
    btn = discord.ui.Button(label="ยืนยันที่จะล้างห้อง?", style=discord.ButtonStyle.danger, emoji="💣")
    btn.callback = confirm
    view.add_item(btn)
    
    await interaction.response.send_message("⚠️ **คำเตือน:** ห้องนี้จะถูกลบและสร้างใหม่ ข้อความทั้งหมดจะหายไป!", view=view, ephemeral=True)

@bot.event
async def on_ready():
    log(f"✅ Logged in as {bot.user}")
    bot.add_view(TicketButton())

@bot.command()
async def setup(ctx):
    await ctx.message.delete()
    await refresh_setup_msg(ctx.channel)

keep_alive()
try: bot.run(os.environ['TOKEN'])
except: print("Error: Token not found")
