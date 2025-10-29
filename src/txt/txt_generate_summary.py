"""
Master Summary Report Generator
Combines all individual TXT comparison reports into a single summary
Can be run independently or called from main comparison script
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from html import escape


class SummaryGenerator:
    """Generate master summary from all comparison reports."""
    
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
        
        identical = sum(1 for a in self.analytics_data if a['similarity_percent'] == 100)
        high_similarity = sum(1 for a in self.analytics_data if 90 <= a['similarity_percent'] < 100)
        medium_similarity = sum(1 for a in self.analytics_data if 70 <= a['similarity_percent'] < 90)
        low_similarity = sum(1 for a in self.analytics_data if a['similarity_percent'] < 70)
        
        total_lines_dev = sum(a['total_lines']['dev'] for a in self.analytics_data)
        total_lines_prod = sum(a['total_lines']['prod'] for a in self.analytics_data)
        
        total_chars_dev = sum(a['characters']['dev'] for a in self.analytics_data)
        total_chars_prod = sum(a['characters']['prod'] for a in self.analytics_data)
        
        most_changes = sorted(self.analytics_data, 
                            key=lambda x: x['changes']['added'] + x['changes']['removed'] + x['changes']['modified'],
                            reverse=True)[:5]
        
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
                'average': round(avg_similarity, 2),
                'identical': identical,
                'high': high_similarity,
                'medium': medium_similarity,
                'low': low_similarity
            },
            'lines': {
                'dev': total_lines_dev,
                'prod': total_lines_prod
            },
            'characters': {
                'dev': total_chars_dev,
                'prod': total_chars_prod
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
    <title>Master Summary Report - {stats['timestamp']}</title>
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
            max-width: 1600px;
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
            border-left: 4px solid #667eea;
            transition: transform 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .stat-label {{
            font-size: 0.85em;
            color: #6c757d;
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: 12px;
        }}
        
        .stat-value {{
            font-size: 2.5em;
            color: #667eea;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        
        .stat-detail {{
            font-size: 0.9em;
            color: #6c757d;
            line-height: 1.6;
        }}
        
        .stat-card.high {{
            border-left-color: #28a745;
        }}
        
        .stat-card.high .stat-value {{
            color: #28a745;
        }}
        
        .stat-card.medium {{
            border-left-color: #ffc107;
        }}
        
        .stat-card.medium .stat-value {{
            color: #ffc107;
        }}
        
        .stat-card.low {{
            border-left-color: #dc3545;
        }}
        
        .stat-card.low .stat-value {{
            color: #dc3545;
        }}
        
        .comparison-section {{
            padding: 40px;
        }}
        
        .comparison-title {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 30px;
            font-weight: 700;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
        }}
        
        .change-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .change-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            border: 2px solid #e9ecef;
            text-align: center;
            transition: transform 0.2s;
        }}
        
        .change-card:hover {{
            transform: translateY(-2px);
        }}
        
        .change-icon {{
            font-size: 2.5em;
            margin-bottom: 15px;
        }}
        
        .change-count {{
            font-size: 2.2em;
            font-weight: 700;
            color: #667eea;
            margin: 10px 0;
        }}
        
        .change-card.added {{
            border-color: #28a745;
            background: #f0f8f5;
        }}
        
        .change-card.added .change-count {{
            color: #28a745;
        }}
        
        .change-card.removed {{
            border-color: #dc3545;
            background: #fdf5f5;
        }}
        
        .change-card.removed .change-count {{
            color: #dc3545;
        }}
        
        .change-card.modified {{
            border-color: #ffc107;
            background: #fffbf0;
        }}
        
        .change-card.modified .change-count {{
            color: #ffc107;
        }}
        
        .change-card.unchanged {{
            border-color: #6c757d;
            background: #f5f5f5;
        }}
        
        .change-card.unchanged .change-count {{
            color: #6c757d;
        }}
        
        .change-label {{
            font-size: 0.9em;
            color: #6c757d;
            text-transform: uppercase;
            font-weight: 600;
        }}
        
        .files-table {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow-x: auto;
        }}
        
        .files-table h3 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead {{
            background: #f8f9fa;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 700;
            color: #667eea;
            border-bottom: 2px solid #e9ecef;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 700;
            color: white;
        }}
        
        .badge-success {{
            background: #28a745;
        }}
        
        .badge-warning {{
            background: #ffc107;
            color: #333;
        }}
        
        .badge-danger {{
            background: #dc3545;
        }}
        
        .change-indicator {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
            margin-right: 5px;
        }}
        
        .change-added {{
            background: #d4edda;
            color: #155724;
        }}
        
        .change-removed {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .change-modified {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .file-link {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s;
        }}
        
        .file-link:hover {{
            color: #764ba2;
            text-decoration: underline;
        }}
        
        .similarity-distribution {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        .distribution-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .distribution-item {{
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            background: #f8f9fa;
        }}
        
        .distribution-label {{
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 10px;
        }}
        
        .distribution-count {{
            font-size: 2em;
            font-weight: 700;
            color: #667eea;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 30px 40px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
            border-top: 1px solid #e9ecef;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            .main-container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <div class="header">
            <h1>📊 TXT Comparison Master Summary</h1>
            <div class="subtitle">Comprehensive Analysis Report</div>
        </div>
        
        <div class="summary-dashboard">
            <h2 class="section-title">📈 Key Metrics</h2>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">📁 Files Compared</div>
                    <div class="stat-value">{stats['total_files']}</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">📊 Average Similarity</div>
                    <div class="stat-value">{stats['similarity']['average']}%</div>
                    <div class="stat-detail">Across all compared files</div>
                </div>
                
                <div class="stat-card high">
                    <div class="stat-label">✅ Identical Files</div>
                    <div class="stat-value">{stats['similarity']['identical']}</div>
                    <div class="stat-detail">100% similarity</div>
                </div>
                
                <div class="stat-card high">
                    <div class="stat-label">🟢 High Similarity</div>
                    <div class="stat-value">{stats['similarity']['high']}</div>
                    <div class="stat-detail">90-99% match</div>
                </div>
                
                <div class="stat-card medium">
                    <div class="stat-label">🟡 Medium Similarity</div>
                    <div class="stat-value">{stats['similarity']['medium']}</div>
                    <div class="stat-detail">70-89% match</div>
                </div>
                
                <div class="stat-card low">
                    <div class="stat-label">🔴 Low Similarity</div>
                    <div class="stat-value">{stats['similarity']['low']}</div>
                    <div class="stat-detail">&lt;70% match</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">📝 Total Lines (Dev)</div>
                    <div class="stat-value">{stats['lines']['dev']:,}</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">📝 Total Lines (Prod)</div>
                    <div class="stat-value">{stats['lines']['prod']:,}</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">💾 Total Characters (Dev)</div>
                    <div class="stat-value">{stats['characters']['dev']:,}</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">💾 Total Characters (Prod)</div>
                    <div class="stat-value">{stats['characters']['prod']:,}</div>
                </div>
            </div>
        </div>
        
        <div class="comparison-section">
            <h2 class="comparison-title">🔄 Aggregate Changes</h2>
            
            <div class="change-summary">
                <div class="change-card added">
                    <div class="change-icon">➕</div>
                    <div class="change-label">Added</div>
                    <div class="change-count">{stats['aggregate_changes']['added']}</div>
                </div>
                <div class="change-card removed">
                    <div class="change-icon">➖</div>
                    <div class="change-label">Removed</div>
                    <div class="change-count">{stats['aggregate_changes']['removed']}</div>
                </div>
                <div class="change-card modified">
                    <div class="change-icon">✏️</div>
                    <div class="change-label">Modified</div>
                    <div class="change-count">{stats['aggregate_changes']['modified']}</div>
                </div>
                <div class="change-card unchanged">
                    <div class="change-icon">✓</div>
                    <div class="change-label">Unchanged</div>
                    <div class="change-count">{stats['aggregate_changes']['unchanged']}</div>
                </div>
            </div>
            
            <div class="similarity-distribution">
                <h3>📊 Similarity Distribution</h3>
                <div class="distribution-grid">
                    <div class="distribution-item">
                        <div class="distribution-label">Identical (100%)</div>
                        <div class="distribution-count">{stats['similarity']['identical']}</div>
                    </div>
                    <div class="distribution-item">
                        <div class="distribution-label">High (90-99%)</div>
                        <div class="distribution-count">{stats['similarity']['high']}</div>
                    </div>
                    <div class="distribution-item">
                        <div class="distribution-label">Medium (70-89%)</div>
                        <div class="distribution-count">{stats['similarity']['medium']}</div>
                    </div>
                    <div class="distribution-item">
                        <div class="distribution-label">Low (&lt;70%)</div>
                        <div class="distribution-count">{stats['similarity']['low']}</div>
                    </div>
                </div>
            </div>
            
            <div class="files-table">
                <h3>⚡ Top 5 Files with Most Changes</h3>
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
                    <tbody>
"""
        
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
                            <th>Lines (Dev/Prod)</th>
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
                            <td>{file_data['total_lines']['dev']} / {file_data['total_lines']['prod']}</td>
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
                            <th>Lines</th>
                            <th>Changes</th>
                            <th>Report</th>
                        </tr>
                    </thead>
                    <tbody>"""
        
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
                            <td>{file_data['total_lines']['dev']} / {file_data['total_lines']['prod']}</td>
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
        
        <div class="footer">
            <p>Generated on """ + stats['timestamp'] + """ | TXT Comparison Tool</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def generate_summary(self) -> str:
        """Generate master summary report."""
        
        print("\n" + "="*80)
        print("📊 GENERATING MASTER SUMMARY REPORT")
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
        output_path = self.reports_dir / f"MASTER_SUMMARY_{timestamp}.html"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ Master summary report generated!")
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
    print("🚀 MASTER SUMMARY REPORT GENERATOR")
    print("="*80)
    
    generator = SummaryGenerator(reports_dir="reports/txt")
    summary_path = generator.generate_summary()
    
    if summary_path:
        print("\n" + "="*80)
        print("✅ SUMMARY GENERATION COMPLETE!")
        print("="*80)
        print(f"\n🌐 Open the summary in your browser:")
        print(f"   file://{summary_path}")


if __name__ == "__main__":
    main()