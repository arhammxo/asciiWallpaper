from utils.logger import Logger
from utils.performance import PerformanceLogger

class ColorHandler:
    def __init__(self, output_mode="terminal"):
        self.logger = Logger().get_logger('color_handler')
        self.perf = PerformanceLogger()
        
        self.output_mode = output_mode
        self.color_schemes = {
            "full_rgb": lambda r, g, b: (r, g, b),
            "pastel": lambda r, g, b: self._pastelize(r, g, b),
            "neon": lambda r, g, b: self._neonize(r, g, b),
            "grayscale": lambda r, g, b: self._to_grayscale(r, g, b)
        }
        self.active_scheme = "full_rgb"
        
        self.logger.info(f"Initialized color handler with output mode: {output_mode}")
    
    def set_output_mode(self, mode):
        """Set output mode (terminal, html, image)"""
        # Convert common format names to their corresponding mode
        format_to_mode = {
            "png": "image",
            "jpg": "image",
            "jpeg": "image",
            "bmp": "image",
            "gif": "image",
            "txt": "terminal",
            "text": "terminal",
            "html": "html",
            "htm": "html"
        }
        
        # Try to map the format to a mode
        if mode.lower() in format_to_mode:
            actual_mode = format_to_mode[mode.lower()]
            self.logger.info(f"Mapping format '{mode}' to output mode '{actual_mode}'")
            mode = actual_mode
        
        valid_modes = ["terminal", "html", "image"]
        if mode.lower() in valid_modes:
            self.logger.info(f"Setting output mode to: {mode}")
            self.output_mode = mode.lower()
            return True
            
        self.logger.warning(f"Invalid output mode: {mode}")
        return False
    
    def set_color_scheme(self, scheme_name):
        """Set active color scheme"""
        if scheme_name in self.color_schemes:
            self.logger.info(f"Setting color scheme to: {scheme_name}")
            self.active_scheme = scheme_name
            return True
            
        self.logger.warning(f"Unknown color scheme: {scheme_name}")
        return False
    
    def _pastelize(self, r, g, b):
        """Make colors more pastel"""
        return (int(r * 0.7 + 255 * 0.3), 
                int(g * 0.7 + 255 * 0.3), 
                int(b * 0.7 + 255 * 0.3))
    
    def _neonize(self, r, g, b):
        """Make colors more neon/vivid"""
        # Boost saturation and brightness
        factor = 1.5
        max_val = max(r, g, b)
        if max_val == 0:
            return (0, 0, 0)
        
        scaling = min(255 / max_val, factor)
        return (min(int(r * scaling), 255),
                min(int(g * scaling), 255),
                min(int(b * scaling), 255))
    
    def _to_grayscale(self, r, g, b):
        """Convert to grayscale"""
        gray = int(0.299 * r + 0.587 * g + 0.114 * b)
        return (gray, gray, gray)
    
    @PerformanceLogger().log_execution_time(threshold_ms=50)
    def apply_color(self, char, rgb, bg_color=None):
        """Apply color to character based on output mode"""
        try:
            # Apply active color scheme
            r, g, b = self.color_schemes[self.active_scheme](*rgb)
            
            if self.output_mode == "terminal":
                # ANSI escape codes for terminal
                fg_code = f"\033[38;2;{r};{g};{b}m"
                bg_code = ""
                if bg_color:
                    br, bg, bb = bg_color
                    bg_code = f"\033[48;2;{br};{bg};{bb}m"
                reset = "\033[0m"
                return f"{fg_code}{bg_code}{char}{reset}"
                
            elif self.output_mode == "html":
                # HTML span with CSS
                bg_style = ""
                if bg_color:
                    br, bg, bb = bg_color
                    bg_style = f"background-color:rgb({br},{bg},{bb});"
                return f'<span style="color:rgb({r},{g},{b});{bg_style}">{char}</span>'
                
            elif self.output_mode == "image":
                # Just return RGB values for image generation
                return (char, (r, g, b), bg_color)
                
            # Default fallback
            self.logger.warning(f"Unknown output mode '{self.output_mode}', returning plain character")
            return char
            
        except Exception as e:
            self.logger.error(f"Error applying color: {e}", exc_info=True)
            return char  # Return uncolored character as fallback