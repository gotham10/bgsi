from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
import httpx
import uvicorn
from string import Template
import json
import html
import io

app = FastAPI(title="BGSI.GG API Explorer & Image Proxy")

HTML_TEMPLATE = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>API Data Response</title>
  <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    body {
      background-color: #080808;
      color: #cccccc;
      font-family: 'Roboto Mono', monospace;
      font-size: 14px;
      line-height: 1.6;
      padding: 2rem;
      margin: 0;
    }
    pre {
      background-color: #161616;
      color: #d0d0d0;
      padding: 2rem;
      border-radius: 10px;
      border: 1px solid #2a2a2a;
      box-shadow: 0 6px 20px rgba(0,0,0,0.6);
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
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BGSI.GG API Explorer</title>
  <meta name="description" content="Explore live JSON responses and images from the BGSI.GG API. A simple and effective tool for API interaction.">
  <meta name="theme-color" content="#080808">

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://bgsi-kyc3.onrender.com/">
  <meta property="og:title" content="BGSI.GG API Explorer">
  <meta property="og:description" content="Explore live JSON responses and images from the BGSI.GG API. A simple and effective tool for API interaction.">
  <meta property="og:image" content="https://bgsi-kyc3.onrender.com/Logo.png">

  <!-- Twitter -->
  <meta property="twitter:card" content="summary_large_image">
  <meta property="twitter:url" content="https://bgsi-kyc3.onrender.com/">
  <meta property="twitter:title" content="BGSI.GG API Explorer">
  <meta property="twitter:description" content="Explore live JSON responses and images from the BGSI.GG API. A simple and effective tool for API interaction.">
  <meta property="twitter:image" content="https://bgsi-kyc3.onrender.com/Logo.png">

  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    @keyframes fadeInDown {
      0% { opacity: 0; transform: translateY(-20px); }
      100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInUp {
      0% { opacity: 0; transform: translateY(20px); }
      100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes backgroundPan {
        0% { background-position: 0% center; }
        100% { background-position: 200% center; }
    }
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
    h1 {
      font-family: 'Orbitron', sans-serif;
      color: #cccccc;
      font-size: 3rem;
      margin-bottom: 1.5rem;
      letter-spacing: 1px;
      animation: fadeInDown 0.8s ease-out 0.2s forwards;
      opacity: 0;
      text-shadow: 0 0 8px rgba(200, 200, 200, 0.15);
    }
    p {
      font-size: 1.1rem;
      line-height: 1.7;
      margin-bottom: 1.5rem;
      animation: fadeInUp 1s ease-out 0.4s forwards;
      opacity: 0;
    }
    .api-info {
      margin-bottom: 2.5rem;
      font-size: 1rem;
      color: #bbbbbb;
      animation: fadeInUp 1s ease-out 0.6s forwards;
      opacity: 0;
    }
    a {
      color: #888888;
      text-decoration: none;
      transition: color 0.3s ease, text-shadow 0.3s ease;
      font-weight: 500;
    }
    a:hover {
      color: #aaaaaa;
      text-shadow: 0 0 8px rgba(170, 170, 170, 0.3);
    }
    .instructions {
      background: rgba(10, 10, 10, 0.8);
      padding: 1.5rem 2rem;
      border-radius: 10px;
      margin-top: 2rem;
      border-left: 4px solid #444444;
      text-align: left;
      animation: fadeInUp 1s ease-out 0.8s forwards;
      opacity: 0;
    }
    .instructions p, .instructions ul li {
        color: #bbbbbb;
        font-size: 1rem;
        margin-bottom: 0.8rem;
        line-height: 1.6;
    }
    .instructions ul {
        padding-left: 20px;
        margin-top: 0.5rem;
    }
    .example-path {
        font-family: 'Roboto Mono', monospace;
        background-color: #101010;
        color: #999999;
        padding: 0.3em 0.6em;
        border-radius: 5px;
        font-weight: 500;
        border: 1px solid #303030;
    }
    .footer-link {
        margin-top: 3rem;
        font-size: 0.9rem;
        color: #777777;
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
    <p>Explore live JSON responses from the <a href="https://api.bgsi.gg" target="_blank" rel="noopener noreferrer">BGSI.GG API</a> or view proxied images.</p>
    <div class="api-info">
      <p>This interface allows you to directly proxy API requests and view data, or proxy images from the target domain.
      To fetch API data, modify the URL by appending the API path you wish to query after <code class="example-path">/api/</code>.
      To view an image, use its path directly (e.g., <code class="example-path">/items/image.png</code>).</p>
    </div>
    <div class="instructions">
        <p><strong>How to use:</strong></p>
        <p>1. <strong>API Data:</strong> To access data from <code class="example-path">/api/some/endpoint</code> on the target API, navigate to:</p>
        <p><a href="/api/some/endpoint">http://127.0.0.1:3000/api/some/endpoint</a></p>
        <p>2. <strong>Images:</strong> To view an image like <code class="example-path">/items/fire-basilisk.png</code> from the target domain, navigate to:</p>
        <p><a href="/items/fire-basilisk.png">http://127.0.0.1:3000/items/fire-basilisk.png</a></p>
        <p>   Or for an image at root like <code class="example-path">/Logo.png</code>:</p>
        <p><a href="/Logo.png">http://127.0.0.1:3000/Logo.png</a></p>
        <p>3. Query parameters work for API paths: <code class="example-path">/api/v1/data?type=example</code></p>
    </div>
    <p class="footer-link">View data and images from <a href="https://www.bgsi.gg" target="_blank" rel="noopener noreferrer">www.bgsi.gg</a>.</p>
  </div>
</body>
</html>
""")

API_BASE_URL = "https://api.bgsi.gg"
IMAGE_BASE_URL = "https://www.bgsi.gg"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico")

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Origin": API_BASE_URL,
}

def create_error_html_response(title: str, message: str, status_code: int, details: str = "", guidance_html: str = ""):
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

@app.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_HTML.substitute()

@app.get("/api/{path:path}", response_class=HTMLResponse)
async def proxy_api(path: str, request: Request):
    query = str(request.query_params)
    target_url = f"{API_BASE_URL}/api/{path}"
    if query:
        target_url += f"?{query}"

    api_headers = {
        **COMMON_HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Referer": f"{API_BASE_URL}/",
    }

    try:
        async with httpx.AsyncClient(headers=api_headers, follow_redirects=True) as client:
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
        return create_error_html_response(
            title=f"API Error: {e.response.status_code}",
            message=f"Error fetching API data from: {html.escape(target_url)}.",
            status_code=e.response.status_code,
            details=f"Reason: {e.response.reason_phrase}\nResponse: {e.response.text}"
        )
    except httpx.RequestError as e:
        return create_error_html_response(
            title="API Connection Error",
            message=f"Could not connect to API endpoint: {html.escape(target_url)}.",
            status_code=503,
            details=str(e)
        )
    except json.JSONDecodeError as e_json:
        raw_text = getattr(e_json, 'doc', 'N/A (could not get raw text from response)')
        if 'response' in locals() and hasattr(response, 'text'): 
             raw_text = response.text
        return create_error_html_response(
            title="API Response Parsing Error",
            message="Failed to parse JSON response from the API.",
            status_code=502,
            details=f"Error: {e_json.msg}\nLine: {e_json.lineno}, Column: {e_json.colno}\n\nRaw Response Text (may be truncated):\n{raw_text[:1000]}"
        )
    except Exception as e:
        return create_error_html_response(
            title="Unexpected API Error",
            message="An unexpected error occurred while proxying the API request.",
            status_code=500,
            details=str(e)
        )

@app.get("/{item_path:path}")
async def proxy_image_or_not_found(item_path: str, request: Request):
    if not item_path.lower().endswith(IMAGE_EXTENSIONS) and item_path != "favicon.ico":
        not_found_guidance = f"""
        <div class="guidance">
            <p>If you were trying to access an image or a specific resource:</p>
            <ul>
                <li>Please verify the URL path for any typos. The path requested was: <code class="example-path">{html.escape(item_path)}</code></li>
                <li>Ensure the path corresponds to an existing resource on <a href="{IMAGE_BASE_URL}" target="_blank">{IMAGE_BASE_URL}</a>.</li>
                <li>Image paths usually end with an extension like <code class="example-path">.png</code>, <code class="example-path">.jpg</code>, etc.</li>
                <li>Example of a correct image path: <a href="/items/fire-basilisk.png">/items/fire-basilisk.png</a></li>
            </ul>
            <p>If you were trying to access API data (JSON):</p>
            <ul>
                <li>API paths must start with <code class="example-path">/api/</code>.</li>
                <li>Example of an API path: <a href="/api/example/data">/api/example/data</a></li>
            </ul>
            <p>You can return to the <a href="/">API Explorer Home Page</a> to start over.</p>
        </div>
        """
        return create_error_html_response(
            title="Resource Not Found",
            message=f"The resource at path '/{html.escape(item_path)}' was not found or is not a recognized image type.",
            status_code=404,
            guidance_html=not_found_guidance
        )

    target_url = f"{IMAGE_BASE_URL}/{item_path}"
    
    image_headers = {
        **COMMON_HEADERS,
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": f"{IMAGE_BASE_URL}/",
    }

    try:
        async with httpx.AsyncClient(headers=image_headers, follow_redirects=True) as client:
            response = await client.get(target_url)
            response.raise_for_status()
            
            content_type = response.headers.get("content-type", "application/octet-stream")
            if not content_type.lower().startswith("image/"):
                 return create_error_html_response(
                    title="Invalid Content Type",
                    message=f"The resource at {html.escape(target_url)} was found but does not appear to be an image.",
                    status_code=415,
                    details=f"Expected content type starting with 'image/', but received '{html.escape(content_type)}'."
                )
            return StreamingResponse(io.BytesIO(response.content), media_type=content_type)

    except httpx.HTTPStatusError as e:
        error_guidance = f"""
        <div class="guidance">
            <p>The server at <a href="{IMAGE_BASE_URL}" target="_blank">{IMAGE_BASE_URL}</a> responded with an error when trying to fetch <code class="example-path">{html.escape(item_path)}</code>.</p>
            <ul>
                <li>This might mean the image doesn't exist there, or there was a server-side issue.</li>
                <li>Verify the image path is correct.</li>
            </ul>
            <p>Return to the <a href="/">API Explorer Home Page</a>.</p>
        </div>
        """
        return create_error_html_response(
            title=f"Image Fetch Error: {e.response.status_code}",
            message=f"Could not retrieve image from: {html.escape(target_url)}.",
            status_code=e.response.status_code,
            details=f"Reason: {e.response.reason_phrase}\nUpstream Response: {e.response.text}",
            guidance_html=error_guidance
        )
    except httpx.RequestError as e:
        return create_error_html_response(
            title="Image Connection Error",
            message=f"Could not connect to image server at: {html.escape(target_url)}.",
            status_code=503,
            details=str(e),
            guidance_html=f"<div class='guidance'><p>Please check your network connection and ensure <a href='{IMAGE_BASE_URL}' target='_blank'>{IMAGE_BASE_URL}</a> is accessible. Return to the <a href='/'>API Explorer Home Page</a>.</p></div>"
        )
    except Exception as e:
        return create_error_html_response(
            title="Unexpected Image Error",
            message="An unexpected error occurred while proxying the image.",
            status_code=500,
            details=str(e),
            guidance_html=f"<div class='guidance'><p>An unknown error occurred. You may want to try again or check the <a href='/'>API Explorer Home Page</a>.</p></div>"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
