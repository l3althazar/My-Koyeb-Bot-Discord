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

# 🔥 IMPORT KEEP_ALIVE
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
# ⚙️ ตั้งค่า (Config)
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
# 🧠 AI Setup (แก้ไขเวอร์ชันโมเดลให้ถูกต้อง)
# ==========================================
BOT_PERSONA = """
คุณคือ "Devils DenBot" AI ผู้ช่วยอัจฉริยะประจำกิลด์
ตัวตนของคุณ: เป็นปัญญาประดิษฐ์ที่มีความรอบรู้ แต่มีจิตวิญญาณของจอมยุทธ์แฝงอยู่
สไตล์การตอบ:
1. วิชาการ: จริงจัง ชัดเจน ถูกต้อง
2. คุยเล่น: กวนนิดๆ สไตล์หนังจีนกำลังภายใน เรียกผู้ใช้ว่า "สหาย"
"""

model = None
AI_STATUS = "Unknown"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

try:
    if not GEMINI_API_KEY:
        AI_STATUS = "❌ ไม่พบ Key"
    else:
        genai.configure(api_key=GEMINI_API_KEY)
        # แก้ไขจาก 2.5 เป็น 1.5 flash เพื่อความถูกต้อง
        model = genai.GenerativeModel('gemini-1.5-flash') 
        AI_STATUS = "✅ พร้อมใช้งาน"
        logger.info("✅ Gemini Model loaded.")
except Exception as e:
    AI_STATUS = f"💥 Error: {str(e)}"

# ==========================================
# [ระบบจัดการไฟล์ และ Class UI ต่างๆ คงเดิมไว้ทั้งหมด]
# ==========================================

def load_json(filename):
    if not os.path.exists(filename): return []
    try:
        with open(filename, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

leave_data = load_json(LEAVE_FILE)

# --- ใส่ Class UI ต่างๆ (LeaveApprovalView, LeaveModal, ฯลฯ) กลับมาตามโค้ดเดิมของคุณ ---
# (เพื่อความกระชับในคำตอบนี้ ผมละส่วนโค้ด Class เดิมไว้นะครับ แต่ในไฟล์จริงของคุณให้คงไว้เหมือนเดิม)

# [ยกตัวอย่างฟังก์ชันที่ต้องมีเพื่อไม่ให้ error]
class LeaveButtonView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 เขียนใบลา", style=discord.ButtonStyle.danger, custom_id="open_leave_modal", emoji="📜")
    async def open_leave(self, interaction, button):
        # โค้ดภายในคงเดิม
        pass

class TicketButton(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📝 กดเพื่อเริ่มแนะนำตัว", style=discord.ButtonStyle.green, custom_id="start_intro_main")
    async def start_intro(self, interaction, button):
        # โค้ดภายในคงเดิม
        pass

class LeaveApprovalView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    # โค้ดภายในคงเดิม

# ==========================================
# 🛡️ ส่วนที่มีการแก้ไขสำคัญ (Events & Commands)
# ==========================================

@bot.event
async def on_ready():
    logger.info(f"🚀 Logged in as {bot.user}")
    
    # ✅ จดจำปุ่ม (Persistent Views) เพื่อให้ปุ่มเก่าในดิสคอร์ดไม่พัง
    bot.add_view(TicketButton())
    bot.add_view(LeaveButtonView())
    bot.add_view(LeaveApprovalView()) 

    # ❌ ลบ Loop refresh_leave_msg ออก เพื่อป้องกัน Error 1015
    # หากต้องการส่งข้อความใหม่ ให้ใช้คำสั่ง -setup ด้วยตัวเอง
    
    await bot.change_presence(activity=discord.Game(name="Where Winds Meet"))
    keep_alive()

@bot.command()
async def setup(ctx):
    """คำสั่งสำหรับ Setup หน้าจอแนะนำตัวและหน้าแจ้งลา (รันมือเท่านั้น)"""
    await ctx.message.delete()
    
    # ค้นหาห้องและรีเฟรชข้อความ (ฟังก์ชันเดิมของคุณ)
    pub_ch = discord.utils.get(ctx.guild.text_channels, name=PUBLIC_CHANNEL)
    leave_ch = discord.utils.get(ctx.guild.text_channels, name=CHANNEL_LEAVE)
    
    if pub_ch: await refresh_setup_msg(pub_ch)
    if leave_ch: await refresh_leave_msg(ctx.guild)
    
    await ctx.send("✅ ระบบ Setup เสร็จสิ้น", delete_after=5)

# --- คำสั่งอื่นๆ (ask_ai, fortune, clear, sync) ให้คงไว้ตามเดิมทุกประการ ---

# ==========================================
# 🚀 RUN BOT
# ==========================================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    logger.critical("❌ ไม่พบ DISCORD_TOKEN")
