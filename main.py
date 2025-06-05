from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import httpx
import uvicorn
from string import Template

app = FastAPI()

HTML_TEMPLATE = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>API Viewer</title>
  <style>
    body {
      background-color: #1a1a1a;
      color: #f0f0f0;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      margin: 0;
      padding: 2rem;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    h1 {
      color: #4fc3f7;
      font-size: 2.5rem;
      margin-bottom: 1rem;
    }
    p {
      max-width: 600px;
      font-size: 1.2rem;
      text-align: center;
      line-height: 1.5;
    }
    a {
      color: #4fc3f7;
      text-decoration: none;
    }
    a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <h1>Hello 👋</h1>
  <p>This is the API Viewer for <a href="https://api.bgsi.gg">bgsi.gg</a>.<br>
     You can use the <a href="/">home page</a> to browse available endpoints, and click to see live data here.</p>
</body>
</html>
""")

INDEX_HTML = Template("""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>Slug Viewer</title>
  <style>
    body {
      background: #1a1a1a;
      color: #f0f0f0;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      margin: 0;
      padding: 2rem;
    }
    h1 {
      text-align: center;
    }
    ul {
      list-style: none;
      padding: 0;
    }
    li {
      margin: 0.5rem 0;
      background: #2c2c2c;
      padding: 1rem;
      border-radius: 8px;
      transition: background 0.3s;
    }
    li:hover {
      background: #3a3a3a;
    }
    a {
      color: #4fc3f7;
      text-decoration: none;
    }
  </style>
</head>
<body>
  <h1>API Slugs</h1>
  <ul>
    $items
  </ul>
</body>
</html>
""")

API_BASE = "https://api.bgsi.gg"

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
