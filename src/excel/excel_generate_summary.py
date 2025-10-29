"""
Master Summary Report Generator for Excel Comparisons
Combines all individual Excel comparison reports into a single summary
Can be run independently or called from main comparison script
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from html import escape


class ExcelSummaryGenerator:
    """Generate master summary from all Excel comparison reports."""
    
    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(reports_dir)
        self.analytics_data = []
        
    def load_analytics(self) -> List[Dict]:
        """Load all analytics JSON files from reports directory."""
        
        if not self.reports_dir.exists():
            print(f"❌ Reports directory not found: {self.reports_dir}")
            return []
        
        json_files = sorted(self.reports_dir.glob("*_analytics.json"))
        
        if not json_files:
            print(f"❌ No analytics files found in {self.reports_dir}")
            return []
        
        print(f"📂 Found {len(json_files)} analytics files")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Add the report filename
                    html_file = json_file.stem.replace('_analytics', '') + '.html'
                    data['report_file'] = html_file
                    self.analytics_data.append(data)
                    print(f"   ✅ Loaded: {json_file.name}")
            except Exception as e:
                print(f"   ❌ Error loading {json_file.name}: {e}")
        
        return self.analytics_data
    
    def calculate_aggregate_stats(self) -> Dict:
        """Calculate aggregate statistics across all comparisons."""
        
        total_files = len(self.analytics_data)
        
        if total_files == 0:
            return {}
        
        total_added = sum(a['changes']['added'] for a in self.analytics_data)
        total_removed = sum(a['changes']['removed'] for a in self.analytics_data)
        total_modified = sum(a['changes']['modified'] for a in self.analytics_data)
        total_unchanged = sum(a['changes']['unchanged'] for a in self.analytics_data)
        
        avg_similarity_ratio = sum(a.get('similarity_ratio', a['similarity_percent'] / 100) for a in self.analytics_data) / total_files
        avg_similarity = avg_similarity_ratio * 100
        
        # Count files by similarity ranges
        identical = sum(1 for a in self.analytics_data if a['similarity_percent'] == 100)
        high_similarity = sum(1 for a in self.analytics_data if 90 <= a['similarity_percent'] < 100)
        medium_similarity = sum(1 for a in self.analytics_data if 70 <= a['similarity_percent'] < 90)
        low_similarity = sum(1 for a in self.analytics_data if a['similarity_percent'] < 70)
        
        total_sheets_dev = sum(a['total_sheets']['dev'] for a in self.analytics_data)
        total_sheets_prod = sum(a['total_sheets']['prod'] for a in self.analytics_data)
        
        total_cells_dev = sum(a['cells']['dev'] for a in self.analytics_data)
        total_cells_prod = sum(a['cells']['prod'] for a in self.analytics_data)
        
        # Find files with most changes
        most_changes = sorted(self.analytics_data, 
                            key=lambda x: x['changes']['added'] + x['changes']['removed'] + x['changes']['modified'],
                            reverse=True)[:5]
        
        # Find files with least similarity
        least_similar = sorted(self.analytics_data, 
                              key=lambda x: x['similarity_percent'])[:5]
        
        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_files': total_files,
            'aggregate_changes': {
                'added': total_added,
                'removed': total_removed,
                'modified': total_modified,
                'unchanged': total_unchanged,
                'total': total_added + total_removed + total_modified
            },
            'similarity': {
                'average': int(avg_similarity),
                'identical': identical,
                'high': high_similarity,
                'medium': medium_similarity,
                'low': low_similarity
            },
            'sheets': {
                'dev': total_sheets_dev,
                'prod': total_sheets_prod
            },
            'cells': {
                'dev': total_cells_dev,
                'prod': total_cells_prod
            },
            'top_changed_files': most_changes,
            'least_similar_files': least_similar
        }
    
    def generate_summary_html(self, stats: Dict) -> str:
        """Generate beautiful HTML summary report."""
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Master Excel Summary Report - {stats['timestamp']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
            padding: 20px;
            color: #333;
            min-height: 100vh;
        }}
        
        .main-container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            margin-bottom: 40px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
            color: white;
            padding: 50px 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.95;
        }}
        
        .summary-dashboard {{
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .section-title {{
            text-align: center;
            margin-bottom: 30px;
            color: #333;
            font-size: 2em;
            font-weight: 700;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #2ecc71;
            transition: transform 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.15);
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: 700;
            color: #2ecc71;
        }}
        
        .stat-subvalue {{
            font-size: 0.95em;
            color: #6c757d;
            margin-top: 8px;
        }}
        
        .similarity-breakdown {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 40px;
        }}
        
        .similarity-breakdown h3 {{
            color: #2ecc71;
            margin-bottom: 20px;
            font-size: 1.5em;
        }}
        
        .similarity-bars {{
            display: grid;
            gap: 15px;
        }}
        
        .similarity-bar-item {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .bar-label {{
            min-width: 150px;
            font-weight: 600;
            color: #333;
        }}
        
        .bar-container {{
            flex: 1;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }}
        
        .bar-fill {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.9em;
            transition: width 0.5s ease;
        }}
        
        .bar-count {{
            min-width: 50px;
            text-align: right;
            font-weight: 600;
            color: #2ecc71;
        }}
        
        .files-table {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 40px;
            overflow-x: auto;
        }}
        
        .files-table h3 {{
            color: #2ecc71;
            margin-bottom: 20px;
            font-size: 1.5em;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead {{
            background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
            color: white;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95em;
        }}
        
        tbody tr {{
            border-bottom: 1px solid #e9ecef;
            transition: background 0.2s;
        }}
        
        tbody tr:hover {{
            background: #f8f9fa;
        }}
        
        td {{
            padding: 15px;
        }}
        
        .file-link {{
            color: #2ecc71;
            text-decoration: none;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .file-link:hover {{
            text-decoration: underline;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
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
        
        .change-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.9em;
        }}
        
        .change-added {{
            color: #28a745;
        }}
        
        .change-removed {{
            color: #dc3545;
        }}
        
        .change-modified {{
            color: #ffc107;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .stat-value {{
                font-size: 2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <div class="header">
            <h1>📊 Master Excel Summary Report</h1>
            <div class="subtitle">Batch Excel Comparison Analysis • {stats['timestamp']}</div>
        </div>
        
        <div class="summary-dashboard">
            <h2 class="section-title">📈 Aggregate Statistics</h2>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Files Compared</div>
                    <div class="stat-value">{stats['total_files']}</div>
                    <div class="stat-subvalue">Excel pairs analyzed</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Average Similarity</div>
                    <div class="stat-value">{stats['similarity']['average']}%</div>
                    <div class="stat-subvalue">Across all files</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Total Changes</div>
                    <div class="stat-value" style="color: #ffc107;">{stats['aggregate_changes']['total']:,}</div>
                    <div class="stat-subvalue">Rows modified in total</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Rows Added</div>
                    <div class="stat-value" style="color: #28a745;">{stats['aggregate_changes']['added']:,}</div>
                    <div class="stat-subvalue">New content</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Rows Removed</div>
                    <div class="stat-value" style="color: #dc3545;">{stats['aggregate_changes']['removed']:,}</div>
                    <div class="stat-subvalue">Deleted content</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Rows Modified</div>
                    <div class="stat-value" style="color: #17a2b8;">{stats['aggregate_changes']['modified']:,}</div>
                    <div class="stat-subvalue">Changed content</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Total Sheets (Dev)</div>
                    <div class="stat-value" style="color: #6c757d;">{stats['sheets']['dev']:,}</div>
                    <div class="stat-subvalue">All dev files combined</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Total Sheets (Prod)</div>
                    <div class="stat-value" style="color: #6c757d;">{stats['sheets']['prod']:,}</div>
                    <div class="stat-subvalue">All prod files combined</div>
                </div>
            </div>
            
            <div class="similarity-breakdown">
                <h3>🎯 Similarity Distribution</h3>
                <div class="similarity-bars">
                    <div class="similarity-bar-item">
                        <div class="bar-label">Identical (100%)</div>
                        <div class="bar-container">
                            <div class="bar-fill" style="width: {(stats['similarity']['identical'] / stats['total_files'] * 100) if stats['total_files'] > 0 else 0}%; background: linear-gradient(90deg, #28a745, #20c997);">
                                {stats['similarity']['identical']} files
                            </div>
                        </div>
                        <div class="bar-count">{stats['similarity']['identical']}</div>
                    </div>
                    
                    <div class="similarity-bar-item">
                        <div class="bar-label">High (90-99%)</div>
                        <div class="bar-container">
                            <div class="bar-fill" style="width: {(stats['similarity']['high'] / stats['total_files'] * 100) if stats['total_files'] > 0 else 0}%; background: linear-gradient(90deg, #20c997, #17a2b8);">
                                {stats['similarity']['high']} files
                            </div>
                        </div>
                        <div class="bar-count">{stats['similarity']['high']}</div>
                    </div>
                    
                    <div class="similarity-bar-item">
                        <div class="bar-label">Medium (70-89%)</div>
                        <div class="bar-container">
                            <div class="bar-fill" style="width: {(stats['similarity']['medium'] / stats['total_files'] * 100) if stats['total_files'] > 0 else 0}%; background: linear-gradient(90deg, #ffc107, #fd7e14);">
                                {stats['similarity']['medium']} files
                            </div>
                        </div>
                        <div class="bar-count">{stats['similarity']['medium']}</div>
                    </div>
                    
                    <div class="similarity-bar-item">
                        <div class="bar-label">Low (&lt;70%)</div>
                        <div class="bar-container">
                            <div class="bar-fill" style="width: {(stats['similarity']['low'] / stats['total_files'] * 100) if stats['total_files'] > 0 else 0}%; background: linear-gradient(90deg, #dc3545, #c82333);">
                                {stats['similarity']['low']} files
                            </div>
                        </div>
                        <div class="bar-count">{stats['similarity']['low']}</div>
                    </div>
                </div>
            </div>
            
            <div class="files-table">
                <h3>🔥 Top 5 Files with Most Changes</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Filename</th>
                            <th>Similarity</th>
                            <th>Added</th>
                            <th>Removed</th>
                            <th>Modified</th>
                            <th>Total Changes</th>
                            <th>Report</th>
                        </tr>
                    </thead>
                    <tbody>"""
        
        for file_data in stats['top_changed_files']:
            total_changes = (file_data['changes']['added'] + 
                           file_data['changes']['removed'] + 
                           file_data['changes']['modified'])
            
            similarity_badge = 'badge-success'
            if file_data['similarity_percent'] < 70:
                similarity_badge = 'badge-danger'
            elif file_data['similarity_percent'] < 90:
                similarity_badge = 'badge-warning'
            
            html += f"""
                        <tr>
                            <td>
                                <div style="font-size: 0.85em; line-height: 1.5;">
                                    <div><strong>Dev:</strong> {escape(file_data['dev_file'])}</div>
                                    <div><strong>Prod:</strong> {escape(file_data['prod_file'])}</div>
                                </div>
                            </td>
                            <td><span class="badge {similarity_badge}">{file_data['similarity_percent']}%</span></td>
                            <td><span class="change-indicator change-added">+{file_data['changes']['added']}</span></td>
                            <td><span class="change-indicator change-removed">-{file_data['changes']['removed']}</span></td>
                            <td><span class="change-indicator change-modified">~{file_data['changes']['modified']}</span></td>
                            <td><strong>{total_changes:,}</strong></td>
                            <td><a href="{file_data['report_file']}" class="file-link">📄 View Report</a></td>
                        </tr>"""
        
        html += """
                    </tbody>
                </table>
            </div>
            
            <div class="files-table">
                <h3>⚠️ Top 5 Files with Lowest Similarity</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Filename</th>
                            <th>Similarity</th>
                            <th>Sheets (Dev/Prod)</th>
                            <th>Added</th>
                            <th>Removed</th>
                            <th>Modified</th>
                            <th>Report</th>
                        </tr>
                    </thead>
                    <tbody>"""
        
        for file_data in stats['least_similar_files']:
            similarity_badge = 'badge-danger'
            if file_data['similarity_percent'] >= 90:
                similarity_badge = 'badge-success'
            elif file_data['similarity_percent'] >= 70:
                similarity_badge = 'badge-warning'
            
            html += f"""
                        <tr>
                            <td>
                                <div style="font-size: 0.85em; line-height: 1.5;">
                                    <div><strong>Dev:</strong> {escape(file_data['dev_file'])}</div>
                                    <div><strong>Prod:</strong> {escape(file_data['prod_file'])}</div>
                                </div>
                            </td>
                            <td><span class="badge {similarity_badge}">{file_data['similarity_percent']}%</span></td>
                            <td>{file_data['total_sheets']['dev']} / {file_data['total_sheets']['prod']}</td>
                            <td><span class="change-indicator change-added">+{file_data['changes']['added']}</span></td>
                            <td><span class="change-indicator change-removed">-{file_data['changes']['removed']}</span></td>
                            <td><span class="change-indicator change-modified">~{file_data['changes']['modified']}</span></td>
                            <td><a href="{file_data['report_file']}" class="file-link">📄 View Report</a></td>
                        </tr>"""
        
        html += """
                    </tbody>
                </table>
            </div>
            
            <div class="files-table">
                <h3>📋 All Comparison Results</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Filename</th>
                            <th>Similarity</th>
                            <th>Sheets</th>
                            <th>Changes</th>
                            <th>Report</th>
                        </tr>
                    </thead>
                    <tbody>"""
        
        # Sort all files by filename
        sorted_data = sorted(self.analytics_data, key=lambda x: x['dev_file'])
        
        for file_data in sorted_data:
            total_changes = (file_data['changes']['added'] + 
                           file_data['changes']['removed'] + 
                           file_data['changes']['modified'])
            
            similarity_badge = 'badge-success'
            if file_data['similarity_percent'] < 70:
                similarity_badge = 'badge-danger'
            elif file_data['similarity_percent'] < 90:
                similarity_badge = 'badge-warning'
            
            html += f"""
                        <tr>
                            <td>
                                <div style="font-size: 0.85em; line-height: 1.5;">
                                    <div><strong>Dev:</strong> {escape(file_data['dev_file'])}</div>
                                    <div><strong>Prod:</strong> {escape(file_data['prod_file'])}</div>
                                </div>
                            </td>
                            <td><span class="badge {similarity_badge}">{file_data['similarity_percent']}%</span></td>
                            <td>{file_data['total_sheets']['dev']} / {file_data['total_sheets']['prod']}</td>
                            <td>
                                <span class="change-indicator change-added">+{file_data['changes']['added']}</span>
                                <span class="change-indicator change-removed">-{file_data['changes']['removed']}</span>
                                <span class="change-indicator change-modified">~{file_data['changes']['modified']}</span>
                            </td>
                            <td><a href="{file_data['report_file']}" class="file-link">📄 View Report</a></td>
                        </tr>"""
        
        html += """
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def generate_summary(self) -> str:
        """Generate master summary report."""
        
        print("\n" + "="*80)
        print("📊 GENERATING MASTER EXCEL SUMMARY REPORT")
        print("="*80 + "\n")
        
        analytics = self.load_analytics()
        
        if not analytics:
            print("❌ No analytics data found. Nothing to summarize.")
            return ""
        
        print(f"\n📈 Calculating aggregate statistics...")
        stats = self.calculate_aggregate_stats()
        
        print(f"🎨 Generating HTML summary...")
        html = self.generate_summary_html(stats)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.reports_dir / f"MASTER_EXCEL_SUMMARY_{timestamp}.html"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ Master Excel summary report generated!")
        print(f"📁 Location: {output_path.absolute()}")
        print(f"\n📊 Summary Statistics:")
        print(f"   • Total files compared: {stats['total_files']}")
        print(f"   • Average similarity: {stats['similarity']['average']}%")
        print(f"   • Total changes: {stats['aggregate_changes']['total']:,}")
        print(f"   • Identical files: {stats['similarity']['identical']}")
        print(f"   • High similarity (90-99%): {stats['similarity']['high']}")
        print(f"   • Medium similarity (70-89%): {stats['similarity']['medium']}")
        print(f"   • Low similarity (<70%): {stats['similarity']['low']}")
        
        return str(output_path.absolute())


def main():
    """Main entry point for standalone summary generation."""
    
    print("="*80)
    print("🚀 MASTER EXCEL SUMMARY REPORT GENERATOR")
    print("="*80)
    
    generator = ExcelSummaryGenerator(reports_dir="reports")
    summary_path = generator.generate_summary()
    
    if summary_path:
        print("\n" + "="*80)
        print("✅ SUMMARY GENERATION COMPLETE!")
        print("="*80)
        print(f"\n🌐 Open the summary in your browser:")
        print(f"   file://{summary_path}")


if __name__ == "__main__":
    main()