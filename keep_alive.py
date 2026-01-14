from flask import Flask, render_template_string
import os

app = Flask('')

html_code = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Devils DenBot | Official Site</title>
    <link rel="icon" href="https://cdn.discordapp.com/attachments/1459905133084410020/1461017854873698535/24a9109c-758b-4252-a908-a1517a93f76a.png?ex=69690669&is=6967b4e9&hm=aa4ab1269d3a96bed6c4cc28c80f7a39e63848b8951913de7419d96dd140c7a39e63848b8951913de7419d96dd140c7a39e63848b8951913de7419d96dd140c7a39e63848b8951913de7419d96dd140c7a39e63848b8951913de7419d96dd140c7a8&">
    
    <link href="https://fonts.googleapis.com/css2?family=Uncial+Antiqua&family=Prompt:wght@300;400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --primary: #c00000;
            --accent: #d4af37;
            --bg-dark: #0a0a0a;
            --text-main: #ffffff;
            --text-muted: #b0b0b0;
            --glass: rgba(0, 0, 0, 0.7);
            --glass-border: rgba(255, 255, 255, 0.1);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: 'Prompt', sans-serif;
            overflow-x: hidden;
            line-height: 1.6;
        }

        /* Background */
        .bg-layer {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -3;
            background: url('https://cdn.discordapp.com/attachments/1459905133084410020/1461017831310098563/ChatGPT_Image_9_.._2569_00_05_07.png?ex=69690663&is=6967b4e3&hm=f13d1d509c1ebe2e010d17ee67532735bea7375eed6bf0d70193317a43d37c46&') no-repeat center center/cover;
        }
        .overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -2;
            background: linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.4) 50%, rgba(0,0,0,0.9) 100%);
        }

        /* Fog Animation */
        .fog-container {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            overflow: hidden; z-index: -1; pointer-events: none;
        }
        .fog-img {
            position: absolute; height: 100vh; width: 300vw;
            background: url('https://raw.githubusercontent.com/danielstuart14/CSS_FOG_ANIMATION/master/fog1.png') repeat-x;
            background-size: contain; animation: fog 60s linear infinite; opacity: 0.3;
        }
        .fog-img-2 {
            background: url('https://raw.githubusercontent.com/danielstuart14/CSS_FOG_ANIMATION/master/fog2.png') repeat-x;
            background-size: contain; animation: fog 40s linear infinite;
            z-index: -1; top: 30%; opacity: 0.2;
        }
        @keyframes fog { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-200vw, 0, 0); } }

        /* Navbar */
        nav {
            display: flex; justify-content: space-between; align-items: center;
            padding: 20px 50px;
            position: fixed; width: 100%; top: 0; z-index: 1000;
            background: rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--glass-border);
        }
        .brand {
            font-family: 'Uncial Antiqua', cursive; font-size: 1.5rem;
            color: var(--text-main); letter-spacing: 2px;
        }
        .brand span { color: var(--primary); }
        
        .nav-links a {
            color: var(--text-muted); text-decoration: none; margin-left: 30px;
            font-size: 0.9rem; transition: 0.3s; text-transform: uppercase; letter-spacing: 1px;
        }
        .nav-links a:hover { color: var(--accent); }
        .btn-main {
            padding: 10px 25px; background: transparent; border: 1px solid var(--accent);
            color: var(--accent); text-decoration: none; border-radius: 2px;
            font-weight: 600; transition: all 0.3s ease;
            text-transform: uppercase; font-size: 0.85rem; letter-spacing: 1px;
        }
        .btn-main:hover {
            background: var(--accent); color: #000; box-shadow: 0 0 20px rgba(212, 175, 55, 0.4);
        }

        /* Hero Section */
        .hero {
            min-height: 90vh; display: flex; flex-direction: column;
            justify-content: center; align-items: center; text-align: center;
            padding: 150px 20px 50px;
        }
        
        h1 {
            font-family: 'Uncial Antiqua', cursive; font-size: 4rem; margin-bottom: 10px;
            color: var(--primary);
            text-shadow: 0 0 20px rgba(192, 0, 0, 0.5);
            letter-spacing: 3px;
        }
        
        .tagline {
            font-size: 1.2rem; color: var(--text-muted); margin-bottom: 40px;
            font-weight: 300; max-width: 700px;
        }

        /* Stats Bar (Static Version) */
        .stats-bar {
            display: flex; gap: 30px; margin-top: 30px;
            padding: 25px 50px;
            background: var(--glass);
            border: 1px solid var(--glass-border);
            border-radius: 50px;
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .stat-item { text-align: center; min-width: 120px; }
        .stat-val { 
            font-family: 'Uncial Antiqua', cursive; font-size: 2rem; 
            color: #2ecc71; /* Green for Online */
            text-shadow: 0 0 10px rgba(46, 204, 113, 0.3);
        }
        .stat-label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }

        /* Features */
        .features {
            padding: 100px 50px;
            max-width: 1200px; margin: 0 auto;
        }
        .section-title {
            font-family: 'Uncial Antiqua', cursive; text-align: center; font-size: 2.5rem;
            color: var(--text-main); margin-bottom: 70px;
            position: relative;
        }
        .section-title::after {
            content: ''; display: block; width: 80px; height: 3px;
            background: var(--primary); margin: 20px auto 0;
        }

        .grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 30px;
        }
        .card {
            background: linear-gradient(145deg, rgba(25,25,25,0.8), rgba(15,15,15,0.9));
            padding: 40px 35px; border: 1px solid var(--glass-border);
            border-radius: 8px; transition: 0.4s;
            position: relative; overflow: hidden;
            backdrop-filter: blur(5px);
        }
        .card:hover {
            transform: translateY(-7px);
            border-color: var(--primary);
            box-shadow: 0 15px 50px rgba(192, 0, 0, 0.2);
        }
        .card i { font-size: 2.5rem; color: var(--primary); margin-bottom: 25px; }
        .card h3 { 
            font-family: 'Uncial Antiqua', cursive; margin-bottom: 15px; 
            color: var(--text-main); font-size: 1.4rem; letter-spacing: 1px;
        }
        .card p { font-size: 0.95rem; color: var(--text-muted); font-weight: 300; line-height: 1.7; }

        footer {
            text-align: center; padding: 50px 20px; color: #666; font-size: 0.9rem;
            background: #050505; border-top: 1px solid rgba(255,255,255,0.05);
        }

        @media (max-width: 768px) {
            h1 { font-size: 2.8rem; }
            .nav-links { display: none; }
            .stats-bar { flex-direction: column; gap: 20px; padding: 30px; border-radius: 20px; width: 80%; }
            nav { padding: 20px; }
            .hero { padding-top: 120px; }
        }
    </style>
</head>
<body>

    <div class="bg-layer"></div>
    <div class="overlay"></div>
    <div class="fog-container">
        <div class="fog-img"></div>
        <div class="fog-img-2"></div>
    </div>

    <nav>
        <div class="brand">DEVILS <span>DEN</span></div>
        <div class="nav-links">
            <a href="#">Home</a>
            <a href="#features">Features</a>
            <a href="https://www.facebook.com/l3althazar.bas" target="_blank">Contact</a>
            <a href="https://discord.com/oauth2/authorize?client_id=1457301588937801739&permissions=8&integration_type=0&scope=bot" class="btn-main">Invite Bot</a>
        </div>
    </nav>

    <section class="hero">
        <h1>DEVILS-DEN-BOT</h1>
        <p class="tagline">
            ผู้ช่วยอัจฉริยะสำหรับ Discord ของคุณ<br>
            จัดการสมาชิก, ระบบกิจกรรม, และความบันเทิง ครบจบในที่เดียวด้วยมาตรฐานระดับสากล
        </p>

        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-val">ONLINE</div>
                <div class="stat-label">System Status</div>
            </div>
            <div class="stat-item">
                <div class="stat-val" style="color: var(--accent);">V.2.0</div>
                <div class="stat-label">Current Version</div>
            </div>
        </div>
    </section>

    <section id="features" class="features">
        <h2 class="section-title">SYSTEM FEATURES</h2>
        <div class="grid">
            <div class="card">
                <i class="fas fa-list-ol"></i>
                <h3>Queue System</h3>
                <p>ระบบจัดคิวลงดันเจี้ยนหรือกิจกรรมต่างๆ แบบ Real-time ใช้งานง่ายด้วยปุ่มกด ไม่ต้องพิมพ์คำสั่งให้ยุ่งยาก</p>
            </div>
            <div class="card">
                <i class="fas fa-user-clock"></i>
                <h3>Leave & Approval</h3>
                <p>ระบบยื่นใบลาพร้อมฟังก์ชันอนุมัติสำหรับ Admin ช่วยให้การจัดการสมาชิกในกิลด์เป็นระเบียบและมีมาตรฐาน</p>
            </div>
            <div class="card">
                <i class="fas fa-user-check"></i>
                <h3>Verification</h3>
                <p>ระบบยืนยันตัวตนสำหรับสมาชิกใหม่ ช่วยคัดกรองคนและมอบยศเริ่มต้นให้อัตโนมัติ</p>
            </div>
            <div class="card">
                <i class="fas fa-dice"></i>
                <h3>Fortune & Fun</h3>
                <p>ระบบเสี่ยงดวงทำนายโชคชะตาประจำวัน และมินิเกมต่างๆ เพื่อสร้างสีสันและความบันเทิงในเซิร์ฟเวอร์</p>
            </div>
            <div class="card">
                <i class="fas fa-robot"></i>
                <h3>AI Assistant</h3>
                <p>พูดคุยและสอบถามข้อมูลกับ AI อัจฉริยะ (Gemini) ที่พร้อมตอบคำถามของคุณได้ตลอดเวลา</p>
            </div>
            <div class="card">
                <i class="fas fa-gavel"></i>
                <h3>Moderation Tools</h3>
                <p>เครื่องมือสำหรับผู้ดูแลระบบ เช่น การลบข้อความจำนวนมาก หรือการรีเซ็ตห้องแชท เพื่อความเรียบร้อย</p>
            </div>
        </div>
    </section>

    <footer>
        <p>© 2026 Devils DenBot. All Rights Reserved. | Designed by ท่านจอมยุทธ์</p>
    </footer>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(html_code)

# ถ้าจะรันใน Render ไม่ต้องมี if __name__ == '__main__' ก็ได้
# เพราะเราสั่ง gunicorn keep_alive:app แล้ว
