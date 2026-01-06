import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import json
import os
import random  # ✅ เพิ่ม: สำหรับสุ่มดวง
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

# --- ระบบจัดการไฟล์ประวัติ ---
def load_history():
    if not os.path.exists(HISTORY_FILE): return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

user_history = load_history()

# --- ฟังก์ชัน Log ---
def log(message):
    time_str = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{time_str}] {message}")

# --- 🔥 ฟังก์ชันรีเฟรชปุ่ม Setup ---
async def refresh_setup_msg(channel):
    try:
        async for message in channel.history(limit=30):
            if message.author == bot.user and message.embeds:
                if message.embeds[0].title == "📢 ยืนยันตัวตน / แนะนำตัว":
                    await message.delete()
    except Exception as e:
        log(f"⚠️ ลบปุ่มเก่าไม่สำเร็จ: {e}")

    embed = discord.Embed(
        title="📢 ยืนยันตัวตน / แนะนำตัว",
        description="กดปุ่มด้านล่างเพื่อเปิดห้องส่วนตัวสำหรับแนะนำตัวครับ 👇",
        color=0x00ff00)
    await channel.send(embed=embed, view=TicketButton())
    log("🔄 ย้ายปุ่ม Setup มาล่างสุดเรียบร้อย")

# --- Dropdown ---
class GameSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Where Winds Meet", emoji="⚔️", description="จอมยุทธ์"),
            discord.SelectOption(label="อื่นๆ", emoji="🎮", description="เกมทั่วไป")
        ]
        super().__init__(placeholder="เลือกเกมที่คุณเล่น...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_value = self.values[0]
        await interaction.response.defer()
        self.view.stop()

class GameView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.selected_value = None
        self.add_item(GameSelect())

# --- ปุ่มกดหลัก ---
class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 กดเพื่อเริ่มแนะนำตัว", style=discord.ButtonStyle.green, custom_id="start_intro")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        guild = interaction.guild
        log(f"🟢 [Start] User '{user.name}' กดปุ่มสร้าง Ticket")

        await interaction.response.send_message("⏳ กำลังเตรียมห้องส่วนตัว...", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel_name = f"verify-{user.name}"
        try:
            ticket_channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
            log(f"🏠 [Room] สร้างห้อง {channel_name} สำเร็จ")
        except Exception as e:
            log(f"❌ [Error] สร้างห้องไม่ได้: {e}")
            return

        view_link = discord.ui.View()
        btn_link = discord.ui.Button(
            label="👉 กดปุ่มนี้ เพื่อเข้าห้องส่วนตัวทันที 👈",
            style=discord.ButtonStyle.link,
            url=ticket_channel.jump_url,
            emoji="🚪")
        view_link.add_item(btn_link)

        await interaction.edit_original_response(
            content=f"✅ **สร้างห้องเรียบร้อยครับ! {user.mention}**\n\n⬇️⬇️ **กดปุ่มสีเทาด้านล่างนี้ เพื่อเริ่มแนะนำตัว** ⬇️⬇️",
            view=view_link)
        
        await self.start_interview(ticket_channel, user, guild)

    async def start_interview(self, channel, user, guild):
        data = {"name": "", "age": "", "game": "", "char_name": "-"}
        def check(m): return m.author == user and m.channel == channel

        try:
            await channel.send(f"{user.mention} **ยินดีต้อนรับครับ!** (ตอบคำถามในห้องนี้ได้เลย)")

            # 1. ชื่อ
            await channel.send(embed=discord.Embed(title="1. ชื่อของคุณคือ?", color=0x3498db))
            msg_name = await bot.wait_for("message", check=check, timeout=300)
            data["name"] = msg_name.content

            # 2. อายุ
            await channel.send(embed=discord.Embed(title="2. อายุเท่าไหร่?", color=0x3498db))
            msg_age = await bot.wait_for("message", check=check, timeout=300)
            data["age"] = msg_age.content

            # 3. เกม
            view = GameView()
            await channel.send(embed=discord.Embed(title="3. เลือกเกมที่คุณเล่น", color=0x3498db), view=view)
            await view.wait()
            if view.selected_value is None:
                await channel.delete()
                return
            data["game"] = view.selected_value

            if data["game"] == "Where Winds Meet":
                await channel.send(embed=discord.Embed(title="⚔️ ชื่อตัวละครของคุณคือ?", color=0xe74c3c))
                msg_char = await bot.wait_for("message", check=check, timeout=300)
                data["char_name"] = msg_char.content
                
                role_wwm = discord.utils.get(guild.roles, name=ROLE_WWM)
                if role_wwm: await user.add_roles(role_wwm)

            # --- บันทึก ---
            await channel.send("⏳ **กำลังตรวจสอบและบันทึกข้อมูล...**")
            embed_summary = discord.Embed(title="✅ สมาชิกใหม่รายงานตัว!", color=0xffd700)
            summary_text = f"**ชื่อ :** {data['name']}\n**อายุ :** {data['age']}\n**เกมที่เล่น :** {data['game']}"
            if data["game"] == "Where Winds Meet":
                summary_text += f"\n**ชื่อในเกม :** {data['char_name']}"
            embed_summary.description = summary_text
            if user.avatar: embed_summary.set_thumbnail(url=user.avatar.url)
            embed_summary.set_footer(text=f"แนะนำตัวโดย {user.name}")

            public_channel = discord.utils.get(guild.text_channels, name=PUBLIC_CHANNEL)
            if public_channel:
                user_id_str = str(user.id)
                if user_id_str in user_history:
                    try:
                        old_msg = await public_channel.fetch_message(user_history[user_id_str])
                        await old_msg.delete()
                    except: pass

                sent_msg = await public_channel.send(embed=embed_summary)
                user_history[user_id_str] = sent_msg.id
                save_history(user_history)
                await refresh_setup_msg(public_channel)

                view_back = discord.ui.View()
                btn_back = discord.ui.Button(label="🔙 กดปุ่มนี้ เพื่อกลับไปดูผลลัพธ์ 🔙", style=discord.ButtonStyle.link, url=sent_msg.jump_url, emoji="✨")
                view_back.add_item(btn_back)
                embed_finish = discord.Embed(title="✅ บันทึกข้อมูลเรียบร้อย!", description="ห้องนี้จะถูกลบใน **15 วินาที**\n\n⬇️ **กดปุ่มด้านล่างเพื่อกลับไปหน้าหลักครับ** ⬇️", color=0x00ff00)
                await channel.send(embed=embed_finish, view=view_back)

            role_basic = discord.utils.get(guild.roles, name=ROLE_VERIFIED)
            if role_basic: await user.add_roles(role_basic)

            await asyncio.sleep(15)
            await channel.delete()

        except asyncio.TimeoutError:
            await channel.delete()
        except Exception as e:
            log(f"❌ Error: {e}")

# ==========================================
# ⚡ ระบบ Slash Command (เมนูเด้ง) & ดูดวง
# ==========================================

# 1. คำสั่ง Sync (สำคัญ! ต้องพิมพ์ -sync ก่อน เมนูถึงจะขึ้น)
@bot.command()
async def sync(ctx):
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ ซิงค์คำสั่งเรียบร้อยแล้ว {len(synced)} คำสั่ง! (ลองพิมพ์ / ดูได้เลย)")
        log(f"🔁 Synced {len(synced)} commands")
    except Exception as e:
        await ctx.send(f"❌ ซิงค์ไม่ผ่าน: {e}")

# 2. คำสั่งดูดวง (Slash Command)
@bot.tree.command(name="ดูดวง", description="เช็คดวงกาชา/ตีบวก ประจำวัน (แม่นยำ 0.0001%)")
async def fortune(interaction: discord.Interaction):
    
    # 📜 รายการคำทำนาย (กวนๆ + เรทเกลือ)
    fortunes = [
        "🌟 **เทพเจ้า RNG ประทับร่าง!** วันนี้กดอะไรก็ติด ออฟชั่นทองมาแน่! (รีบกดก่อนหมดโปร)",
        "💀 **เกลือเค็มปี๋...** อย่าหาทำ ตีบวกแหก ออฟชั่นกาก พักก่อนโยม",
        "🔥 **มือร้อน(เงิน)!** ระวังหมดตัวนะเพื่อน เรท 0.01% มันไม่มีจริงหรอก",
        "🟢 **สีเขียวเหนี่ยวทรัพย์** วันนี้ได้แต่ของกากๆ แน่นอน ทำใจซะ",
        "📈 **ดวงกลางๆ** พอถูไถ แต่อย่าหวังของแรร์เลย แค่ตีไม่แตกก็บุญแล้ว",
        "💎 **มีแววเสียตังค์ฟรี** เปอร์เซ็นต์สำเร็จ 99% = แตก (ตามสูตรเกม)",
        "✨ **แสงสีทองรออยู่!** (ในฝันนะ) ของจริงน่าจะได้แค่เศษเหล็ก",
        "🧘 **ไปทำบุญ 9 วัดก่อน** ค่อยมาสุ่ม ดวงมืดมนมากวันนี้ ราหูอมกาชา",
        "⚔️ **จอมยุทธ์ถังแตก** วันนี้ดวงการเงินรั่วไหล อย่าเสี่ยงดวงเลย เก็บตังค์กินข้าวเถอะ",
        "🧧 **GM รักคุณ** (รักที่จะกินตังค์คุณ) กดกาชาทีไร น้ำตาไหลพรากทุกที"
    ]
    
    result = random.choice(fortunes)
    
    # สีของ Embed (ถ้าดวงดีสีทอง, ถ้าเกลือสีดำ, อื่นๆ สุ่ม)
    if "เทพเจ้า" in result or "แสงสีทอง" in result:
        color = 0xffd700 # ทอง
    elif "เกลือ" in result or "ถังแตก" in result:
        color = 0x000000 # ดำ
    else:
        color = 0x3498db # ฟ้า

    embed = discord.Embed(
        title="🎲 ผลการเสี่ยงทายดวงชะตา", 
        description=f"ผลลัพธ์ของ {interaction.user.mention} คือ...\n\n{result}",
        color=color
    )
    # ใส่รูปฮาๆ หรือไอคอนได้ถ้าต้องการ
    embed.set_footer(text="คำเตือน: โปรดใช้วิจารณญาณในการสุ่ม (อย่าเชื่อบอทมาก)")

    await interaction.response.send_message(embed=embed)

# ==========================================

@bot.event
async def on_ready():
    print('-------------------------------------------')
    log(f"✅ บอทออนไลน์: {bot.user}")
    bot.add_view(TicketButton())

@bot.command()
async def setup(ctx):
    await ctx.message.delete()
    await refresh_setup_msg(ctx.channel)
    log(f"🛠️  Setup ปุ่มในห้อง {ctx.channel.name}")

keep_alive()

try:
    token = os.environ['TOKEN']
    if token == "":
        print("Error: ไม่พบ TOKEN ใน Secrets")
    else:
        bot.run(token)
except KeyError:
    print("Error: อย่าลืมตั้งค่า Secrets (รูปกุญแจ) ใส่ TOKEN ก่อนนะครับ")
