from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import os

from utils.logger import Logger
from utils.performance import PerformanceLogger

class ImageProcessor:
    def __init__(self, path=None, image=None):
        self.logger = Logger().get_logger('image_processor')
        self.perf = PerformanceLogger()
        
        self.image = None
        self.original_width = None
        self.original_height = None
        self.original_mode = None
        
        # Store input dimensions - these won't change with resizing
        self.input_width = None
        self.input_height = None
        
        self.logger.info("Initializing image processor")
        
        if path:
            self.load_from_path(path)
        elif image:
            self.load_from_image(image)
    
    @PerformanceLogger().log_execution_time
    def load_from_path(self, path):
        """Load image from file path"""
        self.logger.info(f"Loading image from path: {path}")
        
        if not os.path.exists(path):
            self.logger.error(f"Image file not found: {path}")
            return False
            
        try:
            self.image = Image.open(path)
            self.original_width, self.original_height = self.image.size
            self.input_width, self.input_height = self.image.size  # Store input dimensions
            self.original_mode = self.image.mode
            
            self.logger.info(f"Loaded image: {path} ({self.original_width}x{self.original_height}, mode={self.original_mode})")
            return True
        except Exception as e:
            self.logger.error(f"Error loading image: {e}", exc_info=True)
            return False
    
    def load_from_image(self, image):
        """Load from PIL Image object"""
        self.logger.info("Loading from PIL Image object")
        
        try:
            self.image = image
            self.original_width, self.original_height = self.image.size
            self.input_width, self.input_height = self.image.size  # Store input dimensions
            self.original_mode = self.image.mode
            
            self.logger.info(f"Loaded image from object ({self.original_width}x{self.original_height}, mode={self.original_mode})")
            return True
        except Exception as e:
            self.logger.error(f"Error loading from image object: {e}", exc_info=True)
            return False
        
    @PerformanceLogger().log_execution_time 
    def calculate_ascii_dimensions(self, output_width, output_height, font_size=12, char_aspect_correction=True):
        """Calculate the number of ASCII characters needed to fill the output dimensions"""
        if not output_width or not output_height:
            self.logger.warning("Cannot calculate ASCII dimensions without output dimensions")
            return None, None
            
        # Estimate character dimensions based on font size
        char_width = font_size * 0.6  # Character width is typically ~60% of font size
        char_height = font_size      # Character height is roughly equal to font size
        
        # Calculate grid dimensions without correction
        raw_cols = int(output_width / char_width)
        raw_rows = int(output_height / char_height)
        
        # Calculate the aspect ratio of the target dimensions
        target_aspect_ratio = output_width / output_height
        
        # Calculate the aspect ratio of the character grid
        grid_aspect_ratio = (raw_cols * char_width) / (raw_rows * char_height)
        
        # Apply aspect ratio correction to ensure we fill the whole image
        # This is the key fix - we're calculating both dimensions to preserve aspect ratio
        if char_aspect_correction:
            # If target is wider than our grid, add more columns
            if target_aspect_ratio > grid_aspect_ratio:
                cols = raw_cols
                # Calculate rows to match target aspect ratio
                rows = int(cols / target_aspect_ratio * (char_width / char_height))
            else:
                # If target is taller than our grid, add more rows
                rows = raw_rows
                # Calculate columns to match target aspect ratio
                cols = int(rows * target_aspect_ratio * (char_height / char_width))
        else:
            cols = raw_cols
            rows = raw_rows
            
        self.logger.info(f"Calculated ASCII dimensions: {cols}x{rows} (font size: {font_size})")
        self.logger.debug(f"Target aspect ratio: {target_aspect_ratio:.3f}, Grid aspect ratio: {cols/rows:.3f}")
        
        return cols, rows
    
    @PerformanceLogger().log_execution_time    
    def resize(self, width=None, height=None, maintain_aspect=True, char_aspect_correction=True):
        """Resize image with options to maintain aspect ratio"""
        if not self.image:
            self.logger.error("No image loaded for resizing")
            return False
        
        original_width = width
        original_height = height
        
        # Calculate dimensions while maintaining aspect ratio if needed
        if maintain_aspect:
            if width and not height:
                ratio = width / self.original_width
                height = int(self.original_height * ratio)
                self.logger.debug(f"Calculated height={height} based on width={width} and aspect ratio")
            elif height and not width:
                ratio = height / self.original_height
                width = int(self.original_width * ratio)
                self.logger.debug(f"Calculated width={width} based on height={height} and aspect ratio")
            elif width and height:
                if char_aspect_correction:
                    # Character aspect ratio compensation (chars are taller than wide)
                    char_aspect = 0.5  # Most terminal fonts are roughly twice as tall as wide
                    self.logger.info(f"Applying character aspect ratio correction: Original width={width}, corrected width={int(width * char_aspect)}")
                    width = int(width * char_aspect)
                else:
                    self.logger.debug(f"No character aspect ratio correction applied")
        
        try:
            self.logger.info(f"Resizing image to {width}x{height} (requested: {original_width}x{original_height})")
            self.image = self.image.resize((width, height), Image.LANCZOS)
            return True
        except Exception as e:
            self.logger.error(f"Error resizing image: {e}", exc_info=True)
            return False
    
    @PerformanceLogger().log_execution_time
    def adjust(self, brightness=1.0, contrast=1.0, sharpness=1.0):
        """Adjust image parameters"""
        if not self.image:
            self.logger.error("No image loaded for adjustment")
            return False
        
        try:
            self.logger.info(f"Adjusting image: brightness={brightness}, contrast={contrast}, sharpness={sharpness}")
            
            with self.perf.start_timer("Brightness adjustment"):
                if brightness != 1.0:
                    enhancer = ImageEnhance.Brightness(self.image)
                    self.image = enhancer.enhance(brightness)
            
            with self.perf.start_timer("Contrast adjustment"):
                if contrast != 1.0:
                    enhancer = ImageEnhance.Contrast(self.image)
                    self.image = enhancer.enhance(contrast)
            
            with self.perf.start_timer("Sharpness adjustment"):
                if sharpness != 1.0:
                    enhancer = ImageEnhance.Sharpness(self.image)
                    self.image = enhancer.enhance(sharpness)
            
            return True
        except Exception as e:
            self.logger.error(f"Error adjusting image: {e}", exc_info=True)
            return False
    
    @PerformanceLogger().log_execution_time
    def apply_filter(self, filter_type="none"):
        """Apply image filters"""
        if not self.image:
            self.logger.error("No image loaded for filtering")
            return False
            
        filters = {
            "blur": ImageFilter.BLUR,
            "contour": ImageFilter.CONTOUR,
            "edge_enhance": ImageFilter.EDGE_ENHANCE,
            "emboss": ImageFilter.EMBOSS,
            "sharpen": ImageFilter.SHARPEN,
            "smooth": ImageFilter.SMOOTH
        }
        
        if filter_type.lower() not in filters and filter_type.lower() != "none":
            self.logger.warning(f"Unknown filter type: {filter_type}")
            return False
        
        try:
            if filter_type.lower() in filters:
                self.logger.info(f"Applying filter: {filter_type}")
                self.image = self.image.filter(filters[filter_type.lower()])
            return True
        except Exception as e:
            self.logger.error(f"Error applying filter: {e}", exc_info=True)
            return False
    
    def to_array(self):
        """Convert image to numpy array"""
        if not self.image:
            self.logger.error("No image loaded for conversion to array")
            return None
            
        try:
            # Convert to RGB if not already (to ensure 3 channels)
            if self.image.mode != 'RGB':
                self.logger.debug(f"Converting image from {self.image.mode} to RGB")
                self.image = self.image.convert('RGB')
                
            return np.array(self.image)
        except Exception as e:
            self.logger.error(f"Error converting image to array: {e}", exc_info=True)
            return None
    
    def get_dimensions(self):
        """Get current image dimensions"""
        if not self.image:
            self.logger.warning("No image loaded for getting dimensions")
            return (0, 0)
            
        return self.image.size