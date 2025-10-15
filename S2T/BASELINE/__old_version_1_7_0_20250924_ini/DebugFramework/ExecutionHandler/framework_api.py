from typing import Dict, List
from .main_framework import Framework

class FrameworkExternalAPI:
    """External API interface for automation systems"""
    
    def __init__(self, framework: Framework):
        self.framework = framework
    
    def end_experiment(self) -> Dict:
        """End current experiment gracefully"""
        success = self.framework.end_experiment()
        return {
            'success': success,
            'message': 'End command sent - experiment will finish current iteration and stop' if success else 'No experiment running or failed to send end command',
            'state': self.framework.get_execution_state()
        }
    
    def continue_next_iteration(self) -> Dict:
        """Continue to next iteration (step-by-step mode only)"""
        success = self.framework.step_continue()
        return {
            'success': success,
            'message': 'Continue command sent' if success else 'Failed to send continue command (check if step-by-step mode is enabled and waiting)',
            'state': self.framework.get_execution_state()
        }
    
    def cancel_experiment(self) -> Dict:
        """Cancel experiment immediately"""
        self.framework.cancel_execution()
        return {
            'success': True,
            'message': 'Cancel command sent - experiment will stop immediately',
            'state': self.framework.get_execution_state()
        }
    
    def get_current_state(self) -> Dict:
        """Get current execution state"""
        return self.framework.get_execution_state()
    
    def get_iteration_statistics(self) -> Dict:
        """Get detailed statistics for decision making"""
        state = self.framework.get_execution_state()
        stats = state.get('current_stats', {})
        
        return {
            'total_completed': stats.get('total_completed', 0),
            'pass_rate': stats.get('pass_rate', 0.0),
            'fail_rate': stats.get('fail_rate', 0.0),
            'recent_trend': self._analyze_recent_trend(state.get('latest_results', [])),
            'recommendation': self._get_recommendation(stats),
            'end_requested': state.get('end_requested', False),
            'sufficient_data': self._has_sufficient_data(stats)
        }
    
    def _has_sufficient_data(self, stats: Dict) -> bool:
        """Determine if we have sufficient data for decision making"""
        total = stats.get('total_completed', 0)
        pass_rate = stats.get('pass_rate', 0.0)
        
        if total >= 10:
            return True
        elif total >= 5:
            if pass_rate >= 95 or pass_rate <= 20:
                return True
        
        return False
    
    def _get_recommendation(self, stats: Dict) -> str:
        """Get recommendation based on current statistics"""
        pass_rate = stats.get('pass_rate', 0.0)
        total = stats.get('total_completed', 0)
        
        if total < 3:
            return "continue"  # Need more data
        elif self._has_sufficient_data(stats):
            if pass_rate >= 90:
                return "sufficient_data_good"  # Can end with good results
            elif pass_rate <= 30:
                return "sufficient_data_poor"  # Can end with poor results
            else:
                return "continue"  # Mixed results, need more data
        elif pass_rate >= 95:
            return "trending_excellent"  # Very good trend
        elif pass_rate <= 20:
            return "trending_poor"  # Very poor trend
        else:
            return "continue"  # Normal operation

    def _analyze_recent_trend(self, recent_results: List) -> str:
        """Analyze recent test trend"""
        if len(recent_results) < 3:
            return "insufficient_data"
        
        # Look at last 3 results
        last_3 = recent_results[-3:]
        pass_count = sum(1 for r in last_3 if r.status in ['PASS', 'SUCCESS', '*'])
        
        if pass_count == 3:
            return "improving"
        elif pass_count == 0:
            return "declining"
        else:
            return "mixed"