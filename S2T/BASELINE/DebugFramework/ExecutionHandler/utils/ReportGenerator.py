import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

	
current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

sys.path.append(parent_dir)


from ExecutionHandler.Configurations import (DragonConfiguration, LinuxConfiguration, 
											 ConfigurationMapping, TestConfiguration, 
											 SystemToTesterConfig, TestResult, ContentType,
											 TestTarget, VoltageType, TestType, TestStatus)

from ExecutionHandler.utils.DebugLogger import debug_log, DebugLogger

class FrameworkReportGenerator:
    """Generate HTML reports for external stakeholder consumption"""
    
    def __init__(self, results: List[TestResult], test_type: str, config: TestConfiguration):
        self.results = results
        self.test_type = test_type
        self.config = config
        self.timestamp = datetime.now()
    
    def generate_html_report(self, output_path: str) -> str:
        """Generate comprehensive HTML report"""
        debug_log(f"Generating HTML report: {output_path}", 1, "REPORT")
        
        html_content = self._create_html_content()
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            debug_log(f"HTML report generated successfully: {output_path}", 1, "REPORT")
            return output_path
        except Exception as e:
            debug_log(f"Failed to generate HTML report: {e}", 3, "REPORT")
            raise
    
    def generate_json_summary(self, output_path: str) -> str:
        """Generate JSON summary for external processing"""
        debug_log(f"Generating JSON summary: {output_path}", 1, "REPORT")
        
        summary_data = self._create_summary_data()
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, default=str)
            debug_log(f"JSON summary generated successfully: {output_path}", 1, "REPORT")
            return output_path
        except Exception as e:
            debug_log(f"Failed to generate JSON summary: {e}", 3, "REPORT")
            raise
    
    def _create_html_content(self) -> str:
        """Create HTML content for the report"""
        summary_data = self._create_summary_data()
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Execution Report - {self.config.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background-color: #ecf0f1; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #2c3e50; }}
        .summary-card .value {{ font-size: 24px; font-weight: bold; color: #27ae60; }}
        .results-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .results-table th, .results-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .results-table th {{ background-color: #34495e; color: white; }}
        .status-pass {{ background-color: #d5f4e6; color: #27ae60; }}
        .status-fail {{ background-color: #fadbd8; color: #e74c3c; }}
        .status-cancelled {{ background-color: #fdeaa7; color: #f39c12; }}
        .config-section {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Test Execution Report</h1>
            <p><strong>Test Name:</strong> {self.config.name}</p>
            <p><strong>Strategy:</strong> {self.test_type}</p>
            <p><strong>Generated:</strong> {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{summary_data['total_tests']}</div>
            </div>
            <div class="summary-card">
                <h3>Success Rate</h3>
                <div class="value">{summary_data['success_rate']:.1f}%</div>
            </div>
            <div class="summary-card">
                <h3>Pass Count</h3>
                <div class="value" style="color: #27ae60;">{summary_data['status_counts'].get('PASS', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Fail Count</h3>
                <div class="value" style="color: #e74c3c;">{summary_data['status_counts'].get('FAIL', 0)}</div>
            </div>
        </div>
        
        <div class="config-section">
            <h2>Test Configuration</h2>
            {self._generate_config_html()}
        </div>
        
        <h2>Test Results</h2>
        <table class="results-table">
            <thead>
                <tr>
                    <th>Iteration</th>
                    <th>Status</th>
                    <th>Name</th>
                    <th>Scratchpad</th>
                    <th>Seed</th>
                    <th>Log File</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_results_table_html()}
            </tbody>
        </table>
        
        <div class="footer">
            <p>Generated by Debug Framework v2.0 | {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def _generate_config_html(self) -> str:
        """Generate HTML for configuration section"""
        config_items = [
            ("Visual ID", self.config.visual),
            ("QDF", self.config.qdf),
            ("Target", self.config.target.value if hasattr(self.config.target, 'value') else str(self.config.target)),
            ("Content", self.config.content.value if hasattr(self.config.content, 'value') else str(self.config.content)),
            ("Core Frequency", f"{self.config.freq_ia} MHz" if self.config.freq_ia else "Default"),
            ("Mesh Frequency", f"{self.config.freq_cfc} MHz" if self.config.freq_cfc else "Default"),
            ("Core Voltage", f"{self.config.volt_IA} V" if self.config.volt_IA else "Default"),
            ("Mesh Voltage", f"{self.config.volt_CFC} V" if self.config.volt_CFC else "Default"),
        ]
        
        html = "<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px;'>"
        for key, value in config_items:
            if value:
                html += f"<div><strong>{key}:</strong> {value}</div>"
        html += "</div>"
        return html
    
    def _generate_results_table_html(self) -> str:
        """Generate HTML for results table"""
        html = ""
        for result in self.results:
            status_class = self._get_status_class(result.status)
            log_link = f"<a href='{result.log_path}' target='_blank'>View Log</a>" if hasattr(result, 'log_path') and result.log_path else "N/A"
            
            html += f"""
            <tr>
                <td>{result.iteration}</td>
                <td class="{status_class}">{result.status}</td>
                <td>{result.name}</td>
                <td>{result.scratchpad or 'N/A'}</td>
                <td>{result.seed or 'N/A'}</td>
                <td>{log_link}</td>
            </tr>"""
        return html
    
    def _get_status_class(self, status: str) -> str:
        """Get CSS class for status"""
        status_upper = status.upper()
        if status_upper in ['PASS', 'SUCCESS', '*']:
            return 'status-pass'
        elif status_upper in ['FAIL', 'FAILED']:
            return 'status-fail'
        elif status_upper in ['CANCELLED']:
            return 'status-cancelled'
        return ''
    
    def _create_summary_data(self) -> Dict[str, Any]:
        """Create summary data structure"""
        total_tests = len(self.results)
        status_counts = {}
        
        for result in self.results:
            status = result.status.upper() if result.status else 'UNKNOWN'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        valid_tests = total_tests - status_counts.get('CANCELLED', 0) - status_counts.get('EXECUTIONFAIL', 0)
        passed_tests = status_counts.get('PASS', 0) + status_counts.get('*', 0) + status_counts.get('SUCCESS', 0)
        success_rate = (passed_tests / valid_tests * 100) if valid_tests > 0 else 0
        
        return {
            'test_name': self.config.name,
            'strategy_type': self.test_type,
            'timestamp': self.timestamp.isoformat(),
            'total_tests': total_tests,
            'valid_tests': valid_tests,
            'success_rate': success_rate,
            'status_counts': status_counts,
            'configuration': {
                'visual_id': self.config.visual,
                'qdf': self.config.qdf,
                'target': str(self.config.target),
                'content': str(self.config.content),
                'frequencies': {
                    'core': self.config.freq_ia,
                    'mesh': self.config.freq_cfc
                },
                'voltages': {
                    'core': self.config.volt_IA,
                    'mesh': self.config.volt_CFC
                }
            },
            'results': [
                {
                    'iteration': r.iteration,
                    'status': r.status,
                    'name': r.name,
                    'scratchpad': r.scratchpad,
                    'seed': r.seed,
                    'log_path': getattr(r, 'log_path', None)
                } for r in self.results
            ]
        }