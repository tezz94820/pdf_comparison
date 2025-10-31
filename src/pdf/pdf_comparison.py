"""
Optimized Professional PDF Comparison Tool with CSV-Based File Mapping
- Resolves O(n²) string concatenation issues
- Implements efficient page-level comparisons
- Uses batch HTML generation with chunking
- Optimized memory management for large PDFs
"""

import fitz  # PyMuPDF
import difflib
import os
import csv
import json
import hashlib
from html import escape
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import Counter, OrderedDict


class PDFComparator:
    """Optimized PDF comparison with efficient analytics and chunked reporting."""
    
    def __init__(self, dev_pdf: str, prod_pdf: str, output_dir: str = "reports", 
                 chunk_size: int = 50, store_full_diffs: bool = True):
        """
        Initialize PDF comparator with optimization options.
        
        Args:
            dev_pdf: Path to development PDF
            prod_pdf: Path to production PDF
            output_dir: Output directory for reports
            chunk_size: Number of pages per HTML chunk (default 50)
            store_full_diffs: Whether to store full diffs in memory (default False)
        """
        self.dev_pdf = Path(dev_pdf)
        self.prod_pdf = Path(prod_pdf)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.dev_pages = []
        self.prod_pages = []
        self.page_stats = []  # Store only stats, not full diffs
        self.analytics = {}
        self.chunk_size = chunk_size
        self.store_full_diffs = store_full_diffs
        
    def extract_text_by_page(self, pdf_path: Path) -> List[str]:
        """Extract text from each page preserving whitespace and layout."""
        pages = []
        total_pages = 0
        
        try:
            with fitz.open(pdf_path) as pdf:
                total_pages = len(pdf)
                print(f"   📖 Total pages in PDF: {total_pages}")
                
                for page_num, page in enumerate(pdf, 1):
                    if page_num % 500 == 0:
                        print(f"      Extracting text: {page_num}/{total_pages} pages...")
                    
                    blocks = page.get_text("dict")["blocks"]
                    
                    page_content = []
                    for block in blocks:
                        if "lines" in block:
                            for line in block["lines"]:
                                line_text = ""
                                for span in line["spans"]:
                                    line_text += span["text"]
                                if line_text.strip():
                                    page_content.append(line_text)
                    
                    pages.append("\n".join(page_content) if page_content else "")
                        
        except Exception as e:
            print(f"❌ Error extracting text from {pdf_path}: {e}")
            return []
        
        return pages
    
    def calculate_page_similarity(self, dev_lines: List[str], prod_lines: List[str]) -> float:
        """Calculate similarity for a single page using SequenceMatcher."""
        if not dev_lines and not prod_lines:
            return 100.0
        
        dev_text = "\n".join(dev_lines)
        prod_text = "\n".join(prod_lines)
        
        matcher = difflib.SequenceMatcher(None, dev_text, prod_text)
        return matcher.ratio() * 100
    
    def count_changes(self, diff_lines: List[str]) -> Tuple[int, int, int, int]:
        """Efficiently count changes by scanning diff once."""
        added = removed = changed = unchanged = 0
        i = 0
        
        while i < len(diff_lines):
            line = diff_lines[i]
            if line.startswith('+ '):
                added += 1
            elif line.startswith('- '):
                removed += 1
            elif line.startswith('? '):
                # Changed lines come in pairs (? for both sides)
                if i + 1 < len(diff_lines) and diff_lines[i + 1].startswith('? '):
                    changed += 1
                    i += 1
            elif line.startswith('  '):
                unchanged += 1
            i += 1
        
        return added, removed, changed, unchanged
    
    def compare_pages(self):
        """Compare PDFs page by page with optimized memory usage."""
        max_pages = max(len(self.dev_pages), len(self.prod_pages))
        
        print(f"   🔄 Comparing {max_pages} pages...")
        
        for page_num in range(max_pages):
            if (page_num + 1) % 500 == 0:
                print(f"      Comparing: {page_num + 1}/{max_pages} pages...")
            
            dev_content = self.dev_pages[page_num] if page_num < len(self.dev_pages) else ""
            prod_content = self.prod_pages[page_num] if page_num < len(self.prod_pages) else ""
            
            dev_lines = dev_content.splitlines()
            prod_lines = prod_content.splitlines()
            
            # Calculate page-level metrics
            similarity = self.calculate_page_similarity(dev_lines, prod_lines)
            
            # Generate diff for change counting and potential display
            differ = difflib.Differ()
            diff = list(differ.compare(dev_lines, prod_lines))
            
            # Count changes efficiently
            added, removed, changed, unchanged = self.count_changes(diff)
            
            # Store only essential page statistics (not full diffs unless needed)
            page_stat = {
                'page_num': page_num + 1,
                'similarity': similarity,
                'changes': {
                    'added': added,
                    'removed': removed,
                    'modified': changed,
                    'unchanged': unchanged
                },
                'dev_lines_count': len(dev_lines),
                'prod_lines_count': len(prod_lines),
            }
            
            # Optionally store full diff for detailed comparison
            if self.store_full_diffs:
                page_stat['diff'] = diff
                page_stat['dev_lines'] = dev_lines
                page_stat['prod_lines'] = prod_lines
            
            self.page_stats.append(page_stat)
    
    def calculate_analytics(self) -> Dict:
        """Calculate comprehensive comparison analytics with optimized page-level similarity."""
        
        print(f"   📈 Calculating analytics...")
        
        total_added = sum(p['changes']['added'] for p in self.page_stats)
        total_removed = sum(p['changes']['removed'] for p in self.page_stats)
        total_changed = sum(p['changes']['modified'] for p in self.page_stats)
        total_unchanged = sum(p['changes']['unchanged'] for p in self.page_stats)
        
        # Calculate AVERAGE similarity from page-level data (O(n) instead of O(n²))
        # This avoids comparing the entire concatenated text
        page_similarities = [p['similarity'] for p in self.page_stats]
        
        if page_similarities:
            avg_similarity = sum(page_similarities) / len(page_similarities)
            min_similarity = min(page_similarities)
            max_similarity = max(page_similarities)
        else:
            avg_similarity = min_similarity = max_similarity = 0
        
        dev_chars = sum(len(self.dev_pages[i]) for i in range(len(self.dev_pages)))
        prod_chars = sum(len(self.prod_pages[i]) for i in range(len(self.prod_pages)))
        
        dev_words = sum(len(self.dev_pages[i].split()) for i in range(len(self.dev_pages)))
        prod_words = sum(len(self.prod_pages[i].split()) for i in range(len(self.prod_pages)))
        
        analytics = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'dev_file': self.dev_pdf.name,
            'prod_file': self.prod_pdf.name,
            'dev_size': self.dev_pdf.stat().st_size if self.dev_pdf.exists() else 0,
            'prod_size': self.prod_pdf.stat().st_size if self.prod_pdf.exists() else 0,
            'similarity_ratio': avg_similarity / 100,
            'similarity_percent': int(avg_similarity),
            'difference_percent': int(100 - avg_similarity),
            'similarity_stats': {
                'average': int(avg_similarity),
                'minimum': int(min_similarity),
                'maximum': int(max_similarity),
            },
            'total_pages': {
                'dev': len(self.dev_pages),
                'prod': len(self.prod_pages),
                'max': max(len(self.dev_pages), len(self.prod_pages))
            },
            'changes': {
                'added': total_added,
                'removed': total_removed,
                'modified': total_changed,
                'unchanged': total_unchanged
            },
            'characters': {
                'dev': dev_chars,
                'prod': prod_chars,
                'diff': abs(dev_chars - prod_chars)
            },
            'words': {
                'dev': dev_words,
                'prod': prod_words,
                'diff': abs(dev_words - prod_words)
            }
        }
        
        return analytics
    
    def generate_html_report(self) -> str:
        """Generate professional HTML report with efficient string building."""
        
        a = self.analytics
        
        # Use list and join instead of string concatenation
        html_parts = []
        
        html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Comparison Report - {a['dev_file']} vs {a['prod_file']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
            min-height: 100vh;
        }}
        
        .main-container {{
            max-width: 1800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            margin-bottom: 40px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.95;
        }}
        
        .analytics-dashboard {{
            padding: 40px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .analytics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #667eea;
            transition: transform 0.2s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .metric-label {{
            font-size: 0.9em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        
        .metric-value {{
            font-size: 2em;
            font-weight: 700;
            color: #667eea;
        }}
        
        .metric-subvalue {{
            font-size: 0.9em;
            color: #6c757d;
            margin-top: 5px;
        }}
        
        .similarity-bar {{
            width: 100%;
            height: 40px;
            background: #e9ecef;
            border-radius: 20px;
            overflow: hidden;
            position: relative;
            margin: 20px 0;
        }}
        
        .similarity-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            width: {a['similarity_percent']}%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 0.9em;
        }}
        
        .stats-grid-2 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .stat-box {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }}
        
        .stat-box-label {{
            font-size: 0.85em;
            color: #6c757d;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        
        .stat-box-value {{
            font-size: 1.5em;
            font-weight: 700;
            color: #333;
        }}
        
        .comparison-section {{
            padding: 40px;
            background: white;
        }}
        
        .section-title {{
            font-size: 1.5em;
            font-weight: 700;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }}
        
        .changes-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        
        .change-stat {{
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            background: #f8f9fa;
        }}
        
        .change-stat.added {{
            background: #d4edda;
            color: #155724;
        }}
        
        .change-stat.removed {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .change-stat.modified {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .change-stat-value {{
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 5px;
        }}
        
        .change-stat-label {{
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        
        .page-summary {{
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .page-summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .page-stat {{
            padding: 15px;
            background: white;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }}
        
        .page-stat-label {{
            font-size: 0.85em;
            color: #6c757d;
        }}
        
        .page-stat-value {{
            font-size: 1.3em;
            font-weight: 700;
            color: #333;
            margin-top: 5px;
        }}
        
        .badge {{
            display: inline-block;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}
        
        .badge-warning {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .badge-danger {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .note {{
            padding: 15px;
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            border-radius: 4px;
            margin-top: 20px;
            font-size: 0.9em;
            color: #1565c0;
        }}
        
        .footer {{
            padding: 20px;
            background: #f8f9fa;
            text-align: center;
            font-size: 0.85em;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <div class="header">
            <h1>📊 PDF Comparison Report</h1>
            <div class="subtitle">Comprehensive Analysis of {a['dev_file']} vs {a['prod_file']}</div>
        </div>
        
        <div class="analytics-dashboard">
            <div class="analytics-grid">
                <div class="metric-card">
                    <div class="metric-label">📈 Overall Similarity</div>
                    <div class="metric-value">{a['similarity_percent']}%</div>
                    <div class="similarity-bar">
                        <div class="similarity-fill"></div>
                    </div>
                    <div class="metric-subvalue">Difference: {a['difference_percent']}%</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">📄 Total Pages</div>
                    <div class="metric-value">{a['total_pages']['max']}</div>
                    <div class="metric-subvalue">Dev: {a['total_pages']['dev']} | Prod: {a['total_pages']['prod']}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">💾 File Size</div>
                    <div class="metric-value">{a['dev_size'] / 1024 / 1024:.2f} MB</div>
                    <div class="metric-subvalue">Prod: {a['prod_size'] / 1024 / 1024:.2f} MB</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">✏️ Total Changes</div>
                    <div class="metric-value">{a['changes']['added'] + a['changes']['removed'] + a['changes']['modified']:,}</div>
                    <div class="metric-subvalue">Added: {a['changes']['added']} | Removed: {a['changes']['removed']}</div>
                </div>
            </div>
        </div>
        
        <div class="comparison-section">
            <div class="section-title">📝 Similarity Analysis</div>
            
            <div class="stats-grid-2">
                <div class="stat-box">
                    <div class="stat-box-label">Average Similarity</div>
                    <div class="stat-box-value">{a['similarity_stats']['average']}%</div>
                </div>
                <div class="stat-box">
                    <div class="stat-box-label">Highest Similarity</div>
                    <div class="stat-box-value">{a['similarity_stats']['maximum']}%</div>
                </div>
                <div class="stat-box">
                    <div class="stat-box-label">Lowest Similarity</div>
                    <div class="stat-box-value">{a['similarity_stats']['minimum']}%</div>
                </div>
            </div>
            
            <div class="section-title" style="margin-top: 30px;">📊 Change Summary</div>
            
            <div class="changes-summary">
                <div class="change-stat added">
                    <div class="change-stat-value">➕ {a['changes']['added']:,}</div>
                    <div class="change-stat-label">Lines Added</div>
                </div>
                <div class="change-stat removed">
                    <div class="change-stat-value">➖ {a['changes']['removed']:,}</div>
                    <div class="change-stat-label">Lines Removed</div>
                </div>
                <div class="change-stat modified">
                    <div class="change-stat-value">✏️ {a['changes']['modified']:,}</div>
                    <div class="change-stat-label">Lines Modified</div>
                </div>
                <div class="change-stat">
                    <div class="change-stat-value">✓ {a['changes']['unchanged']:,}</div>
                    <div class="change-stat-label">Lines Unchanged</div>
                </div>
            </div>
            
            <div class="section-title" style="margin-top: 30px;">📏 Content Analysis</div>
            
            <div class="page-summary-grid">
                <div class="page-stat">
                    <div class="page-stat-label">Dev Characters</div>
                    <div class="page-stat-value">{a['characters']['dev']:,}</div>
                </div>
                <div class="page-stat">
                    <div class="page-stat-label">Prod Characters</div>
                    <div class="page-stat-value">{a['characters']['prod']:,}</div>
                </div>
                <div class="page-stat">
                    <div class="page-stat-label">Character Difference</div>
                    <div class="page-stat-value">{a['characters']['diff']:,}</div>
                </div>
                <div class="page-stat">
                    <div class="page-stat-label">Dev Words</div>
                    <div class="page-stat-value">{a['words']['dev']:,}</div>
                </div>
                <div class="page-stat">
                    <div class="page-stat-label">Prod Words</div>
                    <div class="page-stat-value">{a['words']['prod']:,}</div>
                </div>
                <div class="page-stat">
                    <div class="page-stat-label">Word Difference</div>
                    <div class="page-stat-value">{a['words']['diff']:,}</div>
                </div>
            </div>
            
            <div class="note">
                <strong>📌 Note:</strong> This report uses optimized analytics calculation with page-level similarity aggregation.
                The similarity percentage is calculated as an average of page-level similarities for improved performance on large PDFs.
            </div>
        </div>
        
        <div class="comparison-section">
            <div class="section-title">📄 Page-by-Page Comparison</div>""")
        
        # Add page-by-page comparisons if full diffs are stored
        if self.store_full_diffs:
            for page_data in self.page_stats:
                if 'diff' not in page_data:
                    continue
                
                page_num = page_data['page_num']
                diff = page_data['diff']
                
                html_parts.append(f"""
            <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #667eea;">
                <div style="font-size: 1.2em; font-weight: 700; margin-bottom: 15px; color: #333;">
                    📄 Page {page_num} <span style="color: #667eea;">(Similarity: {int(page_data['similarity'])}%)</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <h4 style="color: #667eea; margin-bottom: 10px;">📝 Dev PDF</h4>
                        <div style="background: white; padding: 10px; border-radius: 4px; max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 0.9em;">""")
                
                for line in diff:
                    if line.startswith('- '):
                        html_parts.append(f'<div style="background: #f8d7da; color: #721c24; padding: 2px 5px; margin: 1px 0; border-radius: 2px;">- {escape(line[2:])}</div>')
                    elif line.startswith('  '):
                        content = line[2:]
                        html_parts.append(f'<div style="padding: 2px 5px; margin: 1px 0;">{escape(content)}</div>')
                
                html_parts.append("""
                        </div>
                    </div>
                    <div>
                        <h4 style="color: #667eea; margin-bottom: 10px;">📝 Prod PDF</h4>
                        <div style="background: white; padding: 10px; border-radius: 4px; max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 0.9em;">""")
                
                for line in diff:
                    if line.startswith('+ '):
                        html_parts.append(f'<div style="background: #d4edda; color: #155724; padding: 2px 5px; margin: 1px 0; border-radius: 2px;">+ {escape(line[2:])}</div>')
                    elif line.startswith('  '):
                        content = line[2:]
                        html_parts.append(f'<div style="padding: 2px 5px; margin: 1px 0;">{escape(content)}</div>')
                
                html_parts.append("""
                        </div>
                    </div>
                </div>
            </div>""")
        else:
            html_parts.append("""
            <div style="padding: 20px; background: #e7f3ff; border-left: 4px solid #2196F3; border-radius: 4px; color: #1565c0;">
                <strong>ℹ️ Note:</strong> Page-by-page content not available. To enable it, use: <code>PDFComparator(..., store_full_diffs=True)</code>
            </div>""")
        
        html_parts.append("""
        </div>
        
        <div class="footer">
            <p>Generated: {a['timestamp']}</p>
            <p>PDF Comparison Tool v2.0 (Optimized)</p>
        </div>
    </div>
</body>
</html>""")
        
        return "".join(html_parts)
    
    def generate_detailed_report(self) -> str:
        """Generate detailed page-by-page report only if needed."""
        
        if not self.store_full_diffs:
            print("   ℹ️  Detailed page-by-page report not available (store_full_diffs=False)")
            return ""
        
        html_parts = []
        html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Detailed Comparison Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: monospace; background: #f5f5f5; padding: 20px; }
        .page-diff { background: white; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .page-header { background: #667eea; color: white; padding: 15px; font-weight: bold; }
        .page-content { padding: 15px; max-height: 600px; overflow-y: auto; }
        .line { margin: 2px 0; padding: 2px 5px; font-size: 0.9em; }
        .line.added { background: #d4edda; color: #155724; }
        .line.removed { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
<h1>📄 Detailed Page-by-Page Comparison</h1>
""")
        
        for page_data in self.page_stats:
            if 'diff' not in page_data:
                continue
            
            page_num = page_data['page_num']
            diff = page_data['diff']
            
            html_parts.append(f"""
<div class="page-diff">
    <div class="page-header">Page {page_num} (Similarity: {int(page_data['similarity'])}%)</div>
    <div class="page-content">""")
            
            for line in diff:
                if line.startswith('- '):
                    html_parts.append(f'<div class="line removed">{escape(line[2:])}</div>')
                elif line.startswith('+ '):
                    html_parts.append(f'<div class="line added">{escape(line[2:])}</div>')
            
            html_parts.append("</div></div>")
        
        html_parts.append("</body></html>")
        return "".join(html_parts)
    
    def compare(self) -> Tuple[str, Dict]:
        """Main comparison workflow - returns (report_path, analytics)."""
        
        print(f"\n{'='*80}")
        print(f"🚀 PDF COMPARISON")
        print(f"{'='*80}\n")
        
        print(f"📂 Loading files:")
        print(f"   Dev:  {self.dev_pdf.name}")
        print(f"   Prod: {self.prod_pdf.name}\n")
        
        print(f"✂️  Extracting text...")
        self.dev_pages = self.extract_text_by_page(self.dev_pdf)
        self.prod_pages = self.extract_text_by_page(self.prod_pdf)
        
        if not self.dev_pages and not self.prod_pages:
            print("  ❌ Error: Could not extract text from either PDF")
            return "", {}
        
        print(f"  ✅ Dev: {len(self.dev_pages)} pages | Prod: {len(self.prod_pages)} pages\n")
        
        self.compare_pages()
        print(f"  ✅ Page comparison complete\n")
        
        self.analytics = self.calculate_analytics()
        print(f"  ✅ Analytics calculated\n")
        
        print(f"🎨 Generating reports...")
        html_report = self.generate_html_report()
        
        # Save main report
        safe_filename = f"{self.dev_pdf.stem}_vs_{self.prod_pdf.stem}".replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"{safe_filename}_{timestamp}.html"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_report)
        
        print(f"  ✅ Report generated: {output_path.name}")
        
        # Save analytics as JSON for summary
        analytics_path = self.output_dir / f"{safe_filename}_{timestamp}_analytics.json"
        with open(analytics_path, "w", encoding="utf-8") as f:
            json.dump(self.analytics, f, indent=2)
        
        print(f"  ✅ Analytics saved: {analytics_path.name}")
        
        return str(output_path.absolute()), self.analytics


class BatchPDFComparator:
    """Batch process PDFs using CSV file mapping with optimized handling."""
    
    def __init__(self, csv_file: str = "pdf_file_mapping.csv", 
                 dev_folder: str = "dev", 
                 prod_folder: str = "prod", 
                 output_dir: str = "reports"):
        
        self.csv_file = Path(csv_file)
        self.dev_folder = Path(dev_folder)
        self.prod_folder = Path(prod_folder)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.file_mappings = []
        self.missing_files = []
        self.comparison_results = []
        
    def load_csv_mappings(self) -> bool:
        """Load file mappings from CSV file."""
        
        if not self.csv_file.exists():
            print(f"❌ CSV file not found: {self.csv_file}")
            print(f"   Please create a CSV file with columns: Sr.No, Dev Filename, Prod Filename")
            return False
        
        print(f"📋 Reading CSV file: {self.csv_file}")
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                if reader.fieldnames is None:
                    print("❌ CSV file is empty")
                    return False
                
                fieldnames = [col.strip().lower() for col in reader.fieldnames]
                
                dev_col = None
                prod_col = None
                
                for col in fieldnames:
                    if 'dev' in col and 'filename' in col:
                        dev_col = reader.fieldnames[fieldnames.index(col)]
                    elif 'prod' in col and 'filename' in col:
                        prod_col = reader.fieldnames[fieldnames.index(col)]
                
                if not dev_col or not prod_col:
                    print("❌ CSV must have 'Dev Filename' and 'Prod Filename' columns")
                    print(f"   Found columns: {', '.join(reader.fieldnames)}")
                    return False
                
                row_count = 0
                for row in reader:
                    dev_filename = row[dev_col].strip()
                    prod_filename = row[prod_col].strip()
                    
                    if dev_filename and prod_filename:
                        self.file_mappings.append({
                            'dev': dev_filename,
                            'prod': prod_filename
                        })
                        row_count += 1
                
                print(f"   ✅ Loaded {row_count} file mappings")
                return True
                
        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")
            return False
    
    def validate_files(self):
        """Validate that all files in CSV exist in their respective folders."""
        
        print(f"\n🔍 Validating file existence...")
        
        valid_mappings = []
        
        for mapping in self.file_mappings:
            dev_path = self.dev_folder / mapping['dev']
            prod_path = self.prod_folder / mapping['prod']
            
            dev_exists = dev_path.exists()
            prod_exists = prod_path.exists()
            
            if dev_exists and prod_exists:
                valid_mappings.append({
                    'dev': mapping['dev'],
                    'prod': mapping['prod'],
                    'dev_path': dev_path,
                    'prod_path': prod_path
                })
            else:
                error_msg = []
                if not dev_exists:
                    error_msg.append(f"Dev file missing: {mapping['dev']}")
                if not prod_exists:
                    error_msg.append(f"Prod file missing: {mapping['prod']}")
                
                self.missing_files.append({
                    'dev': mapping['dev'],
                    'prod': mapping['prod'],
                    'error': ' | '.join(error_msg)
                })
        
        self.file_mappings = valid_mappings
        
        print(f"   ✅ Valid file pairs: {len(valid_mappings)}")
        if self.missing_files:
            print(f"   ⚠️  Missing/Invalid: {len(self.missing_files)}")
            for missing in self.missing_files:
                print(f"      ❌ {missing['error']}")
    
    def compare_all(self):
        """Compare all PDF pairs from CSV mapping."""
        
        if not self.load_csv_mappings():
            return
        
        if not self.file_mappings:
            print("\n❌ No file mappings found in CSV!")
            return
        
        self.validate_files()
        
        if not self.file_mappings:
            print("\n❌ No valid file pairs to compare!")
            return
        
        print(f"\n🔄 Starting batch comparison of {len(self.file_mappings)} PDF pairs...\n")
        
        for idx, mapping in enumerate(self.file_mappings, 1):
            print(f"[{idx}/{len(self.file_mappings)}] Comparing:")
            print(f"   Dev:  {mapping['dev']}")
            print(f"   Prod: {mapping['prod']}")
            
            comparator = PDFComparator(
                str(mapping['dev_path']), 
                str(mapping['prod_path']), 
                str(self.output_dir),
                store_full_diffs=True  # Enable to show page-by-page content in reports
            )
            
            report_path, analytics = comparator.compare()
            
            if report_path:
                self.comparison_results.append({
                    'dev_filename': mapping['dev'],
                    'prod_filename': mapping['prod'],
                    'report_path': report_path,
                    'analytics': analytics
                })
            
            print()
        
        # Generate summary
        print("=" * 80)
        print("📊 BATCH COMPARISON SUMMARY")
        print("=" * 80)
        print(f"\n✅ Successfully compared: {len(self.comparison_results)} PDF pairs")
        print(f"📁 Reports saved to: {self.output_dir.absolute()}\n")
        
        for result in self.comparison_results:
            a = result['analytics']
            print(f"📄 {result['dev_filename']} ↔ {result['prod_filename']}")
            print(f"   Similarity: {a['similarity_percent']}% | "
                  f"Added: {a['changes']['added']} | "
                  f"Removed: {a['changes']['removed']} | "
                  f"Modified: {a['changes']['modified']}")
        
        if self.missing_files:
            print(f"\n⚠️  Skipped {len(self.missing_files)} pairs due to missing files")
        
        print(f"\n🌐 Now generating master summary report...")
        
        # Auto-generate summary
        from pdf_generate_summary_optimized import SummaryGenerator
        summary_gen = SummaryGenerator(str(self.output_dir))
        summary_path = summary_gen.generate_summary()
        
        if summary_path:
            print(f"✅ Master summary generated: {summary_path}")


def main():
    """Main entry point for batch comparison."""
    
    print("="*80)
    print("🚀 PDF BATCH COMPARISON TOOL (CSV-Based) - OPTIMIZED VERSION")
    print("="*80)
    
    batch = BatchPDFComparator(
        csv_file="input/mappings/pdf_file_mapping.csv",
        dev_folder="input/dev/pdf",
        prod_folder="input/prod/pdf",
        output_dir="reports/pdf"
    )
    
    batch.compare_all()
    
    print("\n" + "="*80)
    print("✅ BATCH COMPARISON COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()