from flask import Flask, render_template_string
from threading import Thread

app = Flask('')

# 🎨 HTML/CSS/JS ชุดใหญ่ (ธีม Modern Gothic Ultimate)
html_code = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Devils DenBot | The Modern Gothic</title>
    <link rel="icon" href="https://cdn.discordapp.com/avatars/1457301588937801739/a334b0c7937402868297495034875321.png">
    
    <link href="https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700&family=Kanit:wght@300;400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --primary: #ff003c; /* แดงสดแบบนีออน */
            --secondary: #70001a; /* แดงเลือดหมู */
            --bg-dark: #0a0a0a; /* ดำสนิท */
            --bg-navbar: #140505; /* ดำอมแดงสำหรับเมนู */
            --text: #e0e0e0;
            --neon-glow: 0 0 15px var(--primary), 0 0 30px var(--secondary);
        }

        body {
            background-color: var(--bg-dark);
            color: var(--text);
            font-family: 'Kanit', sans-serif;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
            /* เพิ่ม Texture พื้นหลังแบบ Gothic */
            background-image: radial-gradient(circle at 50% 50%, #2a0a0f 0%, #000000 80%);
            min-height: 100vh;
        }

        /* --- 🎵 Audio Player Widget --- */
        .audio-player {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 2000;
            background: rgba(0,0,0,0.7);
            padding: 10px;
            border-radius: 50px;
            border: 2px solid var(--primary);
            box-shadow: var(--neon-glow);
            display: flex;
            align-items: center;
            gap: 10px;
            backdrop-filter: blur(5px);
        }
        .play-btn {
            background: var(--primary);
            border: none;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2em;
            transition: 0.3s;
        }
        .play-btn:hover { transform: scale(1.1); box-shadow: 0 0 20px var(--primary); }
        .song-info { font-size: 0.9em; color: #ccc; padding-right: 10px; }

        /* --- ✨ Navbar Pop-up --- */
        .navbar {
            background-color: rgba(20, 5, 5, 0.95); /* สีแยกจากพื้นหลังชัดเจน */
            padding: 15px 50px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: fixed;
            top: 0;
            width: 90%;
            z-index: 1000;
            border-bottom: 3px solid var(--primary);
            box-shadow: 0 10px 30px rgba(255, 0, 60, 0.3); /* เงาแดงฟุ้งๆ */
            backdrop-filter: blur(15px);
            /* Animation Pop-up */
            animation: slideDown 0.8s ease-out forwards;
            transform: translateY(-100%); /* ซ่อนไว้ก่อน */
        }

        .logo {
            font-family: 'Cinzel Decorative', cursive; /* ฟอนต์หัวข้อแบบ Gothic */
            font-size: 1.8em;
            color: var(--primary);
            text-shadow: var(--neon-glow);
        }

        .nav-links a {
            color: #aaa;
            text-decoration: none;
            margin-left: 30px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            transition: 0.3s;
        }

        /* ลูกเล่นขีดเส้นใต้เมนู */
        .nav-links a::after {
            content: '';
            position: absolute;
            width: 0;
            height: 2px;
            bottom: -5px;
            left: 0;
            background-color: var(--primary);
            transition: 0.3s;
        }
        .nav-links a:hover { color: white; }
        .nav-links a:hover::after { width: 100%; }

        .btn-invite-nav {
            background: linear-gradient(45deg, var(--secondary), var(--primary));
            color: white !important;
            padding: 10px 25px;
            border-radius: 30px;
            box-shadow: var(--neon-glow);
        }
        .btn-invite-nav:hover { transform: translateY(-3px); }

        /* --- Hero Section --- */
        .hero {
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            position: relative;
        }

        /* พื้นหลังควันเคลื่อนไหว */
        .fog-overlay {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: url('https://media.giphy.com/media/26tOZ42Mg6pbTUPDa/giphy.gif'); /* ใช้ GIF ควันจางๆ เป็น Overlay */
            opacity: 0.05;
            pointer-events: none;
            mix-blend-mode: screen;
        }

        .bot-avatar-container {
            position: relative;
            margin-bottom: 30px;
        }
        
        .bot-avatar {
            width: 200px;
            height: 200px;
            border-radius: 50%;
            border: 5px solid var(--primary);
            box-shadow: 0 0 50px var(--primary), inset 0 0 30px var(--primary);
            animation: float 4s ease-in-out infinite;
            position: relative;
            z-index: 2;
        }
        
        /* วงแหวนเวทย์ด้านหลัง */
        .magic-circle {
            position: absolute;
            top: -20%; left: -20%; width: 140%; height: 140%;
            border: 2px dashed var(--primary);
            border-radius: 50%;
            opacity: 0.3;
            animation: spin 20s linear infinite;
        }

        .status-pill {
            background: rgba(0, 255, 0, 0.1);
            border: 1px solid #00ff00;
            color: #00ff00;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            box-shadow: 0 0 15px rgba(0,255,0,0.3);
        }
        .status-dot {
            width: 12px; height: 12px; background: #00ff00; border-radius: 50%;
            box-shadow: 0 0 10px #00ff00; animation: pulse 1.5s infinite;
        }

        /* 🌈 ชื่อบอทแบบไล่เฉดสีเคลื่อนไหว */
        h1.animated-title {
            font-family: 'Cinzel Decorative', cursive;
            font-size: 4.5em;
            margin: 0;
            background: linear-gradient(to right, var(--primary), #ff5e00, #ff00cc, var(--primary));
            background-size: 300%;
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            animation: gradientShift 5s ease infinite;
            text-transform: uppercase;
            letter-spacing: 5px;
        }

        p.subtitle { font-size: 1.3em; color: #ccc; max-width: 700px; margin-top: 20px; line-height: 1.6; }

        /* Stats แบบใหม่ */
        .stats-row {
            display: flex;
            gap: 30px;
            margin-top: 50px;
        }
        .stat-card {
            background: rgba(255,255,255,0.03);
            padding: 25px 40px;
            border-radius: 15px;
            border-top: 3px solid var(--primary);
            backdrop-filter: blur(10px);
            transition: 0.3s;
        }
        .stat-card:hover { transform: translateY(-10px); box-shadow: var(--neon-glow); background: rgba(255,0,60,0.1); }
        .stat-num { font-size: 3em; font-weight: 800; color: white; }
        .stat-lbl { color: var(--primary); text-transform: uppercase; letter-spacing: 2px; font-size: 0.9em; }

        /* Animations Keyframes */
        @keyframes slideDown { from { transform: translateY(-100%); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
        @keyframes pulse { 0% { opacity: 1; scale: 1; } 50% { opacity: 0.5; scale: 0.8; } 100% { opacity: 1; scale: 1; } }
        @keyframes gradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        @keyframes spin { 100% { transform: rotate(360deg); } }

        /* Mobile Resp. */
        @media (max-width: 768px) {
            .navbar { padding: 15px 20px; }
            .nav-links { display: none; }
            h1.animated-title { font-size: 3em; }
            .stats-row { flex-direction: column; gap: 20px; }
            .audio-player { bottom: 20px; right: 20px; padding: 8px; }
            .song-info { display: none; } /* ซ่อนชื่อเพลงในมือถือ */
        }
    </style>
</head>
<body>

    <audio id="bgMusic" loop>
        <source src="https://pixabay.com/music/download/story-epic-cinematic-trailer-115966.mp3" type="audio/mpeg">
    </audio>

    <div class="audio-player">
        <button id="playToggle" class="play-btn"><i class="fas fa-play"></i></button>
        <div class="song-info">Gothic Epic Theme</div>
    </div>

    <nav class="navbar">
        <div class="logo">😈 DEVILS DEN</div>
        <div class="nav-links">
            <a href="#">หน้าหลัก</a>
            <a href="#services">บริการ</a>
            <a href="https://www.facebook.com/l3althazar.bas" target="_blank">ติดต่อเรา</a>
            <a href="https://discord.com/oauth2/authorize?client_id=1457301588937801739&permissions=8&integration_type=0&scope=bot" class="btn-invite-nav" target="_blank">เชิญบอท +</a>
        </div>
    </nav>

    <section class="hero">
        <div class="fog-overlay"></div> <div class="bot-avatar-container">
            <div class="magic-circle"></div> <img src="https://cdn.discordapp.com/avatars/1457301588937801739/a334b0c7937402868297495034875321.png?size=256" class="bot-avatar" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
        </div>
        
        <div class="status-pill">
            <div class="status-dot"></div> ONLINE 24/7
        </div>

        <h1 class="animated-title">DEVILS DENBOT</h1>
        
        <p class="subtitle">
            "ข้าคือจอมยุทธ์เด๊ะ" — บอทผู้พิทักษ์แห่ง Where Winds Meet<br>
            สัมผัสประสบการณ์ระดับ Premium: ระบบรับน้อง | มูเตลู | มินิเกม
        </p>

        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-num">TOP</div>
                <div class="stat-lbl">Quality</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">24/7</div>
                <div class="stat-lbl">Uptime</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">PRO</div>
                <div class="stat-lbl">Features</div>
            </div>
        </div>
    </section>

    <script>
        // สคริปต์สำหรับปุ่ม Play/Pause เพลง
        const bgMusic = document.getElementById('bgMusic');
        const playToggle = document.getElementById('playToggle');
        const icon = playToggle.querySelector('i');

        bgMusic.volume = 0.3; // ตั้งเสียงเริ่มต้นเบาๆ (30%)

        playToggle.addEventListener('click', () => {
            if (bgMusic.paused) {
                bgMusic.play();
                icon.classList.remove('fa-play');
                icon.classList.add('fa-pause');
                playToggle.style.boxShadow = "0 0 30px var(--primary)";
            } else {
                bgMusic.pause();
                icon.classList.remove('fa-pause');
                icon.classList.add('fa-play');
                playToggle.style.boxShadow = "none";
            }
        });
    </script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(html_code)

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
