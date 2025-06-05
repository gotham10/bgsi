from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import httpx
import uvicorn
from string import Template
import json
import html
import io
from datetime import datetime

app = FastAPI(title="BGSI.GG API Explorer & Image Proxy")

API_BASE_URL = "https://api.bgsi.gg"
IMAGE_BASE_URL = "https://www.bgsi.gg"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico")
PASSWORD_FOR_JSON = "bgsi"

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Origin": API_BASE_URL,
}

class HTMLRenderer:
    @staticmethod
    def get_shared_css():
        return """
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg-dark: #080808;
                --bg-med: #121212;
                --bg-light: #1a1a1a;
                --text-primary: #cccccc;
                --text-secondary: #999999;
                --border-color: #282828;
                --accent-color: #00aaff;
                --font-body: 'Roboto Mono', monospace;
                --font-header: 'Orbitron', sans-serif;
                --rarity-common: #9b9b9b;
                --rarity-unique: #5de24b;
                --rarity-rare: #35a5f1;
                --rarity-epic: #b84bf2;
                --rarity-legendary: #ffc84b;
                --rarity-secret: #ff5e5e;
                --demand-insane: #ff3c3c;
                --demand-amazing: #ff7e36;
                --demand-high: #ffc233;
                --demand-good: #a6e22e;
                --demand-normal: #66d9ef;
                --demand-low: #ae81ff;
                --trend-stable: #87ceeb;
                --trend-unstable: #ffd700;
                --trend-decreasing: #ff6347;
                --trend-increasing: #98fb98;
            }
            body {
                background: var(--bg-dark);
                background-image: linear-gradient(135deg, var(--bg-dark) 0%, var(--bg-med) 50%, var(--bg-dark) 100%);
                color: var(--text-secondary);
                font-family: var(--font-body);
                margin: 0;
                padding: 2rem;
                overflow-x: hidden;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
                background: rgba(18, 18, 18, 0.85);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                border: 1px solid var(--border-color);
                box-shadow: 0 10px 40px rgba(0,0,0,0.7);
            }
            h1, h2, h3 { font-family: var(--font-header); color: var(--text-primary); text-shadow: 0 0 8px rgba(200, 200, 200, 0.1); }
            a { color: var(--accent-color); text-decoration: none; transition: color 0.3s ease, text-shadow 0.3s ease; }
            a:hover { color: #fff; text-shadow: 0 0 5px var(--accent-color); }
            .rarity-common { color: var(--rarity-common); }
            .rarity-unique { color: var(--rarity-unique); }
            .rarity-rare { color: var(--rarity-rare); }
            .rarity-epic { color: var(--rarity-epic); }
            .rarity-legendary { color: var(--rarity-legendary); }
            .rarity-secret { color: var(--rarity-secret); }
            .demand-low { color: var(--demand-low); font-weight: bold; }
            .demand-normal { color: var(--demand-normal); font-weight: bold; }
            .demand-good { color: var(--demand-good); font-weight: bold; }
            .demand-high { color: var(--demand-high); font-weight: bold; }
            .demand-amazing { color: var(--demand-amazing); font-weight: bold; }
            .demand-insane { color: var(--demand-insane); font-weight: bold; }
            .trend-stable { color: var(--trend-stable); }
            .trend-unstable { color: var(--trend-unstable); }
            .trend-decreasing::before { content: '▼ '; color: var(--trend-decreasing); }
            .trend-increasing::before { content: '▲ '; color: var(--trend-increasing); }
            .trend-decreasing { color: var(--trend-decreasing); }
            .trend-increasing { color: var(--trend-increasing); }
        </style>
        """

    @staticmethod
    def render_index_page():
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>BGSI.GG API Explorer</title>
          <meta name="description" content="Explore live JSON responses and images from the BGSI.GG API. A simple and effective tool for API interaction.">
          <meta name="theme-color" content="#080808">
          <meta property="og:type" content="website">
          <meta property="og:url" content="https://bgsi-kyc3.onrender.com/">
          <meta property="og:title" content="BGSI.GG API Explorer">
          <meta property="og:description" content="Explore live JSON responses and images from the BGSI.GG API. A simple and effective tool for API interaction.">
          <meta property="og:image" content="https://bgsi-kyc3.onrender.com/Logo.png">
          <meta property="twitter:card" content="summary_large_image">
          <meta property="twitter:url" content="https://bgsi-kyc3.onrender.com/">
          <meta property="twitter:title" content="BGSI.GG API Explorer">
          <meta property="twitter:description" content="Explore live JSON responses and images from the BGSI.GG API. A simple and effective tool for API interaction.">
          <meta property="twitter:image" content="https://bgsi-kyc3.onrender.com/Logo.png">
          <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
          <style>
            @keyframes fadeInDown { 0% { opacity: 0; transform: translateY(-20px); } 100% { opacity: 1; transform: translateY(0); } }
            @keyframes fadeInUp { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }
            @keyframes backgroundPan { 0% { background-position: 0% center; } 100% { background-position: 200% center; } }
            body {
              background: #080808;
              background-image: linear-gradient(120deg, #080808 0%, #121212 50%, #080808 100%);
              background-size: 200% 100%;
              animation: backgroundPan 45s linear infinite;
              color: #999999;
              font-family: 'Roboto Mono', monospace;
              margin: 0;
              padding: 0;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              min-height: 100vh;
              box-sizing: border-box;
              text-align: center;
              overflow-x: hidden;
            }
            .container {
              background: rgba(18, 18, 18, 0.9);
              backdrop-filter: blur(8px);
              padding: 3rem 4rem;
              border-radius: 15px;
              box-shadow: 0 10px 30px rgba(0,0,0,0.7), 0 0 0 1px rgba(50, 50, 50, 0.5);
              max-width: 900px;
              width: 90%;
              animation: fadeInDown 1s ease-out forwards;
              border: 1px solid #282828;
            }
            h1 { font-family: 'Orbitron', sans-serif; color: #cccccc; font-size: 3rem; margin-bottom: 1.5rem; letter-spacing: 1px; animation: fadeInDown 0.8s ease-out 0.2s forwards; opacity: 0; text-shadow: 0 0 8px rgba(200, 200, 200, 0.15); }
            p { font-size: 1.1rem; line-height: 1.7; margin-bottom: 1.5rem; animation: fadeInUp 1s ease-out 0.4s forwards; opacity: 0; }
            .api-info { margin-bottom: 2.5rem; font-size: 1rem; color: #bbbbbb; animation: fadeInUp 1s ease-out 0.6s forwards; opacity: 0; }
            a { color: #888888; text-decoration: none; transition: color 0.3s ease, text-shadow 0.3s ease; font-weight: 500; }
            a:hover { color: #aaaaaa; text-shadow: 0 0 8px rgba(170, 170, 170, 0.3); }
            .instructions { background: rgba(10, 10, 10, 0.8); padding: 1.5rem 2rem; border-radius: 10px; margin-top: 2rem; border-left: 4px solid #444444; text-align: left; animation: fadeInUp 1s ease-out 0.8s forwards; opacity: 0; }
            .instructions p, .instructions ul li { color: #bbbbbb; font-size: 1rem; margin-bottom: 0.8rem; line-height: 1.6; }
            .instructions ul { padding-left: 20px; margin-top: 0.5rem; }
            .example-path { font-family: 'Roboto Mono', monospace; background-color: #101010; color: #999999; padding: 0.3em 0.6em; border-radius: 5px; font-weight: 500; border: 1px solid #303030; }
            .footer-link { margin-top: 3rem; font-size: 0.9rem; color: #777777; animation: fadeInUp 1s ease-out 1s forwards; opacity: 0; }
            .footer-link a { font-weight: bold; }
            .nav-links { display: flex; gap: 1rem; justify-content: center; margin-top: 1.5rem; flex-wrap: wrap; }
            .nav-links a { background: var(--example-path-bg); border: 1px solid var(--border-color); padding: 0.5rem 1rem; border-radius: 5px; transition: background 0.3s; }
            .nav-links a:hover { background: #2a2a2a; }
          </style>
        </head>
        <body>
          <div class="container">
            <img src="/Hero_Logo.png" alt="Hero Logo" style="max-width: 250px; margin-bottom: 1rem;">
            <h1>API Data Explorer</h1>
            <p>Explore live data from the <a href="https://api.bgsi.gg" target="_blank" rel="noopener noreferrer">BGSI.GG API</a> or view proxied images.</p>
             <div class="nav-links">
                <a href="/api/items/mythic-easter-basket" class="example-path">Example Item</a>
                <a href="/api/stats" class="example-path">Global Stats</a>
                <a href="/api/eggs" class="example-path">View All Eggs</a>
            </div>
            <div class="instructions">
              <p><strong>How to use:</strong></p>
              <ul>
                <li><strong>API Data:</strong> Append the API path after <code class="example-path">/api/</code>. Ex: <a href="/api/stats">/api/stats</a></li>
                <li><strong>Images:</strong> Use the direct path for an image. Ex: <a href="/items/fire-basilisk.png">/items/fire-basilisk.png</a></li>
                <li>Query parameters are supported: <code class="example-path">/api/v1/data?type=example</code></li>
              </ul>
            </div>
            <p class="footer-link">View data and images from <a href="https://www.bgsi.gg" target="_blank" rel="noopener noreferrer">www.bgsi.gg</a>.</p>
          </div>
        </body>
        </html>
        """

    @staticmethod
    def render_error_page(title: str, message: str, status_code: int, details: str = "", guidance_html: str = ""):
        escaped_title = html.escape(title)
        escaped_message = html.escape(message)
        escaped_details = html.escape(details)
        error_page_content = f"""
        <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{escaped_title}</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono&family=Orbitron:wght@700&display=swap" rel="stylesheet">
        <style>
          body {{ background-color: #080808; color: #cccccc; font-family: 'Roboto Mono', monospace; padding: 2rem; margin:0; display: flex; flex-direction: column; align-items: center; justify-content:center; min-height: 90vh; text-align: center; }}
          .error-container {{ background-color: #161616; padding: 2.5rem; border-radius: 10px; border: 1px solid #2a2a2a; box-shadow: 0 6px 20px rgba(0,0,0,0.6); max-width: 800px; width: 90%; }}
          h1 {{ font-family: 'Orbitron', sans-serif; color: #bbbbbb; border-bottom: 1px solid #333333; padding-bottom: 0.5rem; margin-top:0; font-size: 2rem;}}
          p {{ font-size: 1.1rem; line-height: 1.6; color: #aaaaaa; }}
          pre {{ background-color: #0a0a0a; color: #b0b0b0; padding: 1rem; border-radius: 5px; border: 1px solid #222222; white-space: pre-wrap; word-break: break-all; max-height: 200px; overflow-y: auto; text-align: left; font-size: 0.85rem;}}
          .guidance {{ margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid #333333; text-align: left; color: #bbbbbb; }}
          .guidance p, .guidance ul li {{ font-size: 1rem; margin-bottom: 0.7rem; }}
          .guidance ul {{ list-style-type: square; padding-left: 20px; }}
          .guidance a {{ color: #888888; text-decoration: none; font-weight: bold;}}
          .guidance a:hover {{ color: #aaaaaa; }}
          .example-path {{ font-family: 'Roboto Mono', monospace; background-color: #101010; color: #999999; padding: 0.2em 0.5em; border-radius: 4px; border: 1px solid #303030;}}
        </style></head>
        <body><div class="error-container"><h1>{escaped_title}</h1>
        <p>{escaped_message}</p>
        {f"<pre>{escaped_details}</pre>" if escaped_details else ""}
        {guidance_html if guidance_html else ""}
        </div></body></html>
        """
        return HTMLResponse(content=error_page_content, status_code=status_code)

    @staticmethod
    def render_generic_json_page(json_data_str: str, page_title: str):
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>{html.escape(page_title)}</title>
          {HTMLRenderer.get_shared_css()}
          <style>
            pre {{ background-color: #101010; color: #d0d0d0; padding: 2rem; border-radius: 10px; border: 1px solid #2a2a2a; box-shadow: 0 6px 20px rgba(0,0,0,0.6); white-space: pre; overflow-x: auto; font-size: 0.875rem; }}
          </style>
        </head>
        <body>
          <div class="container">
              <pre>{html.escape(json_data_str)}</pre>
          </div>
        </body>
        </html>
        """

    @staticmethod
    def render_stats_page(data, request):
        stats_css = """
        <style>
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; margin-top: 2rem; }
            .stat-card { background: var(--bg-light); padding: 2rem; border-radius: 10px; border: 1px solid var(--border-color); text-align: center; }
            .stat-card h2 { font-size: 1.5rem; margin-top: 0; margin-bottom: 0.5rem; color: var(--text-secondary); }
            .stat-card .value { font-family: var(--font-header); font-size: 3rem; color: var(--text-primary); }
        </style>
        """
        return f"""
        <!DOCTYPE html><html lang="en">
        <head>
            <meta charset="UTF-8"><title>BGSI.GG Global Stats</title>
            {HTMLRenderer.get_shared_css()}{stats_css}
        </head>
        <body>
            <div class="container">
                <h1><img src="/Logo.png" alt="Logo" style="height: 40px; vertical-align: middle; margin-right: 15px;">Global Statistics</h1>
                <div class="stats-grid">
                    <div class="stat-card"><h2>Total Pets</h2><p class="value">{data.get('totalPets', 'N/A'):,}</p></div>
                    <div class="stat-card"><h2>Total Exists</h2><p class="value">{data.get('totalExists', 'N/A'):,}</p></div>
                    <div class="stat-card"><h2>24h Secret Hatches</h2><p class="value">{data.get('secretHatches24h', 'N/A'):,}</p></div>
                    <div class="stat-card"><h2>Users Online</h2><p class="value">{data.get('usersOnline', 'N/A'):,}</p></div>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def render_eggs_page(data, request):
        eggs_css = """
        <style>
            .eggs-grid { display: grid; grid-template-columns: 1fr; gap: 2rem; }
            .egg-card { background: var(--bg-light); border-radius: 10px; border: 1px solid var(--border-color); overflow: hidden; }
            .egg-header { display: flex; align-items: center; gap: 1.5rem; padding: 1.5rem; background: rgba(0,0,0,0.2); border-bottom: 1px solid var(--border-color); }
            .egg-header img { width: 100px; height: 100px; }
            .egg-info h2 { margin: 0 0 0.5rem 0; font-size: 2rem; }
            .egg-info p { margin: 0; color: var(--text-secondary); }
            .egg-info .price { font-weight: bold; color: var(--text-primary); }
            .egg-info .price img { height: 1em; vertical-align: -0.1em; margin-right: 0.25em; }
            .pets-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; padding: 1.5rem; }
            .pet-card { background: var(--bg-med); text-align: center; padding: 1rem; border-radius: 8px; border: 1px solid #333; }
            .pet-card img { width: 80px; height: 80px; margin-bottom: 0.5rem; }
            .pet-card .pet-name { display: block; color: var(--text-primary); font-weight: 500; }
            .pet-card .pet-rarity { display: block; font-size: 0.9em; margin-top: 0.25rem; }
            .pet-card .pet-chance { display: block; font-size: 0.8em; color: var(--text-secondary); margin-top: 0.5rem; }
        </style>
        """
        
        def format_chance(chance):
            return f"{chance:.8f}".rstrip('0').rstrip('.') + '%'

        eggs_html = ""
        for egg in data.get('eggs', []):
            currency_icon = ""
            if egg.get('currency') == "Coins":
                currency_icon = "<img src='/Coin.png' alt='Coins'>"
            
            pets_html = ""
            for pet in egg.get('pets', []):
                pets_html += f"""
                <div class="pet-card">
                    <img src="{IMAGE_BASE_URL}{html.escape(pet.get('image', ''))}" loading="lazy" alt="{html.escape(pet.get('name', ''))}">
                    <span class="pet-name">{html.escape(pet.get('name', ''))}</span>
                    <span class="pet-rarity rarity-{html.escape(pet.get('rarity', 'common').lower())}">{html.escape(pet.get('rarity', ''))}</span>
                    <span class="pet-chance">{format_chance(pet.get('chance', 0))}</span>
                </div>
                """

            eggs_html += f"""
            <div class="egg-card">
                <div class="egg-header">
                    <img src="{IMAGE_BASE_URL}{html.escape(egg.get('image', ''))}" alt="{html.escape(egg.get('name', ''))}">
                    <div class="egg-info">
                        <h2>{html.escape(egg.get('name', ''))}</h2>
                        <p>Location: {html.escape(egg.get('location', 'N/A'))}</p>
                        <p class="price">{currency_icon}{egg.get('price', 'N/A'):,} {html.escape(egg.get('currency', ''))}</p>
                    </div>
                </div>
                <div class="pets-grid">{pets_html}</div>
            </div>
            """

        return f"""
        <!DOCTYPE html><html lang="en">
        <head>
            <meta charset="UTF-8"><title>BGSI.GG Eggs</title>
            {HTMLRenderer.get_shared_css()}{eggs_css}
        </head>
        <body>
            <div class="container">
                 <h1><img src="/Logo.png" alt="Logo" style="height: 40px; vertical-align: middle; margin-right: 15px;">All Eggs</h1>
                 <div class="eggs-grid">{eggs_html}</div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def render_item_page(data, request):
        pet_data = data.get('pet', {})
        if not pet_data:
             return HTMLRenderer.render_error_page("Invalid Item Data", "The API response did not contain valid pet data.", 404)

        item_css = """
        <style>
            .grid-container { display: grid; grid-template-columns: 350px 1fr; gap: 2rem; align-items: flex-start; }
            .left-column, .right-column { display: flex; flex-direction: column; gap: 2rem; }
            .main-card, .info-card, .history-card { background: var(--bg-light); padding: 2rem; border-radius: 10px; border: 1px solid var(--border-color); }
            .main-card .pet-image { width: 100%; max-width: 300px; margin: 0 auto 1rem; display: block; }
            .main-card h1 { text-align: center; font-size: 2.5rem; margin-bottom: 0.5rem; }
            .main-card .description { font-size: 1rem; line-height: 1.6; text-align: center; color: var(--text-secondary); border-top: 1px solid var(--border-color); padding-top: 1rem; margin-top: 1rem;}
            .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
            .stat-box { background: var(--bg-med); padding: 1rem; border-radius: 8px; border-left: 4px solid var(--accent-color); }
            .stat-box .label { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.25rem; }
            .stat-box .value { font-size: 1.2rem; font-weight: bold; color: var(--text-primary); text-transform: capitalize; }
            .stat-bars .stat { margin-bottom: 1rem; }
            .stat-bars .stat-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
            .stat-bars .stat-info .label { font-weight: bold; display: flex; align-items: center; gap: 0.5rem; }
            .stat-bars .stat-info .label img { height: 1.2em; }
            .stat-bars .bar { background: var(--bg-med); border-radius: 5px; height: 10px; overflow: hidden; }
            .stat-bars .bar .fill { background: var(--accent-color); height: 100%; width: 50%; } /* Placeholder width */
            .history-table { width: 100%; border-collapse: collapse; }
            .history-table th, .history-table td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--border-color); }
            .history-table th { font-family: var(--font-header); font-size: 0.9rem; }
            .history-table td { font-size: 0.95rem; }
            .history-table tr:last-child td { border-bottom: none; }
            .table-wrapper { max-height: 400px; overflow-y: auto; }
            .variants-list a { display: block; padding: 0.75rem; background: var(--bg-med); margin-bottom: 0.5rem; border-radius: 5px; transition: background 0.2s; }
            .variants-list a:hover { background: #333; }
            .json-toggle { cursor: pointer; display: block; padding: 0.75rem 1.5rem; background: var(--bg-light); border: 1px solid var(--border-color); border-radius: 8px; text-align: center; margin-top: 1rem; }
            #json-viewer { display: none; margin-top: 1rem; }
            #json-viewer pre { white-space: pre-wrap; word-break: break-all; background: #000; padding: 1rem; border-radius: 8px; }
             @media (max-width: 900px) { .grid-container { grid-template-columns: 1fr; } }
        </style>
        """

        def format_value(value):
            if isinstance(value, int):
                return f"<img src='/gem.png' alt='Gems' style='height:1em;vertical-align:-0.1em;'> {value:,}"
            return html.escape(str(value))

        def format_timestamp(ts):
            try:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except:
                return ts

        stats = pet_data.get('stats', {})
        max_stat = max(stats.get('bubbles', 0), stats.get('coins', 0), stats.get('gems', 0)) or 1
        
        value_history_rows = ""
        for entry in data.get('history', []):
            value_history_rows += f"<tr><td>{format_timestamp(entry.get('timestamp', ''))}</td><td>{format_value(entry.get('value', 'N/A'))}</td></tr>"

        exist_history_rows = ""
        for entry in data.get('existHistories', []):
            exist_history_rows += f"<tr><td>{format_timestamp(entry.get('timestamp', ''))}</td><td>{entry.get('existAmount', 'N/A')}</td></tr>"

        recent_hatches_rows = ""
        for entry in data.get('recentHatches', []):
            player = html.escape(entry.get('playerName') or 'Private')
            recent_hatches_rows += f"<tr><td>{format_timestamp(entry.get('timestamp', ''))}</td><td>{player}</td></tr>"

        variants_html = ""
        for variant in pet_data.get('allVariants', []):
            variants_html += f"""<a href="/api/items/{html.escape(variant.get('slug', ''))}" class="rarity-{html.escape(variant.get('variant', '').lower())}">
                {html.escape(variant.get('name', ''))}
            </a>"""
            
        return f"""
        <!DOCTYPE html><html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>{html.escape(pet_data.get('name', 'Item'))} - BGSI.GG Explorer</title>
            {HTMLRenderer.get_shared_css()}{item_css}
        </head>
        <body>
            <div class="container">
                <div class="grid-container">
                    <div class="left-column">
                        <div class="main-card">
                            <img class="pet-image" src="{IMAGE_BASE_URL}{html.escape(pet_data.get('image', ''))}" alt="{html.escape(pet_data.get('name', ''))}">
                            <h1>{html.escape(pet_data.get('name', ''))}</h1>
                            <p class="description">{html.escape(pet_data.get('description', ''))}</p>
                        </div>
                        <div class="info-card stat-bars">
                            <h3>Base Stats</h3>
                            <div class="stat">
                                <div class="stat-info"><span class="label"><img src="/bubble.png" alt="Bubbles">Bubbles</span> <span>{stats.get('bubbles', 0):,}</span></div>
                                <div class="bar"><div class="fill" style="width: {stats.get('bubbles', 0) / max_stat * 100}%;"></div></div>
                            </div>
                            <div class="stat">
                                <div class="stat-info"><span class="label"><img src="/Coin.png" alt="Coins">Coins</span> <span>{stats.get('coins', 0):,}</span></div>
                                <div class="bar"><div class="fill" style="width: {stats.get('coins', 0) / max_stat * 100}%;"></div></div>
                            </div>
                            <div class="stat">
                                <div class="stat-info"><span class="label"><img src="/gem.png" alt="Gems">Gems</span> <span>{stats.get('gems', 0):,}</span></div>
                                <div class="bar"><div class="fill" style="width: {stats.get('gems', 0) / max_stat * 100}%;"></div></div>
                            </div>
                        </div>
                        <div class="info-card"><h3>Variants</h3><div class="variants-list">{variants_html}</div></div>
                    </div>
                    <div class="right-column">
                        <div class="info-card">
                            <h3>Details</h3>
                            <div class="stats-grid">
                                <div class="stat-box"><div class="label">Value</div><div class="value">{format_value(pet_data.get('value', 'N/A'))}</div></div>
                                <div class="stat-box"><div class="label">Exists</div><div class="value">{pet_data.get('owners', 'N/A')}</div></div>
                                <div class="stat-box"><div class="label">Rarity</div><div class="value rarity-{html.escape(pet_data.get('rarity', '').lower())}">{html.escape(pet_data.get('rarity', 'N/A'))}</div></div>
                                <div class="stat-box"><div class="label">Status</div><div class="value">{html.escape(pet_data.get('status', 'N/A'))}</div></div>
                                <div class="stat-box"><div class="label">Demand</div><div class="value demand-{html.escape(pet_data.get('demand', '').lower())}">{html.escape(pet_data.get('demand', 'N/A'))}</div></div>
                                <div class="stat-box"><div class="label">Trend</div><div class="value trend-{html.escape(pet_data.get('trend', '').lower())}">{html.escape(pet_data.get('trend', 'N/A'))}</div></div>
                            </div>
                        </div>
                        <div class="history-card"><h3>Value History</h3><div class="table-wrapper"><table class="history-table"><thead><tr><th>Date</th><th>Value</th></tr></thead><tbody>{value_history_rows}</tbody></table></div></div>
                        <div class="history-card"><h3>Exist History</h3><div class="table-wrapper"><table class="history-table"><thead><tr><th>Date</th><th>Amount</th></tr></thead><tbody>{exist_history_rows}</tbody></table></div></div>
                        <div class="history-card"><h3>Recent Hatches</h3><div class="table-wrapper"><table class="history-table"><thead><tr><th>Date</th><th>Player</th></tr></thead><tbody>{recent_hatches_rows}</tbody></table></div></div>
                    </div>
                </div>
                <div class="json-viewer-container">
                    <h3 class="json-toggle" onclick="toggleJsonViewer()">View Raw JSON Data (Password Required)</h3>
                    <div id="json-viewer">
                        <pre>{html.escape(json.dumps(data, indent=2))}</pre>
                    </div>
                </div>
            </div>
            <script>
                function toggleJsonViewer() {{
                    const viewer = document.getElementById('json-viewer');
                    if (viewer.style.display === 'block') {{
                        viewer.style.display = 'none';
                        return;
                    }}
                    const password = prompt('Enter password to view raw data:');
                    if (password === '{PASSWORD_FOR_JSON}') {{
                        viewer.style.display = 'block';
                    }} else if (password) {{
                        alert('Incorrect password.');
                    }}
                }}
            </script>
        </body></html>
        """

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=HTMLRenderer.render_index_page())

@app.get("/api/{path:path}", response_class=HTMLResponse)
async def proxy_api(path: str, request: Request):
    query = str(request.query_params)
    target_url = f"{API_BASE_URL}/api/{path}"
    if query:
        target_url += f"?{query}"

    api_headers = {**COMMON_HEADERS, "Accept": "application/json, text/plain, */*", "Referer": f"{API_BASE_URL}/"}

    try:
        async with httpx.AsyncClient(headers=api_headers, follow_redirects=True) as client:
            response = await client.get(target_url)
            response.raise_for_status()
            
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                return HTMLRenderer.render_generic_json_page(response.text, f"Non-JSON Response: {path}")

            json_data = response.json()

            if path.startswith("items/"):
                return HTMLResponse(content=HTMLRenderer.render_item_page(json_data, request))
            elif path == "stats":
                return HTMLResponse(content=HTMLRenderer.render_stats_page(json_data, request))
            elif path == "eggs":
                return HTMLResponse(content=HTMLRenderer.render_eggs_page(json_data, request))
            else:
                pretty_json_str = json.dumps(json_data, indent=2, sort_keys=True)
                return HTMLRenderer.render_generic_json_page(pretty_json_str, f"API Data: {path}")

    except httpx.HTTPStatusError as e:
        return HTMLRenderer.render_error_page(
            title=f"API Error: {e.response.status_code}",
            message=f"Error fetching API data from: {html.escape(target_url)}.",
            status_code=e.response.status_code,
            details=f"Reason: {e.response.reason_phrase}\nResponse: {e.response.text}"
        )
    except httpx.RequestError as e:
        return HTMLRenderer.render_error_page(
            title="API Connection Error",
            message=f"Could not connect to API endpoint: {html.escape(target_url)}.",
            status_code=503,
            details=str(e)
        )
    except json.JSONDecodeError as e_json:
        raw_text = response.text if 'response' in locals() and hasattr(response, 'text') else 'N/A'
        return HTMLRenderer.render_error_page(
            title="API Response Parsing Error",
            message="Failed to parse JSON response from the API.",
            status_code=502,
            details=f"Error: {e_json.msg}\nRaw Response:\n{raw_text[:1000]}"
        )
    except Exception as e:
        return HTMLRenderer.render_error_page(
            title="Unexpected API Error",
            message="An unexpected error occurred while proxying the API request.",
            status_code=500,
            details=str(e)
        )

@app.get("/{item_path:path}")
async def proxy_image_or_not_found(item_path: str, request: Request):
    is_image_path = item_path.lower().endswith(IMAGE_EXTENSIONS)
    is_favicon = item_path.lower() == "favicon.ico"

    if not (is_image_path or is_favicon):
        guidance = f"""
        <div class="guidance">
            <p>If you were trying to access API data, the path must start with <code class="example-path">/api/</code>.</p>
            <ul><li>Example API path: <a href="/api/stats">/api/stats</a></li></ul>
            <p>If you were trying to access an image, ensure the path is correct and ends with an image extension.</p>
            <ul><li>Example image path: <a href="/items/fire-basilisk.png">/items/fire-basilisk.png</a></li></ul>
            <p>Return to the <a href="/">API Explorer Home Page</a>.</p>
        </div>"""
        return HTMLRenderer.render_error_page(
            title="Resource Not Found",
            message=f"The path '/{html.escape(item_path)}' is not a valid API route or a recognized image type.",
            status_code=404, guidance_html=guidance)

    target_url = f"{IMAGE_BASE_URL}/{item_path}"
    image_headers = {**COMMON_HEADERS, "Accept": "image/*,*/*;q=0.8", "Referer": f"{IMAGE_BASE_URL}/"}

    try:
        async with httpx.AsyncClient(headers=image_headers, follow_redirects=True) as client:
            response = await client.get(target_url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "application/octet-stream")
            if not is_favicon and not content_type.lower().startswith("image/"):
                return HTMLRenderer.render_error_page(
                    title="Invalid Content Type",
                    message=f"The resource at {html.escape(target_url)} was found but is not an image.",
                    status_code=415,
                    details=f"Expected 'image/', received '{html.escape(content_type)}'.")
            return StreamingResponse(io.BytesIO(response.content), media_type=content_type)
    except httpx.HTTPStatusError as e:
        return HTMLRenderer.render_error_page(
            title=f"Fetch Error: {e.response.status_code}",
            message=f"Could not retrieve resource from upstream server: {html.escape(target_url)}.",
            status_code=e.response.status_code,
            details=f"Reason: {e.response.reason_phrase}"
        )
    except httpx.RequestError as e:
        return HTMLRenderer.render_error_page(
            title="Connection Error",
            message=f"Could not connect to server at: {html.escape(IMAGE_BASE_URL)}.",
            status_code=503, details=str(e)
        )
    except Exception as e:
        return HTMLRenderer.render_error_page(
            title="Unexpected Error",
            message="An unexpected error occurred while proxying the resource.",
            status_code=500, details=str(e)
        )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
