from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import httpx
import uvicorn
from string import Template
import json
import html
import io
from datetime import datetime

app = FastAPI(title="BGSI.GG API Explorer & Image Proxy", docs_url=None, redoc_url=None)

API_BASE_URL = "https://api.bgsi.gg"
IMAGE_BASE_URL = "https://www.bgsi.gg"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico")
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
    return str(value)

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
    return HTMLResponse(content=f"""
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
</div></body></html>""", status_code=status_code)

def generate_item_page_html(data: dict, request: Request) -> str:
    pet = data.get("pet", {})
    og_image_url = f"{IMAGE_BASE_URL}{pet.get('image', '')}" if pet.get('image') else f"{str(request.base_url).rstrip('/')}/Logo.png"
    og_title = html.escape(pet.get("name", "BGSI Item"))
    og_description = html.escape(pet.get("description", "No description available."))
    og_url = html.escape(str(request.url))
    rarity_style = RARITY_COLORS.get(pet.get("rarity"), "none")
    trend_color, trend_symbol = TREND_STYLES.get(pet.get("trend"), ("#999", '<i class="fas fa-question"></i>'))
    base_url = str(request.base_url).rstrip('/')

    stats_html = ""
    if pet.get("stats"):
        stats = pet["stats"]
        stats_html = f"""
            <div class="stat-item"><img src="{base_url}/bubble.png" alt="Bubbles">Bubbles: <span>{stats.get('bubbles', 0):,}</span></div>
            <div class="stat-item"><img src="{base_url}/Coin.png" alt="Coins">Coins: <span>{stats.get('coins', 0):,}</span></div>
            <div class="stat-item"><img src="{base_url}/gem.png" alt="Gems">Gems: <span>{stats.get('gems', 0):,}</span></div>"""

    variants_html = ""
    if pet.get("allVariants"):
        for variant in pet["allVariants"]:
            if variant.get("slug") != pet.get("slug"):
                variants_html += f"""
                    <a href="/api/items/{variant.get('slug', '')}" class="variant-card">
                        <img src="{IMAGE_BASE_URL}{variant.get('image')}" alt="{html.escape(variant.get('name', ''))}">
                        <div class="variant-name">{html.escape(variant.get('name', ''))}</div>
                    </a>"""
    
    history_rows = "".join([f"<tr><td>{format_timestamp(h.get('timestamp'))}</td><td>{format_value(h.get('value'))}</td></tr>" for h in data.get("history", [])])
    exist_history_rows = "".join([f"<tr><td>{format_timestamp(h.get('timestamp'))}</td><td>{h.get('existAmount')}</td></tr>" for h in data.get("existHistories", [])])
    recent_hatches_rows = "".join([f"<tr><td>{format_timestamp(h.get('timestamp'))}</td><td>{html.escape(h.get('playerName') or 'Private')}</td></tr>" for h in data.get("recentHatches", [])])

    return f"""
<!DOCTYPE html><html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{og_title}</title><meta name="description" content="{og_description}"><meta name="theme-color" content="#080808">
    <meta property="og:type" content="website"><meta property="og:url" content="{og_url}"><meta property="og:title" content="{og_title}"><meta property="og:description" content="{og_description}"><meta property="og:image" content="{og_image_url}">
    <meta property="twitter:card" content="summary_large_image"><meta property="twitter:url" content="{og_url}"><meta property="twitter:title" content="{og_title}"><meta property="twitter:description" content="{og_description}"><meta property="twitter:image" content="{og_image_url}">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body {{ font-family: 'Roboto Mono', monospace; background: #080808 linear-gradient(120deg, #080808 0%, #121212 50%, #080808 100%); color: #ccc; margin: 0; padding: 2rem; }}
        .container {{ max-width: 1200px; margin: auto; background: rgba(18,18,18,0.8); backdrop-filter: blur(10px); border-radius: 15px; border: 1px solid #282828; box-shadow: 0 10px 30px rgba(0,0,0,0.7); overflow: hidden; }}
        .main-grid {{ display: grid; grid-template-columns: 350px 1fr; gap: 2rem; padding: 2rem; }}
        .left-panel, .right-panel {{ display: flex; flex-direction: column; gap: 1.5rem; }}
        .pet-card {{ background: #1c1c1c; border-radius: 10px; padding: 1.5rem; text-align: center; border: 1px solid #333; }}
        .pet-card .pet-name {{ font-family: 'Orbitron', sans-serif; font-size: 2rem; margin: 1rem 0 0.5rem 0; color: #fff; }}
        .pet-card .pet-image {{ max-width: 100%; height: auto; border-radius: 10px; background: rgba(0,0,0,0.2); }}
        .pet-rarity {{ display: inline-block; padding: 0.4rem 1rem; border-radius: 20px; font-weight: 700; color: white; background: {rarity_style}; margin-bottom: 1rem; font-size: 0.9rem; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; text-align: left; }}
        .info-item {{ background: #222; padding: 0.8rem; border-radius: 8px; }}
        .info-item .label {{ color: #888; font-size: 0.8rem; display: block; margin-bottom: 0.25rem; }}
        .info-item .value {{ color: #eee; font-weight: 700; font-size: 1rem; }}
        .info-item .value.trend {{ color: {trend_color}; }}
        .stats-box, .desc-box {{ background: #1c1c1c; border-radius: 10px; padding: 1.5rem; border: 1px solid #333; }}
        h2 {{ font-family: 'Orbitron', sans-serif; color: #eee; border-bottom: 2px solid #444; padding-bottom: 0.5rem; margin-top: 0; }}
        .stat-item {{ display: flex; align-items: center; gap: 0.75rem; font-size: 1.1rem; color: #ddd; margin-bottom: 0.5rem; }}
        .stat-item img {{ width: 24px; height: 24px; }} .stat-item span {{ font-weight: 700; color: #fff; }}
        .desc-box p {{ line-height: 1.7; color: #bbb; margin: 0; }}
        .tabs {{ display: flex; border-bottom: 1px solid #333; }}
        .tab-button {{ background: none; border: none; color: #888; padding: 1rem 1.5rem; cursor: pointer; font-family: 'Orbitron', sans-serif; font-size: 1rem; }}
        .tab-button.active {{ color: #fff; border-bottom: 3px solid #F7971E; }}
        .tab-content {{ display: none; padding: 1.5rem; }} .tab-content.active {{ display: block; }}
        .table-container {{ max-height: 400px; overflow-y: auto; }}
        .history-table {{ width: 100%; border-collapse: collapse; }}
        .history-table th, .history-table td {{ padding: 0.8rem 1rem; text-align: left; border-bottom: 1px solid #333; }}
        .history-table th {{ color: #aaa; }}
        .variants-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem; }}
        .variant-card {{ background: #222; border-radius: 8px; padding: 1rem; text-align: center; text-decoration: none; color: #ccc; transition: all 0.3s ease; }}
        .variant-card:hover {{ transform: translateY(-5px); background: #333; }}
        .variant-card img {{ width: 100px; height: 100px; margin-bottom: 0.5rem; }} .variant-name {{ font-weight: 500; }}
        .json-viewer {{ position: relative; }}
        .json-blur-overlay {{ backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 2; display: flex; align-items: center; justify-content: center; border-radius: 10px; cursor: pointer; }}
        .json-blur-overlay .fa-lock {{ font-size: 4rem; color: rgba(255,255,255,0.5); }}
        pre {{ background-color: #101010; color: #d0d0d0; padding: 1rem; border-radius: 10px; border: 1px solid #2a2a2a; white-space: pre-wrap; overflow-x: auto; font-size: 0.875rem; max-height: 500px; }}
        .footer {{ text-align: center; padding: 1rem; font-size: 0.9rem; color: #777; }}
        a {{ color: #6dd5ed; text-decoration: none; }} a:hover {{ text-decoration: underline; }}
    </style>
</head><body>
<div class="container">
    <div class="main-grid">
        <div class="left-panel">
            <div class="pet-card">
                <img class="pet-image" src="{og_image_url}" alt="{og_title}">
                <h1 class="pet-name">{og_title}</h1>
                <div class="pet-rarity">{html.escape(pet.get("rarity", ''))}</div>
                <div class="info-grid">
                    <div class="info-item"><span class="label">Value</span><span class="value">{format_value(pet.get("value"))}</span></div>
                    <div class="info-item"><span class="label">Demand</span><span class="value">{html.escape(pet.get("demand", 'N/A')).title()}</span></div>
                    <div class="info-item"><span class="label">Trend</span><span class="value trend">{trend_symbol} {html.escape(pet.get("trend", 'N/A')).title()}</span></div>
                    <div class="info-item"><span class="label">Exists</span><span class="value">{pet.get("owners", 0):,}</span></div>
                </div>
            </div>
            <div class="stats-box"><h2>Base Stats</h2>{stats_html}</div>
        </div>
        <div class="right-panel">
            <div class="desc-box"><h2>Description</h2><p>{og_description}</p></div>
            <div class="tabs">
                <button class="tab-button active" onclick="openTab(event, 'history')">Value History</button>
                <button class="tab-button" onclick="openTab(event, 'exist-history')">Exist History</button>
                <button class="tab-button" onclick="openTab(event, 'recent-hatches')">Recent Hatches</button>
                { '<button class="tab-button" onclick="openTab(event, \'variants\')">Variants</button>' if variants_html else '' }
                <button class="tab-button" onclick="openTab(event, 'raw-json')">Raw JSON</button>
            </div>
            <div id="history" class="tab-content active"><div class="table-container"><table class="history-table"><tr><th>Date</th><th>Value</th></tr>{history_rows}</table></div></div>
            <div id="exist-history" class="tab-content"><div class="table-container"><table class="history-table"><tr><th>Date</th><th>Amount</th></tr>{exist_history_rows}</table></div></div>
            <div id="recent-hatches" class="tab-content"><div class="table-container"><table class="history-table"><tr><th>Date</th><th>Player</th></tr>{recent_hatches_rows}</table></div></div>
            <div id="variants" class="tab-content"><div class="variants-grid">{variants_html}</div></div>
            <div id="raw-json" class="tab-content">
                <div class="json-viewer">
                    <div id="json-blur" class="json-blur-overlay" onclick="showJson()"><i class="fas fa-lock"></i></div>
                    <pre>{html.escape(json.dumps(data, indent=2))}</pre>
                </div>
            </div>
        </div>
    </div>
    <div class="footer">Data from <a href="https://bgsi.gg" target="_blank">BGSI.GG</a> | Viewer by 1cy</div>
</div>
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
            if (password === "{ADMIN_PASSWORD}") {{
                overlay.style.display = 'none';
            }} else if (password) {{
                alert("Incorrect password.");
            }}
        }}
    }}
</script>
</body></html>"""

def generate_stats_page_html(data: dict, request: Request) -> str:
    base_url = str(request.base_url).rstrip('/')
    og_url = html.escape(str(request.url))
    return f"""
<!DOCTYPE html><html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>BGSI.GG Global Stats</title>
    <meta name="description" content="Live global statistics from the BGSI.GG API.">
    <meta property="og:title" content="BGSI.GG Global Stats"><meta property="og:description" content="Live global statistics from the BGSI.GG API.">
    <meta property="og:url" content="{og_url}"><meta property="og:image" content="{base_url}/Logo.png">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Roboto Mono', monospace; background: #080808 linear-gradient(120deg, #080808 0%, #121212 50%, #080808 100%); color: #ccc; margin: 0; padding: 2rem; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; }}
        h1 {{ font-family: 'Orbitron', sans-serif; font-size: 3rem; color: #fff; text-shadow: 0 0 15px rgba(255,255,255,0.2); }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; width: 100%; max-width: 1200px; margin-top: 2rem; }}
        .stat-card {{ background: rgba(28,28,28,0.8); backdrop-filter: blur(8px); border: 1px solid #333; border-radius: 10px; padding: 2rem; text-align: center; box-shadow: 0 8px 25px rgba(0,0,0,0.5); }}
        .stat-card h2 {{ font-family: 'Orbitron', sans-serif; font-size: 1.5rem; margin: 0 0 1rem 0; color: #aaa; }}
        .stat-card .value {{ font-size: 2.5rem; font-weight: 700; color: #fff; background-image: linear-gradient(45deg, #FF416C, #FFD200); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .footer {{ text-align: center; padding: 2rem; font-size: 0.9rem; color: #777; position: absolute; bottom: 0; width: 100%; }}
        a {{ color: #6dd5ed; text-decoration: none; }}
    </style>
</head>
<body>
    <h1>Global Stats</h1>
    <div class="stats-grid">
        <div class="stat-card"><h2>Users Online</h2><p class="value">{data.get('usersOnline', 0):,}</p></div>
        <div class="stat-card"><h2>Secrets Hatched (24h)</h2><p class="value">{data.get('secretHatches24h', 0):,}</p></div>
        <div class="stat-card"><h2>Total Pet Types</h2><p class="value">{data.get('totalPets', 0):,}</p></div>
        <div class="stat-card"><h2>Total Pets Existing</h2><p class="value">{data.get('totalExists', 0):,}</p></div>
    </div>
    <div class="footer">Data from <a href="https://bgsi.gg" target="_blank">BGSI.GG</a> | Viewer by 1cy</div>
</body></html>"""

def generate_eggs_page_html(data: dict, request: Request) -> str:
    eggs_data = data.get("eggs", [])
    base_url = str(request.base_url).rstrip('/')
    og_url = html.escape(str(request.url))
    currency_icons = {"Coins": f"{base_url}/Coin.png", "Tickets": f"{base_url}/Hero_Logo.png", "Seashells": f"{base_url}/bubble.png"}

    eggs_html = ""
    for egg in eggs_data:
        pets_html = "".join([f"""
            <div class="pet-item">
                <img src="{IMAGE_BASE_URL}{pet.get('image')}" alt="{html.escape(pet.get('name', ''))}" loading="lazy">
                <div class="pet-info">
                    <span class="pet-name">{html.escape(pet.get('name', ''))}</span>
                    <span class="pet-rarity" style="background: {RARITY_COLORS.get(pet.get('rarity'), '#666')};">{html.escape(pet.get('rarity', ''))}</span>
                    <span class="pet-chance">{pet.get('chance', 0)}%</span>
                </div>
            </div>""" for pet in egg.get("pets", [])])
        
        currency_icon_url = currency_icons.get(egg.get("currency"), "")
        currency_icon_html = f'<img src="{currency_icon_url}" class="currency-icon" alt="{egg.get("currency")}">' if currency_icon_url else ""
        eggs_html += f"""
            <div class="egg-card">
                <div class="egg-header">
                    <img class="egg-image" src="{IMAGE_BASE_URL}{egg.get('image')}" alt="{html.escape(egg.get('name', ''))}">
                    <div class="egg-title">
                        <h2>{html.escape(egg.get('name', ''))}</h2>
                        <div class="egg-price">{currency_icon_html} {egg.get('price', 0):,}</div>
                        <div class="egg-location">{html.escape(egg.get('location', ''))}</div>
                    </div>
                </div>
                <div class="pets-grid">{pets_html}</div>
            </div>"""

    return f"""
<!DOCTYPE html><html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>BGSI.GG Eggs</title>
    <meta name="description" content="Details of all eggs available in BGSI.GG.">
    <meta property="og:title" content="BGSI.GG Eggs"><meta property="og:description" content="Details of all eggs available in BGSI.GG.">
    <meta property="og:url" content="{og_url}"><meta property="og:image" content="{base_url}/Logo.png">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Roboto Mono', monospace; background: #080808 linear-gradient(120deg, #080808 0%, #121212 50%, #080808 100%); color: #ccc; margin: 0; padding: 2rem; }}
        h1 {{ font-family: 'Orbitron', sans-serif; font-size: 3rem; color: #fff; text-shadow: 0 0 15px rgba(255,255,255,0.2); text-align: center; }}
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
        .pet-name {{ color: #ddd; }}
        .pet-rarity {{ font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 10px; color: white; font-weight: bold; }}
        .pet-chance {{ font-size: 0.9rem; color: #aaa; }}
        .footer {{ text-align: center; padding: 2rem; font-size: 0.9rem; color: #777; }}
        a {{ color: #6dd5ed; text-decoration: none; }}
    </style>
</head><body>
<h1>All Eggs</h1><div class="eggs-container">{eggs_html}</div>
<div class="footer">Data from <a href="https://bgsi.gg" target="_blank">BGSI.GG</a> | Viewer by 1cy</div>
</body></html>"""

def generate_api_response_html(json_data_str: str, page_title: str, og_description: str, og_image_url: str, og_url: str) -> str:
    escaped_page_title, escaped_og_description, escaped_og_image_url, escaped_og_url, escaped_json_data_str = map(html.escape, [page_title, og_description, og_image_url, og_url, json_data_str])
    return f"""
<!DOCTYPE html><html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{escaped_page_title}</title>
  <meta name="description" content="{escaped_og_description}"><meta name="theme-color" content="#080808">
  <meta property="og:type" content="website"><meta property="og:url" content="{escaped_og_url}"><meta property="og:title" content="{escaped_page_title}"><meta property="og:description" content="{escaped_og_description}"><meta property="og:image" content="{escaped_og_image_url}">
  <meta property="twitter:card" content="summary_large_image"><meta property="twitter:url" content="{escaped_og_url}"><meta property="twitter:title" content="{escaped_page_title}"><meta property="twitter:description" content="{escaped_og_description}"><meta property="twitter:image" content="{escaped_og_image_url}">
  <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    body {{ background-color: #080808; color: #cccccc; font-family: 'Roboto Mono', monospace; font-size: 14px; line-height: 1.6; padding: 2rem; margin: 0; }}
    pre {{ background-color: #161616; color: #d0d0d0; padding: 2rem; border-radius: 10px; border: 1px solid #2a2a2a; box-shadow: 0 6px 20px rgba(0,0,0,0.6); white-space: pre; overflow-x: auto; font-size: 0.875rem; }}
  </style>
</head><body><pre>{escaped_json_data_str}</pre></body></html>"""

INDEX_HTML_TEMPLATE = Template("""
<!DOCTYPE html><html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>BGSI.GG API Explorer</title>
  <meta name="description" content="Explore live JSON responses and images from the BGSI.GG API."><meta name="theme-color" content="#080808">
  <meta property="og:type" content="website"><meta property="og:url" content="https://bgsi-kyc3.onrender.com/"><meta property="og:title" content="BGSI.GG API Explorer"><meta property="og:description" content="Explore live data from the BGSI.GG API with a rich visual interface."><meta property="og:image" content="https://bgsi-kyc3.onrender.com/Logo.png">
  <meta property="twitter:card" content="summary_large_image"><meta property="twitter:url" content="https://bgsi-kyc3.onrender.com/"><meta property="twitter:title" content="BGSI.GG API Explorer"><meta property="twitter:description" content="Explore live data from the BGSI.GG API with a rich visual interface."><meta property="twitter:image" content="https://bgsi-kyc3.onrender.com/Logo.png">
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    @keyframes fadeInDown {{ 0% {{ opacity: 0; transform: translateY(-20px); }} 100% {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes fadeInUp {{ 0% {{ opacity: 0; transform: translateY(20px); }} 100% {{ opacity: 1; transform: translateY(0); }} }}
    body {{ background: #080808 linear-gradient(120deg, #080808 0%, #121212 50%, #080808 100%); color: #999999; font-family: 'Roboto Mono', monospace; margin: 0; padding: 2rem; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; text-align: center; }}
    .container {{ background: rgba(18, 18, 18, 0.9); backdrop-filter: blur(8px); padding: 3rem 4rem; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.7); border: 1px solid #282828; max-width: 900px; width: 90%; animation: fadeInDown 1s ease-out forwards; }}
    h1 {{ font-family: 'Orbitron', sans-serif; color: #cccccc; font-size: 3rem; margin-bottom: 1.5rem; letter-spacing: 1px; text-shadow: 0 0 8px rgba(200, 200, 200, 0.15); }}
    p {{ font-size: 1.1rem; line-height: 1.7; }} a {{ color: #888888; text-decoration: none; transition: color 0.3s ease; font-weight: 500; }} a:hover {{ color: #aaaaaa; }}
    .instructions {{ background: rgba(10, 10, 10, 0.8); padding: 1.5rem 2rem; border-radius: 10px; margin-top: 2rem; border-left: 4px solid #444444; text-align: left; }}
    .instructions ul {{ list-style: none; padding: 0; }} .instructions ul li {{ margin-bottom: 1rem; }}
    .example-path {{ background-color: #101010; color: #999999; padding: 0.3em 0.6em; border-radius: 5px; border: 1px solid #303030; }}
    .footer-link {{ margin-top: 3rem; font-size: 0.9rem; color: #777777; }}
  </style>
</head><body>
<div class="container">
<h1>API Data Explorer</h1><p>Explore live data from the <a href="https://api.bgsi.gg" target="_blank">BGSI.GG API</a> with a rich visual interface.</p>
<div class="instructions">
  <p><strong>Examples:</strong></p>
  <ul>
    <li><b>Item Details:</b> <a href="/api/items/mythic-easter-basket">/api/items/mythic-easter-basket</a></li>
    <li><b>Global Stats:</b> <a href="/api/stats">/api/stats</a></li>
    <li><b>All Eggs:</b> <a href="/api/eggs">/api/eggs</a></li>
  </ul>
</div>
<p class="footer-link">Viewer by 1cy | Data from <a href="https://www.bgsi.gg" target="_blank">www.bgsi.gg</a>.</p>
</div>
</body></html>""")

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=INDEX_HTML_TEMPLATE.substitute())

@app.get("/api/{path:path}", response_class=HTMLResponse)
async def proxy_api(path: str, request: Request):
    query = str(request.query_params)
    target_url = f"{API_BASE_URL}/api/{path}" + (f"?{query}" if query else "")
    api_headers = {**COMMON_HEADERS, "Accept": "application/json", "Referer": f"{API_BASE_URL}/"}

    try:
        async with httpx.AsyncClient(headers=api_headers, follow_redirects=True) as client:
            response = await client.get(target_url)
            response.raise_for_status()
            json_data_obj = response.json()

            path_prefix = path.split('/')[0]
            if path_prefix == "items" and "pet" in json_data_obj:
                return HTMLResponse(content=generate_item_page_html(json_data_obj, request))
            elif path == "stats":
                return HTMLResponse(content=generate_stats_page_html(json_data_obj, request))
            elif path == "eggs" and "eggs" in json_data_obj:
                return HTMLResponse(content=generate_eggs_page_html(json_data_obj, request))

            pretty_json_str = json.dumps(json_data_obj, indent=2)
            og_page_title = f"{path.replace('/', ' ').title()} - BGSI.GG Data"
            og_description = f"Live data for {path} from the BGSI.GG API."
            og_image_url = f"{str(request.base_url).rstrip('/')}/Logo.png"
            return HTMLResponse(content=generate_api_response_html(pretty_json_str, og_page_title, og_description, og_image_url, str(request.url)))
    except httpx.HTTPStatusError as e:
        return create_error_html_response(f"API Error: {e.response.status_code}", f"Error fetching from: {html.escape(target_url)}.", e.response.status_code, f"Reason: {e.response.reason_phrase}\nResponse: {e.response.text}")
    except (httpx.RequestError, json.JSONDecodeError) as e:
        return create_error_html_response("API Connection/Parsing Error", f"Could not connect to or parse data from: {html.escape(target_url)}.", 503, str(e))
    except Exception as e:
        return create_error_html_response("Unexpected API Error", "An unexpected error occurred.", 500, str(e))

@app.get("/{item_path:path}")
async def proxy_image_or_not_found(item_path: str):
    is_image_path = item_path.lower().endswith(IMAGE_EXTENSIONS)
    is_asset = item_path in ["Coin.png", "gem.png", "bubble.png", "Hero_Logo.png", "Logo.png"]
    if not (is_image_path or is_asset):
        guidance = f"""<div class="guidance"><p>The path requested was: <code class="example-path">{html.escape(item_path)}</code></p><p>API paths must start with <code class="example-path">/api/</code>. Example: <a href="/api/stats">/api/stats</a></p><p>Return to the <a href="/">API Explorer Home Page</a>.</p></div>"""
        return create_error_html_response("Resource Not Found", "The requested path is not a recognized image or API route.", 404, guidance_html=guidance)

    target_url = f"{IMAGE_BASE_URL}/{item_path}"
    headers = {**COMMON_HEADERS, "Accept": "image/*", "Referer": f"{IMAGE_BASE_URL}/"}
    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            response = await client.get(target_url)
            response.raise_for_status()
            return StreamingResponse(io.BytesIO(response.content), media_type=response.headers.get("content-type"))
    except httpx.HTTPStatusError as e:
        return create_error_html_response(f"Fetch Error: {e.response.status_code}", f"Could not retrieve resource from: {html.escape(target_url)}.", e.response.status_code, f"Reason: {e.response.reason_phrase}")
    except Exception as e:
        return create_error_html_response("Connection Error", f"Could not connect to server at: {html.escape(IMAGE_BASE_URL)}.", 503, str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
