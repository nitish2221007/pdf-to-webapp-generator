import fitz
import os
import json
import html
import base64
import zipfile
import shutil

def clean_text(text):
    if not text:
        return ""
    replacements = {
        '\uf0b3': '•',
        '\uf06c': '•',
        '\uf0a7': '•',
        '\uf0d8': '➢',
        '\uf0e0': '✉',
        '\uf0fc': '✔',
        '\u2018': "'",
        '\u2019': "'",
        '\u201c': '"',
        '\u201d': '"',
        '\u2013': '–',
        '\u2014': '—',
        '\u2026': '…',
        '\xa0': ' ',
        '\u2002': ' ',
        '\u2003': ' ',
        '\t': '    '
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def get_font_fallback(font_name):
    fn = font_name.lower()
    if 'dearjoe' in fn or 'script' in fn or 'hand' in fn:
        return "'Caveat', 'Marck Script', 'Brush Script MT', cursive, serif"
    elif 'bookman' in fn:
        return "'URW Bookman', 'Bookman Old Style', 'Bookman', 'Georgia', serif"
    elif 'century-schoolbook' in fn or 'schoolbook' in fn:
        return "'Century Schoolbook', 'Century Schoolbook L', 'Georgia', serif"
    elif 'gothic' in fn or 'helvetica' in fn or 'arial' in fn or 'sans' in fn:
        return "'Century Gothic', 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    elif 'times' in fn or 'serif' in fn:
        return "'Times New Roman', 'Times', 'Georgia', serif"
    elif 'wingdings' in fn or 'symbol' in fn:
        return "'Segoe UI Symbol', 'Arial Unicode MS', sans-serif"
    else:
        return "'URW Bookman', 'Bookman Old Style', 'Georgia', serif"

def build_continuous_scroll_html(doc_title, total_pages, pages_cards_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(doc_title)} - Complete HTML Book</title>
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=Inter:wght@400;500;600;700;800&family=Marck+Script&family=Montserrat:ital,wght@0,400;0,600;1,400&family=URW+Bookman:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
  
  <style>
    :root {{
      --bg-body: #1e293b;
      --bg-page: #ffffff;
      --bar-bg: rgba(15, 23, 42, 0.88);
      --bar-border: rgba(255, 255, 255, 0.12);
      --text-main: #f8fafc;
      --accent: #38bdf8;
    }}

    [data-theme="light"] {{
      --bg-body: #e2e8f0;
      --bar-bg: rgba(255, 255, 255, 0.9);
      --bar-border: rgba(0, 0, 0, 0.1);
      --text-main: #0f172a;
      --accent: #0284c7;
    }}

    [data-theme="sepia"] {{
      --bg-body: #ebd9b8;
      --bar-bg: rgba(245, 230, 203, 0.95);
      --bar-border: rgba(120, 90, 50, 0.2);
      --text-main: #453216;
      --accent: #b45309;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    body {{
      background-color: var(--bg-body);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding-bottom: 80px;
      overflow-x: hidden;
      transition: background-color 0.2s ease;
    }}

    /* Top Floating Reading Bar */
    .floating-header {{
      position: fixed;
      top: 16px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--bar-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--bar-border);
      border-radius: 40px;
      padding: 0.45rem 1.25rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      z-index: 1000;
      box-shadow: 0 10px 25px rgba(0,0,0,0.3);
      color: var(--text-main);
      font-size: 0.85rem;
      font-weight: 600;
    }}

    .book-title-tag {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: 700;
      white-space: nowrap;
      max-width: 280px;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .page-indicator {{
      background: rgba(56,189,248,0.15);
      color: var(--accent);
      padding: 0.2rem 0.6rem;
      border-radius: 20px;
      font-size: 0.78rem;
      font-weight: 700;
    }}

    .btn-icon {{
      background: rgba(255,255,255,0.08);
      border: 1px solid var(--bar-border);
      color: var(--text-main);
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 0.9rem;
      transition: all 0.15s;
    }}

    .btn-icon:hover {{
      background: var(--accent);
      color: #fff;
      transform: scale(1.05);
    }}

    /* Main Continuous Book Container */
    .book-pages-container {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 28px;
      margin-top: 75px;
      width: 100%;
    }}

    /* Individual Page Sheet Card */
    .book-page-sheet {{
      position: relative;
      background: var(--bg-page);
      border-radius: 4px;
      box-shadow: 0 15px 35px rgba(0,0,0,0.25), 0 4px 10px rgba(0,0,0,0.15);
      overflow: hidden;
      user-select: text;
    }}

    .page-number-tag {{
      position: absolute;
      top: 8px;
      right: 12px;
      font-size: 0.65rem;
      color: #94a3b8;
      font-family: sans-serif;
      font-weight: 700;
      z-index: 10;
      pointer-events: none;
      opacity: 0.6;
    }}

    .pdf-page-html-content {{
      background-color: #ffffff;
      overflow: hidden;
    }}

    .text-line {{
      position: absolute;
      white-space: nowrap;
      pointer-events: auto;
      cursor: text;
      transform-origin: left center;
    }}

    .text-span::selection {{
      background-color: rgba(236, 72, 153, 0.35);
      color: #000;
    }}

    /* Print styling */
    @media print {{
      body {{ background: #fff !important; padding: 0 !important; }}
      .floating-header {{ display: none !important; }}
      .book-pages-container {{ margin-top: 0 !important; gap: 0 !important; }}
      .book-page-sheet {{ box-shadow: none !important; margin: 0 !important; page-break-after: always; }}
    }}
  </style>
</head>
<body data-theme="dark">

  <!-- Floating Reading Bar -->
  <div class="floating-header">
    <div class="book-title-tag">
      📖 <span>{html.escape(doc_title)}</span>
    </div>
    
    <div class="page-indicator" id="current-page-badge">
      Page <span id="cur-p">1</span> / {total_pages}
    </div>

    <!-- Quick Page Jump -->
    <input type="number" id="page-jump-input" min="1" max="{total_pages}" value="1" 
      style="width: 46px; height: 26px; border-radius: 6px; border: 1px solid var(--bar-border); background: rgba(0,0,0,0.2); color: var(--text-main); text-align: center; font-weight: 700; font-size: 0.8rem; outline: none;" title="Enter page number to jump">

    <!-- Theme Toggle -->
    <button class="btn-icon" id="theme-btn" title="Toggle Theme (Dark / Light / Sepia)">🌓</button>
    <!-- Scroll to Top -->
    <button class="btn-icon" id="top-btn" title="Scroll to Top">⬆</button>
  </div>

  <!-- Continuous Vertical Pages Stream -->
  <main class="book-pages-container" id="pages-stream">
    {''.join(pages_cards_html)}
  </main>

  <script>
    function adjustLineScales() {{
      document.querySelectorAll('.text-line').forEach(el => {{
        const targetWidth = parseFloat(el.getAttribute('data-target-width'));
        if (targetWidth && el.scrollWidth > targetWidth + 0.5) {{
          const scale = targetWidth / el.scrollWidth;
          el.style.transform = `scaleX(${{scale}})`;
          el.style.transformOrigin = 'left center';
        }}
      }});
    }}

    const pages = document.querySelectorAll('.book-page-sheet');
    const curPBadge = document.getElementById('cur-p');
    const pageJumpInput = document.getElementById('page-jump-input');

    window.addEventListener('scroll', () => {{
      let current = 1;
      const scrollPos = window.scrollY + 250;
      pages.forEach((p, idx) => {{
        if (p.offsetTop <= scrollPos) {{
          current = idx + 1;
        }}
      }});
      curPBadge.textContent = current;
      pageJumpInput.value = current;
    }}, {{ passive: true }});

    pageJumpInput.addEventListener('change', (e) => {{
      const pNum = parseInt(e.target.value, 10);
      if (pNum >= 1 && pNum <= {total_pages}) {{
        const targetEl = document.getElementById(`page-${{pNum}}`);
        if (targetEl) {{
          targetEl.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
      }}
    }});

    document.getElementById('top-btn').addEventListener('click', () => {{
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }});

    const themes = ['dark', 'light', 'sepia'];
    let curTheme = 'dark';
    document.getElementById('theme-btn').addEventListener('click', () => {{
      curTheme = themes[(themes.indexOf(curTheme) + 1) % themes.length];
      document.body.setAttribute('data-theme', curTheme);
    }});

    window.addEventListener('DOMContentLoaded', () => {{
      adjustLineScales();
    }});
  </script>
</body>
</html>"""

def convert_pdf_to_html(pdf_path, output_dir, progress_callback=None):
    os.makedirs(output_dir, exist_ok=True)
    img_dir = os.path.join(output_dir, 'assets', 'images')
    pdf_page_dir = os.path.join(output_dir, 'assets', 'pdf_pages')
    pages_dir = os.path.join(output_dir, 'pages')
    
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(pdf_page_dir, exist_ok=True)
    os.makedirs(pages_dir, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    doc_title = doc.metadata.get('title') or os.path.splitext(os.path.basename(pdf_path))[0]
    
    book_pages = []
    continuous_page_cards = []
    
    for page_idx in range(total_pages):
        page_num = page_idx + 1
        page = doc[page_idx]
        rect = page.rect
        width = round(rect.width, 2)
        height = round(rect.height, 2)
        
        # 1. Render High-Resolution PDF page image
        pdf_img_rel_path = f"assets/pdf_pages/page_{page_num:03d}.png"
        pdf_img_full_path = os.path.join(output_dir, pdf_img_rel_path)
        pix = page.get_pixmap(dpi=150)
        pix.save(pdf_img_full_path)
        
        # 2. Extract embedded images with Base64 encoding
        extracted_images = []
        try:
            img_info_list = page.get_image_info(xrefs=True)
            for img_i, info in enumerate(img_info_list):
                xref = info.get('xref')
                bbox = info.get('bbox')
                bpc = info.get('bpc', 8)
                
                if not xref or not bbox or bpc == 1:
                    continue
                if bbox[2] - bbox[0] < 10 or bbox[3] - bbox[1] < 10:
                    continue
                if bbox[1] >= height - 10 or bbox[0] >= width or bbox[2] <= 0 or bbox[3] <= 0:
                    continue
                
                try:
                    img_filename = f"p{page_num:03d}_img{img_i:02d}.png"
                    img_full_path = os.path.join(img_dir, img_filename)
                    
                    pix_raw = fitz.Pixmap(doc, xref)
                    if pix_raw.colorspace and pix_raw.colorspace.name not in (fitz.csRGB.name, fitz.csGRAY.name):
                        pix_rgb = fitz.Pixmap(fitz.csRGB, pix_raw)
                    else:
                        pix_rgb = pix_raw
                    
                    if len(set(pix_rgb.samples[::100])) <= 2:
                        continue
                    
                    pix_rgb.save(img_full_path)
                    
                    img_bytes = pix_rgb.tobytes("png")
                    b64_data = "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")
                    
                    extracted_images.append({
                        "filename": img_filename,
                        "relPath": f"assets/images/{img_filename}",
                        "base64": b64_data,
                        "bbox": [round(c, 2) for c in bbox],
                        "width": round(bbox[2] - bbox[0], 2),
                        "height": round(bbox[3] - bbox[1], 2),
                        "left": round(bbox[0], 2),
                        "top": round(bbox[1], 2)
                    })
                except Exception:
                    pass
        except Exception:
            pass
            
        # 3. Extract Vector Drawings
        svg_drawings = []
        try:
            drawings = page.get_drawings()
            for d in drawings:
                d_rect = d.get('rect')
                if not d_rect:
                    continue
                fill = d.get('fill')
                stroke = d.get('color')
                w = d.get('width') if d.get('width') is not None else 1.0
                
                if d_rect.y0 >= height - 10 or d_rect.x0 >= width or d_rect.x1 <= 0 or d_rect.y1 <= 0:
                    continue
                if fill and (fill == (0,0,0) or fill == (0.0, 0.0, 0.0)) and (d_rect.width > 120 and d_rect.height > 120):
                    continue
                if d_rect.width >= width * 0.95 and d_rect.height >= height * 0.95:
                    continue
                    
                fill_color = f"rgba({int(fill[0]*255)}, {int(fill[1]*255)}, {int(fill[2]*255)}, {d.get('fill_opacity') or 1.0})" if fill else "none"
                stroke_color = f"rgba({int(stroke[0]*255)}, {int(stroke[1]*255)}, {int(stroke[2]*255)}, {d.get('stroke_opacity') or 1.0})" if stroke else "none"
                
                rx0 = max(0.0, min(width, d_rect.x0))
                ry0 = max(0.0, min(height, d_rect.y0))
                rw = max(0.0, min(width - rx0, d_rect.width))
                rh = max(0.0, min(height - ry0, d_rect.height))
                
                if rw > 0 and rh > 0:
                    svg_drawings.append({
                        "rect": [round(rx0, 2), round(ry0, 2), round(rw, 2), round(rh, 2)],
                        "fill": fill_color,
                        "stroke": stroke_color,
                        "stroke_width": round(w, 2)
                    })
        except Exception:
            pass
            
        # 4. Extract Text
        text_dict = page.get_text('dict')
        page_blocks = []
        raw_text_pieces = []
        
        for block in text_dict.get('blocks', []):
            if block.get('type') == 0:
                block_bbox = [round(c, 2) for c in block.get('bbox', [0, 0, 0, 0])]
                lines = []
                for line in block.get('lines', []):
                    line_bbox = [round(c, 2) for c in line.get('bbox', [0, 0, 0, 0])]
                    if line_bbox[1] >= height - 8:
                        continue
                    
                    spans = []
                    for span in line.get('spans', []):
                        span_text = clean_text(span.get('text', ''))
                        if not span_text:
                            continue
                        
                        raw_text_pieces.append(span_text)
                        
                        font_name = span.get('font', 'Bookman')
                        raw_size = span.get('size', 10.0)
                        font_size = round(raw_size * 0.94, 2) if raw_size < 20 else round(raw_size, 2)
                        font_color = f"#{span.get('color', 0):06x}"
                        flags = span.get('flags', 0)
                        
                        is_bold = bool(flags & 2**4) or ('bold' in font_name.lower()) or ('demi' in font_name.lower())
                        is_italic = bool(flags & 2**1) or ('italic' in font_name.lower()) or ('oblique' in font_name.lower())
                        font_fallback = get_font_fallback(font_name)
                        
                        span_bbox = [round(c, 2) for c in span.get('bbox', [0, 0, 0, 0])]
                        
                        spans.append({
                            "text": span_text,
                            "bbox": span_bbox,
                            "fontSize": font_size,
                            "fontFamily": font_fallback,
                            "color": font_color,
                            "bold": is_bold,
                            "italic": is_italic
                        })
                    
                    if spans:
                        lines.append({
                            "bbox": line_bbox,
                            "spans": spans
                        })
                
                if lines:
                    page_blocks.append({
                        "bbox": block_bbox,
                        "lines": lines
                    })
                    
        # 5. Build HTML
        html_elements_rel = []
        html_elements_b64 = []
        
        if svg_drawings:
            svg_content = f'<svg class="vector-bg" viewBox="0 0 {width} {height}" style="position: absolute; left: 0; top: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1;">\n'
            for sd in svg_drawings:
                rx, ry, rw, rh = sd['rect']
                svg_content += f'  <rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="{sd["fill"]}" stroke="{sd["stroke"]}" stroke-width="{sd["stroke_width"]}"/>\n'
            svg_content += '</svg>'
            html_elements_rel.append(svg_content)
            html_elements_b64.append(svg_content)
            
        for img in extracted_images:
            img_tag_rel = (
                f'<img src="{img["relPath"]}" alt="Graphic" class="page-img" '
                f'style="position: absolute; left: {img["left"]}pt; top: {img["top"]}pt; '
                f'width: {img["width"]}pt; height: {img["height"]}pt; object-fit: contain; z-index: 2;">'
            )
            html_elements_rel.append(img_tag_rel)
            
            src_b64 = img["base64"] if img["base64"] else img["relPath"]
            img_tag_b64 = (
                f'<img src="{src_b64}" alt="Graphic" class="page-img" '
                f'style="position: absolute; left: {img["left"]}pt; top: {img["top"]}pt; '
                f'width: {img["width"]}pt; height: {img["height"]}pt; object-fit: contain; z-index: 2;">'
            )
            html_elements_b64.append(img_tag_b64)
            
        for b_i, block in enumerate(page_blocks):
            for l_i, line in enumerate(block["lines"]):
                lx0, ly0, lx1, ly1 = line["bbox"]
                lw = round(lx1 - lx0, 2)
                line_html_parts = []
                
                for s in line["spans"]:
                    s_font = s["fontFamily"]
                    s_size = s["fontSize"]
                    s_color = s["color"]
                    s_weight = "bold" if s["bold"] else "normal"
                    s_style = "italic" if s["italic"] else "normal"
                    escaped_text = html.escape(s["text"])
                    
                    span_style = f"font-family: {s_font}; font-size: {s_size}pt; color: {s_color}; font-weight: {s_weight}; font-style: {s_style}; line-height: 1.15;"
                    line_html_parts.append(f'<span class="text-span" style="{span_style}">{escaped_text}</span>')
                
                line_content = "".join(line_html_parts)
                line_tag = (
                    f'<div class="text-line" data-target-width="{lw}" style="position: absolute; left: {lx0}pt; top: {ly0}pt; '
                    f'width: {lw}pt; max-width: {lw}pt; letter-spacing: -0.02em; white-space: nowrap; z-index: 3;">{line_content}</div>'
                )
                html_elements_rel.append(line_tag)
                html_elements_b64.append(line_tag)
                
        full_page_html_rel = f"""<div class="pdf-page-html-content" id="html-page-{page_num}" style="position: relative; width: {width}pt; height: {height}pt; background-color: #ffffff; margin: 0 auto; box-shadow: 0 4px 20px rgba(0,0,0,0.12); overflow: hidden;">
{chr(10).join(html_elements_rel)}
</div>"""

        full_page_html_b64 = f"""<div class="pdf-page-html-content" id="html-page-{page_num}" style="position: relative; width: {width}pt; height: {height}pt; background-color: #ffffff; margin: 0 auto; box-shadow: 0 4px 20px rgba(0,0,0,0.12); overflow: hidden;">
{chr(10).join(html_elements_b64)}
</div>"""

        page_card = f"""
        <div class="book-page-sheet" id="page-{page_num}" data-page="{page_num}" style="width: {width}pt; height: {height}pt;">
          <div class="page-number-tag">Page {page_num}</div>
          <div class="pdf-page-html-content" style="position: relative; width: {width}pt; height: {height}pt;">
            {chr(10).join(html_elements_b64)}
          </div>
        </div>
        """
        continuous_page_cards.append(page_card)
        
        # Single page file
        page_html_path = os.path.join(pages_dir, f"page_{page_num:03d}.html")
        with open(page_html_path, "w", encoding="utf-8") as f_page:
            f_page.write(full_page_html_b64)
            
        plain_text = " ".join(raw_text_pieces)
        
        book_pages.append({
            "pageNumber": page_num,
            "width": width,
            "height": height,
            "pdfImage": pdf_img_rel_path,
            "htmlSnippet": full_page_html_rel,
            "plainText": plain_text,
            "imageCount": len(extracted_images),
            "textLineCount": sum(len(b["lines"]) for b in page_blocks)
        })
        
        if progress_callback:
            progress_callback(page_num, total_pages)
            
    doc.close()
    
    # 6. Generate 1 Single Scrollable HTML Book File
    continuous_html_content = build_continuous_scroll_html(doc_title, total_pages, continuous_page_cards)
    continuous_book_path = os.path.join(output_dir, f"{doc_title}_Complete_Book.html")
    with open(continuous_book_path, "w", encoding="utf-8") as f_book:
        f_book.write(continuous_html_content)
        
    bundle_data = {
        "title": doc_title,
        "totalPages": total_pages,
        "pages": book_pages
    }
    
    json_path = os.path.join(output_dir, "assets", "book_data.json")
    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(bundle_data, f_json, ensure_ascii=False)
        
    js_path = os.path.join(output_dir, "assets", "book_data.js")
    with open(js_path, "w", encoding="utf-8") as f_js:
        f_js.write("window.BOOK_DATA = " + json.dumps(bundle_data, ensure_ascii=False) + ";")
        
    # ZIP
    zip_filename = f"{doc_title}_HTML_Package.zip"
    zip_path = os.path.join(output_dir, zip_filename)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.zip'):
                    continue
                file_full = os.path.join(root, file)
                rel_path = os.path.relpath(file_full, output_dir)
                zipf.write(file_full, rel_path)
                
    return {
        "title": doc_title,
        "totalPages": total_pages,
        "continuousBookPath": continuous_book_path,
        "continuousBookFilename": f"{doc_title}_Complete_Book.html",
        "zipPath": zip_path,
        "zipFilename": zip_filename,
        "data": bundle_data
    }
