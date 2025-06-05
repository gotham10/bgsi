from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import httpx
import uvicorn
from string import Template
import json
import html

app = FastAPI()

HTML_TEMPLATE = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>API Data Response</title>
  <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    body {
      background-color: #1e1e2e;
      color: #c0c5ce;
      font-family: 'Roboto Mono', monospace;
      font-size: 14px;
      line-height: 1.6;
      padding: 2rem;
      margin: 0;
    }
    pre {
      background-color: #282a36;
      color: #f8f8f2;
      padding: 2rem;
      border-radius: 10px;
      border: 1px solid #44475a;
      box-shadow: 0 8px 25px rgba(0,0,0,0.5);
      white-space: pre;
      overflow-x: auto;
      font-size: 0.875rem;
    }
  </style>
</head>
<body>
  <pre>$json</pre>
</body>
</html>
""")

INDEX_HTML = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>BGSI.GG API Explorer</title>
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    @keyframes fadeInDown {
      0% { opacity: 0; transform: translateY(-30px); }
      100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInUp {
      0% { opacity: 0; transform: translateY(30px); }
      100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulseGlow {
      0% { text-shadow: 0 0 5px #00ffff, 0 0 10px #00ffff, 0 0 15px #00ffff, 0 0 20px #228DFF; }
      50% { text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 30px #228DFF, 0 0 40px #228DFF; }
      100% { text-shadow: 0 0 5px #00ffff, 0 0 10px #00ffff, 0 0 15px #00ffff, 0 0 20px #228DFF; }
    }
    @keyframes backgroundPan {
        0% { background-position: 0% center; }
        100% { background-position: 200% center; }
    }
    body {
      background: #0d1117;
      background-image: linear-gradient(120deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
      background-size: 200% 100%;
      animation: backgroundPan 30s linear infinite;
      color: #c9d1d9;
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
      background: rgba(22, 27, 34, 0.85);
      backdrop-filter: blur(10px);
      padding: 3rem 4rem;
      border-radius: 20px;
      box-shadow: 0 15px 40px rgba(0,0,0,0.7), 0 0 0 1px rgba(76, 140, 255, 0.3);
      max-width: 900px;
      width: 90%;
      animation: fadeInDown 1s ease-out forwards;
      border: 1px solid rgba(76, 140, 255, 0.2);
    }
    h1 {
      font-family: 'Orbitron', sans-serif;
      color: #58a6ff;
      font-size: 3.5rem;
      margin-bottom: 1.5rem;
      letter-spacing: 1px;
      animation: pulseGlow 3s infinite ease-in-out, fadeInDown 0.8s ease-out 0.2s forwards;
      opacity: 0;
    }
    p {
      font-size: 1.15rem;
      line-height: 1.8;
      margin-bottom: 1.5rem;
      color: #8b949e;
      animation: fadeInUp 1s ease-out 0.4s forwards;
      opacity: 0;
    }
    .api-info {
      margin-bottom: 2.5rem;
      font-size: 1rem;
      color: #c9d1d9;
      animation: fadeInUp 1s ease-out 0.6s forwards;
      opacity: 0;
    }
    a {
      color: #58a6ff;
      text-decoration: none;
      transition: color 0.3s ease, text-shadow 0.3s ease;
      font-weight: 500;
    }
    a:hover {
      color: #79c0ff;
      text-shadow: 0 0 10px #79c0ff;
    }
    .instructions {
      background: rgba(13, 17, 23, 0.7);
      padding: 1.5rem 2rem;
      border-radius: 12px;
      margin-top: 2rem;
      border-left: 4px solid #58a6ff;
      text-align: left;
      animation: fadeInUp 1s ease-out 0.8s forwards;
      opacity: 0;
    }
    .instructions p {
        color: #c9d1d9;
        font-size: 1rem;
        margin-bottom: 0.8rem;
        line-height: 1.6;
    }
    .example-path {
        font-family: 'Roboto Mono', monospace;
        background-color: #010409;
        color: #58a6ff;
        padding: 0.3em 0.6em;
        border-radius: 5px;
        font-weight: 500;
        border: 1px solid #30363d;
    }
    .footer-link {
        margin-top: 3rem;
        font-size: 0.9rem;
        color: #8b949e;
        animation: fadeInUp 1s ease-out 1s forwards;
        opacity: 0;
    }
    .footer-link a {
        font-weight: bold;
    }

  </style>
</head>
<body>
  <div class="container">
    <h1>API Data Explorer</h1>
    <p>Dynamically inspect live JSON responses from the <a href="https://api.bgsi.gg" target="_blank" rel="noopener noreferrer">BGSI.GG API</a>.</p>
    <div class="api-info">
      <p>This interface allows you to directly proxy requests and view data.
      To fetch data, modify the URL by appending the API path you wish to query after <code class="example-path">/api/</code>.</p>
    </div>
    <div class="instructions">
        <p><strong>How to use:</strong></p>
        <p>1. Identify the API endpoint you want to access from <a href="https://api.bgsi.gg" target="_blank" rel="noopener noreferrer">api.bgsi.gg</a>.</p>
        <p>2. In your browser's address bar, append the path to this page's URL.<br>
           For instance, to access data from <code class="example-path">/api/some/endpoint</code> on the target API, you would navigate to:</p>
        <p><a href="/api/some/endpoint">localhost:3000/api/some/endpoint</a></p>
        <p>3. If the API endpoint requires query parameters, like <code class="example-path">/api/v1/data?type=example&id=123</code>, include them as well:</p>
        <p><a href="/api/v1/data?type=example&id=123">localhost:3000/api/v1/data?type=example&id=123</a></p>
    </div>
    <p class="footer-link">Powered by FastAPI &amp; HTTMX. View data from <a href="https://api.bgsi.gg" target="_blank" rel="noopener noreferrer">api.bgsi.gg</a>.</p>
  </div>
</body>
</html>
""")

API_BASE = "https://api.bgsi.gg"

@app.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_HTML.substitute()

@app.get("/api/{path:path}", response_class=HTMLResponse)
async def proxy_api(path: str, request: Request):
    query = str(request.query_params)
    target_url = f"{API_BASE}/api/{path}"
    if query:
        target_url += f"?{query}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"{API_BASE}/",
        "Origin": API_BASE,
    }

    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            response = await client.get(target_url)
            response.raise_for_status()
            
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                json_data = response.json()
                pretty_json = json.dumps(json_data, indent=2, sort_keys=True)
            else:
                pretty_json = response.text

            escaped_output = html.escape(pretty_json)
            return HTML_TEMPLATE.substitute(json=escaped_output)

    except httpx.HTTPStatusError as e:
        error_message = f"HTTP Error: {e.response.status_code} {e.response.reason_phrase}\nURL: {e.request.url}\nResponse: {e.response.text}"
        return HTMLResponse(f"<h1 style='color:red;'>Error fetching API:</h1><pre>{html.escape(error_message)}</pre>", status_code=e.response.status_code)
    except httpx.RequestError as e:
        error_message = f"Request Error: {str(e)}\nURL: {e.request.url}"
        return HTMLResponse(f"<h1 style='color:red;'>Error connecting to API:</h1><pre>{html.escape(error_message)}</pre>", status_code=503)
    except json.JSONDecodeError as e:
        error_message = f"JSON Decode Error: {e.msg}\nLine: {e.lineno}, Column: {e.colno}\nPossibly malformed JSON received from upstream API."
        return HTMLResponse(f"<h1 style='color:red;'>Error parsing API response:</h1><pre>{html.escape(error_message)}</pre><hr><h3 style='color:orange'>Raw Response Text:</h3><pre>{html.escape(response.text)}</pre>", status_code=502)
    except Exception as e:
        return HTMLResponse(f"<h1 style='color:red;'>An unexpected error occurred:</h1><pre>{html.escape(str(e))}</pre>", status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
