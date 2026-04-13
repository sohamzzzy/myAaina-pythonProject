import os
import random
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from flask import Flask, render_template, request, jsonify, Response

from recommender import (
    User, Recommender,
    save_profile, load_profile,
    log_purchase, get_purchase_history,
    get_category_stats, get_spend_timeline,
    get_platform_spend, remove_from_history,
    toggle_wishlist, load_wishlist,
    load_catalog_dataframe
)
from hardcoded_data import (
    HARDCODED_WEDDING_ITEMS, 
    HARDCODED_OFFICE_ITEMS,
    HARDCODED_CASUAL_ITEMS,
    HARDCODED_FESTIVE_ITEMS
)
app = Flask(__name__)
recommender = Recommender()


# ─── Pages ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    profile = load_profile()
    mock_stats = {
        'total_products': '1,000,000',
        'total_categories': 150,
        'total_platforms': 3,
        'price_range': [200, 20000]
    }
    return render_template('index.html', profile=profile, catalog_stats=mock_stats)


# ─── Profile ─────────────────────────────────────────────────────────────────
@app.route('/api/save-profile', methods=['POST'])
def save_profile_route():
    try:
        data = request.json
        user = User(
            name=data['name'],
            age=int(data['age']),
            gender=data['gender'],
            body_type=data['body_type'],
            skin_tone=data['skin_tone'],
            size=data['size'],
            budget_min=int(data['budget_min']),
            budget_max=int(data['budget_max']),
            interests=data.get('interests', [])
        )
        save_profile(user)
        return jsonify({'success': True, 'message': f'Profile saved for {user.name}!'})
    except (KeyError, ValueError) as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/profile', methods=['GET'])
def get_profile():
    profile = load_profile()
    if profile:
        return jsonify({'success': True, 'profile': profile.to_dict()})
    return jsonify({'success': False, 'message': 'No profile found'}), 404


# ─── Recommendations ──────────────────────────────────────────────────────────
@app.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        data    = request.json
        profile = load_profile()
        if not profile:
            return jsonify({'success': False, 'message': 'Please create your profile first!'}), 400

        occasion = data.get('occasion', '')
        sort_by  = data.get('sort_by', 'price')

        if not occasion:
            return jsonify({'success': False, 'message': 'Please select an occasion!'}), 400

        # Clean slate: Online/offline removed. Using HARDCODED AMAZON links
        results = []
        if occasion and occasion.lower() in ['wedding', 'shaadi']:
            results = HARDCODED_WEDDING_ITEMS.copy()
        elif occasion and occasion.lower() in ['office', 'formal', 'formals']:
            results = HARDCODED_OFFICE_ITEMS.copy()
        elif occasion and occasion.lower() in ['casual', 'daily']:
            results = HARDCODED_CASUAL_ITEMS.copy()
        elif occasion and occasion.lower() in ['festive', 'party']:
            results = HARDCODED_FESTIVE_ITEMS.copy()
        elif occasion and occasion.lower() in ['college']:
            results = HARDCODED_CASUAL_ITEMS.copy()
            random.shuffle(results)
        elif occasion and occasion.lower() in ['pooja', 'religious', 'religion']:
            results = HARDCODED_FESTIVE_ITEMS.copy()
            random.shuffle(results)

        # Apply gender filter based on user profile
        if results and profile:
            user_gender = getattr(profile, 'gender', '').strip()
            if user_gender in ('Male', 'Female'):
                results = [item for item in results if item.get('gender', 'Unisex') in (user_gender, 'Unisex')]

        # Apply sorting to ALL categories
        if results:
            if sort_by == 'price':
                results.sort(key=lambda x: x['price'])
            elif sort_by == 'quality':
                results.sort(key=lambda x: x['quality_rating'], reverse=True)
            elif sort_by == 'delivery':
                results.sort(key=lambda x: x['delivery_days'])

        price_chart      = build_platform_chart(results, 'price') if results else {}
        quality_chart    = build_platform_chart(results, 'quality_rating') if results else {}
        delivery_chart   = build_platform_chart(results, 'delivery_days') if results else {}

        return jsonify({
            'success': True,
            'results': results,
            'price_chart': price_chart,
            'quality_chart': quality_chart,
            'delivery_chart': delivery_chart,
            'occasion': occasion,
            'user': profile.name
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── Search ───────────────────────────────────────────────────────────────────
@app.route('/api/search', methods=['GET'])
def search():
    try:
        q       = request.args.get('q', '').strip()
        profile = load_profile()
        if not q:
            return jsonify({'success': False, 'message': 'Empty query'}), 400
            
        results = []
        ql = q.lower()

        # 1. Check for occasion-specific keywords first
        if 'wedding' in ql or 'shaadi' in ql:
            results = HARDCODED_WEDDING_ITEMS.copy()
        elif 'office' in ql or 'formal' in ql:
            results = HARDCODED_OFFICE_ITEMS.copy()
        elif 'casual' in ql or 'daily' in ql:
            results = HARDCODED_CASUAL_ITEMS.copy()
        elif 'festive' in ql or 'party' in ql:
            results = HARDCODED_FESTIVE_ITEMS.copy()
        elif 'college' in ql:
            results = HARDCODED_CASUAL_ITEMS.copy()
            random.shuffle(results)
        elif 'pooja' in ql or 'religious' in ql or 'religion' in ql:
            results = HARDCODED_FESTIVE_ITEMS.copy()
            random.shuffle(results)
        else:
            # 2. Generic search: match against name, category, platform, match_reason
            all_items = (HARDCODED_WEDDING_ITEMS + HARDCODED_OFFICE_ITEMS +
                         HARDCODED_CASUAL_ITEMS + HARDCODED_FESTIVE_ITEMS)
            keywords = ql.split()
            results = [item for item in all_items
                       if any(kw in item.get('name', '').lower() or
                              kw in item.get('category', '').lower() or
                              kw in item.get('platform', '').lower() or
                              kw in item.get('match_reason', '').lower()
                              for kw in keywords)]

        # Apply gender filter based on user profile
        if results and profile:
            user_gender = getattr(profile, 'gender', '') if hasattr(profile, 'gender') else profile.get('gender', '') if isinstance(profile, dict) else ''
            user_gender = user_gender.strip() if user_gender else ''
            if user_gender in ('Male', 'Female'):
                results = [item for item in results if item.get('gender', 'Unisex') in (user_gender, 'Unisex')]
            
        return jsonify({'success': True, 'results': results, 'query': q})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── Trending & Deals ────────────────────────────────────────────────────────
@app.route('/api/trending', methods=['GET'])
def trending():
    try:
        # Pull a shuffled mix of items from all categories
        all_items = (HARDCODED_WEDDING_ITEMS + HARDCODED_OFFICE_ITEMS +
                     HARDCODED_CASUAL_ITEMS + HARDCODED_FESTIVE_ITEMS)
        pool = all_items.copy()
        random.shuffle(pool)
        show_all = request.args.get('all', 'false').lower() == 'true'
        results = pool if show_all else pool[:12]
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/deals', methods=['GET'])
def deals():
    try:
        budget  = int(request.args.get('budget', 1000))
        all_items = (HARDCODED_WEDDING_ITEMS + HARDCODED_OFFICE_ITEMS +
                     HARDCODED_CASUAL_ITEMS + HARDCODED_FESTIVE_ITEMS)
        results = [item for item in all_items if item['price'] <= budget]
        results.sort(key=lambda x: x['price'])
        return jsonify({'success': True, 'results': results, 'budget': budget})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── Catalog Meta ─────────────────────────────────────────────────────────────
@app.route('/api/catalog/stats', methods=['GET'])
def catalog_stats():
    return jsonify({'success': True, 'stats': {}})


@app.route('/api/catalog/occasions', methods=['GET'])
def catalog_occasions():
    return jsonify({'success': True, 'occasions': ["Wedding", "Festive", "Casual", "Office", "College", "Pooja"]})


@app.route('/api/catalog/categories', methods=['GET'])
def catalog_categories():
    return jsonify({'success': True, 'categories': ["Sarees", "Kurtis", "Lehengas", "Shirts", "Trousers"]})


# ─── Wishlist ─────────────────────────────────────────────────────────────────
@app.route('/api/wishlist/toggle', methods=['POST'])
def wishlist_toggle():
    try:
        data    = request.json
        item_id = data.get('item_id')
        added   = toggle_wishlist(item_id)
        msg     = 'Added to Wishlist ❤️' if added else 'Removed from Wishlist'
        return jsonify({'success': True, 'added': added, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/wishlist', methods=['GET'])
def get_wishlist():
    try:
        ids     = load_wishlist()
        if not ids:
            return jsonify({'success': True, 'items': []})
        # Look up items from hardcoded data instead of dead CSV files
        all_items = (HARDCODED_WEDDING_ITEMS + HARDCODED_OFFICE_ITEMS +
                     HARDCODED_CASUAL_ITEMS + HARDCODED_FESTIVE_ITEMS)
        id_set = set(str(i) for i in ids)
        items = [item.copy() for item in all_items if str(item['id']) in id_set]
        for item in items:
            item['in_wishlist'] = True
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── Purchase History ─────────────────────────────────────────────────────────
@app.route('/api/log-purchase', methods=['POST'])
def log_purchase_route():
    try:
        data    = request.json
        item_id = data.get('item_id')
        item_payload = data.get('item')
        success = log_purchase(item_id, item_payload)
        if success:
            return jsonify({'success': True, 'message': 'Purchase logged!'})
        return jsonify({'success': False, 'message': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def history():
    try:
        import math
        items         = get_purchase_history()
        stats         = get_category_stats()
        spend_timeline = get_spend_timeline()
        platform_spend = get_platform_spend()

        # Sanitize NaN values from pandas CSV reads
        for item in items:
            for key, val in item.items():
                if isinstance(val, float) and math.isnan(val):
                    item[key] = '' if key in ('category', 'gender', 'match_reason', 'in_wishlist') else 0

        total_spend   = sum(float(i.get('price', 0)) for i in items)
        return jsonify({
            'success': True,
            'items': items,
            'stats': stats,
            'spend_timeline': spend_timeline,
            'platform_spend': platform_spend,
            'total_spend': round(total_spend, 2),
            'total_items': len(items)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/history/remove', methods=['POST'])
def history_remove():
    try:
        data    = request.json
        item_id = data.get('item_id')
        success = remove_from_history(item_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/image-proxy', methods=['GET'])
def image_proxy():
    try:
        image_url = request.args.get('url', '').strip()
        if not image_url.startswith(('http://', 'https://')):
            return jsonify({'success': False, 'message': 'Invalid image URL'}), 400

        parsed = urlparse(image_url)
        referer_map = {
            'myntra.com': 'https://www.myntra.com/',
            'manyavar.com': 'https://www.manyavar.com/',
            'bewakoof.com': 'https://www.bewakoof.com/',
        }

        referer = None
        for domain, value in referer_map.items():
            if domain in parsed.netloc:
                referer = value
                break

        headers = {'User-Agent': 'Mozilla/5.0'}
        if referer:
            headers['Referer'] = referer

        req = Request(image_url, headers=headers)
        with urlopen(req, timeout=25) as response:
            content = response.read()
            mimetype = response.headers.get_content_type()

        return Response(
            content,
            mimetype=mimetype,
            headers={'Cache-Control': 'public, max-age=21600'}
        )
    except Exception:
        # Return a 1x1 transparent PNG so the browser shows a blank pixel
        # instead of "HTTP Error 471" or a broken image
        import base64
        pixel = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIABQAB'
            'Nl7BcQAAAABJRU5ErkJggg=='
        )
        return Response(pixel, mimetype='image/png', headers={'Cache-Control': 'public, max-age=60'})





def build_platform_chart(results, field):
    grouped = {}
    for item in results:
        platform = item.get('platform')
        value = item.get(field)
        if platform is None or value is None:
            continue
        grouped.setdefault(platform, []).append(float(value))

    chart = {}
    for platform, values in grouped.items():
        if values:
            chart[platform] = round(sum(values) / len(values), 2)
    return chart

if __name__ == '__main__':
    app.run(debug=True)
