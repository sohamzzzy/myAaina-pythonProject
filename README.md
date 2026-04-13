# 🪡 Vastra — Desi Smart Clothing Recommender

A Python + Flask + HTML/CSS/JS web app that recommends Indian clothing
based on your body type, size, budget, and occasion.

## 📁 Project Structure
```
desi_clothing_recommender/
├── app.py                  # Flask backend
├── recommender.py          # OOP + Pandas logic
├── requirements.txt
├── data/
│   ├── products.csv        # 40 Indian clothing items
│   └── user_profile.json   # Your saved profile
├── templates/
│   └── index.html          # Main UI
└── static/
    ├── css/style.css
    └── js/main.js
```

## 🚀 How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

## ✨ Features
- Save your style profile (body type, size, skin tone, budget)
- Select occasion (Wedding, Festive, Casual, Office, College, Pooja)
- Get outfit recommendations filtered by your profile
- Sort by: Lowest Price / Highest Quality / Fastest Delivery
- Price & Quality comparison charts (Myntra vs Meesho vs Amazon)
- Log purchases and track wardrobe history
- Category breakdown doughnut chart

## 📚 Python Concepts & Libraries Used

Throughout the development of this project, numerous core and advanced Python concepts were utilized to build a robust backend architecture:

### 1. Object-Oriented Programming (OOP)
- **Classes & Objects**: Created dedicated models (`User`, `ClothingItem`) to structure data.
- **Encapsulation**: Using class methods (`to_dict()`) to serialize objects for JSON responses.
- **Static Methods**: Leveraging `@staticmethod` (e.g., `from_dict()`) for clean object instantiation from raw data.

### 2. Web Frameworks & API Architecture (Flask)
- **Routing & Endpoints**: Using decoraters (`@app.route`) to define RESTful API endpoints.
- **Request Handling**: Parsing query parameters (`request.args.get()`) and JSON payloads (`request.json`).
- **Response Formatting**: Using Flask's `jsonify` to serialize Python dictionaries into HTTP-ready JSON.

### 3. Data Science & Analytics (Pandas)
- **DataFrames**: Loading and persisting historical data via `pd.read_csv()` and `df.to_csv()`.
- **Data Manipulation**: Filtering rows (`df = df[df['id'] != item_id]`) and mutating data types.
- **Aggregations**: Using `value_counts()` properties to generate time-series and categorical data for the charts.
- **Data Sanitization**: Handling missing `NaN` values derived from empty CSV cells via the `math.isnan` standard library function.

### 4. File I/O & Serialization
- **JSON Handling**: `json.load()` and `json.dump()` for volatile state management (User profiles and Wishlists).
- **Persistent Storage**: Validating file existence using `os.path.exists()` before performing read/write operations.

### 5. Advanced Web Scraping & Networking
- **HTTP Requests**: Using `urllib.request.urlopen` with custom `User-Agent` headers to fetch raw HTML from third-party sites.
- **SSL Contexts**: Generating unverified SSL contexts (`ssl.CERT_NONE`, `ssl.create_default_context()`) to bypass restrictive server certificates during scraping.
- **Regular Expressions (`re`)**: Utilizing complex Regex patterns to parse `<meta og:image>` tags and raw JSON strings (`"price": 999`) across various e-commerce DOM structures.

### 6. Control Flow & Functional Programming
- **List Comprehensions**: Elegant data filtering algorithms (`[item for item in items if kw in item['name'].lower()]`).
- **Generator Expressions**: Memory-efficient calculations (e.g., `sum(float(i.get('price', 0)) for i in items)`).
- **Exception Handling**: Robust use of `try...except` blocks globally to trap `FileNotFoundError`, `JSONDecodeError`, and general `Exception`s, guaranteeing the API never crashes fatally.
- **Randomization**: Applying `random.shuffle()` to arrays to generate dynamic algorithms for "Trending" tabs.
