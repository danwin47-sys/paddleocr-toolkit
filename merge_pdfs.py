#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合併 input 資料夾中的所有 PDF 檔案"""

import fitz
import os

input_dir = 'input'
output_path = 'input/merged_output.pdf'

# Get all compatible files (PDFs and images)
files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')) and f != 'merged_output.pdf'])

# Filter for specific user request if needed, but the user asked for "input 1.2.3.4.5"
# It implies 1.JPG, 2.JPG etc. and maybe existing PDFs.
# Let's filter to ensure we act on 1-5 if they exist, or just all.
# User said "print 1.2.3.4.5". Let's try to just include everything for now or prioritize the numbered ones if we want to be strict.
# But "1.2.3.4.5" strongly implies the numbered files.
# Let's target all supported files but ensure sort order is numeric if possible, or just string sort which works for 1-5.
files = [f for f in files if f.split('.')[0] in ['1', '2', '3', '4', '5']]

print(f'找到 {len(files)} 個檔案：')
for p in files:
    print(f'  - {p}')

# Merge
merged = fitz.open()
for fname in files:
    fpath = os.path.join(input_dir, fname)
    doc = fitz.open(fpath)
    
    if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
        # Convert image to PDF page
        pdfbytes = doc.convert_to_pdf()
        img_pdf = fitz.open("pdf", pdfbytes)
        merged.insert_pdf(img_pdf)
        print(f'已合併圖片: {fname}')
    else:
        # It's a PDF
        merged.insert_pdf(doc)
        print(f'已合併 PDF: {fname} ({len(doc)} 頁)')
    
    doc.close()

merged.save(output_path)
print(f'\n✅ 合併完成！')
print(f'輸出: {output_path}')
print(f'總頁數: {len(merged)}')
merged.close()
