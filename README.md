# 📚 PDF to HTML+CSS Converter Studio (Universal WebApp & Mobile App)

> Convert **ANY PDF** (Textbooks, Books, Notes, Research Papers, Slides, Reports) into **100% Matching HTML & CSS** with Live Dual-View Studio, Standalone 1-File HTML Book Exporter, and Continuous Scroll Reading!

---

## 📱 Download Android Mobile App (APK)

You can download the Android Mobile App directly from GitHub:
1. Go to the **[Releases](https://github.com/nitish2221007/pdf-to-webapp-generator/releases)** section of this repository.
2. Download **`PDF_to_HTML_Converter.apk`**.
3. Install on your Android phone to convert & read PDF books on the go!

---

## ✨ Features

- 🎯 **Exact 1:1 Visual Replica**: Matches font sizes, weights, colors, vector graphics, and absolute coordinates.
- 📖 **Single-File Continuous Scroll HTML Book**: Download 1 single `.html` file with all pages combined vertically for smooth, continuous reading in any browser offline.
- 📱 **Mobile App & PWA Ready**: Includes Android APK build workflow and installable PWA mobile app support.
- 🖼️ **Clean sRGB Image Extraction**: Automatically filters out 1-bit prepress printing masks and converts CMYK plates to clean web PNGs.
- ⚡ **Precision Margin Protection (`scaleX`)**: Prevents character expansion from colliding with side borders and decorative stripes.
- 🌓 **Reading Modes**: Built-in Dark Mode, Light Mode, and Warm Sepia Mode.
- 🔍 **Full-Text Global Search**: Instant keyword search with contextual highlights across all pages.
- 📦 **1-Click Full Package ZIP**: Download standalone single-page HTML files, CSS stylesheets, and image assets.

---

## 🚀 Quick Start (Web Studio)

### 1. Clone the Repository
```bash
git clone https://github.com/nitish2221007/pdf-to-webapp-generator.git
cd pdf-to-webapp-generator
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the WebApp
```bash
python app.py
```
Open **`http://localhost:8090`** in your browser! *(Or on Windows, double-click `Start_App.bat`)*

---

## 🛠️ Automated Mobile App CI/CD

- Automated GitHub Actions workflow located in [`.github/workflows/build-apk.yml`](.github/workflows/build-apk.yml) compiles the Android Gradle project in [`android/`](android/) and publishes the `.apk` under GitHub Releases automatically on every push!

---

## 📄 License
MIT License
