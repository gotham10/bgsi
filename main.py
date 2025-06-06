from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
import httpx
import uvicorn
import json
import html
import io

app = FastAPI(title="BGSI.GG API Explorer & Image Proxy")

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BGSI.GG API Documentation</title>
    <meta name="description" content="Official API documentation for the BGSI.GG platform. Explore endpoints for items, eggs, hatches, and more.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&family=Fira+Code:wght@500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --text-primary: #c9d1d9;
            --text-secondary: #8b949e;
            --accent-color: #58a6ff;
            --http-get: #61afef;
        }
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            padding: 2rem 1rem;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 3rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
        }
        header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -1px;
            margin-bottom: 0.5rem;
        }
        header p {
            font-size: 1.1rem;
            color: var(--text-secondary);
        }
        .endpoint-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 1rem;
            overflow: hidden;
            transition: all 0.2s ease-in-out;
        }
        .endpoint-header {
            display: flex;
            align-items: center;
            padding: 1rem 1.5rem;
            cursor: pointer;
            background-color: rgba(0,0,0,0.1);
        }
        .endpoint-header:hover {
            background-color: rgba(88, 166, 255, 0.1);
        }
        .http-method {
            background-color: var(--http-get);
            color: #161b22;
            padding: 0.25rem 0.6rem;
            border-radius: 5px;
            font-weight: 700;
            font-size: 0.9rem;
            margin-right: 1rem;
            font-family: 'Fira Code', monospace;
        }
        .endpoint-path {
            font-family: 'Fira Code', monospace;
            font-size: 1.1rem;
            color: var(--text-primary);
            font-weight: 500;
        }
        .endpoint-details {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
            border-top: 1px solid var(--border-color);
        }
        .endpoint-details.active {
            max-height: 1000px;
            transition: max-height 0.5s ease-in;
        }
        .details-content {
            padding: 1.5rem;
        }
        .details-content p {
            margin-bottom: 1rem;
        }
        .details-content h4 {
            font-size: 1rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
        }
        .param-list {
            list-style: none;
            padding-left: 1rem;
        }
        .param-list li {
            margin-bottom: 0.75rem;
        }
        code {
            font-family: 'Fira Code', monospace;
            background-color: rgba(110,118,129,0.2);
            padding: 0.2em 0.4em;
            margin: 0;
            font-size: 85%;
            border-radius: 6px;
        }
        .example-block {
            background-color: #010409;
            padding: 1rem;
            border-radius: 6px;
            font-family: 'Fira Code', monospace;
            font-size: 0.9rem;
            white-space: pre-wrap;
            word-wrap: break-word;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>BGSI.GG API Documentation</h1>
            <p>Your comprehensive guide to interacting with the BGSI.GG API.</p>
        </header>

        <div class="endpoints">
            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/auth/user</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Retrieves information about the currently authenticated user.</p>
                    </div>
                </div>
            </div>

            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/stats</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Gets general statistics for the site or application.</p>
                    </div>
                </div>
            </div>

            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/items</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>A comprehensive endpoint to search, filter, and sort items.</p>
                        <h4>Query Parameters</h4>
                        <ul class="param-list">
                            <li><code>search</code>: The name of the item to search for.</li>
                            <li><code>sort</code>: The order to sort results (e.g., <code>value-desc</code>).</li>
                            <li><code>variant</code>: The specific version of the item (e.g., <code>Normal</code>, <code>Shiny</code>).</li>
                            <li><code>category</code>: The category of the item (e.g., <code>all</code>, <code>secret</code>).</li>
                            <li><code>page</code>: The page number for the results.</li>
                            <li><code>limit</code>: The number of results to return per page.</li>
                        </ul>
                        <h4>Example</h4>
                        <div class="example-block">/api/items?search=kraken&amp;sort=value-desc&amp;variant=Shiny&amp;category=secret&amp;page=1&amp;limit=20</div>
                    </div>
                </div>
            </div>

            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/items/high-demand</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Fetches a list of items that are currently in high demand.</p>
                        <h4>Query Parameters</h4>
                        <ul class="param-list">
                            <li><code>limit</code>: The maximum number of high-demand items to return.</li>
                        </ul>
                        <h4>Example</h4>
                        <div class="example-block">/api/items/high-demand?limit=10</div>
                    </div>
                </div>
            </div>

            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/items/highest-value</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Retrieves a list of the items with the highest value.</p>
                        <h4>Query Parameters</h4>
                        <ul class="param-list">
                            <li><code>limit</code>: The maximum number of highest-value items to return.</li>
                        </ul>
                        <h4>Example</h4>
                        <div class="example-block">/api/items/highest-value?limit=10</div>
                    </div>
                </div>
            </div>

            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/items/recent</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Gets a list of the most recently added items.</p>
                        <h4>Query Parameters</h4>
                        <ul class="param-list">
                            <li><code>limit</code>: The maximum number of recent items to return.</li>
                        </ul>
                        <h4>Example</h4>
                        <div class="example-block">/api/items/recent?limit=10</div>
                    </div>
                </div>
            </div>
            
            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/items/{ITEM_NAME}</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Retrieves details for a single, specific item. Replace <code>{ITEM_NAME}</code> with the exact name of the pet or item.</p>
                        <h4>Example</h4>
                        <div class="example-block">/api/items/soarin-surfer</div>
                    </div>
                </div>
            </div>

            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/eggs</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Returns a list of all available eggs.</p>
                    </div>
                </div>
            </div>

            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/eggs/{EGG_NAME}</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Retrieves information for a single, specific egg. Replace <code>{EGG_NAME}</code> with the name of the egg.</p>
                        <h4>Example</h4>
                        <div class="example-block">/api/eggs/icecream-egg</div>
                    </div>
                </div>
            </div>

            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/hatches</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Provides a list of pet hatches, with multiple filtering options.</p>
                        <h4>Query Parameters</h4>
                        <ul class="param-list">
                            <li><code>petName</code>: Filter by the name of the hatched pet.</li>
                            <li><code>hatcherName</code>: Filter by the name of the player who hatched the pet.</li>
                            <li><code>eggType</code>: Filter by the type of egg.</li>
                            <li><code>minValue</code>: Set a minimum value for the hatched pets shown.</li>
                            <li><code>publicOnly</code>: Can be <code>true</code> or <code>false</code> to show only public hatches or all hatches.</li>
                            <li><code>page</code>: The page number for the results.</li>
                            <li><code>limit</code>: The number of results to return per page.</li>
                        </ul>
                        <h4>Example</h4>
                        <div class="example-block">/api/hatches?petName=kraken&amp;hatcherName=e&amp;eggType=Egg&amp;minValue=5&amp;publicOnly=false&amp;page=1&amp;limit=20</div>
                    </div>
                </div>
            </div>

            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/trade-ads</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Fetches a list of trade advertisements.</p>
                        <h4>Query Parameters</h4>
                        <ul class="param-list">
                             <li><code>page</code>: The page number for the results.</li>
                             <li><code>limit</code>: The number of ads to return per page.</li>
                             <li><code>status</code>: The current status of the trade ad (e.g., <code>published</code>).</li>
                        </ul>
                        <h4>Example</h4>
                        <div class="example-block">/api/trade-ads?page=1&amp;limit=10&amp;status=published</div>
                    </div>
                </div>
            </div>

            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/conversations</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Retrieves a list of user conversations.</p>
                        <h4>Query Parameters</h4>
                        <ul class="param-list">
                            <li><code>page</code>: The page number for the results.</li>
                            <li><code>limit</code>: The number of conversations to return per page.</li>
                        </ul>
                        <h4>Example</h4>
                        <div class="example-block">/api/conversations?page=1&amp;limit=20</div>
                    </div>
                </div>
            </div>

            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/conversations/{ID}/messages</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Gets the messages within a specific conversation. Replace <code>{ID}</code> with the unique ID for the conversation.</p>
                        <h4>Query Parameters</h4>
                        <ul class="param-list">
                            <li><code>limit</code>: The number of messages to retrieve.</li>
                        </ul>
                        <h4>Example</h4>
                        <div class="example-block">/api/conversations/1bb50f6a-b22e-4c6b-91fd-b2990cc2374c/messages?limit=25</div>
                    </div>
                </div>
            </div>

            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/conversations/{ID}/trade-offers</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Fetches trade offers associated with a specific conversation. Replace <code>{ID}</code> with the unique ID for the conversation.</p>
                        <h4>Example</h4>
                        <div class="example-block">/api/conversations/1bb50f6a-b22e-4c6b-91fd-b2990cc2374c/trade-offers</div>
                    </div>
                </div>
            </div>
            
            <div class="endpoint-card">
                <div class="endpoint-header">
                    <span class="http-method">GET</span>
                    <span class="endpoint-path">/api/reports</span>
                </div>
                <div class="endpoint-details">
                    <div class="details-content">
                        <p>Likely used for submitting or viewing reports.</p>
                    </div>
                </div>
            </div>

        </div>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const headers = document.querySelectorAll('.endpoint-header');
            headers.forEach(header => {
                header.addEventListener('click', () => {
                    const details = header.nextElementSibling;
                    details.classList.toggle('active');
                });
            });
        });
    </script>
</body>
</html>
"""

API_BASE_URL = "https://api.bgsi.gg"
IMAGE_BASE_URL = "https://www.bgsi.gg"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico")

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Origin": API_BASE_URL,
}

def generate_api_response_html(json_data_str: str, page_title: str, og_description: str, og_image_url: str, og_url: str, favicon_url: str) -> str:
    escaped_page_title = html.escape(page_title)
    escaped_og_description = html.escape(og_description)
    escaped_og_image_url = html.escape(og_image_url)
    escaped_og_url = html.escape(og_url)
    escaped_favicon_url = html.escape(favicon_url)
    escaped_json_data_str = html.escape(json_data_str)
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escaped_page_title}</title>
  <meta name="description" content="{escaped_og_description}">
  <meta name="theme-color" content="#161616">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{escaped_og_url}">
  <meta property="og:title" content="{escaped_page_title}">
  <meta property="og:description" content="{escaped_og_description}">
  <meta property="og:image" content="{escaped_og_image_url}">
  <meta property="twitter:card" content="summary_large_image">
  <meta property="twitter:url" content="{escaped_og_url}">
  <meta property="twitter:title" content="{escaped_page_title}">
  <meta property="twitter:description" content="{escaped_og_description}">
  <meta property="twitter:image" content="{escaped_og_image_url}">
  <link rel="icon" href="{escaped_favicon_url}" type="image/png">
  <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    body {{ background-color: #161616; color: #d0d0d0; font-family: 'Roboto Mono', monospace; font-size: 14px; line-height: 1.6; padding: 2rem; margin: 0; }}
    pre {{ white-space: pre-wrap; word-wrap: break-word; font-size: 0.875rem; }}
  </style>
</head>
<body>
  <pre>{escaped_json_data_str}</pre>
</body>
</html>
"""

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
    return HTMLResponse(content=INDEX_HTML)

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
            
            json_data_obj = {}
            pretty_json_str = response.text
            content_type = response.headers.get("content-type", "")

            if "application/json" in content_type:
                try:
                    json_data_obj = response.json()
                    pretty_json_str = json.dumps(json_data_obj, indent=2, sort_keys=True)
                except json.JSONDecodeError:
                    pass

            og_page_title = f"{path.replace('/', ' ').title()} - BGSI.GG Data"
            og_description = f"Live data for {path} from the BGSI.GG API, via API Explorer."
            og_image_url = f"{str(request.base_url).rstrip('/')}/Logo.png"
            og_url = str(request.url)

            if path.startswith("items/") and isinstance(json_data_obj, dict):
                item_slug_from_path = path.split('/')[-1]
                pet_data_root = json_data_obj.get("pet")
                target_variant_data_for_og = None

                if isinstance(pet_data_root, dict):
                    if pet_data_root.get("slug") == item_slug_from_path:
                        target_variant_data_for_og = pet_data_root
                    
                    if isinstance(pet_data_root.get("allVariants"), list):
                        for variant_in_list in pet_data_root["allVariants"]:
                            if isinstance(variant_in_list, dict) and variant_in_list.get("slug") == item_slug_from_path:
                                target_variant_data_for_og = variant_in_list 
                                break
                    
                    if target_variant_data_for_og is None:
                        target_variant_data_for_og = pet_data_root

                    if target_variant_data_for_og and isinstance(target_variant_data_for_og, dict):
                        og_page_title = target_variant_data_for_og.get("name", og_page_title)
                        og_description = target_variant_data_for_og.get("description", f"Details for {og_page_title}.")
                        pet_image_path_suffix = target_variant_data_for_og.get("image")
                        if pet_image_path_suffix:
                            og_image_url = f"{IMAGE_BASE_URL}{pet_image_path_suffix}"
            
            elif path == "stats" and isinstance(json_data_obj, dict):
                og_page_title = "BGSI.GG API Statistics"
                og_description = "Live global statistics and counts from the BGSI.GG API."
            
            html_content = generate_api_response_html(
                json_data_str=pretty_json_str,
                page_title=og_page_title,
                og_description=og_description,
                og_image_url=og_image_url,
                og_url=og_url,
                favicon_url=f"{str(request.base_url).rstrip('/')}/favicon.ico"
            )
            return HTMLResponse(content=html_content)

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
        raw_text = response.text if 'response' in locals() and hasattr(response, 'text') else 'N/A'
        return create_error_html_response(
            title="API Response Parsing Error",
            message="Failed to parse JSON response from the API (or it was not JSON).",
            status_code=502,
            details=f"Error: {e_json.msg if hasattr(e_json, 'msg') else str(e_json)}\n\nRaw Response Text (may be truncated):\n{raw_text[:1000]}"
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
    is_image_path = item_path.lower().endswith(IMAGE_EXTENSIONS)
    is_favicon = item_path.lower() == "favicon.ico"

    if not (is_image_path or is_favicon):
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
            if not is_favicon and not content_type.lower().startswith("image/"):
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
                <li>This might mean the image or resource doesn't exist there, or there was a server-side issue.</li>
                <li>Verify the path is correct.</li>
            </ul>
            <p>Return to the <a href="/">API Explorer Home Page</a>.</p>
        </div>
        """
        return create_error_html_response(
            title=f"Fetch Error: {e.response.status_code}",
            message=f"Could not retrieve resource from: {html.escape(target_url)}.",
            status_code=e.response.status_code,
            details=f"Reason: {e.response.reason_phrase}\nUpstream Response: {e.response.text}",
            guidance_html=error_guidance
        )
    except httpx.RequestError as e:
        return create_error_html_response(
            title="Connection Error",
            message=f"Could not connect to server at: {html.escape(target_url)}.",
            status_code=503,
            details=str(e),
            guidance_html=f"<div class='guidance'><p>Please check your network connection and ensure <a href='{IMAGE_BASE_URL}' target='_blank'>{IMAGE_BASE_URL}</a> is accessible. Return to the <a href='/'>API Explorer Home Page</a>.</p></div>"
        )
    except Exception as e:
        return create_error_html_response(
            title="Unexpected Error",
            message="An unexpected error occurred while proxying the resource.",
            status_code=500,
            details=str(e),
            guidance_html=f"<div class='guidance'><p>An unknown error occurred. You may want to try again or check the <a href='/'>API Explorer Home Page</a>.</p></div>"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
