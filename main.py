from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

app = FastAPI()

# Global cache variables
last_fetched = None
cached_data = None

def convert_volume(value: str) -> int:
    value = value.upper().replace(",", "").strip()
    try:
        if value.endswith("K"):
            return int(float(value[:-1]) * 1_000)
        elif value.endswith("M"):
            return int(float(value[:-1]) * 1_000_000)
        elif value.endswith("B"):
            return int(float(value[:-1]) * 1_000_000_000)
        return int(float(value))
    except:
        return 0

@app.get("/")
def root():
    return {"message": "Stock API is running"}

@app.get("/volume-gainers")
def get_volume_gainers():
    global last_fetched, cached_data
    now = datetime.now()

    # ✅ If cache exists and is fresh (<10 min), return it
    if cached_data and last_fetched and now - last_fetched < timedelta(minutes=10):
        return {"status": "success", "data": cached_data, "source": "cache"}

    try:
        url = "https://trendlyne.com/stock-screeners/volume-based/high-volume-stocks/top-gainers/today/index/NIFTY500/nifty-500/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/114.0.0.0 Safari/537.36"
        }

        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.select("table tbody tr")

        data = []

        for r in rows:
            cols = [c.text.strip() for c in r.find_all("td")]
            if len(cols) < 6:
                continue

            try:
                percent_change = float(cols[2].split("(")[0].replace("%", "").strip())
            except:
                percent_change = 0.0

            try:
                volume = convert_volume(cols[3])
                avg_volume = convert_volume(cols[4])
                volume_ratio = float(cols[5].replace("X", "").strip())
            except:
                volume = avg_volume = volume_ratio = 0

            data.append({
                "symbol": cols[0],
                "ltp": float(cols[1].replace(",", "")),
                "percentChange": percent_change,
                "volume": volume,
                "avgVolume": avg_volume,
                "volumeRatio": volume_ratio
            })

        # ✅ Update cache
        cached_data = data
        last_fetched = now

        return {"status": "success", "data": data, "source": "fresh"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
