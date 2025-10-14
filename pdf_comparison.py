"""
Professional PDF Comparison Tool with Batch Folder Processing
Compares all matching PDFs between dev and prod folders
"""

import fitz  # PyMuPDF
import difflib
import os
import json
from html import escape
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import Counter


class PDFComparator:
    """Professional PDF comparison with page-by-page analytics."""
    
    def __init__(self, dev_pdf: str, prod_pdf: str, output_dir: str = "reports"):
        self.dev_pdf = Path(dev_pdf)
        self.prod_pdf = Path(prod_pdf)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.dev_pages = []
        self.prod_pages = []
        self.page_diffs = []
        self.analytics = {}
        
    def extract_text_by_page(self, pdf_path: Path) -> List[str]:
        """Extract text from each page preserving whitespace and layout."""
        pages = []
        
        try:
            with fitz.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf, 1):
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
    
    def compare_pages(self):
        """Compare PDFs page by page and store differences."""
        max_pages = max(len(self.dev_pages), len(self.prod_pages))
        
        for page_num in range(max_pages):
            dev_content = self.dev_pages[page_num] if page_num < len(self.dev_pages) else ""
            prod_content = self.prod_pages[page_num] if page_num < len(self.prod_pages) else ""
            
            dev_lines = dev_content.splitlines()
            prod_lines = prod_content.splitlines()
            
            differ = difflib.Differ()
            diff = list(differ.compare(dev_lines, prod_lines))
            
            self.page_diffs.append({
                'page_num': page_num + 1,
                'dev_lines': dev_lines,
                'prod_lines': prod_lines,
                'diff': diff
            })
    
    def calculate_analytics(self) -> Dict:
        """Calculate comprehensive comparison analytics."""
        
        total_added = 0
        total_removed = 0
        total_changed = 0
        total_unchanged = 0
        
        for page_diff in self.page_diffs:
            diff = page_diff['diff']
            total_added += len([l for l in diff if l.startswith('+ ')])
            total_removed += len([l for l in diff if l.startswith('- ')])
            total_changed += len([l for l in diff if l.startswith('? ')]) // 2
            total_unchanged += len([l for l in diff if l.startswith('  ')])
        
        dev_text = "\n".join(self.dev_pages)
        prod_text = "\n".join(self.prod_pages)
        
        matcher = difflib.SequenceMatcher(None, dev_text, prod_text)
        similarity = matcher.ratio() * 100
        
        dev_chars = len(dev_text)
        prod_chars = len(prod_text)
        dev_words = len(dev_text.split())
        prod_words = len(prod_text.split())
        
        analytics = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'dev_file': self.dev_pdf.name,
            'prod_file': self.prod_pdf.name,
            'dev_size': self.dev_pdf.stat().st_size if self.dev_pdf.exists() else 0,
            'prod_size': self.prod_pdf.stat().st_size if self.prod_pdf.exists() else 0,
            'similarity_percent': round(similarity, 2),
            'difference_percent': round(100 - similarity, 2),
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
        """Generate professional HTML report with page-by-page comparison."""
        
        a = self.analytics
        
        html = f"""<!DOCTYPE html>
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
            <h1>📊 PDF Comparison Report</h1>
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
                    <h3>📄 Dev PDF</h3>
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
                </div>
                
                <div class="file-card">
                    <h3>📄 Prod PDF</h3>
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
        
        <div class="pages-container">"""
        
        for page_data in self.page_diffs:
            page_num = page_data['page_num']
            diff = page_data['diff']
            
            html += f"""
            <div class="page-comparison">
                <div class="page-header">
                    📄 Page {page_num}
                </div>
                <div class="page-content">
                    <div class="page-column">
                        <h3>Dev PDF</h3>
                        <div class="content">"""
            
            if page_num <= len(self.dev_pages) and self.dev_pages[page_num - 1].strip():
                for line in diff:
                    if line.startswith('- '):
                        html += f'<div class="line removed">{escape(line[2:])}</div>'
                    elif line.startswith('? '):
                        continue
                    elif line.startswith('+ '):
                        continue
                    else:
                        content = line[2:] if line.startswith('  ') else line
                        html += f'<div class="line">{escape(content)}</div>'
            else:
                html += '<div class="empty-page">📭 No content on this page</div>'
            
            html += """</div>
                    </div>
                    <div class="page-column">
                        <h3>Prod PDF</h3>
                        <div class="content">"""
            
            if page_num <= len(self.prod_pages) and self.prod_pages[page_num - 1].strip():
                for line in diff:
                    if line.startswith('+ '):
                        html += f'<div class="line added">{escape(line[2:])}</div>'
                    elif line.startswith('? '):
                        continue
                    elif line.startswith('- '):
                        continue
                    else:
                        content = line[2:] if line.startswith('  ') else line
                        html += f'<div class="line">{escape(content)}</div>'
            else:
                html += '<div class="empty-page">📭 No content on this page</div>'
            
            html += """</div>
                    </div>
                </div>
            </div>"""
        
        html += """
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def compare(self) -> Tuple[str, Dict]:
        """Main comparison method - returns report path and analytics."""
        
        print(f"  🔍 Extracting text from Dev PDF...")
        self.dev_pages = self.extract_text_by_page(self.dev_pdf)
        
        print(f"  🔍 Extracting text from Prod PDF...")
        self.prod_pages = self.extract_text_by_page(self.prod_pdf)
        
        if not self.dev_pages and not self.prod_pages:
            print("  ❌ Error: Could not extract text from either PDF")
            return "", {}
        
        print(f"  📄 Dev: {len(self.dev_pages)} pages | Prod: {len(self.prod_pages)} pages")
        
        print(f"  🔄 Comparing pages...")
        self.compare_pages()
        
        print(f"  📈 Calculating analytics...")
        self.analytics = self.calculate_analytics()
        
        print(f"  🎨 Generating HTML report...")
        html_report = self.generate_html_report()
        
        # Save report with sanitized filename
        safe_filename = self.dev_pdf.stem.replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"{safe_filename}_{timestamp}.html"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_report)
        
        # Save analytics as JSON for summary
        analytics_path = self.output_dir / f"{safe_filename}_{timestamp}_analytics.json"
        with open(analytics_path, "w", encoding="utf-8") as f:
            json.dump(self.analytics, f, indent=2)
        
        print(f"  ✅ Report generated: {output_path.name}")
        
        return str(output_path.absolute()), self.analytics


class BatchPDFComparator:
    """Batch process PDFs from dev and prod folders."""
    
    def __init__(self, dev_folder: str = "dev", prod_folder: str = "prod", 
                 output_dir: str = "reports"):
        self.dev_folder = Path(dev_folder)
        self.prod_folder = Path(prod_folder)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.matched_pdfs = []
        self.dev_only_pdfs = []
        self.prod_only_pdfs = []
        self.comparison_results = []
        
    def find_matching_pdfs(self):
        """Find PDFs with matching names in both folders."""
        
        if not self.dev_folder.exists():
            print(f"❌ Dev folder not found: {self.dev_folder}")
            return
        
        if not self.prod_folder.exists():
            print(f"❌ Prod folder not found: {self.prod_folder}")
            return
        
        # Get all PDF files
        dev_pdfs = {f.name: f for f in self.dev_folder.glob("*.pdf")}
        prod_pdfs = {f.name: f for f in self.prod_folder.glob("*.pdf")}
        
        # Find matches
        dev_names = set(dev_pdfs.keys())
        prod_names = set(prod_pdfs.keys())
        
        matched_names = dev_names & prod_names
        self.dev_only_pdfs = sorted(dev_names - prod_names)
        self.prod_only_pdfs = sorted(prod_names - dev_names)
        
        self.matched_pdfs = [(dev_pdfs[name], prod_pdfs[name]) 
                            for name in sorted(matched_names)]
        
        print(f"\n📊 PDF Inventory:")
        print(f"   ✅ Matched PDFs: {len(self.matched_pdfs)}")
        print(f"   📁 Dev only: {len(self.dev_only_pdfs)}")
        print(f"   📁 Prod only: {len(self.prod_only_pdfs)}")
        
        if self.dev_only_pdfs:
            print(f"\n   📋 Files only in Dev folder:")
            for name in self.dev_only_pdfs:
                print(f"      • {name}")
        
        if self.prod_only_pdfs:
            print(f"\n   📋 Files only in Prod folder:")
            for name in self.prod_only_pdfs:
                print(f"      • {name}")
    
    def compare_all(self):
        """Compare all matched PDFs."""
        
        self.find_matching_pdfs()
        
        if not self.matched_pdfs:
            print("\n❌ No matching PDFs found to compare!")
            return
        
        print(f"\n🔄 Starting batch comparison of {len(self.matched_pdfs)} PDF pairs...\n")
        
        for idx, (dev_pdf, prod_pdf) in enumerate(self.matched_pdfs, 1):
            print(f"[{idx}/{len(self.matched_pdfs)}] Comparing: {dev_pdf.name}")
            
            comparator = PDFComparator(
                str(dev_pdf), 
                str(prod_pdf), 
                str(self.output_dir)
            )
            
            report_path, analytics = comparator.compare()
            
            if report_path:
                self.comparison_results.append({
                    'filename': dev_pdf.name,
                    'report_path': report_path,
                    'analytics': analytics
                })
            
            print()
        
        # Generate summary
        print("=" * 80)
        print("📊 BATCH COMPARISON SUMMARY")
        print("=" * 80)
        print(f"\n✅ Successfully compared: {len(self.comparison_results)} PDFs")
        print(f"📁 Reports saved to: {self.output_dir.absolute()}\n")
        
        for result in self.comparison_results:
            a = result['analytics']
            print(f"📄 {result['filename']}")
            print(f"   Similarity: {a['similarity_percent']}% | "
                  f"Added: {a['changes']['added']} | "
                  f"Removed: {a['changes']['removed']} | "
                  f"Modified: {a['changes']['modified']}")
        
        print(f"\n🌐 Now generating master summary report...")
        
        # Auto-generate summary
        from generate_summary import SummaryGenerator
        summary_gen = SummaryGenerator(str(self.output_dir))
        summary_path = summary_gen.generate_summary()
        
        if summary_path:
            print(f"✅ Master summary generated: {summary_path}")


def main():
    """Main entry point for batch comparison."""
    
    print("="*80)
    print("🚀 PDF BATCH COMPARISON TOOL")
    print("="*80)
    
    # Initialize batch comparator
    batch = BatchPDFComparator(
        dev_folder="dev",
        prod_folder="prod",
        output_dir="reports"
    )
    
    # Run comparison
    batch.compare_all()
    
    print("\n" + "="*80)
    print("✅ BATCH COMPARISON COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()