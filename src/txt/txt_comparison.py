"""
Professional TXT Comparison Tool with CSV-Based File Mapping
Maps dev and prod files using a CSV configuration file
Divides TXT files into pages for memory-efficient comparison
"""

import difflib
import os
import csv
import json
from html import escape
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Set
import gc


class TXTComparator:
    """Professional TXT comparison with page-by-page analytics."""
    
    def __init__(self, dev_txt: str, prod_txt: str, output_dir: str = "reports", page_lines: int = 500):
        self.dev_txt = Path(dev_txt)
        self.prod_txt = Path(prod_txt)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.page_lines = page_lines  # Lines per page
        
        self.dev_page_count = 0
        self.prod_page_count = 0
        self.page_diffs = []
        self.analytics = {}
        
    def load_file_by_pages(self, file_path: Path) -> List[List[str]]:
        """Load text file and divide into pages."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
            
            # Divide lines into pages
            pages = []
            for i in range(0, len(all_lines), self.page_lines):
                page = all_lines[i:i + self.page_lines]
                pages.append(page)
            
            total_pages = len(pages)
            print(f"      Loaded {len(all_lines)} lines divided into {total_pages} pages")
            return pages
            
        except Exception as e:
            print(f"❌ Error loading file {file_path}: {e}")
            return []
    
    def compare_pages_streaming(self, dev_pages: List[List[str]], prod_pages: List[List[str]]):
        """Compare TXT files page by page with streaming analytics calculation."""
        max_pages = max(len(dev_pages), len(prod_pages))
        
        # Initialize counters for incremental analytics
        total_added = 0
        total_removed = 0
        total_changed = 0
        total_unchanged = 0
        
        # Incremental similarity calculation
        matching_chars = 0
        total_chars = 0
        
        print(f"      Comparing {max_pages} pages...", end='', flush=True)
        
        for page_num in range(max_pages):
            dev_page_lines = dev_pages[page_num] if page_num < len(dev_pages) else []
            prod_page_lines = prod_pages[page_num] if page_num < len(prod_pages) else []
            
            # Compare lines
            differ = difflib.Differ()
            diff = list(differ.compare(dev_page_lines, prod_page_lines))
            
            # Count changes for this page
            page_added = len([l for l in diff if l.startswith('+ ')])
            page_removed = len([l for l in diff if l.startswith('- ')])
            page_changed = len([l for l in diff if l.startswith('? ')]) // 2
            page_unchanged = len([l for l in diff if l.startswith('  ')])
            
            total_added += page_added
            total_removed += page_removed
            total_changed += page_changed
            total_unchanged += page_unchanged
            
            # Calculate page-level similarity for incremental average
            dev_content = "".join(dev_page_lines)
            prod_content = "".join(prod_page_lines)
            page_total = len(dev_content) + len(prod_content)
            
            if page_total > 0:
                matcher = difflib.SequenceMatcher(None, dev_content, prod_content)
                matching_chars += matcher.ratio() * page_total
                total_chars += page_total
            
            self.page_diffs.append({
                'page_num': page_num + 1,
                'dev_lines': dev_page_lines,
                'prod_lines': prod_page_lines,
                'diff': diff
            })
            
            # Progress indicator
            if (page_num + 1) % 10 == 0:
                print(f"\r      Comparing {max_pages} pages... {page_num + 1}/{max_pages}", end='', flush=True)
            
            # Clear memory periodically
            if (page_num + 1) % 100 == 0:
                gc.collect()
        
        print(f"\r      Comparing {max_pages} pages... Done!     ")
        
        # Store pre-calculated metrics
        self._precalc_changes = {
            'added': total_added,
            'removed': total_removed,
            'modified': total_changed,
            'unchanged': total_unchanged
        }
        
        # Calculate average similarity from page-level similarities
        self._precalc_similarity_ratio = matching_chars / total_chars if total_chars > 0 else 1.0
        
        # Pre-calculate character and word counts
        dev_total_chars = sum(len("".join(page_diff['dev_lines'])) for page_diff in self.page_diffs)
        prod_total_chars = sum(len("".join(page_diff['prod_lines'])) for page_diff in self.page_diffs)
        
        # Estimate word counts by sampling
        dev_words = sum(len("".join(page_diff['dev_lines']).split()) for page_diff in self.page_diffs[::10])
        prod_words = sum(len("".join(page_diff['prod_lines']).split()) for page_diff in self.page_diffs[::10])
        
        # Scale up the word count based on sampling ratio
        sampling_ratio = len(self.page_diffs) / max(len(self.page_diffs[::10]), 1)
        dev_words = int(dev_words * sampling_ratio)
        prod_words = int(prod_words * sampling_ratio)
        
        self._precalc_dev_chars = dev_total_chars
        self._precalc_prod_chars = prod_total_chars
        self._precalc_dev_words = dev_words
        self._precalc_prod_words = prod_words
    
    def calculate_analytics(self) -> Dict:
        """Calculate comprehensive comparison analytics using pre-calculated values."""
        
        # Use pre-calculated values
        total_added = self._precalc_changes['added']
        total_removed = self._precalc_changes['removed']
        total_changed = self._precalc_changes['modified']
        total_unchanged = self._precalc_changes['unchanged']
        
        similarity_ratio = self._precalc_similarity_ratio
        similarity = similarity_ratio * 100
        
        dev_chars = self._precalc_dev_chars
        prod_chars = self._precalc_prod_chars
        dev_words = self._precalc_dev_words
        prod_words = self._precalc_prod_words
        
        # Calculate total lines from pages
        dev_total_lines = sum(len(page_diff['dev_lines']) for page_diff in self.page_diffs)
        prod_total_lines = sum(len(page_diff['prod_lines']) for page_diff in self.page_diffs)
        
        analytics = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'dev_file': self.dev_txt.name,
            'prod_file': self.prod_txt.name,
            'dev_size': self.dev_txt.stat().st_size if self.dev_txt.exists() else 0,
            'prod_size': self.prod_txt.stat().st_size if self.prod_txt.exists() else 0,
            'similarity_ratio': similarity_ratio,
            'similarity_percent': int(similarity),
            'difference_percent': int(100 - similarity),
            'total_pages': {
                'dev': self.dev_page_count,
                'prod': self.prod_page_count,
                'max': max(self.dev_page_count, self.prod_page_count)
            },
            'total_lines': {
                'dev': dev_total_lines,
                'prod': prod_total_lines,
                'max': max(dev_total_lines, prod_total_lines)
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
        """Generate professional HTML report with page-by-page comparison."""
        
        a = self.analytics
        
        # Build HTML in parts for memory efficiency
        html_parts = []
        
        html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TXT Comparison Report - {a['dev_file']} vs {a['prod_file']}</title>
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
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            transition: width 1s ease;
        }}
        
        .legend {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 30px 0;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }}
        
        .legend-added {{ background: #d4edda; }}
        .legend-removed {{ background: #f8d7da; }}
        .legend-changed {{ background: #fff3cd; }}
        
        .file-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }}
        
        .file-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        .file-card h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.2em;
        }}
        
        .file-detail {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .file-detail:last-child {{
            border-bottom: none;
        }}
        
        .file-label {{
            color: #6c757d;
        }}
        
        .file-value {{
            font-weight: 600;
            color: #333;
        }}
        
        .pages-container {{
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .page-comparison {{
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 40px;
            overflow: hidden;
            border: 2px solid #e9ecef;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .page-comparison:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.15);
        }}
        
        .page-comparison:last-child {{
            margin-bottom: 0;
        }}
        
        .page-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            font-size: 1.3em;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .page-content {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
        }}
        
        .page-column {{
            padding: 30px;
            background: #ffffff;
        }}
        
        .page-column:first-child {{
            border-right: 2px solid #e9ecef;
            background: #fafbfc;
        }}
        
        .page-column h3 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.2em;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
            position: sticky;
            top: 0;
            background: inherit;
            z-index: 5;
        }}
        
        .content {{
            font-family: 'Courier New', 'Consolas', monospace;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .line {{
            padding: 6px 10px;
            margin: 2px 0;
            border-radius: 4px;
            transition: all 0.15s;
        }}
        
        .line:hover {{
            opacity: 0.85;
        }}
        
        .added {{
            background-color: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
            padding-left: 12px;
        }}
        
        .removed {{
            background-color: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
            padding-left: 12px;
        }}
        
        .changed {{
            background-color: #fff3cd;
            color: #856404;
            border-left: 4px solid #ffc107;
            padding-left: 12px;
        }}
        
        .empty-page {{
            color: #6c757d;
            font-style: italic;
            padding: 40px 20px;
            text-align: center;
            background: #f8f9fa;
            border-radius: 8px;
            border: 2px dashed #dee2e6;
        }}
        
        @media (max-width: 1200px) {{
            .page-content {{
                grid-template-columns: 1fr;
            }}
            
            .page-column:first-child {{
                border-right: none;
                border-bottom: 2px solid #e9ecef;
            }}
            
            .analytics-grid {{
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            }}
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .main-container {{
                box-shadow: none;
            }}
            
            .page-comparison {{
                page-break-inside: avoid;
                margin-bottom: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <div class="header">
            <h1>📊 TXT Comparison Report</h1>
            <div class="subtitle">{a['dev_file']} vs {a['prod_file']} • {a['timestamp']}</div>
        </div>
        
        <div class="analytics-dashboard">
            <h2 style="text-align: center; margin-bottom: 30px; color: #333; font-size: 1.8em;">
                📈 Analytics Dashboard
            </h2>
            
            <div class="analytics-grid">
                <div class="metric-card">
                    <div class="metric-label">Similarity Score</div>
                    <div class="metric-value">{a['similarity_percent']}%</div>
                    <div class="metric-subvalue">{a['difference_percent']}% different</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Total Pages</div>
                    <div class="metric-value" style="color: #6c757d;">{a['total_pages']['max']}</div>
                    <div class="metric-subvalue">Dev: {a['total_pages']['dev']} | Prod: {a['total_pages']['prod']}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Total Lines</div>
                    <div class="metric-value" style="color: #6c757d;">{a['total_lines']['max']}</div>
                    <div class="metric-subvalue">Dev: {a['total_lines']['dev']} | Prod: {a['total_lines']['prod']}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Lines Added</div>
                    <div class="metric-value" style="color: #28a745;">{a['changes']['added']}</div>
                    <div class="metric-subvalue">New content in Prod</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Lines Removed</div>
                    <div class="metric-value" style="color: #dc3545;">{a['changes']['removed']}</div>
                    <div class="metric-subvalue">Removed from Dev</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Lines Modified</div>
                    <div class="metric-value" style="color: #ffc107;">{a['changes']['modified']}</div>
                    <div class="metric-subvalue">Content changes</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Character Count (Dev)</div>
                    <div class="metric-value" style="color: #17a2b8;">{a['characters']['dev']:,}</div>
                    <div class="metric-subvalue">{a['words']['dev']:,} words</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Character Count (Prod)</div>
                    <div class="metric-value" style="color: #17a2b8;">{a['characters']['prod']:,}</div>
                    <div class="metric-subvalue">{a['words']['prod']:,} words</div>
                </div>
            </div>
            
            <div class="similarity-bar">
                <div class="similarity-fill" style="width: {a['similarity_percent']}%">
                    {a['similarity_percent']}% Match
                </div>
            </div>
            
            <div class="file-info">
                <div class="file-card">
                    <h3>📄 Dev TXT</h3>
                    <div class="file-detail">
                        <span class="file-label">Filename:</span>
                        <span class="file-value">{a['dev_file']}</span>
                    </div>
                    <div class="file-detail">
                        <span class="file-label">File Size:</span>
                        <span class="file-value">{a['dev_size'] / 1024:.2f} KB</span>
                    </div>
                    <div class="file-detail">
                        <span class="file-label">Pages:</span>
                        <span class="file-value">{a['total_pages']['dev']}</span>
                    </div>
                    <div class="file-detail">
                        <span class="file-label">Lines:</span>
                        <span class="file-value">{a['total_lines']['dev']}</span>
                    </div>
                </div>
                
                <div class="file-card">
                    <h3>📄 Prod TXT</h3>
                    <div class="file-detail">
                        <span class="file-label">Filename:</span>
                        <span class="file-value">{a['prod_file']}</span>
                    </div>
                    <div class="file-detail">
                        <span class="file-label">File Size:</span>
                        <span class="file-value">{a['prod_size'] / 1024:.2f} KB</span>
                    </div>
                    <div class="file-detail">
                        <span class="file-label">Pages:</span>
                        <span class="file-value">{a['total_pages']['prod']}</span>
                    </div>
                    <div class="file-detail">
                        <span class="file-label">Lines:</span>
                        <span class="file-value">{a['total_lines']['prod']}</span>
                    </div>
                </div>
            </div>
            
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color legend-added"></div>
                    <span><strong>Added:</strong> {a['changes']['added']} lines</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color legend-removed"></div>
                    <span><strong>Removed:</strong> {a['changes']['removed']} lines</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color legend-changed"></div>
                    <span><strong>Modified:</strong> {a['changes']['modified']} lines</span>
                </div>
            </div>
        </div>
        
        <div class="pages-container">""")
        
        # Generate page comparisons in chunks
        print(f"      Generating HTML report...", end='', flush=True)
        
        for idx, page_data in enumerate(self.page_diffs):
            page_num = page_data['page_num']
            diff = page_data['diff']
            
            page_html = f"""
            <div class="page-comparison">
                <div class="page-header">
                    📄 Page {page_num}
                </div>
                <div class="page-content">
                    <div class="page-column">
                        <h3>Dev TXT</h3>
                        <div class="content">"""
            
            if page_num <= self.dev_page_count and any(line.strip() for line in page_data['dev_lines']):
                for line in diff:
                    if line.startswith('- '):
                        page_html += f'<div class="line removed">{escape(line[2:])}</div>'
                    elif line.startswith('? '):
                        continue
                    elif line.startswith('+ '):
                        continue
                    else:
                        content = line[2:] if line.startswith('  ') else line
                        page_html += f'<div class="line">{escape(content)}</div>'
            else:
                page_html += '<div class="empty-page">🔭 No content on this page</div>'
            
            page_html += """</div>
                    </div>
                    <div class="page-column">
                        <h3>Prod TXT</h3>
                        <div class="content">"""
            
            if page_num <= self.prod_page_count and any(line.strip() for line in page_data['prod_lines']):
                for line in diff:
                    if line.startswith('+ '):
                        page_html += f'<div class="line added">{escape(line[2:])}</div>'
                    elif line.startswith('? '):
                        continue
                    elif line.startswith('- '):
                        continue
                    else:
                        content = line[2:] if line.startswith('  ') else line
                        page_html += f'<div class="line">{escape(content)}</div>'
            else:
                page_html += '<div class="empty-page">🔭 No content on this page</div>'
            
            page_html += """</div>
                    </div>
                </div>
            </div>"""
            
            html_parts.append(page_html)
            
            # Progress indicator
            if (idx + 1) % 10 == 0:
                print(f"\r      Generating HTML report... {idx + 1}/{len(self.page_diffs)}", end='', flush=True)
        
        print(f"\r      Generating HTML report... Done!     ")
        
        html_parts.append("""
        </div>
    </div>
</body>
</html>""")
        
        return ''.join(html_parts)
    
    def compare(self) -> Tuple[str, Dict]:
        """Main comparison workflow."""
        
        print(f"\n{'='*80}")
        print(f"📄 TXT FILE COMPARISON")
        print(f"{'='*80}\n")
        
        print(f"📂 Loading files...")
        print(f"   Dev:  {self.dev_txt}")
        print(f"   Prod: {self.prod_txt}")
        
        print(f"  📖 Extracting text from Dev TXT (page size: {self.page_lines} lines)...")
        dev_pages = self.load_file_by_pages(self.dev_txt)
        self.dev_page_count = len(dev_pages)
        
        print(f"  📖 Extracting text from Prod TXT (page size: {self.page_lines} lines)...")
        prod_pages = self.load_file_by_pages(self.prod_txt)
        self.prod_page_count = len(prod_pages)
        
        if not dev_pages and not prod_pages:
            print("❌ Failed to load one or both files!")
            return "", {}
        
        print(f"  ✅ Dev: {self.dev_page_count} pages | Prod: {self.prod_page_count} pages")
        
        print(f"\n🔍 Comparing files...")
        self.compare_pages_streaming(dev_pages, prod_pages)
        
        # Clear pages from memory
        del dev_pages
        del prod_pages
        gc.collect()
        
        print(f"📊 Calculating analytics...")
        self.analytics = self.calculate_analytics()
        
        a = self.analytics
        print(f"   ✅ Similarity: {a['similarity_percent']}%")
        print(f"   ✅ Added lines: {a['changes']['added']}")
        print(f"   ✅ Removed lines: {a['changes']['removed']}")
        print(f"   ✅ Modified lines: {a['changes']['modified']}")
        
        print(f"\n🎨 Generating HTML report...")
        html = self.generate_html_report()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{self.dev_txt.stem}_vs_{self.prod_txt.stem}_{timestamp}"
        
        output_path = self.output_dir / f"{base_name}.html"
        analytics_path = self.output_dir / f"{base_name}_analytics.json"
        
        print(f"      Writing report to disk...", end='', flush=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\r      Writing report to disk... Done!     ")
        
        with open(analytics_path, "w", encoding="utf-8") as f:
            json.dump(self.analytics, f, indent=2)
        
        print(f"  ✅ Report generated: {output_path.name}")
        
        return str(output_path.absolute()), self.analytics


class BatchTXTComparator:
    """Batch process TXT files using CSV file mapping."""
    
    def __init__(self, csv_file: str = "txt_file_mapping.csv", 
                 dev_folder: str = "dev", 
                 prod_folder: str = "prod", 
                 output_dir: str = "reports",
                 page_lines: int = 500):
        
        self.csv_file = Path(csv_file)
        self.dev_folder = Path(dev_folder)
        self.prod_folder = Path(prod_folder)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.page_lines = page_lines
        
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
        """Compare all TXT pairs from CSV mapping."""
        
        if not self.load_csv_mappings():
            return
        
        if not self.file_mappings:
            print("\n❌ No file mappings found in CSV!")
            return
        
        self.validate_files()
        
        if not self.file_mappings:
            print("\n❌ No valid file pairs to compare!")
            return
        
        print(f"\n📄 Starting batch comparison of {len(self.file_mappings)} TXT pairs...\n")
        
        for idx, mapping in enumerate(self.file_mappings, 1):
            print(f"[{idx}/{len(self.file_mappings)}] Comparing:")
            print(f"   Dev:  {mapping['dev']}")
            print(f"   Prod: {mapping['prod']}")
            
            comparator = TXTComparator(
                str(mapping['dev_path']), 
                str(mapping['prod_path']), 
                str(self.output_dir),
                page_lines=self.page_lines
            )
            
            report_path, analytics = comparator.compare()
            
            if report_path:
                self.comparison_results.append({
                    'dev_filename': mapping['dev'],
                    'prod_filename': mapping['prod'],
                    'report_path': report_path,
                    'analytics': analytics
                })
            
            # Clear memory between comparisons
            del comparator
            gc.collect()
            
            print()
        
        print("=" * 80)
        print("📊 BATCH COMPARISON SUMMARY")
        print("=" * 80)
        print(f"\n✅ Successfully compared: {len(self.comparison_results)} TXT pairs")
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
        
        from txt_generate_summary import SummaryGenerator
        summary_gen = SummaryGenerator(str(self.output_dir))
        summary_path = summary_gen.generate_summary()
        
        if summary_path:
            print(f"✅ Master summary generated: {summary_path}")


def main():
    """Main entry point for batch comparison."""
    
    print("="*80)
    print("🚀 TXT BATCH COMPARISON TOOL (CSV-Based)")
    print("="*80)
    
    batch = BatchTXTComparator(
        csv_file="input/mappings/txt_file_mapping.csv",
        dev_folder="input/dev/txt",
        prod_folder="input/prod/txt",
        output_dir="reports/txt",
        page_lines=80  # 80 lines per page
    )
    
    batch.compare_all()
    
    print("\n" + "="*80)
    print("✅ BATCH COMPARISON COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()