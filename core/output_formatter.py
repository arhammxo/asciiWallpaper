import os
from PIL import Image, ImageDraw, ImageFont
import html
from utils.logger import Logger
from utils.performance import PerformanceLogger

class OutputFormatter:
    def __init__(self):
        self.font_path = os.path.join(os.path.dirname(__file__), "../../presets/fonts/DejaVuSansMono.ttf")
        self.font_size = 12
        self.logger = Logger().get_logger('output_formatter')
        
    def to_string(self, ascii_rows):
        """Convert ASCII art rows to a single string"""
        return "\n".join(ascii_rows)
    
    def to_html(self, ascii_rows, title="ASCII Art", css=""):
        """Create HTML document from ASCII art"""
        # Replace < characters with &lt; to avoid HTML issues
        
        # Default CSS if none provided
        if not css:
            css = """
            body { background-color: #000; margin: 0; padding: 10px; }
            pre { 
                font-family: 'Courier New', monospace; 
                font-size: 10px;
                line-height: 1.0;
                letter-spacing: 0;
                display: inline-block;
            }
            """
        
        html_content = f"""<!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>{css}</style>
        </head>
        <body>
            <pre>{''.join(ascii_rows)}</pre>
        </body>
        </html>"""
        
        return html_content
    
    def to_image(self, ascii_data, background_color=(0, 0, 0), output_width=None, output_height=None, high_density=False):
        """Render ASCII art to an image
        
        Args:
            ascii_data: ASCII art data
            background_color: RGB background color
            output_width: Desired output width (will scale the image)
            output_height: Desired output height (will scale the image)
            high_density: Whether to use high-density mode
        """
        self.logger.info(f"Generating image from ASCII art with {len(ascii_data)} rows")
        
        if not ascii_data:
            self.logger.error("No ASCII data provided for image generation")
            return None
            
        rows = len(ascii_data)
        cols = max(len(row) for row in ascii_data)
        
        self.logger.debug(f"ASCII dimensions: {cols}x{rows}")
        
        try:
            font = ImageFont.truetype(self.font_path, self.font_size)
            self.logger.debug(f"Using TrueType font: {self.font_path} (size: {self.font_size})")
        except Exception as e:
            self.logger.warning(f"Failed to load custom font: {e}")
            # Fallback to default
            font = ImageFont.load_default()
            self.logger.debug("Fallback to default font")
            
        # Get character dimensions using the available method
        if hasattr(font, 'getsize'):
            # Old Pillow version
            char_width, char_height = font.getsize('X')
        else:
            # New Pillow version (9.0.0+)
            left, top, right, bottom = font.getbbox('X')
            char_width = right - left
            char_height = bottom - top
            
        self.logger.debug(f"Character dimensions: {char_width}x{char_height}")
        
        # Calculate image dimensions
        if high_density and output_width and output_height:
            # We want to fill the exact target dimensions
            # Calculate character scales for width and height
            char_scale_w = output_width / (cols * char_width)
            char_scale_h = output_height / (rows * char_height)
            
            # We have two options:
            # 1. Use the same scale for both (may not fill one dimension)
            # 2. Use different scales (will stretch characters)
            
            # Let's use different scales to fill exactly
            # This is the key change - we're using separate scales
            scale_w = char_scale_w
            scale_h = char_scale_h
            
            self.logger.info(f"Using separate scaling factors: width={scale_w:.3f}, height={scale_h:.3f}")
            
            # Calculate final dimensions (should match target exactly)
            base_width = output_width
            base_height = output_height
        else:
            # Standard mode - just use character dimensions
            base_width = cols * char_width
            base_height = rows * char_height
            scale_w = 1.0
            scale_h = 1.0
        
        self.logger.debug(f"Base image dimensions: {base_width}x{base_height}")
        
        # Create base image
        base_image = Image.new('RGB', (base_width, base_height), color=background_color)
        draw = ImageDraw.Draw(base_image)
        
        # Draw each character
        for y, row in enumerate(ascii_data):
            for x, data in enumerate(row):
                # Handle different data formats
                if isinstance(data, tuple) and len(data) >= 2:
                    # Image mode format (char, fg_color, bg_color)
                    char, fg_color = data[0], data[1]
                    bg_color = data[2] if len(data) > 2 and data[2] else None
                else:
                    # Plain text, no color
                    char = data
                    fg_color = (255, 255, 255)  # Default white
                    bg_color = None
                
                # Calculate position with separate scaling
                if high_density and output_width and output_height:
                    pos_x = x * char_width * scale_w
                    pos_y = y * char_height * scale_h
                    
                    # Calculate character box size
                    char_box_w = char_width * scale_w
                    char_box_h = char_height * scale_h
                else:
                    pos_x = x * char_width
                    pos_y = y * char_height
                    char_box_w = char_width
                    char_box_h = char_height
                
                # Draw background if specified
                if bg_color:
                    draw.rectangle(
                        [pos_x, pos_y, pos_x + char_box_w, pos_y + char_box_h],
                        fill=bg_color
                    )
                
                # Draw character
                # Create a temporary image for the character to scale it properly
                if high_density and scale_w != scale_h and abs(scale_w - scale_h) > 0.1:
                    # If scales are very different, we need to handle stretching
                    char_img = Image.new('RGBA', (char_width, char_height), (0, 0, 0, 0))
                    char_draw = ImageDraw.Draw(char_img)
                    char_draw.text((0, 0), char, font=font, fill=fg_color)
                    
                    # Calculate stretched size
                    stretch_w = int(char_width * scale_w)
                    stretch_h = int(char_height * scale_h)
                    
                    # Resize the character image
                    stretched_char = char_img.resize((stretch_w, stretch_h), Image.LANCZOS)
                    
                    # Paste the stretched character
                    base_image.paste(stretched_char, (int(pos_x), int(pos_y)), stretched_char)
                else:
                    # Draw directly if no extreme stretching
                    draw.text(
                        (pos_x, pos_y),
                        char,
                        font=font,
                        fill=fg_color
                    )
        
        # Scale the image to the desired output size if specified
        final_image = base_image
        if not high_density and (output_width or output_height):
            if output_width and output_height:
                self.logger.info(f"Scaling image to {output_width}x{output_height}")
                final_image = base_image.resize((output_width, output_height), Image.LANCZOS)
            elif output_width:
                # Maintain aspect ratio
                aspect_ratio = base_height / base_width
                scaled_height = int(output_width * aspect_ratio)
                self.logger.info(f"Scaling image to {output_width}x{scaled_height} (maintained aspect ratio)")
                final_image = base_image.resize((output_width, scaled_height), Image.LANCZOS)
            elif output_height:
                # Maintain aspect ratio
                aspect_ratio = base_width / base_height
                scaled_width = int(output_height * aspect_ratio)
                self.logger.info(f"Scaling image to {scaled_width}x{output_height} (maintained aspect ratio)")
                final_image = base_image.resize((scaled_width, output_height), Image.LANCZOS)
        
        return final_image
    
    def save_to_file(self, content, file_path, format_type="txt"):
        """Save content to file based on format"""
        try:
            if format_type.lower() == "txt":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            elif format_type.lower() == "html":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            elif format_type.lower() in ["png", "jpg", "jpeg", "bmp", "gif"]:
                content.save(file_path, format_type.upper())
                
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False