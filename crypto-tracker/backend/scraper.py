from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path
import argparse
import re
import pandas as pd
import time

COINMARKETCAP_URL = "https://coinmarketcap.com/"
DEFAULT_OUTPUT_FILE = "crypto_data.csv"
ASSET_COLORS = [
    "#c9f269", "#77d6c5", "#f5b97d", "#a8b8ff", "#f28f9d",
    "#c8a5f5", "#f4df69", "#8ed1f0", "#d4b483", "#9ee493",
]
ASSET_COLOR_BY_SYMBOL = {
    "BTC": "#c9f269", "ETH": "#77d6c5", "USDT": "#f5b97d", "BNB": "#a8b8ff",
    "XRP": "#f28f9d", "USDC": "#c8a5f5", "SOL": "#f4df69", "TRX": "#8ed1f0",
    "HYPE": "#d4b483", "ZEC": "#9ee493",
}


def get_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def scrape_top_coins(limit=10, headless=True):
    driver = get_driver(headless=headless)
    coins = []
    try:
        driver.get(COINMARKETCAP_URL)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )
        time.sleep(2)

        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 8:
                    continue

                name_cell = cells[2]
                name_parts = name_cell.find_elements(By.CSS_SELECTOR, "p")
                name = name_parts[0].text.strip()
                symbol = name_parts[1].text.strip() if len(name_parts) > 1 else ""

                if symbol == "CMC20":
                    continue

                price = cells[3].text.strip()
                change_24h = cells[4].text.strip()
                market_cap = cells[7].text.strip()

                coins.append({
                    "name": name,
                    "symbol": symbol,
                    "price": price,
                    "change_24h": change_24h,
                    "market_cap": market_cap,
                })
                if len(coins) >= limit:
                    break
            except Exception as row_error:
                print(f"Skipped a row: {row_error}")
                continue
    finally:
        driver.quit()

    return coins


def _number_from_text(value):
    """Convert currency/percentage text into a comparable number."""
    cleaned = re.sub(r"[^0-9.-]", "", value.replace(",", ""))
    try:
        return float(cleaned)
    except ValueError:
        return None


def _market_cap_number(value):
    """Convert abbreviated market-cap text such as '$1.6T' to USD."""
    text = str(value).strip().replace(",", "").replace("$", "")
    multiplier = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
    suffix = text[-1].upper() if text and text[-1].upper() in multiplier else ""
    number = text[:-1] if suffix else text
    try:
        return float(number) * multiplier.get(suffix, 1)
    except ValueError:
        return None


def _normalize_coin(coin, timestamp):
    """Return CSV-friendly numeric fields while retaining the scrape identity."""
    symbol = coin["symbol"]
    color = ASSET_COLOR_BY_SYMBOL.get(
        symbol,
        ASSET_COLORS[sum(ord(character) for character in symbol) % len(ASSET_COLORS)],
    )
    return {
        "name": coin["name"],
        "symbol": coin["symbol"],
        "price_usd": _number_from_text(coin["price"]),
        "change_24h_percent": _number_from_text(coin["change_24h"]),
        "market_cap_usd": _market_cap_number(coin["market_cap"]),
        "color_hex": color,
        "timestamp": timestamp,
    }


def filter_coins(coins, minimum_price=None, minimum_change=None):
    """Filter coins by minimum price and/or 24-hour percentage change."""
    filtered = coins
    if minimum_price is not None:
        filtered = [
            coin for coin in filtered
            if (_number_from_text(coin["price"]) or 0) >= minimum_price
        ]
    if minimum_change is not None:
        filtered = [
            coin for coin in filtered
            if (_number_from_text(coin["change_24h"]) or 0) >= minimum_change
        ]
    return filtered


def save_to_csv(coins, filename=DEFAULT_OUTPUT_FILE):
    """Append a normalized numeric snapshot to the historical CSV."""
    if not coins:
        print("No coins matched the selected filters.")
        return

    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame([_normalize_coin(coin, timestamp) for coin in coins])

    try:
        existing = pd.read_csv(output_path)
        if "price_usd" not in existing.columns or "color_hex" not in existing.columns:
            existing = pd.DataFrame([
                _normalize_coin(row, row["timestamp"])
                for row in existing.to_dict("records")
                if row.get("symbol") != "CMC20"
            ])
        existing = existing.dropna(subset=["name", "symbol", "timestamp"])
        df = pd.concat([existing, df], ignore_index=True)
    except FileNotFoundError:
        pass

    df.to_csv(output_path, index=False)
    print(f"Saved {len(coins)} coins to {output_path}")


def migrate_csv(filename=DEFAULT_OUTPUT_FILE):
    """Convert an older display-text CSV to the normalized numeric schema."""
    output_path = Path(filename)
    if not output_path.exists():
        raise SystemExit(f"CSV file not found: {output_path}")

    existing = pd.read_csv(output_path)
    if "price_usd" in existing.columns:
        existing = existing[existing["symbol"] != "CMC20"].copy()
        existing["color_hex"] = existing["symbol"].map(
            lambda symbol: ASSET_COLOR_BY_SYMBOL.get(
                symbol,
                ASSET_COLORS[
                    sum(ord(character) for character in symbol) % len(ASSET_COLORS)
                ],
            )
        )
        existing.to_csv(output_path, index=False)
    else:
        rows = [
            _normalize_coin(row, row["timestamp"])
            for row in existing.to_dict("records")
            if row.get("symbol") != "CMC20"
        ]
        pd.DataFrame(rows).to_csv(output_path, index=False)
    print(f"Migrated {len(existing)} rows in {output_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape top cryptocurrency prices.")
    parser.add_argument("--limit", type=int, default=10, help="Number of coins to scrape.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_FILE, help="CSV output path.")
    parser.add_argument("--minimum-price", type=float, help="Keep coins at or above this price.")
    parser.add_argument(
        "--minimum-change",
        type=float,
        help="Keep coins at or above this 24-hour percentage change.",
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Show Chrome while scraping instead of using headless mode.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Repeat scraping at the selected interval.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Seconds between captures when --watch is enabled.",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Convert an older CSV to the normalized numeric schema without scraping.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    if args.interval < 1:
        raise SystemExit("--interval must be at least 1 second")
    if args.migrate:
        migrate_csv(filename=args.output)
        raise SystemExit(0)

    while True:
        data = scrape_top_coins(limit=args.limit, headless=not args.show_browser)
        data = filter_coins(
            data,
            minimum_price=args.minimum_price,
            minimum_change=args.minimum_change,
        )
        for coin in data:
            print(coin)
        save_to_csv(data, filename=args.output)

        if not args.watch:
            break
        print(f"Next capture in {args.interval} seconds. Press Ctrl+C to stop.")
        time.sleep(args.interval)