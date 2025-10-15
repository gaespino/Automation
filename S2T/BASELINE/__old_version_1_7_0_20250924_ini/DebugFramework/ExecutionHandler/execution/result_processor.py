import pandas as pd
from typing import List, Dict, Any
from ..core.interfaces import IResultProcessor
from ..configurations.test_configurations import TestResult

class TestResultProcessor(IResultProcessor):
    """Utility class for processing and analyzing test results"""
    
    @staticmethod
    def create_shmoo_data(results: List[TestResult], test_type: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Create shmoo data and legends from test results (1D)"""
        shmoo_data = []
        legends = []
        fail_count = 0
        
        for result in results:
            if result.status == 'FAIL' or result.status == 'FAILED':
                fail_letter = chr(65 + fail_count)
                legends.append(f'{fail_letter} - {result.iteration}:{result.scratchpad}:{result.seed}')
                shmoo_data.append([fail_letter])
                fail_count += 1
            else:
                shmoo_data.append(["*"])
        
        shmoo_df = pd.DataFrame(shmoo_data, columns=[test_type])
        legends_df = pd.DataFrame(legends, columns=["Legends"])
        
        return shmoo_df, legends_df
    
    @staticmethod
    def create_2d_shmoo_data(results: List[TestResult], x_values: List[float], 
                           y_values: List[float]) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Create 2D shmoo data for shmoo plots"""
        legends = []
        fail_count = 0
        
        # Create 2D array for shmoo data
        shmoo_matrix = []
        result_index = 0
        
        for y_val in y_values:
            row = []
            for x_val in x_values:
                if result_index < len(results):
                    result = results[result_index]
                    if result.status == 'FAIL' or result.status == 'FAILED':
                        fail_letter = chr(65 + fail_count)
                        legends.append(f'{fail_letter} - {result.iteration}:{result.scratchpad}:{result.seed}')
                        row.append(fail_letter)
                        fail_count += 1
                    else:
                        row.append("*")
                    result_index += 1
                else:
                    row.append("N/A")
            shmoo_matrix.append(row)
        
        shmoo_df = pd.DataFrame(shmoo_matrix, columns=x_values, index=y_values)
        legends_df = pd.DataFrame(legends, columns=["Legends"])
        
        return shmoo_df, legends_df
    
    @staticmethod
    def _calculate_status_counts(results):
        """Calculate status counts for summary"""
        status_counts = {}
        for result in results:
            status = result.status.upper() if result.status else 'UNKNOWN'
            status_counts[status] = status_counts.get(status, 0) + 1
        return status_counts

    @staticmethod
    def _extract_failure_patterns(results):
        """Extract failure patterns for summary"""
        failure_patterns = {}
        for result in results:
            if result.status == "FAIL" and result.scratchpad:
                pattern = result.scratchpad
                failure_patterns[pattern] = failure_patterns.get(pattern, 0) + 1
        return dict(sorted(failure_patterns.items(), key=lambda x: x[1], reverse=True))