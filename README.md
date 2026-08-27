# 📚 PDF to HTML+CSS Converter Studio (Universal WebApp)

> Convert **ANY PDF** (Textbooks, Books, Notes, Research Papers, Slides, Reports) into **100% Matching HTML & CSS** with Live Dual-View Studio, Standalone 1-File HTML Book Exporter, and Continuous Scroll Reading!

---

## ✨ Features

- 🎯 **Exact 1:1 Visual Replica**: Matches font sizes, weights, colors, vector graphics, and absolute coordinates.
- 📖 **Single-File HTML Book Exporter**: Download 1 single `.html` file with all pages combined vertically for smooth, continuous reading in any browser offline.
- 🖼️ **Clean sRGB Image Extraction**: Automatically filters out 1-bit prepress printing masks and converts CMYK plates to clean web PNGs.
- ⚡ **Precision Margin Protection (`scaleX`)**: Prevents character expansion from colliding with side borders and decorative stripes.
- 🌓 **Reading Modes**: Built-in Dark Mode, Light Mode, and Warm Sepia Mode.
- 🔍 **Full-Text Global Search**: Instant keyword search with contextual highlights across all pages.
- 📦 **1-Click Full Package ZIP**: Download standalone single-page HTML files, CSS stylesheets, and image assets.

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/<YOUR_USERNAME>/pdf-to-html-converter-studio.git
cd pdf-to-html-converter-studio
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the WebApp
```bash
python app.py
```
Open **`http://localhost:8090`** in your browser!

*(Or on Windows, simply double-click `Start_App.bat`)*

---

## 🛠️ Tech Stack

- **Backend:** Python 3, Flask, PyMuPDF (`fitz`), Pillow (`PIL`), Werkzeug
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Google Fonts, Lucide Icons

---

## 📄 License
MIT License
