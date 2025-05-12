import time
import threading
import cv2
import numpy as np
import os
import platform
import subprocess
from PIL import Image

class LiveWallpaper:
    def __init__(self, video_path=None, fps=15, width=100, height=50):
        self.video_path = video_path
        self.fps = fps
        self.width = width
        self.height = height
        self.running = False
        self.thread = None
        self.current_frame = None
        self.frame_count = 0
        
        # Components
        self.image_processor = None
        self.ascii_converter = None
        self.output_formatter = None
        
    def initialize(self):
        """Initialize components"""
        from core.image_processor import ImageProcessor
        from core.ascii_converter import AsciiConverter
        from core.output_formatter import OutputFormatter
        
        self.image_processor = ImageProcessor()
        self.ascii_converter = AsciiConverter()
        self.output_formatter = OutputFormatter()
        
    def load_video(self, video_path):
        """Load video from file"""
        self.video_path = video_path
        
    def start(self):
        """Start live wallpaper processing"""
        if not self.video_path:
            print("No video loaded")
            return False
            
        if not os.path.exists(self.video_path):
            print(f"Video file not found: {self.video_path}")
            return False
            
        if self.running:
            print("Live wallpaper is already running")
            return False
            
        self.initialize()
        self.running = True
        self.thread = threading.Thread(target=self._process_video)
        self.thread.daemon = True
        self.thread.start()
        return True
        
    def stop(self):
        """Stop live wallpaper processing"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        
    def _process_video(self):
        """Process video frames to ASCII in a separate thread"""
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                print(f"Error opening video file: {self.video_path}")
                self.running = False
                return
                
            frame_delay = 1.0 / self.fps
            
            while self.running:
                start_time = time.time()
                
                ret, frame = cap.read()
                if not ret:
                    # Loop back to beginning of video
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                # Convert frame from BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Load frame into image processor
                self.image_processor.load_from_image(Image.fromarray(frame_rgb))
                
                # Resize to target dimensions
                self.image_processor.resize(self.width, self.height)
                
                # Convert to ASCII
                image_array = self.image_processor.to_array()
                ascii_frame = self.ascii_converter.image_to_ascii(
                    image_array, 
                    colored=True,
                    invert=False
                )
                
                # Store current frame
                self.current_frame = ascii_frame
                self.frame_count += 1
                
                # Check if we should set as wallpaper
                if self.frame_count % 5 == 0:  # Update wallpaper every 5 frames
                    self._set_as_wallpaper()
                
                # Calculate delay for consistent frame rate
                process_time = time.time() - start_time
                if process_time < frame_delay:
                    time.sleep(frame_delay - process_time)
                    
            cap.release()
            
        except Exception as e:
            print(f"Error processing video: {e}")
            self.running = False
            
    def _set_as_wallpaper(self):
        """Set current ASCII frame as wallpaper"""
        if not self.current_frame:
            return
            
        # Initialize formatter if needed
        if not self.output_formatter:
            from core.output_formatter import OutputFormatter
            self.output_formatter = OutputFormatter()
            
        # Generate HTML for wallpaper
        html_content = self.output_formatter.to_html(self.current_frame)
        
        # Save to temporary file
        temp_file = os.path.join(os.path.expanduser("~"), "ascii_wallpaper_temp.html")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        # Set as wallpaper (platform dependent)
        system = platform.system()
        
        if system == "Windows":
            try:
                import ctypes
                # Convert to image first as Windows can't use HTML directly
                self.ascii_converter.color_handler.set_output_mode("image")
                image_data = self.ascii_converter.image_to_ascii(
                    self.image_processor.to_array(),
                    colored=True
                )
                image = self.output_formatter.to_image(image_data)
                
                # Save as PNG
                temp_img = os.path.join(os.path.expanduser("~"), "ascii_wallpaper_temp.png")
                image.save(temp_img)
                
                # Set as wallpaper
                ctypes.windll.user32.SystemParametersInfoW(20, 0, temp_img, 3)
            except Exception as e:
                print(f"Error setting Windows wallpaper: {e}")
                
        elif system == "Darwin":  # macOS
            try:
                script = f'''
                tell application "Finder"
                    set desktop picture to POSIX file "{temp_file}"
                end tell
                '''
                subprocess.run(["osascript", "-e", script])
            except Exception as e:
                print(f"Error setting macOS wallpaper: {e}")
                
        elif system == "Linux":
            try:
                # Attempt to detect desktop environment
                desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
                
                if "gnome" in desktop_env:
                    subprocess.run([
                        "gsettings", "set", "org.gnome.desktop.background",
                        "picture-uri", f"file://{temp_file}"
                    ])
                elif "kde" in desktop_env:
                    subprocess.run([
                        "qdbus", "org.kde.plasmashell", "/PlasmaShell",
                        "org.kde.PlasmaShell.evaluateScript",
                        f"var allDesktops = desktops();for (i=0;i<allDesktops.length;i++){{d = allDesktops[i];d.wallpaperPlugin = 'org.kde.image';d.currentConfigGroup = Array('Wallpaper','org.kde.image','General');d.writeConfig('Image','{temp_file}')}}"
                    ])
                else:
                    print(f"Unsupported Linux desktop environment: {desktop_env}")
            except Exception as e:
                print(f"Error setting Linux wallpaper: {e}")