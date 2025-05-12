import argparse
import sys
import os
import traceback

from core.image_processor import ImageProcessor
from core.ascii_converter import AsciiConverter
from core.color_handler import ColorHandler
from core.output_formatter import OutputFormatter
from ui.cli import CLI
from ui.gui import GUI
from utils.logger import Logger
from utils.config import Config
from utils.performance import PerformanceLogger

def main():
    # Initialize logging with default settings
    logger = Logger().get_logger('main')
    perf = PerformanceLogger()
    
    # Set up global exception logging
    Logger.setup_exception_logging()
    
    # Load configuration
    config = Config()
    
    # Enable/disable performance logging based on config
    perf.set_enable_logging(config.get('logging', 'log_performance', True))
    
    logger.info("Starting ASCII Art Wallpaper Generator")
    
    # Parse command line arguments
    with perf.start_timer("Argument parsing"):
        parser = argparse.ArgumentParser(description="Convert images to colorful ASCII art wallpapers")
        parser.add_argument('-i', '--input', help='Input image path')
        parser.add_argument('-o', '--output', help='Output file path')
        parser.add_argument('-w', '--width', type=int, help='Width in characters')
        parser.add_argument('-ht', '--height', type=int, help='Height in characters')
        parser.add_argument('-c', '--color', action='store_true', help='Use color')
        parser.add_argument('-cs', '--charset', 
                   choices=['standard', 'detailed', 'simple', 'blocks', 'minimal', 'diagonal', 'manga', 'contrast'],
                   default='standard', help='Character set to use')
        parser.add_argument('-cm', '--colormode', help='Color mode (full_rgb, pastel, neon, grayscale)')
        parser.add_argument('-f', '--format', help='Output format (txt, html, png, jpg)')
        parser.add_argument('-g', '--gui', action='store_true', help='Start with GUI interface')
        parser.add_argument('-b', '--brightness', type=float, default=1.0, help='Brightness adjustment (0.1-2.0)')
        parser.add_argument('-ct', '--contrast', type=float, default=1.0, help='Contrast adjustment (0.1-2.0)')
        parser.add_argument('-iv', '--invert', action='store_true', help='Invert character mapping')
        parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
        parser.add_argument('-fs', '--fontsize', type=int, default=12, help='Font size for image output')
        parser.add_argument('-kd', '--keepdims', action='store_true', help='Keep original image dimensions for output')
        parser.add_argument('-ow', '--outputwidth', type=int, help='Custom output image width')
        parser.add_argument('-oh', '--outputheight', type=int, help='Custom output image height')
        parser.add_argument('-pre', '--preprocess', choices=['none', 'edge', 'sharpen', 'contrast'], 
                   default='none', help='Image preprocessing method')
        parser.add_argument('-dir', '--directional', action='store_true', 
                   help='Enable directional character selection')
        
        parser.add_argument('--high-density', action='store_true', 
                            help='Use high-density mode for more detailed ASCII art')
        parser.add_argument('--density-factor', type=float, default=1.0,
                            help='Density multiplier for high-density mode (higher = more characters)')
        
        args = parser.parse_args()
    
    # Set debug mode if requested
    if args.debug:
        logger.info("Debug mode enabled")
        config.set('logging', 'level', 'DEBUG')
    
    # Log startup information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Running from: {os.path.abspath('.')}")
    
    # If GUI mode or no input file specified, launch GUI
    if args.gui or not args.input:
        logger.info("Starting in GUI mode")
        try:
            app = GUI()
            app.run()
        except Exception as e:
            logger.critical(f"Error in GUI mode: {e}", exc_info=True)
        return
    
    # Process through command-line
    logger.info("Starting in CLI mode")
    
    with perf.start_timer("Image processing"):
        try:
            # Load image
            logger.info(f"Loading image: {args.input}")
            processor = ImageProcessor(args.input)
            
            if not processor.image:
                logger.error("Failed to load image")
                return
            
            # Apply preprocessing if specified
            if args.preprocess != 'none':
                logger.info(f"Applying preprocessing: {args.preprocess}")
                if args.preprocess == 'edge':
                    # Apply edge detection
                    from PIL import ImageFilter
                    processor.image = processor.image.filter(ImageFilter.FIND_EDGES)
                elif args.preprocess == 'sharpen':
                    # Enhance edges
                    from PIL import ImageFilter
                    processor.image = processor.image.filter(ImageFilter.SHARPEN)
                elif args.preprocess == 'contrast':
                    # Enhance contrast
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Contrast(processor.image)
                    processor.image = enhancer.enhance(2.0)  # Double the contrast

            # Determine dimensions for ASCII conversion
            if args.high_density:
                # High-density mode - calculate based on output dimensions and font size
                logger.info("Using high-density mode for ASCII conversion")
                
                # Determine output dimensions
                output_width = args.outputwidth or processor.input_width
                output_height = args.outputheight or processor.input_height
                
                if args.keepdims:
                    output_width = processor.input_width
                    output_height = processor.input_height
                
                # Calculate required ASCII dimensions
                font_size = args.fontsize or 12
                density_factor = args.density_factor or 1.0
                
                # Apply density factor (higher = more characters)
                adjusted_font_size = font_size / density_factor
                
                # Calculate grid dimensions with proper aspect ratio preservation
                cols, rows = processor.calculate_ascii_dimensions(
                    output_width, 
                    output_height, 
                    adjusted_font_size,
                    char_aspect_correction=True
                )
                
                logger.info(f"Using ASCII grid dimensions: {cols}x{rows}")
                
                # Resize image to match ASCII grid
                # IMPORTANT: Don't apply aspect correction again, since we calculated with it
                processor.resize(cols, rows, char_aspect_correction=False)
            else:
                # Standard mode - use fixed dimensions
                width = args.width or config.get('image', 'default_width', 100)
                height = args.height or config.get('image', 'default_height', 50)
                logger.info(f"Resizing to {width}x{height}")
                processor.resize(width, height, char_aspect_correction=True)
            
            # Apply adjustments
            logger.info(f"Adjusting image: brightness={args.brightness}, contrast={args.contrast}")
            processor.adjust(brightness=args.brightness, contrast=args.contrast)
            
            # Convert to ASCII
            logger.info("Converting to ASCII")
            converter = AsciiConverter()
            if args.charset:
                converter.set_char_set(args.charset)
            
            # Set directional character selection
            if args.directional:
                logger.info("Enabling directional character selection")
                converter.set_directional_mode(True)

            # Set color handling
            color_handler = converter.color_handler
            if args.colormode:
                color_handler.set_color_scheme(args.colormode)
            
            # Format for output
            output_format = args.format or config.get('output', 'default_format', 'txt')
            color_handler.set_output_mode("terminal" if output_format == "txt" else output_format)
            
            # Convert image to ASCII
            image_array = processor.to_array()
            if image_array is None:
                logger.error("Failed to convert image to array")
                return
                
            ascii_rows = converter.image_to_ascii(
                image_array, 
                colored=args.color, 
                invert=args.invert
            )
            
            if not ascii_rows:
                logger.error("ASCII conversion produced no output")
                return
                
            # Format output with better error checking for each format type
            logger.info(f"Formatting output as {output_format}")
            formatter = OutputFormatter()
            
            if output_format == "txt":
                # Text output
                output = formatter.to_string(ascii_rows)
                if args.output:
                    logger.info(f"Saving to file: {args.output}")
                    formatter.save_to_file(output, args.output, output_format)
                else:
                    logger.info("Printing to console")
                    print(output)
                    
            elif output_format == "html":
                # HTML output
                output = formatter.to_html(ascii_rows)
                output_path = args.output or "ascii_art.html"
                logger.info(f"Saving HTML to: {output_path}")
                formatter.save_to_file(output, output_path, output_format)
                    
            elif output_format in ["png", "jpg", "jpeg", "bmp", "gif"]:
                # For image output we need different data formatting
                logger.info("Creating image output")
                
                # Make sure color handler is properly set for image output
                logger.info("Setting color handler to image mode")
                converter.color_handler.set_output_mode("image")
                
                # Re-convert with proper image formatting if needed
                if not isinstance(ascii_rows[0], list) and not (isinstance(ascii_rows[0], tuple) and len(ascii_rows[0]) > 1):
                    logger.info("Re-converting image with image output format")
                    ascii_rows = converter.image_to_ascii(
                        image_array, 
                        colored=args.color, 
                        invert=args.invert
                    )
                
                # Create image
                try:
                    # Determine output dimensions
                    output_width = None
                    output_height = None
                    
                    if args.keepdims:
                        # Use original dimensions
                        output_width = processor.input_width
                        output_height = processor.input_height
                        logger.info(f"Using original image dimensions for output: {output_width}x{output_height}")
                    elif args.outputwidth or args.outputheight:
                        # Use custom dimensions
                        output_width = args.outputwidth
                        output_height = args.outputheight
                        logger.info(f"Using custom output dimensions: {output_width}x{output_height}")
                    
                    # Set font size
                    if args.fontsize:
                        formatter.font_size = args.fontsize
                        logger.info(f"Using custom font size: {args.fontsize}")
                    
                    # Generate the ASCII image
                    image = formatter.to_image(
                        ascii_rows,
                        output_width=output_width,
                        output_height=output_height,
                        high_density=args.high_density
                    )
                    
                    output_path = args.output or f"ascii_art.{output_format}"
                    logger.info(f"Saving image to: {output_path}")
                    formatter.save_to_file(image, output_path, output_format)
                except AttributeError as e:
                    if "getsize" in str(e):
                        logger.error("Pillow API compatibility issue: getsize method not found")
                        logger.info("This is likely due to using a newer version of Pillow (9.0.0+)")
                        print("Error: Pillow API compatibility issue. Run the debug_image_gen.py script for diagnosis.")
                        return 1
                    else:
                        raise
            
            logger.info("Processing completed successfully")
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {e.filename}", exc_info=True)
            print(f"Error: Could not find file '{e.filename}'")
            print("Please check that the file exists and you have permissions to read it.")
            return 1
        except PermissionError as e:
            logger.error(f"Permission error: {e}", exc_info=True)
            print(f"Error: Permission denied when accessing '{e.filename}'")
            print("Please check file permissions.")
            return 1
        except AttributeError as e:
            logger.error(f"API compatibility error: {e}", exc_info=True)
            print(f"Error: API compatibility issue: {e}")
            print("This may be due to using a newer version of Pillow or other library.")
            return 1
        except Exception as e:
            error_msg = f"Error processing image: {e}"
            logger.critical(error_msg, exc_info=True)
            print(f"Error: {error_msg}")
            print(traceback.format_exc())
            return 1

if __name__ == "__main__":
    main()