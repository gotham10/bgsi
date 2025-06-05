from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import httpx
import uvicorn
from string import Template

app = FastAPI()

HTML_TEMPLATE = Template("""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <title>API Data</title>
  <style>
    body {
      background: #0f0f0f;
      color: #fefefe;
      font-family: monospace;
      font-size: 13px;
      padding: 1rem;
      margin: 0;
      white-space: pre;
      overflow-x: auto;
    }
  </style>
</head>
<body>$json</body>
</html>
""")

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BGSI API Viewer</title>
  <style>
    body {
      background: #121212;
      color: #f0f0f0;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      margin: 0;
      padding: 3rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
    }
    h1 {
      font-size: 2.5rem;
      margin-bottom: 1rem;
    }
    p {
      font-size: 1.2rem;
      max-width: 600px;
      text-align: center;
    }
    code {
      background: #333;
      padding: 0.2rem 0.5rem;
      border-radius: 5px;
      color: #00eaff;
    }
  </style>
</head>
<body>
  <h1>Welcome to the BGSI API Viewer</h1>
  <p>To explore data, use the <code>/api/&lt;slug&gt;</code> endpoint in the address bar.</p>
  <p>Example: <code>/api/stats</code></p>
</body>
</html>
""")

API_BASE = "https://api.bgsi.gg"

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(INDEX_HTML)

@app.get("/", response_class=HTMLResponse)
async def index():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://api.bgsi.gg/",
        "Origin": "https://api.bgsi.gg",
    }
    try:
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(f"{API_BASE}/api/stats")
            response.raise_for_status()
            data = response.json()
            slugs = data.get("slugs", [])
    except Exception as e:
        return HTMLResponse(f"<h1 style='color:red;'>Error loading slugs:</h1><pre>{str(e)}</pre>", status_code=500)

    items_html = "\n".join([f'<li><a href=\"/api/{slug}\">{slug}</a></li>' for slug in slugs])
    return INDEX_HTML.substitute(items=items_html)

@app.get("/api/{path:path}", response_class=HTMLResponse)
async def proxy_api(path: str, request: Request):
    query = str(request.query_params)
    target_url = f"{API_BASE}/api/{path}"
    if query:
        target_url += f"?{query}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://api.bgsi.gg/",
        "Origin": "https://api.bgsi.gg",
    }

    try:
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(target_url)
            response.raise_for_status()
            json_data = response.json()
    except Exception as e:
        return HTMLResponse(f"<h1 style='color:red;'>Error fetching API:</h1><pre>{str(e)}</pre>", status_code=500)

    return HTML_TEMPLATE.substitute(json=html_escape_json(json_data))

def html_escape_json(json_data):
    import json
    import html
    formatted = json.dumps(json_data, indent=2)
    return html.escape(formatted)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
