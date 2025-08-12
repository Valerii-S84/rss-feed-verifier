# 📰 RSS/Atom Feed Verifier

**RSS/Atom Feed Verifier** is a simple Python script that checks a list of websites from an Excel file and identifies which ones have working RSS or Atom feeds.  
Perfect for preparing "whitelists" of feeds for projects like automated news aggregators (e.g., [n8n](https://n8n.io/)).

---

## ✨ Features
- Checks websites from an Excel file for valid RSS/Atom feeds.
- Finds `<link rel="alternate" type="application/rss+xml">` in HTML.
- Automatically tries common feed paths (`/feed`, `/rss`, `/rss.xml`, `/atom.xml`).
- Generates three output files:
  - **feeds.js** — ready-to-use `const feeds = [...]` array for your code.
  - **feeds.json** — list of feeds in JSON format.
  - **feed_audit.csv** — table with a verification status for each site.

---

## 📦 Requirements
- Python 3.8+
- Modules:
  ```bash
  pip install requests beautifulsoup4 openpyxl pandas
  ```

---

## 📂 Excel File Format
Your Excel file must have a column named **`Internet Address`** or in Ukrainian **`Інтернет-адреса`**.

Example:

| №  | Internet Address                 |
|----|-----------------------------------|
| 1  | https://www.pravda.com.ua/        |
| 2  | https://www.ukrinform.ua/         |
| 3  | https://www.bbc.com/news/health   |

---

## 🚀 Usage
1. Clone or download this repository:
   ```bash
   git clone https://github.com/your-username/rss-feed-verifier.git
   cd rss-feed-verifier
   ```

2. Make sure you have the dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```
   *(or use the installation command from the "Requirements" section above)*

3. Run the verifier:
   ```bash
   python verify_feeds.py "example.xlsx"
   ```
   or with a full file path:
   ```bash
   python verify_feeds.py "C:\Users\User\Desktop\sites.xlsx"
   ```

4. After execution, you will get:
   - `feeds.js` — ready array for your code.
   - `feeds.json` — list of feeds in JSON.
   - `feed_audit.csv` — verification report.

---

## 🛠 Example in Code
```javascript
const feeds = [
  "https://www.pravda.com.ua/rss/",
  "https://www.ukrinform.ua/rss.xml",
  "https://www.bbc.com/news/health/rss.xml"
];
// Your code for processing feeds
```

---

## 📜 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🤝 Author
Created by **Valerii S.** in 2025.
