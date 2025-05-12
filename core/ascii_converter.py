import numpy as np
from utils.logger import Logger
from utils.performance import PerformanceLogger
from .color_handler import ColorHandler

class AsciiConverter:
    def __init__(self, char_set=None):
        self.logger = Logger().get_logger('ascii_converter')
        self.perf = PerformanceLogger()
        
        # Default character set from dense/dark to light
        self.char_sets = {
            "standard": "@%#*+=-:. ",
            "bright": " .:-=+*#%@",     # New! Inverted for brightness
            "detailed": "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. ",
            "simple": "#@%*+=-:. ",
            "blocks": "█▓▒░ ",
            "minimal": "@:. ",
            "manga": "█▓▒░@%#*/\\()[]{}=_-+~<>!;:,. ",
            "diagonal": "\\|/─│┌┐└┘┼▄▀█▓▒░ ",
            "contrast": "@%#*+=-:. "
        }
        
        self.char_set = char_set if char_set else self.char_sets["standard"]
        self.char_set_name = "standard"
        self.color_handler = ColorHandler()
        self.directional_mode = False  # Default to disabled
        
        self.logger.info(f"Initialized ASCII converter with {len(self.char_set)} characters")
        self.logger.debug(f"Character set: '{self.char_set}'")

    def set_directional_mode(self, enabled=True):
        """Enable or disable directional character selection"""
        self.directional_mode = enabled
        self.logger.info(f"Directional character selection {'enabled' if enabled else 'disabled'}")
        return True
    
    def set_char_set(self, set_name=None, custom_chars=None):
        """Set character set from predefined or custom set"""
        if custom_chars:
            self.logger.info(f"Setting custom character set with {len(custom_chars)} characters")
            self.logger.debug(f"Custom characters: '{custom_chars}'")
            self.char_set = custom_chars
            self.char_set_name = "custom"
        elif set_name in self.char_sets:
            self.logger.info(f"Setting character set to '{set_name}' with {len(self.char_sets[set_name])} characters")
            self.char_set = self.char_sets[set_name]
            self.char_set_name = set_name
        else:
            self.logger.warning(f"Unknown character set '{set_name}', keeping current set")
            
        return self.char_set
    
    @PerformanceLogger().log_execution_time(threshold_ms=50)
    def pixel_to_ascii(self, pixel, x=0, y=0, image_array=None, colored=True, bg_color=None, invert=False, brightness_boost=1.5):
        """Convert a single pixel to ASCII character with optional color"""
        try:
            # Extract RGB values
            if len(pixel) >= 3:
                r, g, b = pixel[:3]
            else:
                r = g = b = pixel[0]
                
            # Calculate intensity/brightness (0-255)
            # Use a more brightness-friendly method (max component)
            intensity = max(r, g, b)  # Changed from weighted RGB
            
            # Apply brightness boost
            adjusted_intensity = min(255, intensity * brightness_boost)
            
            # Map intensity to character index with brightness correction
            if invert:
                char_index = int((255 - adjusted_intensity) / 255 * (len(self.char_set) - 1))
            else:
                char_index = int(adjusted_intensity / 255 * (len(self.char_set) - 1))
            
            # Ensure index is in bounds
            char_index = max(0, min(char_index, len(self.char_set) - 1))
            
            # Get the character from the set
            char = self.char_set[char_index]
            
            # Apply directional character selection if enabled
            if self.directional_mode and image_array is not None:
                try:
                    direction = self.detect_direction(image_array, x, y)
                    
                    # Special character mapping for manga/line art
                    if self.char_set_name in ["manga", "diagonal"]:
                        if direction == 'ne':
                            char = '/'
                        elif direction == 'nw':
                            char = '\\'
                        elif direction == 'n' or direction == 's':
                            char = '|'
                        elif direction == 'e' or direction == 'w':
                            char = '-'
                        elif direction == 'se':
                            char = '\\'
                        elif direction == 'sw':
                            char = '/'
                        # If 'none', use intensity-based character (already set)
                except Exception as e:
                    self.logger.error(f"Error in directional character selection: {e}")
                    # Continue with normal character
            
            # Apply color if requested
            if colored:
                return self.color_handler.apply_color(char, (r, g, b), bg_color)
            else:
                return char
        except Exception as e:
            self.logger.error(f"Error converting pixel to ASCII: {e}", exc_info=True)
            # Return a safe fallback character
            return " "
    
    @PerformanceLogger().log_execution_time
    def image_to_ascii(self, image_array, colored=True, bg_color=None, invert=False, brightness_boost=1.5):
        """Convert entire image array to ASCII art"""
        if image_array is None:
            self.logger.error("Cannot convert None image array to ASCII")
            return []
            
        try:
            height, width = image_array.shape[:2]
            self.logger.info(f"Converting {width}x{height} image to ASCII (colored={colored}, invert={invert}, brightness_boost={brightness_boost})")
            
            # Check if we're in image output mode
            is_image_mode = hasattr(self.color_handler, 'output_mode') and self.color_handler.output_mode == "image"
            
            ascii_rows = []
            
            # Use a smaller sample for performance logging if image is large
            log_frequency = max(1, height // 10)
            
            for y in range(height):
                with self.perf.start_timer(f"Row {y} conversion") if y % log_frequency == 0 else NoOpContextManager():
                    if is_image_mode:
                        # For image mode, we need to preserve more data
                        ascii_row = []
                    else:
                        ascii_row = ""
                        
                    for x in range(width):
                        pixel = image_array[y, x]
                        result = self.pixel_to_ascii(
                            pixel, 
                            x, y, 
                            image_array,  # Pass the entire array for direction detection
                            colored, 
                            bg_color, 
                            invert,
                            brightness_boost  # Pass the brightness boost parameter
                        )
                        
                        if is_image_mode:
                            # For image mode, append to list
                            ascii_row.append(result)
                        else:
                            # For text modes, concatenate to string
                            ascii_row += result
                            
                    ascii_rows.append(ascii_row)
            
            self.logger.info(f"Completed ASCII conversion: {len(ascii_rows)} rows")
            return ascii_rows
        except Exception as e:
            self.logger.error(f"Error converting image to ASCII: {e}", exc_info=True)
            return []

    def detect_direction(self, image_array, x, y, window_size=3):
        """Detect the predominant direction around a pixel"""
        import numpy as np  # Make sure numpy is imported
        
        if image_array is None:
            return None
            
        # Get window boundaries
        h, w = image_array.shape[:2]
        x_min = max(0, x - window_size//2)
        x_max = min(w - 1, x + window_size//2)
        y_min = max(0, y - window_size//2)
        y_max = min(h - 1, y + window_size//2)
        
        # Sobel operators for edge detection
        h_kernel = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
        v_kernel = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
        
        # Extract the window
        window = image_array[y_min:y_max+1, x_min:x_max+1]
        if len(window.shape) > 2:
            # Convert to grayscale if color
            window_gray = np.mean(window, axis=2).astype(np.uint8)
        else:
            window_gray = window
        
        # Pad if too small for convolution
        if window_gray.shape[0] < 3 or window_gray.shape[1] < 3:
            return 'none'
        
        # Apply Sobel operators
        gx = np.abs(np.sum(window_gray * h_kernel))
        gy = np.abs(np.sum(window_gray * v_kernel))
        
        # Determine direction
        if gx < 20 and gy < 20:  # Low gradient = no strong direction
            return 'none'
        
        angle = np.arctan2(gy, gx) * 180 / np.pi
        
        # Map angle to direction
        if 22.5 <= angle < 67.5:
            return 'ne'  # Northeast
        elif 67.5 <= angle < 112.5:
            return 'n'   # North
        elif 112.5 <= angle < 157.5:
            return 'nw'  # Northwest
        elif 157.5 <= angle <= 180 or -180 <= angle < -157.5:
            return 'w'   # West
        elif -157.5 <= angle < -112.5:
            return 'sw'  # Southwest
        elif -112.5 <= angle < -67.5:
            return 's'   # South
        elif -67.5 <= angle < -22.5:
            return 'se'  # Southeast
        else:
            return 'e'   # East

class NoOpContextManager:
    """A no-op context manager for conditional timers"""
    def __enter__(self):
        pass
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass