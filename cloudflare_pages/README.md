# ⚡ Cloudflare Pages Frontend Deployment

This directory contains the standalone, decoupled frontend for **PDF to HTML Converter Studio**, ready to deploy on **Cloudflare Pages**.

---

## 🚀 How to Deploy on Cloudflare Pages:

### Method 1: Direct Folder Upload (Drag & Drop - 30 seconds!)
1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. In the left sidebar, navigate to **Compute (Workers & Pages)** &rarr; **Create** &rarr; **Pages** &rarr; **Upload assets**.
3. Set project name (e.g. `pdf-to-html-studio`).
4. Drag and drop this entire `cloudflare_pages/` folder into the upload box.
5. Click **Deploy site**!
6. Your fast CDN website will be live at `https://pdf-to-html-studio.pages.dev`!

---

### Method 2: Git Integration (Auto-Deploy on Push)
1. In Cloudflare Pages, select **Connect to Git**.
2. Select your repository: `nitish2221007/pdf-to-webapp-generator`.
3. In the build settings:
   - **Framework preset:** `None`
   - **Build command:** *(Leave empty)*
   - **Build output directory:** `cloudflare_pages`
4. Click **Save and Deploy**!

---

## 🔗 Connecting to Hugging Face Spaces Backend:
Once your backend is running on Hugging Face Spaces (e.g. `https://your-username-pdf-studio.hf.space`):
1. Open your Cloudflare Pages website in the browser.
2. Click the **Backend: Connected** badge in the top-right navbar.
3. Enter your Hugging Face Space URL & save.
*(Or paste it into `config.js` before deploying!)*
