import time
import functools
from .logger import Logger

class PerformanceLogger:
    """Performance tracking utilities for measuring execution time"""
    
    def __init__(self):
        self.logger = Logger().get_logger('performance')
        self.enable_logging = True
    
    def set_enable_logging(self, enable):
        """Enable or disable performance logging"""
        self.enable_logging = enable
    
    def log_execution_time(self, func=None, threshold_ms=None):
        """Decorator to log function execution time
        
        Args:
            func: The function to decorate
            threshold_ms: Only log if execution time exceeds this threshold (in ms)
        """
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                if not self.enable_logging:
                    return f(*args, **kwargs)
                
                start_time = time.time()
                result = f(*args, **kwargs)
                end_time = time.time()
                
                execution_time_ms = (end_time - start_time) * 1000
                
                # Log if no threshold or if execution time exceeds threshold
                if threshold_ms is None or execution_time_ms > threshold_ms:
                    self.logger.debug(f"{f.__name__} executed in {execution_time_ms:.2f}ms")
                
                return result
            return wrapper
        
        # Handle both @log_execution_time and @log_execution_time(threshold_ms=100)
        if func is None:
            return decorator
        return decorator(func)
    
    def start_timer(self, name):
        """Start a named timer"""
        return Timer(name, self.logger, self.enable_logging)


class Timer:
    """Context manager for timing code blocks"""
    
    def __init__(self, name, logger, enabled=True):
        self.name = name
        self.logger = logger
        self.enabled = enabled
        self.start_time = None
    
    def __enter__(self):
        if self.enabled:
            self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.enabled and self.start_time is not None:
            end_time = time.time()
            execution_time_ms = (end_time - self.start_time) * 1000
            self.logger.debug(f"{self.name} completed in {execution_time_ms:.2f}ms")