import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

urls = {
    "Myntra": "https://www.myntra.com/kurtas/okara/okara-floral-printed-cotton-kurta/40954809/buy",
    "Manyavar": "https://www.manyavar.com/en-in/saree/wine-chinon-saree/UC156778.html",
    "Bewakoof": "https://www.bewakoof.com/p/mens-black-oversized-t-shirt",
}

for name, url in urls.items():
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as res:
            html = res.read().decode('utf-8', errors='ignore')
        
        # Try all common price meta tags
        price_patterns = [
            (r'product:price:amount.*?content=["\']([^"\']+)', 'product:price:amount'),
            (r'og:price:amount.*?content=["\']([^"\']+)', 'og:price:amount'),
            (r'content=["\']([^"\']+).*?product:price:amount', 'product:price:amount rev'),
            (r'content=["\']([^"\']+).*?og:price:amount', 'og:price:amount rev'),
            (r'"price"\s*:\s*"?(\d+[\d,.]*)', 'JSON price'),
            (r'"sellingPrice"\s*:\s*(\d+)', 'sellingPrice'),
            (r'"discountedPrice"\s*:\s*(\d+)', 'discountedPrice'),
            (r'"finalPrice"\s*:\s*(\d+)', 'finalPrice'),
            (r'"offer_price"\s*:\s*"?(\d+)', 'offer_price'),
        ]
        
        found = False
        for pattern, label in price_patterns:
            match = re.search(pattern, html)
            if match:
                print(f"[{name}] {label}: Rs.{match.group(1)}")
                found = True
        
        if not found:
            print(f"[{name}] No price found in meta tags or JSON")
            
    except Exception as e:
        print(f"[{name}] ERROR: {e}")
    print()
