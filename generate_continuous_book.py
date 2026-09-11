import fitz
import os
import json
import html
import base64

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

def build_page_article_html(page, extracted_images, page_num, total_pages, use_base64=True):
    width, height = round(page.rect.width, 2), round(page.rect.height, 2)
    text_dict = page.get_text('dict', sort=True)
    raw_blocks = text_dict.get('blocks', [])
    
    html_elements = []
    sorted_imgs = sorted(extracted_images, key=lambda img: img.get('top', 0))
    img_idx = 0
    
    valid_blocks = []
    for b in raw_blocks:
        if b.get('type') != 0:
            continue
        bx0, by0, bx1, by1 = b.get('bbox', [0,0,0,0])
        lines = b.get('lines', [])
        txt = ' '.join([''.join([clean_text(s['text']) for s in l['spans']]) for l in lines]).strip()
        if not txt:
            continue
        if (by1 >= height - 28 or by0 <= 22) and (len(txt) < 16 or txt.isdigit()):
            continue
        valid_blocks.append((b, bx0, by0, bx1, by1, txt))
        
    left_count = sum(1 for item in valid_blocks if (item[3] - item[1]) < width * 0.55 and (item[1]+item[3])/2 < width * 0.50)
    right_count = sum(1 for item in valid_blocks if (item[3] - item[1]) < width * 0.55 and (item[1]+item[3])/2 >= width * 0.50)
    has_two_cols = (left_count >= 2 and right_count >= 2)

    def get_sort_key(item):
        b, bx0, by0, bx1, by1, txt = item
        cx = (bx0 + bx1) / 2
        is_wide = (bx1 - bx0) > (width * 0.60)
        if is_wide and by0 < height * 0.25:
            col = 0
        elif is_wide:
            col = 1
        elif cx < width * 0.50:
            col = 2
        else:
            col = 3
        return (col, round(by0, 1), round(bx0, 1))

    if has_two_cols:
        valid_blocks.sort(key=get_sort_key)
    else:
        valid_blocks.sort(key=lambda item: (round(item[2], 1), round(item[1], 1)))

    for item in valid_blocks:
        b, bx0, by0, bx1, by1, block_text = item
        lines = b.get('lines', [])
        
        while img_idx < len(sorted_imgs) and sorted_imgs[img_idx].get('top', 0) <= by0:
            img = sorted_imgs[img_idx]
            src = img.get('base64') if use_base64 and img.get('base64') else img.get('relPath', '')
            if src and img.get('width', 0) >= 30 and img.get('height', 0) >= 30:
                html_elements.append(f'<div class="article-media-wrap"><img src="{src}" alt="Illustration" class="article-img" loading="lazy"></div>')
            img_idx += 1
            
        max_size = 0
        is_bold = False
        for l in lines:
            for s in l.get('spans', []):
                if s.get('size', 0) > max_size:
                    max_size = s.get('size', 0)
                if 'bold' in s.get('font', '').lower() or 'demi' in s.get('font', '').lower():
                    is_bold = True
                    
        clean_para = html.escape(block_text)
        if max_size >= 24:
            html_elements.append(f'<h1 class="article-title">{clean_para}</h1>')
        elif max_size >= 16:
            html_elements.append(f'<h2 class="article-heading-2">{clean_para}</h2>')
        elif max_size >= 12.5 and (is_bold or len(clean_para) < 80):
            html_elements.append(f'<h3 class="article-heading-3">{clean_para}</h3>')
        elif (bx1 - bx0 < width * 0.38) and len(clean_para) < 250:
            html_elements.append(f'<aside class="article-callout"><p>{clean_para}</p></aside>')
        else:
            html_elements.append(f'<p class="article-para">{clean_para}</p>')

    while img_idx < len(sorted_imgs):
        img = sorted_imgs[img_idx]
        src = img.get('base64') if use_base64 and img.get('base64') else img.get('relPath', '')
        if src and img.get('width', 0) >= 30 and img.get('height', 0) >= 30:
            html_elements.append(f'<div class="article-media-wrap"><img src="{src}" alt="Illustration" class="article-img" loading="lazy"></div>')
        img_idx += 1
        
    content_html = '\n'.join(html_elements)
    
    return f"""<article class="article-page-card" id="article-page-{page_num}" data-page="{page_num}">
  <div class="article-page-badge">Page {page_num} of {total_pages}</div>
  <div class="article-body">
    {content_html}
  </div>
</article>"""

def generate_continuous_scroll_book(pdf_path, output_html_path):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc_title = doc.metadata.get('title') or os.path.splitext(os.path.basename(pdf_path))[0]
    
    print(f"Generating Continuous Scroll & Web Article HTML Book for '{doc_title}' ({total_pages} pages)...")
    
    all_pages_html = []
    article_page_cards = []
    
    for page_idx in range(total_pages):
        page_num = page_idx + 1
        page = doc[page_idx]
        rect = page.rect
        width = round(rect.width, 2)
        height = round(rect.height, 2)
        
        # 1. Extract embedded images with Base64 encoding
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
                    pix_raw = fitz.Pixmap(doc, xref)
                    if pix_raw.colorspace and pix_raw.colorspace.name not in (fitz.csRGB.name, fitz.csGRAY.name):
                        pix_rgb = fitz.Pixmap(fitz.csRGB, pix_raw)
                    else:
                        pix_rgb = pix_raw
                    
                    if len(set(pix_rgb.samples[::100])) <= 2:
                        continue
                    
                    img_bytes = pix_rgb.tobytes("png")
                    b64_data = "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")
                    
                    extracted_images.append({
                        "base64": b64_data,
                        "width": round(bbox[2] - bbox[0], 2),
                        "height": round(bbox[3] - bbox[1], 2),
                        "left": round(bbox[0], 2),
                        "top": round(bbox[1], 2)
                    })
                except Exception:
                    pass
        except Exception:
            pass
            
        # 2. Extract Vector Drawings
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
            
        # 3. Extract Text
        text_dict = page.get_text('dict')
        page_blocks = []
        
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
                    
        # 4. Build 1:1 Canvas Elements
        html_elements = []
        
        if svg_drawings:
            svg_content = f'<svg class="vector-bg" viewBox="0 0 {width} {height}" style="position: absolute; left: 0; top: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1;">\n'
            for sd in svg_drawings:
                rx, ry, rw, rh = sd['rect']
                svg_content += f'  <rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="{sd["fill"]}" stroke="{sd["stroke"]}" stroke-width="{sd["stroke_width"]}"/>\n'
            svg_content += '</svg>'
            html_elements.append(svg_content)
            
        for img in extracted_images:
            img_tag = (
                f'<img src="{img["base64"]}" alt="Graphic" class="page-img" '
                f'style="position: absolute; left: {img["left"]}pt; top: {img["top"]}pt; '
                f'width: {img["width"]}pt; height: {img["height"]}pt; object-fit: contain; z-index: 2;">'
            )
            html_elements.append(img_tag)
            
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
                html_elements.append(line_tag)
                
        page_card = f"""
        <div class="book-page-sheet-container" style="display: flex; justify-content: center; width: 100%;">
          <div class="book-page-sheet" id="page-{page_num}" data-page="{page_num}" data-width="{width}" data-height="{height}" style="width: {width}pt; height: {height}pt; transform-origin: top center; transition: transform 0.15s ease;">
            <div class="page-number-tag">Page {page_num}</div>
            <div class="pdf-page-html-content" style="position: relative; width: {width}pt; height: {height}pt;">
              {chr(10).join(html_elements)}
            </div>
          </div>
        </div>
        """
        all_pages_html.append(page_card)
        
        # 5. Build Web Article Card
        article_card = build_page_article_html(page, extracted_images, page_num, total_pages, use_base64=True)
        article_page_cards.append(article_card)
        
        if page_num % 25 == 0 or page_num == total_pages:
            print(f"Processed {page_num}/{total_pages} pages...", flush=True)
            
    doc.close()
    
    full_html_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
  <title>{html.escape(doc_title)} - Complete HTML Web Book</title>
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=Inter:wght@400;500;600;700;800&family=Marck+Script&family=Montserrat:ital,wght@0,400;0,600;1,400&family=URW+Bookman:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
  
  <style>
    :root {{
      --bg-body: #090d16;
      --bg-surface: #111827;
      --bg-card: #1f293d;
      --bg-page: #ffffff;
      --bar-bg: rgba(15, 23, 42, 0.92);
      --bar-border: rgba(255, 255, 255, 0.12);
      --text-main: #f8fafc;
      --text-body: #cbd5e1;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
    }}

    [data-theme="light"] {{
      --bg-body: #f1f5f9;
      --bg-surface: #ffffff;
      --bg-card: #e2e8f0;
      --bar-bg: rgba(255, 255, 255, 0.95);
      --bar-border: rgba(0, 0, 0, 0.1);
      --text-main: #0f172a;
      --text-body: #334155;
      --text-muted: #64748b;
      --accent: #0284c7;
    }}

    [data-theme="sepia"] {{
      --bg-body: #f5eedc;
      --bg-surface: #fbf5e8;
      --bg-card: #ebd9b8;
      --bar-bg: rgba(245, 230, 203, 0.95);
      --bar-border: rgba(120, 90, 50, 0.2);
      --text-main: #2e2010;
      --text-body: #453216;
      --text-muted: #7c6240;
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
      padding-bottom: 110px;
      overflow-x: hidden;
      transition: background-color 0.2s ease;
      -webkit-font-smoothing: antialiased;
    }}

    /* Top Floating Reading Bar */
    .floating-header {{
      position: fixed;
      top: 14px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--bar-bg);
      backdrop-filter: blur(14px);
      border: 1px solid var(--bar-border);
      border-radius: 40px;
      padding: 0.35rem 0.85rem;
      display: flex;
      align-items: center;
      gap: 0.6rem;
      z-index: 1000;
      box-shadow: 0 10px 30px rgba(0,0,0,0.35);
      color: var(--text-main);
      font-size: 0.82rem;
      font-weight: 600;
      max-width: calc(100vw - 24px);
    }}

    .book-title-tag {{
      display: flex;
      align-items: center;
      gap: 0.4rem;
      font-weight: 700;
      white-space: nowrap;
      max-width: 180px;
      overflow: hidden;
      text-overflow: ellipsis;
      cursor: pointer;
    }}

    .segmented-control {{
      display: inline-flex;
      background: rgba(0,0,0,0.25);
      border: 1px solid var(--bar-border);
      border-radius: 20px;
      padding: 2px;
      gap: 2px;
    }}

    .seg-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 0.28rem 0.65rem;
      border-radius: 16px;
      font-size: 0.74rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      transition: all 0.15s ease;
      white-space: nowrap;
    }}

    .seg-btn:hover {{
      color: var(--text-main);
    }}

    .seg-btn.active {{
      background: var(--accent);
      color: #090d16;
      font-weight: 700;
      box-shadow: 0 2px 8px rgba(56,189,248,0.4);
    }}

    .page-indicator {{
      background: rgba(56,189,248,0.15);
      color: var(--accent);
      padding: 0.22rem 0.6rem;
      border-radius: 20px;
      font-size: 0.76rem;
      font-weight: 700;
      white-space: nowrap;
    }}

    .btn-icon {{
      background: rgba(255,255,255,0.08);
      border: 1px solid var(--bar-border);
      color: var(--text-main);
      width: 30px;
      height: 30px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 0.85rem;
      transition: all 0.15s;
      flex-shrink: 0;
    }}

    .btn-icon:hover {{
      background: var(--accent);
      color: #090d16;
      transform: scale(1.05);
    }}

    .btn-icon-pill {{
      width: auto !important;
      padding: 0 0.65rem !important;
      border-radius: 20px !important;
      font-size: 0.75rem !important;
      gap: 0.3rem !important;
      font-weight: 600 !important;
      display: inline-flex !important;
    }}

    /* Web Article Container */
    .web-article-container {{
      width: 100%;
      max-width: 760px;
      margin-top: 68px;
      padding: 0.75rem 1rem;
      display: flex;
      flex-direction: column;
      gap: 1.75rem;
    }}

    .article-page-card {{
      background: var(--bg-surface);
      border: 1px solid var(--bar-border);
      border-radius: 16px;
      padding: 2rem 1.75rem;
      box-shadow: 0 10px 30px rgba(0,0,0,0.22);
    }}

    [data-theme="light"] .article-page-card {{
      background: #ffffff;
      border-color: rgba(0,0,0,0.08);
      box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    }}

    [data-theme="sepia"] .article-page-card {{
      background: #fbf5e8;
      border-color: rgba(120, 90, 50, 0.16);
      box-shadow: 0 4px 20px rgba(120, 90, 50, 0.08);
    }}

    .article-page-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--accent);
      background: rgba(56,189,248,0.12);
      padding: 0.22rem 0.65rem;
      border-radius: 20px;
      margin-bottom: 1.25rem;
    }}

    .article-body {{
      color: var(--text-body);
      line-height: 1.8;
      font-size: 1.05rem;
    }}

    .article-title {{
      font-size: 1.85rem;
      font-weight: 800;
      line-height: 1.25;
      margin: 0.5rem 0 1.25rem;
      color: var(--text-main);
      letter-spacing: -0.02em;
    }}

    .article-heading-2 {{
      font-size: 1.4rem;
      font-weight: 700;
      line-height: 1.35;
      margin: 1.75rem 0 0.85rem;
      color: var(--text-main);
      border-bottom: 2px solid rgba(56,189,248,0.25);
      padding-bottom: 0.4rem;
    }}

    .article-heading-3 {{
      font-size: 1.15rem;
      font-weight: 600;
      line-height: 1.4;
      margin: 1.25rem 0 0.5rem;
      color: var(--accent);
    }}

    .article-para {{
      font-size: 1.05rem;
      line-height: 1.8;
      margin-bottom: 1.15rem;
      color: var(--text-body);
      text-align: justify;
    }}

    .article-callout {{
      background: rgba(56,189,248,0.07);
      border-left: 4px solid var(--accent);
      border-radius: 0 10px 10px 0;
      padding: 1rem 1.25rem;
      margin: 1.35rem 0;
      font-size: 0.96rem;
      line-height: 1.65;
      color: var(--text-main);
      font-style: italic;
    }}

    .article-media-wrap {{
      margin: 1.5rem auto;
      text-align: center;
      max-width: 100%;
    }}

    .article-img {{
      max-width: 100%;
      height: auto;
      border-radius: 10px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.2);
      object-fit: contain;
      background: #fff;
    }}

    /* 1:1 Canvas Container */
    .book-pages-container {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 28px;
      margin-top: 68px;
      width: 100%;
    }}

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

    /* Bottom Floating Nav Bar */
    .bottom-nav-bar {{
      position: fixed;
      bottom: 16px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--bar-bg);
      backdrop-filter: blur(14px);
      border: 1px solid var(--bar-border);
      border-radius: 40px;
      padding: 0.35rem 0.65rem;
      display: flex;
      align-items: center;
      gap: 0.6rem;
      z-index: 1000;
      box-shadow: 0 12px 32px rgba(0,0,0,0.4);
    }}

    .bottom-nav-btn {{
      background: rgba(255,255,255,0.08);
      border: 1px solid var(--bar-border);
      color: var(--text-main);
      padding: 0.45rem 1rem;
      border-radius: 20px;
      font-size: 0.82rem;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      transition: all 0.15s;
      white-space: nowrap;
    }}

    .bottom-nav-btn:hover:not(:disabled) {{
      background: var(--accent);
      color: #090d16;
      transform: translateY(-1px);
    }}

    .bottom-nav-btn:disabled {{
      opacity: 0.35;
      cursor: not-allowed;
    }}

    /* Mobile Responsive */
    @media screen and (max-width: 768px) {{
      .floating-header {{
        top: 8px !important;
        width: calc(100% - 12px) !important;
        padding: 0.3rem 0.45rem !important;
        gap: 0.35rem !important;
        border-radius: 30px !important;
        font-size: 0.72rem !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        scrollbar-width: none !important;
      }}
      .floating-header::-webkit-scrollbar {{ display: none; }}
      .book-title-tag {{
        max-width: 85px !important;
        font-size: 0.72rem !important;
      }}
      .seg-btn {{
        padding: 0.22rem 0.45rem !important;
        font-size: 0.68rem !important;
      }}
      .page-indicator {{
        font-size: 0.68rem !important;
        padding: 0.15rem 0.4rem !important;
      }}
      #page-jump-input {{
        width: 34px !important;
        height: 22px !important;
        font-size: 0.7rem !important;
      }}
      .btn-icon {{
        width: 26px !important;
        height: 26px !important;
        min-width: 26px !important;
        font-size: 0.72rem !important;
      }}
      .web-article-container {{
        margin-top: 50px !important;
        padding: 0.5rem 0.5rem 1.5rem !important;
        gap: 1rem !important;
      }}
      .article-page-card {{
        padding: 1.25rem 1rem !important;
        border-radius: 12px !important;
      }}
      .article-title {{ font-size: 1.45rem !important; }}
      .article-heading-2 {{ font-size: 1.2rem !important; }}
      .article-heading-3 {{ font-size: 1.05rem !important; }}
      .article-para {{
        font-size: 0.98rem !important;
        line-height: 1.7 !important;
        text-align: left !important;
      }}
      .book-pages-container {{
        margin-top: 50px !important;
        gap: 12px !important;
        padding: 0 4px !important;
      }}
      .bottom-nav-bar {{
        bottom: 10px !important;
        padding: 0.28rem 0.45rem !important;
        gap: 0.4rem !important;
      }}
      .bottom-nav-btn {{
        padding: 0.35rem 0.75rem !important;
        font-size: 0.76rem !important;
      }}
    }}

    @media print {{
      body {{ background: #fff !important; padding: 0 !important; }}
      .floating-header, .bottom-nav-bar {{ display: none !important; }}
      .article-page-card, .book-page-sheet {{ box-shadow: none !important; margin: 0 !important; page-break-after: always; }}
    }}
  </style>
</head>
<body data-theme="dark">

  <!-- Floating Reading Bar -->
  <header class="floating-header">
    <div class="book-title-tag" id="book-title" title="{html.escape(doc_title)}">
      📖 <span>{html.escape(doc_title)}</span>
    </div>
    
    <!-- View Switcher -->
    <div class="segmented-control" id="view-mode-control">
      <button class="seg-btn active" id="btn-mode-article" title="Switch to Mobile Web Article (Large readable text)">
        📱 Article
      </button>
      <button class="seg-btn" id="btn-mode-canvas" title="Switch to 1:1 Print Replica Layout">
        🎯 1:1 Canvas
      </button>
    </div>

    <!-- Scroll Mode Switcher -->
    <div class="segmented-control" id="scroll-mode-control">
      <button class="seg-btn active" id="btn-scroll-page" title="Page-by-Page Reading (No Endless Scroll!)">
        📄 Page
      </button>
      <button class="seg-btn" id="btn-scroll-stream" title="Continuous Vertical Scroll">
        📜 Stream
      </button>
    </div>

    <div class="page-indicator" id="current-page-badge">
      <span id="cur-p">1</span> / {total_pages}
    </div>

    <!-- Quick Page Jump -->
    <input type="number" id="page-jump-input" min="1" max="{total_pages}" value="1" 
      style="width: 40px; height: 24px; border-radius: 6px; border: 1px solid var(--bar-border); background: rgba(0,0,0,0.25); color: var(--text-main); text-align: center; font-weight: 700; font-size: 0.75rem; outline: none;" title="Jump to page">

    <!-- Canvas Zoom Controls -->
    <div id="zoom-controls-wrap" style="display: none; align-items: center; gap: 0.35rem;">
      <button class="btn-icon" id="btn-zoom-out" title="Zoom Out (-)" style="font-weight: 800;">−</button>
      <button class="btn-icon btn-icon-pill" id="btn-zoom-reset" title="Fit to Width">
        <span id="zoom-text">Fit</span>
      </button>
      <button class="btn-icon" id="btn-zoom-in" title="Zoom In (+)" style="font-weight: 800;">+</button>
    </div>

    <button class="btn-icon" id="btn-fullscreen" title="Toggle Fullscreen Mode">⛶</button>
    <button class="btn-icon" id="theme-btn" title="Toggle Theme (Dark / Light / Sepia)">🌓</button>
    <button class="btn-icon" id="top-btn" title="Scroll to Top">⬆</button>
  </header>

  <!-- 1. Mobile Web Article View -->
  <main class="web-article-container" id="article-stream">
    {''.join(article_page_cards)}
  </main>

  <!-- 2. Continuous Vertical Canvas Stream (1:1 Exact Print Replica) -->
  <main class="book-pages-container" id="pages-stream" style="display: none;">
    {''.join(all_pages_html)}
  </main>

  <!-- Bottom Floating Navigation Bar -->
  <nav class="bottom-nav-bar" id="bottom-nav-bar">
    <button class="bottom-nav-btn" id="b-btn-prev" title="Previous Page">
      ‹ Prev Page
    </button>
    <div class="page-indicator" style="background: transparent; border: 1px solid var(--bar-border);">
      Page <span id="b-cur-p">1</span> / {total_pages}
    </div>
    <button class="bottom-nav-btn" id="b-btn-next" title="Next Page">
      Next Page ›
    </button>
  </nav>

  <script>
    const totalPages = {total_pages};
    let currentPage = 1;
    let currentViewMode = 'article';
    let currentScrollMode = 'page';
    let currentZoomMultiplier = 1.0;

    const articleStream = document.getElementById('article-stream');
    const pagesStream = document.getElementById('pages-stream');
    const curPBadge = document.getElementById('cur-p');
    const bCurPBadge = document.getElementById('b-cur-p');
    const pageJumpInput = document.getElementById('page-jump-input');
    const bottomNavBar = document.getElementById('bottom-nav-bar');
    const bBtnPrev = document.getElementById('b-btn-prev');
    const bBtnNext = document.getElementById('b-btn-next');
    const zoomControlsWrap = document.getElementById('zoom-controls-wrap');

    const btnModeArticle = document.getElementById('btn-mode-article');
    const btnModeCanvas = document.getElementById('btn-mode-canvas');
    const btnScrollPage = document.getElementById('btn-scroll-page');
    const btnScrollStream = document.getElementById('btn-scroll-stream');

    function updatePageVisibility() {{
      curPBadge.textContent = currentPage;
      bCurPBadge.textContent = currentPage;
      pageJumpInput.value = currentPage;

      bBtnPrev.disabled = (currentPage <= 1);
      bBtnNext.disabled = (currentPage >= totalPages);

      if (currentScrollMode === 'page') {{
        document.querySelectorAll('.article-page-card').forEach(el => {{
          const p = parseInt(el.getAttribute('data-page'), 10);
          el.style.display = (p === currentPage) ? 'block' : 'none';
        }});
        document.querySelectorAll('.book-page-sheet-container').forEach(el => {{
          const sheet = el.querySelector('.book-page-sheet');
          const p = sheet ? parseInt(sheet.getAttribute('data-page'), 10) : 0;
          el.style.display = (p === currentPage) ? 'flex' : 'none';
        }});
        bottomNavBar.style.display = 'flex';
        window.scrollTo({{ top: 0, behavior: 'smooth' }});
      }} else {{
        document.querySelectorAll('.article-page-card').forEach(el => el.style.display = 'block');
        document.querySelectorAll('.book-page-sheet-container').forEach(el => el.style.display = 'flex');
        bottomNavBar.style.display = 'flex';
      }}

      if (currentViewMode === 'canvas') {{
        setTimeout(applyCanvasScaling, 50);
      }}
    }}

    function setViewMode(mode) {{
      currentViewMode = mode;
      if (mode === 'article') {{
        articleStream.style.display = 'flex';
        pagesStream.style.display = 'none';
        zoomControlsWrap.style.display = 'none';
        btnModeArticle.classList.add('active');
        btnModeCanvas.classList.remove('active');
      }} else {{
        articleStream.style.display = 'none';
        pagesStream.style.display = 'flex';
        zoomControlsWrap.style.display = 'inline-flex';
        btnModeCanvas.classList.add('active');
        btnModeArticle.classList.remove('active');
        applyCanvasScaling();
      }}
      updatePageVisibility();
    }}

    function setScrollMode(mode) {{
      currentScrollMode = mode;
      if (mode === 'page') {{
        btnScrollPage.classList.add('active');
        btnScrollStream.classList.remove('active');
      }} else {{
        btnScrollStream.classList.add('active');
        btnScrollPage.classList.remove('active');
      }}
      updatePageVisibility();
    }}

    function goToPage(pNum) {{
      if (pNum < 1) pNum = 1;
      if (pNum > totalPages) pNum = totalPages;
      currentPage = pNum;

      if (currentScrollMode === 'page') {{
        updatePageVisibility();
      }} else {{
        const targetId = (currentViewMode === 'article') ? `article-page-${{pNum}}` : `page-${{pNum}}`;
        const targetEl = document.getElementById(targetId);
        if (targetEl) {{
          targetEl.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
        curPBadge.textContent = currentPage;
        bCurPBadge.textContent = currentPage;
        pageJumpInput.value = currentPage;
      }}
    }}

    bBtnPrev.addEventListener('click', () => goToPage(currentPage - 1));
    bBtnNext.addEventListener('click', () => goToPage(currentPage + 1));
    btnModeArticle.addEventListener('click', () => setViewMode('article'));
    btnModeCanvas.addEventListener('click', () => setViewMode('canvas'));
    btnScrollPage.addEventListener('click', () => setScrollMode('page'));
    btnScrollStream.addEventListener('click', () => setScrollMode('stream'));

    pageJumpInput.addEventListener('change', (e) => {{
      const val = parseInt(e.target.value, 10);
      if (!isNaN(val)) goToPage(val);
    }});

    window.addEventListener('scroll', () => {{
      if (currentScrollMode !== 'stream') return;
      const scrollPos = window.scrollY + 200;
      let cur = 1;

      if (currentViewMode === 'article') {{
        document.querySelectorAll('.article-page-card').forEach(card => {{
          if (card.offsetTop <= scrollPos) {{
            cur = parseInt(card.getAttribute('data-page'), 10);
          }}
        }});
      }} else {{
        document.querySelectorAll('.book-page-sheet').forEach(sheet => {{
          if (sheet.offsetTop <= scrollPos) {{
            cur = parseInt(sheet.getAttribute('data-page'), 10);
          }}
        }});
      }}

      currentPage = cur;
      curPBadge.textContent = cur;
      bCurPBadge.textContent = cur;
      pageJumpInput.value = cur;
      bBtnPrev.disabled = (currentPage <= 1);
      bBtnNext.disabled = (currentPage >= totalPages);
    }}, {{ passive: true }});

    // Touch Swipe Gesture
    let touchStartX = 0;
    let touchStartY = 0;
    window.addEventListener('touchstart', (e) => {{
      touchStartX = e.changedTouches[0].screenX;
      touchStartY = e.changedTouches[0].screenY;
    }}, {{ passive: true }});

    window.addEventListener('touchend', (e) => {{
      const touchEndX = e.changedTouches[0].screenX;
      const touchEndY = e.changedTouches[0].screenY;
      const diffX = touchEndX - touchStartX;
      const diffY = touchEndY - touchStartY;

      if (Math.abs(diffX) > 60 && Math.abs(diffY) < 50) {{
        if (diffX < 0) goToPage(currentPage + 1);
        else goToPage(currentPage - 1);
      }}
    }}, {{ passive: true }});

    window.addEventListener('keydown', (e) => {{
      if (e.target.tagName === 'INPUT') return;
      if (e.key === 'ArrowRight' || e.key === 'PageDown') goToPage(currentPage + 1);
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') goToPage(currentPage - 1);
    }});

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

    function applyCanvasScaling() {{
      const sheets = document.querySelectorAll('.book-page-sheet');
      const winWidth = window.innerWidth;
      const isMobile = winWidth < 768;
      const padding = isMobile ? 12 : 40;
      const availWidth = Math.max(160, winWidth - padding);
      
      sheets.forEach(sheet => {{
        const origWidthPt = parseFloat(sheet.getAttribute('data-width') || sheet.style.width);
        const origHeightPt = parseFloat(sheet.getAttribute('data-height') || sheet.style.height);
        const origWidthPx = origWidthPt * (96 / 72);
        const origHeightPx = origHeightPt * (96 / 72);
        const container = sheet.closest('.book-page-sheet-container');
        
        const baseScale = availWidth / origWidthPx;
        const scale = baseScale * currentZoomMultiplier;
        
        sheet.style.transform = `scale(${{scale}})`;
        sheet.style.transformOrigin = 'top center';
        sheet.style.maxWidth = 'none';
        sheet.style.minWidth = `${{origWidthPt}}pt`;
        sheet.style.width = `${{origWidthPt}}pt`;
        sheet.style.boxShadow = isMobile ? '0 6px 18px rgba(0,0,0,0.3)' : '0 20px 50px rgba(0,0,0,0.35)';
        
        if (container) {{
          container.style.height = `${{origHeightPx * scale + (isMobile ? 12 : 24)}}px`;
          container.style.width = '100%';
          container.style.display = (currentScrollMode === 'page' && parseInt(sheet.getAttribute('data-page'), 10) !== currentPage) ? 'none' : 'flex';
          container.style.justifyContent = 'center';
          container.style.overflowX = currentZoomMultiplier > 1.05 ? 'auto' : 'hidden';
        }}
      }});
      
      const zoomText = document.getElementById('zoom-text');
      if (zoomText) {{
        zoomText.textContent = currentZoomMultiplier === 1.0 ? 'Fit' : `${{Math.round(currentZoomMultiplier * 100)}}%`;
      }}
      
      adjustLineScales();
    }}

    document.getElementById('btn-zoom-in')?.addEventListener('click', () => {{
      currentZoomMultiplier = Math.min(2.5, +(currentZoomMultiplier + 0.2).toFixed(1));
      applyCanvasScaling();
    }});

    document.getElementById('btn-zoom-out')?.addEventListener('click', () => {{
      currentZoomMultiplier = Math.max(0.6, +(currentZoomMultiplier - 0.2).toFixed(1));
      applyCanvasScaling();
    }});

    document.getElementById('btn-zoom-reset')?.addEventListener('click', () => {{
      currentZoomMultiplier = 1.0;
      applyCanvasScaling();
    }});

    document.getElementById('btn-fullscreen')?.addEventListener('click', () => {{
      if (!document.fullscreenElement) {{
        document.documentElement.requestFullscreen().catch(() => {{}});
      }} else {{
        document.exitFullscreen().catch(() => {{}});
      }}
    }});

    document.getElementById('top-btn')?.addEventListener('click', () => {{
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }});

    const themes = ['dark', 'light', 'sepia'];
    let curTheme = 'dark';
    document.getElementById('theme-btn')?.addEventListener('click', () => {{
      curTheme = themes[(themes.indexOf(curTheme) + 1) % themes.length];
      document.body.setAttribute('data-theme', curTheme);
    }});

    window.addEventListener('resize', () => {{
      if (currentViewMode === 'canvas') applyCanvasScaling();
    }});

    document.addEventListener('DOMContentLoaded', () => {{
      const isMobile = window.innerWidth < 768;
      setViewMode('article');
      setScrollMode('page');
      updatePageVisibility();
    }});
  </script>
</body>
</html>"""

    with open(output_html_path, "w", encoding="utf-8") as f_out:
        f_out.write(full_html_document)
        
    print(f"SUCCESS! Continuous Scroll & Web Article HTML Book saved at: {output_html_path}", flush=True)
    return output_html_path

if __name__ == '__main__':
    pdf_path = r'C:\Users\yniti\NCERT_Class11\English\Class 11 English - Hornbill.pdf'
    out_file = r'C:\Users\yniti\Hornbill_HTML_Viewer\Hornbill_Complete_Book.html'
    if os.path.exists(pdf_path):
        generate_continuous_scroll_book(pdf_path, out_file)
