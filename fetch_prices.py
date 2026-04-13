"""Fetch real prices from all product pages and update hardcoded_data.py"""
import json, re, urllib.request, ssl, time
import hardcoded_data as h

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch_price(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as res:
            html = res.read().decode('utf-8', errors='ignore')
        
        # Try discountedPrice first (best deal price)
        for pattern in [
            r'"discountedPrice"\s*:\s*(\d+)',
            r'"sellingPrice"\s*:\s*(\d+)',
            r'"finalPrice"\s*:\s*(\d+)',
            r'"offer_price"\s*:\s*"?(\d+)',
            r'"price"\s*:\s*"?(\d+)',
        ]:
            match = re.search(pattern, html)
            if match:
                return int(match.group(1))
        return None
    except:
        return None

cats = {
    'HARDCODED_WEDDING_ITEMS': list(h.HARDCODED_WEDDING_ITEMS),
    'HARDCODED_OFFICE_ITEMS': list(h.HARDCODED_OFFICE_ITEMS),
    'HARDCODED_CASUAL_ITEMS': list(h.HARDCODED_CASUAL_ITEMS),
    'HARDCODED_FESTIVE_ITEMS': list(h.HARDCODED_FESTIVE_ITEMS),
}

total = sum(len(v) for v in cats.values())
success = 0
idx = 0

for cat_name, items in cats.items():
    for item in items:
        idx += 1
        url = item.get('product_url', '')
        name = item['name'][:35]
        print(f"[{idx}/{total}] {name}...", end=" ", flush=True)
        
        price = fetch_price(url)
        if price and price > 0:
            item['price'] = price
            success += 1
            print(f"Rs.{price}")
        else:
            print(f"KEEP Rs.{item['price']}")
        
        time.sleep(0.3)

print(f"\nPrices updated: {success}/{total}")

with open('hardcoded_data.py', 'w', encoding='utf-8') as f:
    for name, items in cats.items():
        f.write(f"{name} = " + json.dumps(items, indent=4, ensure_ascii=False) + "\n\n")

print("Done!")
