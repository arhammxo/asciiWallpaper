# debug_image_gen.py
import os
import sys
from PIL import Image, ImageFont, ImageDraw
from utils.logger import Logger

def test_font_rendering():
    """Test font rendering to diagnose issues"""
    logger = Logger().get_logger('debug')
    logger.info("Testing font rendering")
    
    # Create a small test image
    img = Image.new('RGB', (300, 100), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Try different font loading approaches
    try:
        # Default font
        logger.info("Testing default font")
        default_font = ImageFont.load_default()
        draw.text((10, 10), "Default font test", font=default_font, fill=(255, 255, 255))
        
        # Check font methods
        logger.info("Checking available font methods")
        font_methods = dir(default_font)
        logger.info(f"Font methods: {[m for m in font_methods if not m.startswith('_')]}")
        
        # Test getting font dimensions 
        logger.info("Testing font dimension methods")
        if hasattr(default_font, 'getsize'):
            w, h = default_font.getsize('X')
            logger.info(f"getsize('X') = {w}x{h}")
        else:
            logger.info("getsize method not available")
            
        if hasattr(default_font, 'getbbox'):
            bbox = default_font.getbbox('X')
            logger.info(f"getbbox('X') = {bbox}")
        else:
            logger.info("getbbox method not available")
            
        # Try to load a TrueType font
        font_dirs = [
            ".",  # Current directory
            "./presets/fonts",  # Project font directory
            "C:/Windows/Fonts",  # Windows fonts
            "/usr/share/fonts",  # Linux fonts
            "/System/Library/Fonts"  # macOS fonts
        ]
        
        # Try to find a font file
        font_found = False
        for font_dir in font_dirs:
            if not os.path.exists(font_dir):
                continue
                
            logger.info(f"Checking font directory: {font_dir}")
            font_files = []
            
            # Only check first level for system directories to avoid too much scanning
            if "Windows" in font_dir or "share" in font_dir or "System" in font_dir:
                font_files = [f for f in os.listdir(font_dir) if f.endswith(('.ttf', '.TTF'))][:5]
            else:
                # Check all subdirectories for project directories
                for root, dirs, files in os.walk(font_dir):
                    font_files.extend([os.path.join(root, f) for f in files if f.endswith(('.ttf', '.TTF'))])
                    if len(font_files) >= 5:
                        break
            
            # Try first 5 font files
            for font_file in font_files[:5]:
                if "Windows" in font_dir or "share" in font_dir or "System" in font_dir:
                    full_path = os.path.join(font_dir, font_file)
                else:
                    full_path = font_file
                    
                try:
                    logger.info(f"Trying to load font: {full_path}")
                    ttf_font = ImageFont.truetype(full_path, 12)
                    
                    # Test font
                    if hasattr(ttf_font, 'getsize'):
                        w, h = ttf_font.getsize('X')
                    elif hasattr(ttf_font, 'getbbox'):
                        left, top, right, bottom = ttf_font.getbbox('X')
                        w, h = right - left, bottom - top
                    
                    logger.info(f"Successfully loaded font: {font_file} (char size: {w}x{h})")
                    draw.text((10, 40), f"TrueType font test: {font_file}", font=ttf_font, fill=(255, 255, 255))
                    font_found = True
                    break
                except Exception as e:
                    logger.warning(f"Failed to load font {font_file}: {e}")
            
            if font_found:
                break
        
        # Save test image
        output_path = "font_test.png"
        img.save(output_path)
        logger.info(f"Saved test image to {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Font testing failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    test_font_rendering()