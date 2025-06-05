from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import httpx
import uvicorn
import json
import html
import io
from datetime import datetime

app = FastAPI(title="BGSI.GG API Explorer & Image Proxy", docs_url=None, redoc_url=None)

API_BASE_URL = "https://api.bgsi.gg"
IMAGE_BASE_URL = "https://www.bgsi.gg"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico")
ASSETS = ["Coin.png", "gem.png", "bubble.png", "Hero_Logo.png", "Logo.png"]
ADMIN_PASSWORD = "flux"

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Origin": API_BASE_URL,
}

RARITY_COLORS = {
    "Secret": "radial-gradient(ellipse at center, #FF416C 0%, #FF4B2B 100%)",
    "Legendary": "radial-gradient(ellipse at center, #F7971E 0%, #FFD200 100%)",
    "Epic": "radial-gradient(ellipse at center, #8A2387 0%, #E94057 50%, #F27121 100%)",
    "Rare": "radial-gradient(ellipse at center, #2193b0 0%, #6dd5ed 100%)",
    "Unique": "radial-gradient(ellipse at center, #11998e 0%, #38ef7d 100%)",
    "Common": "radial-gradient(ellipse at center, #636363 0%, #a2ab58 100%)"
}

TREND_STYLES = {
    "rising": ("#38ef7d", '<i class="fas fa-arrow-trend-up"></i>'),
    "falling": ("#FF416C", '<i class="fas fa-arrow-trend-down"></i>'),
    "stable": ("#6dd5ed", '<i class="fas fa-minus"></i>'),
    "unstable": ("#F7971E", '<i class="fas fa-bolt"></i>')
}

def format_value(value):
    if isinstance(value, int):
        return f"{value:,}"
    return html.escape(str(value))

def format_timestamp(ts_str):
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.strftime('%b %d, %Y, %I:%M %p UTC')
    except (ValueError, TypeError):
        return ts_str

def create_error_html_response(title: str, message: str, status_code: int, details: str = "", guidance_html: str = ""):
    escaped_title = html.escape(title)
    escaped_message = html.escape(message)
    escaped_details = html.escape(details)
    details_html = "<pre>{}</pre>".format(escaped_details) if escaped_details else ""
    error_template = """
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono&family=Orbitron:wght@700&display=swap" rel="stylesheet">
    <style>
        body {{ background-color: #080808; color: #cccccc; font-family: 'Roboto Mono', monospace; padding: 2rem; margin:0; display: flex; flex-direction: column; align-items: center; justify-content:center; min-height: 90vh; text-align: center; }}
        .error-container {{ background-color: #161616; padding: 2.5rem; border-radius: 10px; border: 1px solid #2a2a2a; box-shadow: 0 6px 20px rgba(0,0,0,0.6); max-width: 800px; width: 90%; }}
        h1 {{ font-family: 'Orbitron', sans-serif; color: #bbbbbb; border-bottom: 1px solid #333333; padding-bottom: 0.5rem; margin-top:0; font-size: 2rem;}}
        p {{ font-size: 1.1rem; line-height: 1.6; color: #aaaaaa; }}
        pre {{ background-color: #0a0a0a; color: #b0b0b0; padding: 1rem; border-radius: 5px; border: 1px solid #222222; white-space: pre-wrap; word-break: break-all; max-height: 200px; overflow-y: auto; text-align: left; font-size: 0.85rem;}}
        .guidance {{ margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid #333333; text-align: left; color: #bbbbbb; }}
    </style></head>
    <body><div class="error-container"><h1>{title}</h1><p>{message}</p>{details_html}{guidance_html}</div></body></html>
    """
    return HTMLResponse(content=error_template.format(title=escaped_title, message=escaped_message, details_html=details_html, guidance_html=guidance_html), status_code=status_code)

def generate_item_page_html(data: dict, request: Request) -> str:
    pet = data.get("pet", {})
    base_url = str(request.base_url).rstrip('/')
    og_image_url = "{}{}".format(IMAGE_BASE_URL, pet.get('image', '')) if pet.get('image') else "{}/Logo.png".format(base_url)
    og_title = html.escape(pet.get("name", "BGSI Item"))
    og_description = html.escape(pet.get("description", "No description available."))
    og_url = html.escape(str(request.url))
    rarity_style = RARITY_COLORS.get(pet.get("rarity"), "none")
    trend_color, trend_symbol = TREND_STYLES.get(pet.get("trend"), ("#999", '<i class="fas fa-question"></i>'))

    stats_html = ""
    if pet.get("stats"):
        stats = pet["stats"]
        stats_html = """
            <div class="stat-item"><img src="{base_url}/bubble.png" alt="Bubbles">Bubbles: <span>{bubbles}</span></div>
            <div class="stat-item"><img src="{base_url}/Coin.png" alt="Coins">Coins: <span>{coins}</span></div>
            <div class="stat-item"><img src="{base_url}/gem.png" alt="Gems">Gems: <span>{gems}</span></div>
        """.format(base_url=base_url, bubbles=format_value(stats.get('bubbles', 0)), coins=format_value(stats.get('coins', 0)), gems=format_value(stats.get('gems', 0)))

    variants_html = ""
    if pet.get("allVariants"):
        for variant in pet["allVariants"]:
            if variant.get("slug") != pet.get("slug"):
                variants_html += """
                    <a href="/api/items/{slug}" class="variant-card">
                        <img src="{image_base}{image_path}" alt="{name}">
                        <div class="variant-name">{name}</div>
                    </a>""".format(slug=variant.get('slug', ''), image_base=IMAGE_BASE_URL, image_path=variant.get('image'), name=html.escape(variant.get('name', '')))
    
    history_rows = "".join(["<tr><td>{}</td><td>{}</td></tr>".format(format_timestamp(h.get('timestamp')), format_value(h.get('value'))) for h in data.get("history", [])])
    exist_history_rows = "".join(["<tr><td>{}</td><td>{}</td></tr>".format(format_timestamp(h.get('timestamp')), h.get('existAmount')) for h in data.get("existHistories", [])])
    recent_hatches_rows = "".join(["<tr><td>{}</td><td>{}</td></tr>".format(format_timestamp(h.get('timestamp')), html.escape(h.get('playerName') or 'Private')) for h in data.get("recentHatches", [])])
    
    variants_button_html = '<button class="tab-button" onclick="openTab(event, \'variants\')">Variants</button>' if variants_html else ''
    
    page_template = """
    <!DOCTYPE html><html lang="en"><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{og_title}</title>
    <meta name="description" content="{og_description}"><meta name="theme-color" content="#080808">
    <meta property="og:type" content="website"><meta property="og:url" content="{og_url}"><meta property="og:title" content="{og_title}"><meta property="og:description" content="{og_description}"><meta property="og:image" content="{og_image_url}">
    <meta property="twitter:card" content="summary_large_image"><meta property="twitter:url" content="{og_url}"><meta property="twitter:title" content="{og_title}"><meta property="twitter:description" content="{og_description}"><meta property="twitter:image" content="{og_image_url}">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet"><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body {{ font-family: 'Roboto Mono', monospace; background: #080808 linear-gradient(120deg, #080808 0%, #121212 50%, #080808 100%); color: #ccc; margin: 0; padding: 2rem; }}
        .container {{ max-width: 1200px; margin: auto; background: rgba(18,18,18,0.8); backdrop-filter: blur(10px); border-radius: 15px; border: 1px solid #282828; box-shadow: 0 10px 30px rgba(0,0,0,0.7); overflow: hidden; }}
        .main-grid {{ display: grid; grid-template-columns: 350px 1fr; gap: 2rem; padding: 2rem; }}
        .left-panel, .right-panel {{ display: flex; flex-direction: column; gap: 1.5rem; }}
        .pet-card {{ background: #1c1c1c; border-radius: 10px; padding: 1.5rem; text-align: center; border: 1px solid #333; }}
        .pet-name {{ font-family: 'Orbitron', sans-serif; font-size: 2rem; margin: 1rem 0 0.5rem 0; color: #fff; }}
        .pet-image {{ max-width: 100%; height: auto; border-radius: 10px; background: rgba(0,0,0,0.2); }}
        .pet-rarity {{ display: inline-block; padding: 0.4rem 1rem; border-radius: 20px; font-weight: 700; color: white; background: {rarity_style}; margin-bottom: 1rem; font-size: 0.9rem; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; text-align: left; }}
        .info-item {{ background: #222; padding: 0.8rem; border-radius: 8px; }}
        .label {{ color: #888; font-size: 0.8rem; display: block; margin-bottom: 0.25rem; }}
        .value {{ color: #eee; font-weight: 700; font-size: 1rem; }}
        .value.trend {{ color: {trend_color}; }}
        .stats-box, .desc-box {{ background: #1c1c1c; border-radius: 10px; padding: 1.5rem; border: 1px solid #333; }}
        h2 {{ font-family: 'Orbitron', sans-serif; color: #eee; border-bottom: 2px solid #444; padding-bottom: 0.5rem; margin-top: 0; }}
        .stat-item {{ display: flex; align-items: center; gap: 0.75rem; font-size: 1.1rem; margin-bottom: 0.5rem; }}
        .stat-item img {{ width: 24px; height: 24px; }} .stat-item span {{ font-weight: 700; color: #fff; }}
        .desc-box p {{ line-height: 1.7; color: #bbb; margin: 0; }}
        .tabs {{ display: flex; border-bottom: 1px solid #333; }}
        .tab-button {{ background: none; border: none; color: #888; padding: 1rem 1.5rem; cursor: pointer; font-family: 'Orbitron', sans-serif; font-size: 1rem; }}
        .tab-button.active {{ color: #fff; border-bottom: 3px solid #F7971E; }}
        .tab-content {{ display: none; padding: 1.5rem; }} .tab-content.active {{ display: block; }}
        .table-container {{ max-height: 400px; overflow-y: auto; }}
        .history-table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 0.8rem 1rem; text-align: left; border-bottom: 1px solid #333; }}
        th {{ color: #aaa; }}
        .variants-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem; }}
        .variant-card {{ background: #222; border-radius: 8px; padding: 1rem; text-decoration: none; color: #ccc; transition: all 0.3s ease; text-align: center; }}
        .variant-card:hover {{ transform: translateY(-5px); background: #333; }}
        .variant-card img {{ width: 100px; height: 100px; margin-bottom: 0.5rem; }}
        .json-viewer {{ position: relative; }}
        .json-blur-overlay {{ backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 2; display: flex; align-items: center; justify-content: center; border-radius: 10px; cursor: pointer; transition: opacity 0.3s; }}
        .json-blur-overlay .fa-lock {{ font-size: 4rem; color: rgba(255,255,255,0.5); }}
        pre {{ background-color: #101010; padding: 1rem; border-radius: 10px; border: 1px solid #2a2a2a; white-space: pre-wrap; font-size: 0.875rem; max-height: 500px; }}
        .footer {{ text-align: center; padding: 1rem; font-size: 0.9rem; color: #777; }}
        a {{ color: #6dd5ed; text-decoration: none; }}
    </style></head><body>
    <div class="container">
    <div class="main-grid">
    <div class="left-panel">
    <div class="pet-card">
        <img class="pet-image" src="{og_image_url}" alt="{og_title}"><h1 class="pet-name">{og_title}</h1>
        <div class="pet-rarity">{rarity}</div>
        <div class="info-grid">
        <div class="info-item"><span class="label">Value</span><span class="value">{value}</span></div>
        <div class="info-item"><span class="label">Demand</span><span class="value">{demand}</span></div>
        <div class="info-item"><span class="label">Trend</span><span class="value trend">{trend_symbol} {trend}</span></div>
        <div class="info-item"><span class="label">Exists</span><span class="value">{owners}</span></div>
        </div></div>
    <div class="stats-box"><h2>Base Stats</h2>{stats_html}</div></div>
    <div class="right-panel">
    <div class="desc-box"><h2>Description</h2><p>{og_description}</p></div>
    <div class="tabs">
        <button class="tab-button active" onclick="openTab(event, 'history')">Value History</button>
        <button class="tab-button" onclick="openTab(event, 'exist-history')">Exist History</button>
        <button class="tab-button" onclick="openTab(event, 'recent-hatches')">Recent Hatches</button>
        {variants_button_html}
        <button class="tab-button" onclick="openTab(event, 'raw-json')">Raw JSON</button>
    </div>
    <div id="history" class="tab-content active"><div class="table-container"><table class="history-table"><tr><th>Date</th><th>Value</th></tr>{history_rows}</table></div></div>
    <div id="exist-history" class="tab-content"><div class="table-container"><table class="history-table"><tr><th>Date</th><th>Amount</th></tr>{exist_history_rows}</table></div></div>
    <div id="recent-hatches" class="tab-content"><div class="table-container"><table class="history-table"><tr><th>Date</th><th>Player</th></tr>{recent_hatches_rows}</table></div></div>
    <div id="variants" class="tab-content"><div class="variants-grid">{variants_html}</div></div>
    <div id="raw-json" class="tab-content"><div class="json-viewer">
        <div id="json-blur" class="json-blur-overlay" onclick="showJson()"><i class="fas fa-lock"></i></div>
        <pre>{escaped_json}</pre></div></div></div></div>
    <div class="footer">Data from <a href="https://bgsi.gg" target="_blank">BGSI.GG</a> | Viewer by 1cy</div></div>
    <script>
        function openTab(evt, tabName) {{
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {{ tabcontent[i].style.display = "none"; }}
            tablinks = document.getElementsByClassName("tab-button");
            for (i = 0; i < tablinks.length; i++) {{ tablinks[i].classList.remove("active"); }}
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.classList.add("active");
        }}
        document.getElementsByClassName("tab-button")[0].click();
        function showJson() {{
            const overlay = document.getElementById('json-blur');
            if (!overlay.style.display || overlay.style.display !== 'none') {{
                const password = prompt("Enter admin password to view raw JSON:");
                if (password === "{admin_password}") {{
                    overlay.style.display = 'none';
                }} else if (password !== null) {{
                    alert("Incorrect password.");
                }}
            }}
        }}
    </script></body></html>
    """
    return page_template.format(og_title=og_title, og_description=og_description, og_url=og_url, og_image_url=og_image_url, rarity_style=rarity_style, trend_color=trend_color, trend_symbol=trend_symbol, stats_html=stats_html, variants_button_html=variants_button_html, variants_html=variants_html, history_rows=history_rows, exist_history_rows=exist_history_rows, recent_hatches_rows=recent_hatches_rows, escaped_json=html.escape(json.dumps(data, indent=2)), rarity=html.escape(pet.get("rarity", '')), value=format_value(pet.get("value")), demand=html.escape(pet.get("demand", 'N/A')).title(), trend=html.escape(pet.get("trend", 'N/A')).title(), owners=format_value(pet.get("owners", 0)), admin_password=ADMIN_PASSWORD)

def generate_stats_page_html(data: dict, request: Request) -> str:
    base_url = str(request.base_url).rstrip('/')
    page_template = """
    <!DOCTYPE html><html lang="en"><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>BGSI.GG Global Stats</title>
    <meta name="description" content="Live global statistics from the BGSI.GG API."><meta property="og:title" content="BGSI.GG Global Stats"><meta property="og:description" content="Live global statistics from the BGSI.GG API."><meta property="og:url" content="{og_url}"><meta property="og:image" content="{base_url}/Logo.png">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Roboto Mono', monospace; background: #080808 linear-gradient(120deg, #080808 0%, #121212 50%, #080808 100%); color: #ccc; margin: 0; padding: 2rem; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; }}
        h1 {{ font-family: 'Orbitron', sans-serif; font-size: 3rem; color: #fff; text-shadow: 0 0 15px rgba(255,255,255,0.2); }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; width: 100%; max-width: 1200px; margin-top: 2rem; }}
        .stat-card {{ background: rgba(28,28,28,0.8); backdrop-filter: blur(8px); border: 1px solid #333; border-radius: 10px; padding: 2rem; text-align: center; box-shadow: 0 8px 25px rgba(0,0,0,0.5); }}
        .stat-card h2 {{ font-family: 'Orbitron', sans-serif; font-size: 1.5rem; margin: 0 0 1rem 0; color: #aaa; }}
        .stat-card .value {{ font-size: 2.5rem; font-weight: 700; color: #fff; background-image: linear-gradient(45deg, #FF416C, #FFD200); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .footer {{ text-align: center; padding: 2rem; font-size: 0.9rem; color: #777; position: absolute; bottom: 0; width: 100%; }} a {{ color: #6dd5ed; }}
    </style></head><body>
    <h1>Global Stats</h1>
    <div class="stats-grid">
        <div class="stat-card"><h2>Users Online</h2><p class="value">{users_online}</p></div>
        <div class="stat-card"><h2>Secrets Hatched (24h)</h2><p class="value">{hatches}</p></div>
        <div class="stat-card"><h2>Total Pet Types</h2><p class="value">{total_pets}</p></div>
        <div class="stat-card"><h2>Total Pets Existing</h2><p class="value">{total_exists}</p></div>
    </div>
    <div class="footer">Data from <a href="https://bgsi.gg" target="_blank">BGSI.GG</a> | Viewer by 1cy</div>
    </body></html>""".format(og_url=html.escape(str(request.url)), base_url=base_url, users_online=format_value(data.get('usersOnline', 0)), hatches=format_value(data.get('secretHatches24h', 0)), total_pets=format_value(data.get('totalPets', 0)), total_exists=format_value(data.get('totalExists', 0)))
    return page_template

def generate_eggs_page_html(data: dict, request: Request) -> str:
    base_url = str(request.base_url).rstrip('/')
    currency_icons = {"Coins": "{}/Coin.png".format(base_url), "Tickets": "{}/Hero_Logo.png".format(base_url), "Seashells": "{}/bubble.png".format(base_url)}
    eggs_html = ""
    for egg in data.get("eggs", []):
        pets_html = "".join(['''
            <div class="pet-item">
                <img src="{image_base}{image_path}" alt="{name}" loading="lazy">
                <div class="pet-info">
                    <span class="pet-name">{name}</span>
                    <span class="pet-rarity" style="background: {rarity_color};">{rarity}</span>
                    <span class="pet-chance">{chance}%</span>
                </div></div>'''.format(image_base=IMAGE_BASE_URL, image_path=pet.get('image'), name=html.escape(pet.get('name', '')), rarity_color=RARITY_COLORS.get(pet.get('rarity'), '#666'), rarity=html.escape(pet.get('rarity', '')), chance=pet.get('chance', 0)) for pet in egg.get("pets", [])])
        
        currency_icon_url = currency_icons.get(egg.get("currency"), "")
        currency_icon_html = '<img src="{}" class="currency-icon" alt="{}">'.format(currency_icon_url, egg.get("currency")) if currency_icon_url else ""
        eggs_html += '''
            <div class="egg-card">
                <div class="egg-header">
                    <img class="egg-image" src="{image_base}{image_path}" alt="{name}">
                    <div class="egg-title">
                        <h2>{name}</h2>
                        <div class="egg-price">{currency_icon}{price}</div>
                        <div class="egg-location">{location}</div>
                    </div></div><div class="pets-grid">{pets}</div></div>
        '''.format(image_base=IMAGE_BASE_URL, image_path=egg.get('image'), name=html.escape(egg.get('name', '')), currency_icon=currency_icon_html, price=format_value(egg.get('price', 0)), location=html.escape(egg.get('location', '')), pets=pets_html)

    return """
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>BGSI.GG Eggs</title>
    <meta name="description" content="Details of all eggs available in BGSI.GG."><meta property="og:title" content="BGSI.GG Eggs"><meta property="og:description" content="Details of all eggs available in BGSI.GG."><meta property="og:url" content="{og_url}"><meta property="og:image" content="{base_url}/Logo.png">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Roboto Mono', monospace; background: #080808 linear-gradient(120deg, #080808 0%, #121212 50%, #080808 100%); color: #ccc; margin: 0; padding: 2rem; }}
        h1 {{ font-family: 'Orbitron', sans-serif; font-size: 3rem; color: #fff; text-align: center; }}
        .eggs-container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 1.5rem; max-width: 1800px; margin: 2rem auto; }}
        .egg-card {{ background: #1c1c1c; border: 1px solid #333; border-radius: 10px; overflow: hidden; }}
        .egg-header {{ display: flex; align-items: center; gap: 1rem; padding: 1rem; background: #222; }}
        .egg-image {{ width: 80px; height: 80px; }}
        .egg-title h2 {{ font-family: 'Orbitron', sans-serif; margin: 0; font-size: 1.5rem; color: #eee; }}
        .egg-price {{ font-size: 1.1rem; color: #fff; font-weight: bold; display: flex; align-items: center; gap: 0.5rem; }}
        .currency-icon {{ width: 20px; height: 20px; }}
        .egg-location {{ font-size: 0.9rem; color: #888; }}
        .pets-grid {{ padding: 1rem; display: grid; grid-template-columns: 1fr; gap: 0.5rem; }}
        .pet-item {{ display: flex; align-items: center; gap: 1rem; background: #2a2a2a; padding: 0.5rem; border-radius: 5px; }}
        .pet-item img {{ width: 40px; height: 40px; }}
        .pet-info {{ display: flex; justify-content: space-between; align-items: center; width: 100%; }}
        .pet-rarity {{ font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 10px; color: white; font-weight: bold; }}
        .footer {{ text-align: center; padding: 2rem; font-size: 0.9rem; color: #777; }} a {{ color: #6dd5ed; }}
    </style></head><body>
    <h1>All Eggs</h1><div class="eggs-container">{eggs_html}</div>
    <div class="footer">Data from <a href="https://bgsi.gg" target="_blank">BGSI.GG</a> | Viewer by 1cy</div>
    </body></html>""".format(og_url=html.escape(str(request.url)), base_url=base_url, eggs_html=eggs_html)

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content="""
    <!DOCTYPE html><html lang="en">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>BGSI.GG API Explorer</title>
    <meta name="description" content="Explore live data from the BGSI.GG API with a rich visual interface."><meta name="theme-color" content="#080808">
    <meta property="og:title" content="BGSI.GG API Explorer"><meta property="og:description" content="Explore live data from the BGSI.GG API with a rich visual interface."><meta property="og:image" content="/Logo.png">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
    body {{ background: #080808 linear-gradient(120deg, #080808 0%, #121212 50%, #080808 100%); color: #999; font-family: 'Roboto Mono', monospace; margin: 0; padding: 2rem; display: flex; align-items: center; justify-content: center; min-height: 100vh; text-align: center; }}
    .container {{ background: rgba(18, 18, 18, 0.9); backdrop-filter: blur(8px); padding: 3rem 4rem; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.7); border: 1px solid #282828; max-width: 900px; width: 90%; }}
    h1 {{ font-family: 'Orbitron', sans-serif; color: #ccc; font-size: 3rem; margin-bottom: 1.5rem; }} p {{ font-size: 1.1rem; }}
    .instructions {{ background: rgba(10, 10, 10, 0.8); padding: 1.5rem 2rem; border-radius: 10px; margin-top: 2rem; border-left: 4px solid #444; text-align: left; }}
    ul {{ list-style: none; padding: 0; }} li {{ margin-bottom: 1rem; }} a {{ color: #6dd5ed; text-decoration: none; }}
    .footer-link {{ margin-top: 3rem; font-size: 0.9rem; color: #777; }}
    </style></head><body>
    <div class="container"><h1>API Data Explorer</h1><p>Explore live data from the <a href="https://api.bgsi.gg" target="_blank">BGSI.GG API</a>.</p>
    <div class="instructions"><p><strong>Examples:</strong></p>
    <ul><li><b>Item Details:</b> <a href="/api/items/mythic-easter-basket">/api/items/mythic-easter-basket</a></li>
    <li><b>Global Stats:</b> <a href="/api/stats">/api/stats</a></li><li><b>All Eggs:</b> <a href="/api/eggs">/api/eggs</a></li></ul></div>
    <p class="footer-link">Viewer by 1cy | Data from <a href="https://www.bgsi.gg" target="_blank">www.bgsi.gg</a>.</p>
    </div></body></html>""")

@app.get("/api/{path:path}", response_class=HTMLResponse)
async def proxy_api(path: str, request: Request):
    query = str(request.query_params)
    target_url = "{}/api/{}".format(API_BASE_URL, path) + ("?{}".format(query) if query else "")
    try:
        async with httpx.AsyncClient(headers=COMMON_HEADERS, follow_redirects=True) as client:
            response = await client.get(target_url)
            response.raise_for_status()
            json_data_obj = response.json()

            path_prefix = path.split('/')[0]
            if path_prefix == "items" and "pet" in json_data_obj:
                return HTMLResponse(content=generate_item_page_html(json_data_obj, request))
            elif path == "stats" and "usersOnline" in json_data_obj:
                return HTMLResponse(content=generate_stats_page_html(json_data_obj, request))
            elif path == "eggs" and "eggs" in json_data_obj:
                return HTMLResponse(content=generate_eggs_page_html(json_data_obj, request))
            
            return HTMLResponse(content="<pre>{}</pre>".format(html.escape(json.dumps(json_data_obj, indent=2))))

    except httpx.HTTPStatusError as e:
        return create_error_html_response("API Error: {}".format(e.response.status_code), "Error fetching from: {}".format(html.escape(target_url)), e.response.status_code, "Reason: {}\nResponse: {}".format(e.response.reason_phrase, e.response.text))
    except (httpx.RequestError, json.JSONDecodeError) as e:
        return create_error_html_response("API Connection/Parsing Error", "Could not connect or parse data from: {}".format(html.escape(target_url)), 503, str(e))
    except Exception as e:
        return create_error_html_response("Unexpected API Error", "An unexpected error occurred.", 500, str(e))

@app.get("/{item_path:path}")
async def proxy_image_or_not_found(item_path: str):
    if not (item_path.lower().endswith(IMAGE_EXTENSIONS) or item_path in ASSETS):
        guidance = '''<div class="guidance"><p>The path requested was: <code>{path}</code></p><p>API paths must start with <code>/api/</code>.</p><p>Return to the <a href="/">API Explorer Home Page</a>.</p></div>'''.format(path=html.escape(item_path))
        return create_error_html_response("Resource Not Found", "The requested path is not a recognized image or API route.", 404, guidance_html=guidance)

    target_url = "{}/{}".format(IMAGE_BASE_URL, item_path)
    headers = {**COMMON_HEADERS, "Accept": "image/*", "Referer": "{}/".format(IMAGE_BASE_URL)}
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            response = await client.get(target_url)
            response.raise_for_status()
            return StreamingResponse(io.BytesIO(response.content), media_type=response.headers.get("content-type"))
    except httpx.HTTPStatusError as e:
        return create_error_html_response("Fetch Error: {}".format(e.response.status_code), "Could not retrieve resource from: {}".format(html.escape(target_url)), e.response.status_code, "Reason: {}".format(e.response.reason_phrase))
    except Exception as e:
        return create_error_html_response("Connection Error", "Could not connect to server at: {}".format(html.escape(IMAGE_BASE_URL)), 503, str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
