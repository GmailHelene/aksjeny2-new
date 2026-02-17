"""
Performance monitoring service for Aksjeradar
"""
import time
import logging
from datetime import datetime, timedelta
from flask import request, current_app, g
from functools import wraps
import json
import os

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Service for monitoring response times and errors"""
    
    def __init__(self):
        self.log_file = 'performance.log'
        self.error_log = 'errors.log'
    
    def log_request(self, duration, endpoint, status_code, user_id=None):
        """Log request performance data"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'duration_ms': round(duration * 1000, 2),
                'endpoint': endpoint,
                'status_code': status_code,
                'user_id': user_id,
                'method': request.method if request else 'Unknown',
                'ip': request.remote_addr if request else 'Unknown'
            }
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Performance logging error: {e}")
    
    def log_error(self, error, endpoint, user_id=None):
        """Log error details"""
        try:
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'error_message': str(error),
                'endpoint': endpoint,
                'user_id': user_id,
                'method': request.method if request else 'Unknown',
                'ip': request.remote_addr if request else 'Unknown'
            }
            
            with open(self.error_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Error logging error: {e}")
    
    def get_performance_stats(self, hours=24):
        """Get performance statistics for last N hours"""
        try:
            stats = {
                'total_requests': 0,
                'avg_response_time': 0,
                'slow_requests': 0,
                'error_count': 0,
                'error_rate': 0,
                'endpoints': {},
                'slowest_endpoints': [],
                'most_used_endpoints': []
            }
            
            cutoff = datetime.now() - timedelta(hours=hours)
            
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    response_times = []
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            entry_time = datetime.fromisoformat(entry['timestamp'])
                            if entry_time > cutoff:
                                stats['total_requests'] += 1
                                duration = entry['duration_ms']
                                response_times.append(duration)
                                if duration > 2000:  # Slow request threshold
                                    stats['slow_requests'] += 1
                                # Track per endpoint
                                endpoint = entry['endpoint']
                                if endpoint not in stats['endpoints']:
                                    stats['endpoints'][endpoint] = {'count': 0, 'avg_time': 0, 'times': []}
                                stats['endpoints'][endpoint]['count'] += 1
                                stats['endpoints'][endpoint]['times'].append(duration)
                        except:
                            continue
                    
                    if response_times:
                        stats['avg_response_time'] = round(sum(response_times) / len(response_times), 2)
                    
                    # Calculate per-endpoint averages
                    for endpoint in stats['endpoints']:
                        times = stats['endpoints'][endpoint]['times']
                        if times:
                            stats['endpoints'][endpoint]['avg_time'] = round(sum(times) / len(times), 2)
                    
                    # Get slowest endpoints
                    slowest = sorted(stats['endpoints'].items(), 
                                   key=lambda x: x[1]['avg_time'], reverse=True)[:10]
                    stats['slowest_endpoints'] = [
                        {'endpoint': ep, 'avg_time': data['avg_time'], 'count': data['count']} 
                        for ep, data in slowest
                    ]
                    
                    # Get most used endpoints
                    most_used = sorted(stats['endpoints'].items(), 
                                     key=lambda x: x[1]['count'], reverse=True)[:10]
                    stats['most_used_endpoints'] = [
                        {'endpoint': ep, 'count': data['count'], 'avg_time': data['avg_time']} 
                        for ep, data in most_used
                    ]
            
            # Calculate error rate
            if stats['total_requests'] > 0:
                error_count = self._count_errors(cutoff)
                stats['error_count'] = error_count
                stats['error_rate'] = round((error_count / stats['total_requests']) * 100, 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            # Return empty stats on error
            return {
                'total_requests': 0,
                'avg_response_time': 0,
                'slow_requests': 0,
                'error_count': 0,
                'error_rate': 0,
                'endpoints': {},
                'slowest_endpoints': [],
                'most_used_endpoints': []
            }
    
    def _count_errors(self, cutoff):
        """Count errors since cutoff time"""
        try:
            if not os.path.exists(self.error_log):
                return 0
            
            error_count = 0
            with open(self.error_log, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry['timestamp'])
                        if entry_time > cutoff:
                            error_count += 1
                    except:
                        continue
            return error_count
        except Exception:
            return 0
    
    def get_error_log(self, limit=50):
        """Get recent error log entries"""
        try:
            if not os.path.exists(self.error_log):
                return []
            
            errors = []
            with open(self.error_log, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                        errors.append(entry)
                    except:
                        continue
            
            # Sort by timestamp (newest first) and limit
            errors.sort(key=lambda x: x['timestamp'], reverse=True)
            return errors[:limit]
            
        except Exception as e:
            logger.error(f"Error getting error log: {e}")
            return []

def monitor_performance(f):
    """Decorator to monitor route performance"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            response = f(*args, **kwargs)
            status_code = getattr(response, 'status_code', 200)
            
            # Log successful request
            duration = time.time() - start_time
            monitor = PerformanceMonitor()
            try:
                from flask_login import current_user
                user_id = getattr(current_user, 'id', None) if hasattr(current_user, 'id') else None
            except:
                user_id = None
            monitor.log_request(duration, request.endpoint, status_code, user_id)
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            monitor = PerformanceMonitor()
            try:
                from flask_login import current_user
                user_id = getattr(current_user, 'id', None) if hasattr(current_user, 'id') else None
            except:
                user_id = None
            monitor.log_error(e, request.endpoint, user_id)
            monitor.log_request(duration, request.endpoint, 500, user_id)
            
            raise  # Re-raise the exception
    
    return decorated_function
