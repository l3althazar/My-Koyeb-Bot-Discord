from flask import Flask, render_template_string

app = Flask('')

html_code = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Devils DenBot | The Ultimate Guardian</title>
    <link rel="icon" href="https://cdn.discordapp.com/attachments/1459905133084410020/1461017854873698535/24a9109c-758b-4252-a908-a1517a93f76a.png?ex=69690669&is=6967b4e9&hm=aa4ab1269d3a96bed6c4cc28c80f7a39e63848b8951913de7419d96dd140c7a39e63848b8951913de7419d96dd140c7a39e63848b8951913de7419d96dd140c7a8&">
    
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Prompt:wght@300;400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --primary: #c00000;       /* Crimson Red */
            --accent: #d4af37;        /* Luxury Gold */
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

        /* Background Setup */
        .bg-layer {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -2;
            background: url('https://cdn.discordapp.com/attachments/1459905133084410020/1461017831310098563/ChatGPT_Image_9_.._2569_00_05_07.png?ex=69690663&is=6967b4e3&hm=f13d1d509c1ebe2e010d17ee67532735bea7375eed6bf0d70193317a43d37c46&') no-repeat center center/cover;
        }
        .overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
            background: linear-gradient(to bottom, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.4) 50%, rgba(0,0,0,0.9) 100%);
        }

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
            font-family: 'Cinzel', serif; font-size: 1.5rem; font-weight: 700;
            color: var(--text-main); letter-spacing: 2px;
            text-transform: uppercase;
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
            height: 100vh; display: flex; flex-direction: column;
            justify-content: center; align-items: center; text-align: center;
            padding: 0 20px;
        }
        
        .profile-container {
            position: relative; margin-bottom: 30px;
        }
        .bot-img {
            width: 180px; height: 180px; border-radius: 50%;
            object-fit: cover;
            border: 2px solid var(--primary);
            box-shadow: 0 0 60px rgba(192, 0, 0, 0.3);
            animation: pulse-glow 3s infinite alternate;
        }
        
        @keyframes pulse-glow {
            from { box-shadow: 0 0 20px rgba(192, 0, 0, 0.2); }
            to { box-shadow: 0 0 50px rgba(192, 0, 0, 0.6); transform: scale(1.02); }
        }

        h1 {
            font-family: 'Cinzel', serif; font-size: 3.5rem; margin-bottom: 10px;
            background: linear-gradient(45deg, #fff, #b0b0b0);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 10px 20px rgba(0,0,0,0.5);
        }
        
        .tagline {
            font-size: 1.1rem; color: var(--text-muted); margin-bottom: 40px;
            font-weight: 300; letter-spacing: 1px; max-width: 600px;
        }
        .highlight { color: var(--primary); font-weight: 500; }

        .stats-bar {
            display: flex; gap: 40px; margin-top: 40px;
            padding: 20px 40px;
            background: var(--glass);
            border: 1px solid var(--glass-border);
            border-radius: 50px;
            backdrop-filter: blur(10px);
        }
        .stat-item { text-align: center; }
        .stat-val { font-family: 'Cinzel', serif; font-size: 1.5rem; color: var(--text-main); }
        .stat-label { font-size: 0.75rem; color: var(--accent); text-transform: uppercase; letter-spacing: 2px; }

        /* Features */
        .features {
            padding: 100px 50px;
            max-width: 1200px; margin: 0 auto;
        }
        .section-title {
            font-family: 'Cinzel', serif; text-align: center; font-size: 2rem;
            color: var(--text-main); margin-bottom: 60px;
            position: relative; display: inline-block; left: 50%; transform: translateX(-50%);
        }
        .section-title::after {
            content: ''; display: block; width: 60px; height: 2px;
            background: var(--primary); margin: 15px auto 0;
        }

        .grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px;
        }
        .card {
            background: linear-gradient(145deg, rgba(20,20,20,0.6), rgba(10,10,10,0.8));
            padding: 40px 30px; border: 1px solid var(--glass-border);
            border-radius: 4px; transition: 0.4s;
            position: relative; overflow: hidden;
        }
        .card:hover {
            transform: translateY(-5px);
            border-color: var(--primary);
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }
        .card i { font-size: 2rem; color: var(--primary); margin-bottom: 20px; }
        .card h3 { font-family: 'Cinzel', serif; margin-bottom: 15px; color: var(--text-main); font-size: 1.2rem; }
        .card p { font-size: 0.9rem; color: var(--text-muted); font-weight: 300; }

        footer {
            text-align: center; padding: 40px; color: #555; font-size: 0.8rem;
            border-top: 1px solid rgba(255,255,255,0.05); background: #050505;
        }

        /* Mobile */
        @media (max-width: 768px) {
            h1 { font-size: 2.5rem; }
            .nav-links { display: none; }
            .stats-bar { flex-direction: column; gap: 15px; border-radius: 10px; }
            nav { padding: 20px; }
        }
    </style>
</head>
<body>

    <div class="bg-layer"></div>
    <div class="overlay"></div>

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
        <div class="profile-container">
            <img src="https://cdn.discordapp.com/attachments/1459905133084410020/1461017854873698535/24a9109c-758b-4252-a908-a1517a93f76a.png?ex=69690669&is=6967b4e9&hm=aa4ab1269d3a96bed6c4cc28c80f7a39e63848b8951913de7419d96dd140c7a39e63848b8951913de7419d96dd140c7a39e63848b8951913de7419d96dd140c7a39e63848b8951913de7419d96dd140c7a8&" alt="Devils Den Bot" class="bot-img">
        </div>
        
        <h1>DEVILS DENBOT</h1>
        <p class="tagline">
            "ข้าคือจอมยุทธ์เด๊ะ" — ผู้พิทักษ์แห่ง <span class="highlight">Where Winds Meet</span><br>
            ระบบจัดการกิลด์ครบวงจร ด้วยมาตรฐานระดับสากล
        </p>

        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-val">24/7</div>
                <div class="stat-label">Online</div>
            </div>
            <div class="stat-item">
                <div class="stat-val">RPG</div>
                <div class="stat-label">Systems</div>
            </div>
            <div class="stat-item">
                <div class="stat-val">100%</div>
                <div class="stat-label">Secure</div>
            </div>
        </div>
    </section>

    <section id="features" class="features">
        <h2 class="section-title">CORE FEATURES</h2>
        <div class="grid">
            <div class="card">
                <i class="fas fa-scroll"></i>
                <h3>Advanced Queue</h3>
                <p>ระบบจัดคิวลงดันเจี้ยนและบอสโลกแบบ Real-time พร้อมปุ่มกดที่ใช้งานง่าย ไม่ต้องพิมพ์คำสั่ง</p>
            </div>
            <div class="card">
                <i class="fas fa-gavel"></i>
                <h3>Approval System</h3>
                <p>ระบบใบลาที่มีมาตรฐาน พร้อมฟังก์ชันอนุมัติสำหรับ Admin เพื่อความเป็นระเบียบของกิลด์</p>
            </div>
            <div class="card">
                <i class="fas fa-dice-d20"></i>
                <h3>Fortune & RPG</h3>
                <p>ระบบเสี่ยงดวงทำนายโชคชะตา และมินิเกมที่จะทำให้สมาชิกในกิลด์สนุกสนานไม่มีเบื่อ</p>
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
