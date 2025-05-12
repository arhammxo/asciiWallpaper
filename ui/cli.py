import os
import sys
import time
from utils.logger import Logger
from utils.performance import PerformanceLogger

class CLI:
    def __init__(self):
        self.logger = Logger().get_logger('cli')
        self.perf = PerformanceLogger()
        
        self.logger.info("Initializing CLI interface")
        
        self.commands = {
            'load': self.load_image,
            'convert': self.convert,
            'save': self.save,
            'adjust': self.adjust,
            'view': self.view,
            'help': self.show_help,
            'exit': self.exit,
            'debug': self.toggle_debug
        }
        
        self.image_processor = None
        self.ascii_converter = None
        self.output_formatter = None
        self.ascii_result = None
        
    def start(self):
        """Start the CLI interface"""
        self.logger.info("Starting CLI interface")
        print("ASCII Art Wallpaper Generator - CLI Interface")
        print("Type 'help' for available commands")
        
        while True:
            try:
                cmd = input("\n> ").strip().lower()
                self.logger.debug(f"Command entered: {cmd}")
                
                parts = cmd.split(maxsplit=1)
                command = parts[0] if parts else ""
                args = parts[1] if len(parts) > 1 else ""
                
                if command in self.commands:
                    with self.perf.start_timer(f"Command: {command}"):
                        self.commands[command](args)
                elif command:
                    self.logger.warning(f"Unknown command: {command}")
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                print("\nCommand interrupted. Type 'exit' to quit.")
            except Exception as e:
                self.logger.error(f"Error processing command: {e}", exc_info=True)
                print(f"Error: {e}")
    
    def load_image(self, args):
        """Load an image from file"""
        if not args:
            self.logger.warning("No image path specified")
            print("Please specify an image path: load <image_path>")
            return
            
        self.logger.info(f"Loading image: {args}")
        
        try:
            from core.image_processor import ImageProcessor
            self.image_processor = ImageProcessor(args)
            
            if self.image_processor.image:
                print(f"Image loaded: {args}")
            else:
                print(f"Failed to load image: {args}")
        except Exception as e:
            self.logger.error(f"Error loading image: {e}", exc_info=True)
            print(f"Error loading image: {e}")
        
    def convert(self, args):
        """Convert loaded image to ASCII"""
        if not self.image_processor:
            self.logger.warning("No image loaded for conversion")
            print("No image loaded. Use 'load <image_path>' first")
            return
            
        self.logger.info(f"Converting image with args: {args}")
        
        try:
            # Parse arguments
            width = None
            height = None
            char_set = "standard"
            color = True
            color_scheme = "full_rgb"
            invert = False
            
            for arg in args.split():
                if arg.startswith("width="):
                    width = int(arg.split("=")[1])
                elif arg.startswith("height="):
                    height = int(arg.split("=")[1])
                elif arg.startswith("charset="):
                    char_set = arg.split("=")[1]
                elif arg.startswith("color="):
                    color = arg.split("=")[1].lower() == "true"
                elif arg.startswith("scheme="):
                    color_scheme = arg.split("=")[1]
                elif arg.startswith("invert="):
                    invert = arg.split("=")[1].lower() == "true"
            
            self.logger.debug(f"Conversion parameters: width={width}, height={height}, charset={char_set}, color={color}, scheme={color_scheme}, invert={invert}")
            
            # Resize image
            if width or height:
                self.image_processor.resize(width, height)
                
            # Initialize converter if needed
            if not self.ascii_converter:
                from core.ascii_converter import AsciiConverter
                self.ascii_converter = AsciiConverter()
            
            # Set character set
            self.ascii_converter.set_char_set(char_set)
            
            # Set color scheme
            self.ascii_converter.color_handler.set_color_scheme(color_scheme)
            
            # Convert to ASCII
            with self.perf.start_timer("ASCII conversion"):
                image_array = self.image_processor.to_array()
                if image_array is None:
                    self.logger.error("Failed to convert image to array")
                    print("Error: Failed to process image")
                    return
                    
                self.ascii_result = self.ascii_converter.image_to_ascii(
                    image_array, 
                    colored=color, 
                    invert=invert
                )
            
            if self.ascii_result:
                self.logger.info(f"Conversion complete: {len(self.ascii_result)} rows generated")
                print("Conversion complete")
            else:
                self.logger.error("Conversion failed to produce output")
                print("Error: Conversion failed")
                
        except Exception as e:
            self.logger.error(f"Error during conversion: {e}", exc_info=True)
            print(f"Error: {e}")
    
    def adjust(self, args):
        """Adjust image parameters"""
        if not self.image_processor:
            self.logger.warning("No image loaded for adjustment")
            print("No image loaded. Use 'load <image_path>' first")
            return
            
        self.logger.info(f"Adjusting image with args: {args}")
        
        try:
            # Parse arguments
            brightness = 1.0
            contrast = 1.0
            sharpness = 1.0
            filter_type = "none"
            
            for arg in args.split():
                if arg.startswith("brightness="):
                    brightness = float(arg.split("=")[1])
                elif arg.startswith("contrast="):
                    contrast = float(arg.split("=")[1])
                elif arg.startswith("sharpness="):
                    sharpness = float(arg.split("=")[1])
                elif arg.startswith("filter="):
                    filter_type = arg.split("=")[1]
            
            self.logger.debug(f"Adjustment parameters: brightness={brightness}, contrast={contrast}, sharpness={sharpness}, filter={filter_type}")
            
            # Apply adjustments
            self.image_processor.adjust(brightness, contrast, sharpness)
            if filter_type != "none":
                self.image_processor.apply_filter(filter_type)
                
            print(f"Applied adjustments: brightness={brightness}, contrast={contrast}, sharpness={sharpness}, filter={filter_type}")
            
        except Exception as e:
            self.logger.error(f"Error during image adjustment: {e}", exc_info=True)
            print(f"Error adjusting image: {e}")
    
    def view(self, args):
        """View current ASCII result in terminal"""
        if not self.ascii_result:
            self.logger.warning("No ASCII result available for viewing")
            print("No conversion result available. Use 'convert' first")
            return
            
        self.logger.info("Viewing ASCII result in terminal")
        
        try:
            # Initialize formatter if needed
            if not self.output_formatter:
                from core.output_formatter import OutputFormatter
                self.output_formatter = OutputFormatter()
                
            # Get terminal dimensions
            terminal_width, terminal_height = self._get_terminal_size()
            self.logger.debug(f"Terminal dimensions: {terminal_width}x{terminal_height}")
            
            # Limit preview height to terminal
            preview_rows = self.ascii_result[:terminal_height-5]  # Leave space for commands
            
            # Print ASCII art
            print("\n" + self.output_formatter.to_string(preview_rows))
            
        except Exception as e:
            self.logger.error(f"Error viewing ASCII result: {e}", exc_info=True)
            print(f"Error: {e}")
    
    def save(self, args):
        """Save current result to file"""
        if not self.ascii_result:
            self.logger.warning("No ASCII result available for saving")
            print("No conversion result available. Use 'convert' first")
            return
            
        self.logger.info(f"Saving ASCII result with args: {args}")
        
        try:
            # Parse arguments
            output_path = "ascii_art.txt"
            format_type = "txt"
            
            for arg in args.split():
                if arg.startswith("path="):
                    output_path = arg.split("=")[1]
                elif arg.startswith("format="):
                    format_type = arg.split("=")[1]
            
            self.logger.debug(f"Save parameters: path={output_path}, format={format_type}")
            
            # Initialize formatter if needed
            if not self.output_formatter:
                from core.output_formatter import OutputFormatter
                self.output_formatter = OutputFormatter()
                
            # Prepare output based on format
            with self.perf.start_timer(f"Save as {format_type}"):
                if format_type == "txt":
                    output = self.output_formatter.to_string(self.ascii_result)
                    self.output_formatter.save_to_file(output, output_path, format_type)
                    
                elif format_type == "html":
                    output = self.output_formatter.to_html(self.ascii_result)
                    self.output_formatter.save_to_file(output, output_path, format_type)
                    
                elif format_type in ["png", "jpg", "jpeg", "bmp", "gif"]:
                    # For image output we need to reformat data
                    self.ascii_converter.color_handler.set_output_mode("image")
                    image_data = self.ascii_converter.image_to_ascii(
                        self.image_processor.to_array(),
                        colored=True
                    )
                    image = self.output_formatter.to_image(image_data)
                    self.output_formatter.save_to_file(image, output_path, format_type)
                    
            self.logger.info(f"File saved: {output_path}")
            print(f"Saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving file: {e}", exc_info=True)
            print(f"Error saving file: {e}")
    
    def show_help(self, args):
        """Show help information"""
        self.logger.info("Showing help")
        help_text = """
Available commands:
  load <image_path>            - Load an image from file
  adjust [options]             - Adjust image (brightness, contrast, etc)
    Options: brightness=0.0-2.0 contrast=0.0-2.0 sharpness=0.0-2.0 filter=blur|sharpen|etc
  convert [options]            - Convert image to ASCII
    Options: width=N height=N charset=standard|detailed|simple|blocks|minimal color=true|false scheme=full_rgb|pastel|neon|grayscale invert=true|false
  view                         - Preview the current ASCII art in terminal
  save [options]               - Save the current result
    Options: path=filename format=txt|html|png|jpg
  debug [on|off]               - Toggle debug logging
  help                         - Show this help text
  exit                         - Exit the program
        """
        print(help_text)
    
    def toggle_debug(self, args):
        """Toggle debug logging"""
        from utils.config import Config
        config = Config()
        
        if args.lower() == "on":
            self.logger.info("Enabling debug mode")
            config.set('logging', 'level', 'DEBUG')
            print("Debug logging enabled")
        elif args.lower() == "off":
            self.logger.info("Disabling debug mode")
            config.set('logging', 'level', 'INFO')
            print("Debug logging disabled")
        else:
            # Toggle current state
            current_level = config.get('logging', 'level')
            if current_level == 'DEBUG':
                self.logger.info("Disabling debug mode")
                config.set('logging', 'level', 'INFO')
                print("Debug logging disabled")
            else:
                self.logger.info("Enabling debug mode")
                config.set('logging', 'level', 'DEBUG')
                print("Debug logging enabled")
    
    def exit(self, args):
        """Exit the program"""
        self.logger.info("Exiting application")
        print("Goodbye!")
        sys.exit(0)
    
    def _get_terminal_size(self):
        """Get terminal dimensions"""
        try:
            columns, lines = os.get_terminal_size()
            return columns, lines
        except Exception as e:
            self.logger.warning(f"Failed to get terminal size: {e}")
            return 80, 24  # Default fallback