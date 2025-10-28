"""
Professional TXT Comparison Tool with CSV-Based File Mapping
Maps dev and prod files using a CSV configuration file
"""

import difflib
import os
import csv
import json
from html import escape
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Set


class TXTComparator:
    """Professional TXT comparison with line-by-line analytics."""
    
    def __init__(self, dev_txt: str, prod_txt: str, output_dir: str = "reports"):
        self.dev_txt = Path(dev_txt)
        self.prod_txt = Path(prod_txt)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.dev_lines = []
        self.prod_lines = []
        self.diff = []
        self.analytics = {}
        
    def load_file(self, file_path: Path) -> List[str]:
        """Load text file and return lines."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.readlines()
        except Exception as e:
            print(f"❌ Error loading file {file_path}: {e}")
            return []
    
    def compare_files(self):
        """Compare TXT files line by line and store differences."""
        differ = difflib.Differ()
        self.diff = list(differ.compare(self.dev_lines, self.prod_lines))
    
    def calculate_analytics(self) -> Dict:
        """Calculate comprehensive comparison analytics."""
        
        total_added = len([l for l in self.diff if l.startswith('+ ')])
        total_removed = len([l for l in self.diff if l.startswith('- ')])
        total_changed = len([l for l in self.diff if l.startswith('? ')]) // 2
        total_unchanged = len([l for l in self.diff if l.startswith('  ')])
        
        dev_text = "".join(self.dev_lines)
        prod_text = "".join(self.prod_lines)
        
        matcher = difflib.SequenceMatcher(None, dev_text, prod_text)
        similarity = matcher.ratio() * 100
        
        dev_chars = len(dev_text)
        prod_chars = len(prod_text)
        dev_words = len(dev_text.split())
        prod_words = len(prod_text.split())
        
        analytics = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'dev_file': self.dev_txt.name,
            'prod_file': self.prod_txt.name,
            'dev_size': self.dev_txt.stat().st_size if self.dev_txt.exists() else 0,
            'prod_size': self.prod_txt.stat().st_size if self.prod_txt.exists() else 0,
            'similarity_percent': round(similarity, 2),
            'difference_percent': round(100 - similarity, 2),
            'total_lines': {
                'dev': len(self.dev_lines),
                'prod': len(self.prod_lines),
                'max': max(len(self.dev_lines), len(self.prod_lines))
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
        """Generate professional HTML report with left-right page comparison."""
        
        a = self.analytics
        
        html = f"""<!DOCTYPE html>
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
        
        <div class="pages-container">
            <div class="page-comparison">
                <div class="page-header">
                    📄 File Comparison
                </div>
                <div class="page-content">
                    <div class="page-column">
                        <h3>Dev TXT</h3>
                        <div class="content">"""
        
        if self.dev_lines and "".join(self.dev_lines).strip():
            for line in self.diff:
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
            html += '<div class="empty-page">📭 No content in this file</div>'
        
        html += """</div>
                    </div>
                    <div class="page-column">
                        <h3>Prod TXT</h3>
                        <div class="content">"""
        
        if self.prod_lines and "".join(self.prod_lines).strip():
            for line in self.diff:
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
            html += '<div class="empty-page">📭 No content in this file</div>'
        
        html += """</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def compare(self) -> Tuple[str, Dict]:
        """Main comparison workflow."""
        
        print(f"\n{'='*80}")
        print(f"📄 TXT FILE COMPARISON")
        print(f"{'='*80}\n")
        
        print(f"📂 Loading files...")
        print(f"   Dev:  {self.dev_txt}")
        print(f"   Prod: {self.prod_txt}")
        
        self.dev_lines = self.load_file(self.dev_txt)
        self.prod_lines = self.load_file(self.prod_txt)
        
        if not self.dev_lines or not self.prod_lines:
            print("❌ Failed to load one or both files!")
            return "", {}
        
        print(f"   ✅ Dev file: {len(self.dev_lines)} lines loaded")
        print(f"   ✅ Prod file: {len(self.prod_lines)} lines loaded")
        
        print(f"\n🔍 Comparing files...")
        self.compare_files()
        
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
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        with open(analytics_path, "w", encoding="utf-8") as f:
            json.dump(self.analytics, f, indent=2)
        
        print(f"  ✅ Report generated: {output_path.name}")
        
        return str(output_path.absolute()), self.analytics


class BatchTXTComparator:
    """Batch process TXT files using CSV file mapping."""
    
    def __init__(self, csv_file: str = "txt_file_mapping.csv", 
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
        
        print(f"\n🔄 Starting batch comparison of {len(self.file_mappings)} TXT pairs...\n")
        
        for idx, mapping in enumerate(self.file_mappings, 1):
            print(f"[{idx}/{len(self.file_mappings)}] Comparing:")
            print(f"   Dev:  {mapping['dev']}")
            print(f"   Prod: {mapping['prod']}")
            
            comparator = TXTComparator(
                str(mapping['dev_path']), 
                str(mapping['prod_path']), 
                str(self.output_dir)
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
        output_dir="reports/txt"
    )
    
    batch.compare_all()
    
    print("\n" + "="*80)
    print("✅ BATCH COMPARISON COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()