import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler
import traceback

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[94m',     # Blue
        'INFO': '\033[92m',      # Green
        'WARNING': '\033[93m',   # Yellow
        'ERROR': '\033[91m',     # Red
        'CRITICAL': '\033[1;91m' # Bold Red
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_message = super().format(record)
        if record.levelname in self.COLORS and sys.stdout.isatty():
            return f"{self.COLORS[record.levelname]}{log_message}{self.RESET}"
        return log_message

class Logger:
    """Centralized logging configuration for the application"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, log_level=logging.INFO, log_to_file=True):
        if self._initialized:
            return
            
        self.logger = logging.getLogger('ascii_wallpaper')
        self.logger.setLevel(log_level)
        self.logger.propagate = False
        
        # Clear any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
            
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Create detailed formatter for console
        console_format = '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
        console_date_format = '%H:%M:%S'
        console_formatter = CustomFormatter(fmt=console_format, datefmt=console_date_format)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Create file handler if requested
        if log_to_file:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, f'ascii_wallpaper_{time.strftime("%Y%m%d")}.log')
            file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
            file_handler.setLevel(log_level)
            
            # More detailed formatter for file
            file_format = '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d (%(funcName)s) - %(message)s'
            file_formatter = logging.Formatter(fmt=file_format)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        self._initialized = True
    
    def get_logger(self, name):
        """Get a named logger that inherits from the main logger configuration"""
        child_logger = logging.getLogger(f'ascii_wallpaper.{name}')
        return child_logger
    
    @classmethod
    def setup_exception_logging(cls):
        """Set up global exception handling to log unhandled exceptions"""
        def exception_handler(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                # Don't log keyboard interrupt
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
                
            logger = cls().get_logger('uncaught')
            logger.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
            
        sys.excepthook = exception_handler