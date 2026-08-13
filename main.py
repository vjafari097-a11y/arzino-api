import os
import httpx
import asyncio
import uvicorn
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# اجازه دسترسی به سایت شما (GitHub Pages) برای جلوگیری از خطای CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache_data = {}
_cache_time = {}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
_AJAX_URLS = (
    "https://call1.tgju.org/ajax.json",
    "https://call2.tgju.org/ajax.json",
)
_BULK_TTL = 90


def _parse_price(raw):
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return int(raw)
    text = str(raw).replace(",", "").replace("٬", "").replace(" ", "").strip()
    if not text:
        return None
    try:
        return int(float(text))
    except Exception:
        return None


async def _fetch_bulk() -> dict:
    now = datetime.now().timestamp()
    # نکته: اینجا کلیدها بدون فاصله اضافی نوشته شدن تا باگ کد اصلی رفع بشه
    if "bulk" in _cache_data and now - _cache_time.get("bulk", 0) < _BULK_TTL:
        return _cache_data["bulk"]

    current = {}
    async with httpx.AsyncClient(timeout=8.0, headers=HEADERS, follow_redirects=True) as client:
        for url in _AJAX_URLS:
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    data = r.json() or {}
                    current = data.get("current") or {}
                    if current:
                        break
            except Exception as e:
                print(f"tgju ajax error: {e}")

    if current:
        _cache_data["bulk"] = current
        _cache_time["bulk"] = now
    return current


async def get_dollar_price():
    key = "dollar"
    now = datetime.now().timestamp()
    if key in _cache_data and now - _cache_time.get(key, 0) < _BULK_TTL:
        return _cache_data[key]
    
    bulk = await _fetch_bulk()
    item = bulk.get("price_dollar_rl") or {}
    price = _parse_price(item.get("p") if isinstance(item, dict) else item)
    
    if price:
        _cache_data[key] = price
        _cache_time[key] = now
    return price


async def get_gold18_price():
    key = "gold18"
    now = datetime.now().timestamp()
    if key in _cache_data and now - _cache_time.get(key, 0) < _BULK_TTL:
        return _cache_data[key]
    
    bulk = await _fetch_bulk()
    item = bulk.get("geram18") or {}
    price = _parse_price(item.get("p") if isinstance(item, dict) else item)
    
    if price:
        _cache_data[key] = price
        _cache_time[key] = now
    return price


@app.get("/prices")
async def get_prices():
    dollar, gold = await asyncio.gather(
        get_dollar_price(),
        get_gold18_price(),
        return_exceptions=True,
    )
    
    # اگر خطایی رخ داده بود، None برگردون
    dollar = None if isinstance(dollar, Exception) else dollar
    gold = None if isinstance(gold, Exception) else gold

    return {
        "dollar": dollar,
        "dollar_toman": dollar // 10 if dollar else None,
        "gold18": gold,
        "gold18_toman": gold // 10 if gold else None,
        "last_update": datetime.now().strftime("%H:%M:%S"),
    }


@app.get("/")
async def root():
    return {"status": "ok", "message": "Arzino API is running ✅"}


# این قسمت دقیقاً با دو زیرخط در اول و آخر نوشته شده
if name == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
