from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import httpx
import uvicorn

app = FastAPI()

from string import Template

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

API_BASE = "https://api.bgsi.gg"

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
