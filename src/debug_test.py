import time
import re
import random
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def debug_scrape(lat, lon, keyword="cafe"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = f"https://www.google.com/maps/search/{keyword}/@{lat},{lon},15z?gl=tr"

        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Sayfa yüklenemedi: {e}")
            browser.close()
            return

        try:
            page.locator('div[role="feed"]').hover()
        except:
            pass

        try:
            page.wait_for_selector('div[role="article"]', timeout=15000)
        except Exception as e:
            print(f"Kartlar yüklenmedi: {e}")
            browser.close()
            return

        for _ in range(5):
            page.mouse.wheel(0, 1000)
            time.sleep(random.uniform(1.5, 3.5))

        html_stuff = page.content()
        browser.close()

    soup = BeautifulSoup(html_stuff, "html.parser")
    venue_cards = soup.find_all("div", role="article")

    with open("debug_output.txt", "w", encoding="utf-8") as f:
        f.write(f"Kart sayisi: {len(venue_cards)}\n\n")
        for i, card in enumerate(venue_cards[:3]):
            f.write(f"--- KART {i} ---\n")
            f.write(card.prettify())
            f.write("\n\n")

    print(f"Bitti. {len(venue_cards)} kart bulundu. debug_output.txt dosyasına yazıldı.")

if __name__ == "__main__":
    # kendi test bölgenin lat/lon'unu buraya yaz
    debug_scrape(lat=41.0846126, lon=28.0701698, keyword="cafe")