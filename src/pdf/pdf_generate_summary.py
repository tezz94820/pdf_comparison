"""
Optimized Master Summary Report Generator
Combines all individual PDF comparison reports into a single summary
Uses efficient aggregation and batch HTML building
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from html import escape


class SummaryGenerator:
    """Generate master summary from all comparison reports with optimized aggregation."""
    
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
        """Calculate aggregate statistics across all comparisons with optimized aggregation."""
        
        total_files = len(self.analytics_data)
        
        if total_files == 0:
            return {}
        
        # Single pass aggregation - O(n) instead of multiple passes
        aggregate_stats = {
            'total_added': 0,
            'total_removed': 0,
            'total_modified': 0,
            'total_unchanged': 0,
            'total_similarity_sum': 0,
            'total_pages_dev': 0,
            'total_pages_prod': 0,
            'total_chars_dev': 0,
            'total_chars_prod': 0,
            'similarity_percentiles': [],
            'identical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
        }
        
        most_changed_files = []
        least_similar_files = []
        
        # Single pass through all data
        for file_data in self.analytics_data:
            # Aggregate changes
            aggregate_stats['total_added'] += file_data['changes']['added']
            aggregate_stats['total_removed'] += file_data['changes']['removed']
            aggregate_stats['total_modified'] += file_data['changes']['modified']
            aggregate_stats['total_unchanged'] += file_data['changes']['unchanged']
            
            # Aggregate similarity
            similarity = file_data['similarity_percent']
            aggregate_stats['total_similarity_sum'] += similarity
            aggregate_stats['similarity_percentiles'].append(similarity)
            
            # Count by ranges
            if similarity == 100:
                aggregate_stats['identical'] += 1
            elif similarity >= 90:
                aggregate_stats['high'] += 1
            elif similarity >= 70:
                aggregate_stats['medium'] += 1
            else:
                aggregate_stats['low'] += 1
            
            # Aggregate page counts
            aggregate_stats['total_pages_dev'] += file_data['total_pages']['dev']
            aggregate_stats['total_pages_prod'] += file_data['total_pages']['prod']
            
            # Aggregate character counts
            aggregate_stats['total_chars_dev'] += file_data['characters']['dev']
            aggregate_stats['total_chars_prod'] += file_data['characters']['prod']
            
            # Track for top changed files
            total_changes = (file_data['changes']['added'] + 
                           file_data['changes']['removed'] + 
                           file_data['changes']['modified'])
            most_changed_files.append((total_changes, file_data))
            least_similar_files.append((similarity, file_data))
        
        # Calculate average
        avg_similarity = aggregate_stats['total_similarity_sum'] / total_files if total_files > 0 else 0
        
        # Get top 5 by changes and least similar
        most_changed_files.sort(reverse=True)
        least_similar_files.sort()
        
        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_files': total_files,
            'aggregate_changes': {
                'added': aggregate_stats['total_added'],
                'removed': aggregate_stats['total_removed'],
                'modified': aggregate_stats['total_modified'],
                'unchanged': aggregate_stats['total_unchanged'],
                'total': aggregate_stats['total_added'] + aggregate_stats['total_removed'] + aggregate_stats['total_modified']
            },
            'similarity': {
                'average': int(avg_similarity),
                'identical': aggregate_stats['identical'],
                'high': aggregate_stats['high'],
                'medium': aggregate_stats['medium'],
                'low': aggregate_stats['low']
            },
            'pages': {
                'dev': aggregate_stats['total_pages_dev'],
                'prod': aggregate_stats['total_pages_prod']
            },
            'characters': {
                'dev': aggregate_stats['total_chars_dev'],
                'prod': aggregate_stats['total_chars_prod']
            },
            'top_changed_files': [item[1] for item in most_changed_files[:5]],
            'least_similar_files': [item[1] for item in least_similar_files[:5]]
        }
    
    def generate_summary_html(self, stats: Dict) -> str:
        """Generate beautiful HTML summary report using efficient string building."""
        
        # Use list and join for efficient string building
        html_parts = []
        
        html_parts.append(f"""<!DOCTYPE html>
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
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #6c757d;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: 700;
            color: #667eea;
        }}
        
        .stat-subtext {{
            font-size: 0.9em;
            color: #6c757d;
            margin-top: 10px;
        }}
        
        .similarity-distribution {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .similarity-box {{
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .similarity-box.identical {{
            background: #d4edda;
            color: #155724;
        }}
        
        .similarity-box.high {{
            background: #cfe2ff;
            color: #084298;
        }}
        
        .similarity-box.medium {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .similarity-box.low {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .similarity-box-value {{
            font-size: 2em;
            font-weight: 700;
        }}
        
        .similarity-box-label {{
            font-size: 0.9em;
            text-transform: uppercase;
            margin-top: 5px;
        }}
        
        .section {{
            padding: 40px;
            background: white;
            margin-top: 20px;
            border-top: 1px solid #e9ecef;
        }}
        
        .section-heading {{
            font-size: 1.5em;
            font-weight: 700;
            margin-bottom: 20px;
            color: #333;
        }}
        
        .files-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .files-table thead {{
            background: #f8f9fa;
        }}
        
        .files-table th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .files-table td {{
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .files-table tbody tr:hover {{
            background: #f8f9fa;
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
        
        .file-link {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }}
        
        .file-link:hover {{
            text-decoration: underline;
        }}
        
        .change-indicator {{
            display: inline-block;
            margin-right: 10px;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
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
        
        .footer {{
            padding: 20px;
            background: #f8f9fa;
            text-align: center;
            font-size: 0.9em;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <div class="header">
            <h1>📊 PDF Comparison Master Summary</h1>
            <div class="subtitle">Aggregated Analysis of {stats['total_files']} PDF Comparisons</div>
        </div>
        
        <div class="summary-dashboard">
            <h2 class="section-title">📈 Overall Statistics</h2>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Files Compared</div>
                    <div class="stat-value">{stats['total_files']}</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Average Similarity</div>
                    <div class="stat-value">{stats['similarity']['average']}%</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Total Changes</div>
                    <div class="stat-value">{stats['aggregate_changes']['total']:,}</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Total Pages</div>
                    <div class="stat-value">{stats['pages']['dev'] + stats['pages']['prod']:,}</div>
                </div>
            </div>
            
            <h2 class="section-title" style="margin-top: 30px;">🎯 Similarity Distribution</h2>
            
            <div class="similarity-distribution">
                <div class="similarity-box identical">
                    <div class="similarity-box-value">{stats['similarity']['identical']}</div>
                    <div class="similarity-box-label">Identical (100%)</div>
                </div>
                <div class="similarity-box high">
                    <div class="similarity-box-value">{stats['similarity']['high']}</div>
                    <div class="similarity-box-label">High (90-99%)</div>
                </div>
                <div class="similarity-box medium">
                    <div class="similarity-box-value">{stats['similarity']['medium']}</div>
                    <div class="similarity-box-label">Medium (70-89%)</div>
                </div>
                <div class="similarity-box low">
                    <div class="similarity-box-value">{stats['similarity']['low']}</div>
                    <div class="similarity-box-label">Low (&lt;70%)</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-heading">📊 Change Summary</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div style="padding: 20px; background: #d4edda; border-radius: 8px; text-align: center; color: #155724;">
                    <div style="font-size: 2em; font-weight: 700;">➕ {stats['aggregate_changes']['added']:,}</div>
                    <div style="margin-top: 5px;">Lines Added</div>
                </div>
                <div style="padding: 20px; background: #f8d7da; border-radius: 8px; text-align: center; color: #721c24;">
                    <div style="font-size: 2em; font-weight: 700;">➖ {stats['aggregate_changes']['removed']:,}</div>
                    <div style="margin-top: 5px;">Lines Removed</div>
                </div>
                <div style="padding: 20px; background: #fff3cd; border-radius: 8px; text-align: center; color: #856404;">
                    <div style="font-size: 2em; font-weight: 700;">✏️ {stats['aggregate_changes']['modified']:,}</div>
                    <div style="margin-top: 5px;">Lines Modified</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-heading">🚀 Top 5 Files with Most Changes</h2>
            
            <table class="files-table">
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Similarity</th>
                        <th>Added</th>
                        <th>Removed</th>
                        <th>Modified</th>
                        <th>Total</th>
                        <th>Report</th>
                    </tr>
                </thead>
                <tbody>""")
        
        for file_data in stats['top_changed_files']:
            total_changes = (file_data['changes']['added'] + 
                           file_data['changes']['removed'] + 
                           file_data['changes']['modified'])
            
            similarity_badge = 'badge-success'
            if file_data['similarity_percent'] < 70:
                similarity_badge = 'badge-danger'
            elif file_data['similarity_percent'] < 90:
                similarity_badge = 'badge-warning'
            
            html_parts.append(f"""
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
                    </tr>""")
        
        html_parts.append("""
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2 class="section-heading">⚠️ Top 5 Files with Lowest Similarity</h2>
            
            <table class="files-table">
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Similarity</th>
                        <th>Pages (Dev/Prod)</th>
                        <th>Added</th>
                        <th>Removed</th>
                        <th>Modified</th>
                        <th>Report</th>
                    </tr>
                </thead>
                <tbody>""")
        
        for file_data in stats['least_similar_files']:
            similarity_badge = 'badge-danger'
            if file_data['similarity_percent'] >= 90:
                similarity_badge = 'badge-success'
            elif file_data['similarity_percent'] >= 70:
                similarity_badge = 'badge-warning'
            
            html_parts.append(f"""
                    <tr>
                        <td>
                            <div style="font-size: 0.85em; line-height: 1.5;">
                                <div><strong>Dev:</strong> {escape(file_data['dev_file'])}</div>
                                <div><strong>Prod:</strong> {escape(file_data['prod_file'])}</div>
                            </div>
                        </td>
                        <td><span class="badge {similarity_badge}">{file_data['similarity_percent']}%</span></td>
                        <td>{file_data['total_pages']['dev']} / {file_data['total_pages']['prod']}</td>
                        <td><span class="change-indicator change-added">+{file_data['changes']['added']}</span></td>
                        <td><span class="change-indicator change-removed">-{file_data['changes']['removed']}</span></td>
                        <td><span class="change-indicator change-modified">~{file_data['changes']['modified']}</span></td>
                        <td><a href="{file_data['report_file']}" class="file-link">📄 View Report</a></td>
                    </tr>""")
        
        html_parts.append(f"""
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Generated: {stats['timestamp']}</p>
            <p>PDF Summary Generator v2.0 (Optimized)</p>
        </div>
    </div>
</body>
</html>""")
        
        return "".join(html_parts)
    
    def generate_summary(self) -> str:
        """Generate master summary report."""
        
        print("\n" + "="*80)
        print("📊 GENERATING MASTER SUMMARY REPORT (OPTIMIZED)")
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
    print("🚀 MASTER SUMMARY REPORT GENERATOR (OPTIMIZED)")
    print("="*80)
    
    generator = SummaryGenerator(reports_dir="reports/pdf")
    summary_path = generator.generate_summary()
    
    if summary_path:
        print("\n" + "="*80)
        print("✅ SUMMARY GENERATION COMPLETE!")
        print("="*80)
        print(f"\n🌐 Open the summary in your browser:")
        print(f"   file://{summary_path}")


if __name__ == "__main__":
    main()