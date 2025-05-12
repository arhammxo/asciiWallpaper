import os
import json
import logging
from .logger import Logger

class Config:
    """Configuration management for the application"""
    
    DEFAULT_CONFIG = {
        "logging": {
            "level": "INFO",
            "log_to_file": True,
            "log_performance": True
        },
        "image": {
            "default_width": 100,
            "default_height": 50
        },
        "ascii": {
            "default_charset": "standard",
            "default_color_scheme": "full_rgb"
        },
        "output": {
            "default_format": "txt"
        },
        "ui": {
            "theme": "system",
            "show_preview": True
        }
    }
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_path=None):
        if self._initialized:
            return
            
        self.logger = Logger().get_logger('config')
        
        # Determine config path
        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_path = os.path.join(base_dir, 'config.json')
        else:
            self.config_path = config_path
            
        # Load or create configuration
        self.config = self._load_config()
        
        # Setup logging based on config
        self._setup_logging()
        
        self._initialized = True
    
    def _load_config(self):
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.logger.debug(f"Configuration loaded from {self.config_path}")
                    return config
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
        
        # Save default config
        self._save_config(self.DEFAULT_CONFIG)
        return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self, config):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            self.logger.debug(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def _setup_logging(self):
        """Configure logging based on settings"""
        log_level_name = self.config.get('logging', {}).get('level', 'INFO')
        log_level = getattr(logging, log_level_name)
        log_to_file = self.config.get('logging', {}).get('log_to_file', True)
        
        # Reinitialize the logger with config settings
        Logger(log_level=log_level, log_to_file=log_to_file)
        self.logger = Logger().get_logger('config')  # Refresh logger
    
    def get(self, section, key=None, default=None):
        """Get configuration value"""
        if key is None:
            return self.config.get(section, {})
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section, key, value):
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        self._save_config(self.config)
        
        # Reconfigure logging if logging settings changed
        if section == 'logging':
            self._setup_logging()