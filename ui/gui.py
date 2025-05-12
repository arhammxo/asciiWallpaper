import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import io
import os
from utils.logger import Logger
from utils.performance import PerformanceLogger

class GUI:
    def __init__(self):
        self.logger = Logger().get_logger('gui')
        self.perf = PerformanceLogger()
        
        self.logger.info("Initializing GUI interface")
        
        self.root = tk.Tk()
        self.root.title("ASCII Art Wallpaper Generator")
        self.root.geometry("1200x800")
        
        # Set up error handler for Tkinter
        self._setup_exception_handler()
        
        self.image_processor = None
        self.ascii_converter = None
        self.output_formatter = None
        self.ascii_result = None
        self.current_image = None
        
        self.setup_ui()
    
    def _setup_exception_handler(self):
        """Set up custom exception handler for Tkinter"""
        old_report_callback = self.root.report_callback_exception
        
        def report_callback_exception(exc, val, tb):
            self.logger.critical("Unhandled exception in GUI:", exc_info=(exc, val, tb))
            messagebox.showerror("Error", f"An error occurred: {val}\nCheck the log file for details.")
            old_report_callback(exc, val, tb)
            
        self.root.report_callback_exception = report_callback_exception
    
    def setup_ui(self):
        """Create GUI elements"""
        # Main frames
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False)
        
        preview_frame = ttk.Frame(self.root, padding="10")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Control sections
        file_frame = ttk.LabelFrame(control_frame, text="Image", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        conversion_frame = ttk.LabelFrame(control_frame, text="Conversion", padding="10")
        conversion_frame.pack(fill=tk.X, pady=5)
        
        adjustment_frame = ttk.LabelFrame(control_frame, text="Adjustments", padding="10")
        adjustment_frame.pack(fill=tk.X, pady=5)
        
        output_frame = ttk.LabelFrame(control_frame, text="Output", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        # File section widgets
        ttk.Button(file_frame, text="Load Image", command=self.load_image).pack(fill=tk.X)
        
        # Preview elements
        self.preview_notebook = ttk.Notebook(preview_frame)
        self.preview_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Image preview tab
        self.image_preview_frame = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.image_preview_frame, text="Original Image")
        
        self.image_preview_label = ttk.Label(self.image_preview_frame)
        self.image_preview_label.pack(fill=tk.BOTH, expand=True)
        
        # ASCII preview tab
        self.ascii_preview_frame = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(self.ascii_preview_frame, text="ASCII Result")
        
        self.ascii_preview_text = tk.Text(self.ascii_preview_frame, wrap=tk.NONE, font=("Courier", 10))
        self.ascii_preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Add horizontal and vertical scrollbars for ASCII preview
        h_scrollbar = ttk.Scrollbar(self.ascii_preview_frame, orient=tk.HORIZONTAL, command=self.ascii_preview_text.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.ascii_preview_text.configure(xscrollcommand=h_scrollbar.set)
        
        v_scrollbar = ttk.Scrollbar(self.ascii_preview_frame, orient=tk.VERTICAL, command=self.ascii_preview_text.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ascii_preview_text.configure(yscrollcommand=v_scrollbar.set)
        
        # Conversion widgets
        ttk.Label(conversion_frame, text="Width:").grid(row=0, column=0, sticky=tk.W)
        self.width_var = tk.IntVar(value=100)
        ttk.Entry(conversion_frame, textvariable=self.width_var, width=10).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(conversion_frame, text="Height:").grid(row=1, column=0, sticky=tk.W)
        self.height_var = tk.IntVar(value=50)
        ttk.Entry(conversion_frame, textvariable=self.height_var, width=10).grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(conversion_frame, text="Character Set:").grid(row=2, column=0, sticky=tk.W)
        self.charset_var = tk.StringVar(value="standard")
        charset_combobox = ttk.Combobox(conversion_frame, textvariable=self.charset_var, width=15)
        charset_combobox['values'] = ('standard', 'detailed', 'simple', 'blocks', 'minimal')
        charset_combobox.grid(row=2, column=1, padx=5, pady=2)
        
        self.color_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(conversion_frame, text="Use Color", variable=self.color_var).grid(row=3, column=0, columnspan=2, sticky=tk.W)
        
        self.invert_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(conversion_frame, text="Invert", variable=self.invert_var).grid(row=4, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(conversion_frame, text="Color Scheme:").grid(row=5, column=0, sticky=tk.W)
        self.color_scheme_var = tk.StringVar(value="full_rgb")
        scheme_combobox = ttk.Combobox(conversion_frame, textvariable=self.color_scheme_var, width=15)
        scheme_combobox['values'] = ('full_rgb', 'pastel', 'neon', 'grayscale')
        scheme_combobox.grid(row=5, column=1, padx=5, pady=2)
        
        ttk.Button(conversion_frame, text="Convert", command=self.convert_image).grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # Adjustment widgets
        ttk.Label(adjustment_frame, text="Brightness:").grid(row=0, column=0, sticky=tk.W)
        self.brightness_var = tk.DoubleVar(value=1.0)
        ttk.Scale(adjustment_frame, from_=0.1, to=2.0, orient=tk.HORIZONTAL, variable=self.brightness_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(adjustment_frame, text="Contrast:").grid(row=1, column=0, sticky=tk.W)
        self.contrast_var = tk.DoubleVar(value=1.0)
        ttk.Scale(adjustment_frame, from_=0.1, to=2.0, orient=tk.HORIZONTAL, variable=self.contrast_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(adjustment_frame, text="Filter:").grid(row=2, column=0, sticky=tk.W)
        self.filter_var = tk.StringVar(value="none")
        filter_combobox = ttk.Combobox(adjustment_frame, textvariable=self.filter_var, width=15)
        filter_combobox['values'] = ('none', 'blur', 'contour', 'edge_enhance', 'emboss', 'sharpen', 'smooth')
        filter_combobox.grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Button(adjustment_frame, text="Apply", command=self.apply_adjustments).grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # Output widgets
        ttk.Label(output_frame, text="Format:").grid(row=0, column=0, sticky=tk.W)
        self.format_var = tk.StringVar(value="txt")
        format_combobox = ttk.Combobox(output_frame, textvariable=self.format_var, width=15)
        format_combobox['values'] = ('txt', 'html', 'png', 'jpg')
        format_combobox.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Button(output_frame, text="Save", command=self.save_output).grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=10)
    
    def load_image(self):
        """Open file dialog and load image"""
        self.logger.info("Opening file dialog to load image")
        
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[
                    ("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                self.logger.info("No file selected")
                return
                
            self.logger.info(f"Selected file: {file_path}")
            
            with self.perf.start_timer("Load image"):
                from core.image_processor import ImageProcessor
                self.image_processor = ImageProcessor(file_path)
                
                if not self.image_processor.image:
                    self.logger.error(f"Failed to load image: {file_path}")
                    messagebox.showerror("Error", "Failed to load image")
                    return
                
                # Display preview
                self.current_image = Image.open(file_path)
                self.update_image_preview()
                
                # Select the image preview tab
                self.preview_notebook.select(0)
                
                self.logger.info("Image loaded successfully")
                messagebox.showinfo("Success", "Image loaded successfully")
                
        except Exception as e:
            self.logger.error(f"Error loading image: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to load image: {e}")
    
    def update_image_preview(self):
        """Update the image preview"""
        if not self.current_image:
            return
            
        # Calculate preview size
        preview_width = self.image_preview_frame.winfo_width() - 20
        preview_height = self.image_preview_frame.winfo_height() - 20
        
        if preview_width <= 0:
            preview_width = 400
        if preview_height <= 0:
            preview_height = 400
            
        # Resize image for preview
        img_width, img_height = self.current_image.size
        ratio = min(preview_width / img_width, preview_height / img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        preview_img = self.current_image.resize((new_width, new_height), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(preview_img)
        
        # Update label
        self.image_preview_label.configure(image=tk_img)
        self.image_preview_label.image = tk_img  # Keep reference
    
    def convert_image(self):
        """Convert image to ASCII"""
        if not self.image_processor:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            # Get parameters
            width = self.width_var.get()
            height = self.height_var.get()
            
            # Resize image
            self.image_processor.resize(width, height)
            
            # Initialize converter if needed
            if not self.ascii_converter:
                from core.ascii_converter import AsciiConverter
                self.ascii_converter = AsciiConverter()
                
            # Initialize formatter if needed
            if not self.output_formatter:
                from core.output_formatter import OutputFormatter
                self.output_formatter = OutputFormatter()
            
            # Set character set
            self.ascii_converter.set_char_set(self.charset_var.get())
            
            # Set color scheme
            self.ascii_converter.color_handler.set_color_scheme(self.color_scheme_var.get())
            
            # Convert to ASCII
            image_array = self.image_processor.to_array()
            self.ascii_result = self.ascii_converter.image_to_ascii(
                image_array, 
                colored=self.color_var.get(), 
                invert=self.invert_var.get()
            )
            
            # Update preview
            self.update_ascii_preview()
            
            # Select the ASCII preview tab
            self.preview_notebook.select(1)
            
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {e}")
    
    def update_ascii_preview(self):
        """Update the ASCII preview text"""
        if not self.ascii_result:
            return
            
        # Clear current text
        self.ascii_preview_text.delete(1.0, tk.END)
        
        # Insert new ASCII art
        if self.format_var.get() == "html":
            # For HTML preview, show formatted text
            html_content = self.output_formatter.to_html(self.ascii_result)
            self.ascii_preview_text.insert(tk.END, html_content)
        else:
            # For text preview, show plain text
            text_content = self.output_formatter.to_string(self.ascii_result)
            self.ascii_preview_text.insert(tk.END, text_content)
    
    def apply_adjustments(self):
        """Apply image adjustments"""
        if not self.image_processor:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            # Get adjustment values
            brightness = self.brightness_var.get()
            contrast = self.contrast_var.get()
            filter_type = self.filter_var.get()
            
            # Apply adjustments
            self.image_processor.adjust(brightness=brightness, contrast=contrast)
            if filter_type != "none":
                self.image_processor.apply_filter(filter_type)
                
            # Update current image for preview
            img_array = self.image_processor.to_array()
            self.current_image = Image.fromarray(img_array)
            
            # Update previews
            self.update_image_preview()
            
            # If ASCII result exists, update it too
            if self.ascii_result:
                self.convert_image()
                
            messagebox.showinfo("Success", "Adjustments applied")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply adjustments: {e}")
    
    def save_output(self):
        """Save current ASCII result"""
        if not self.ascii_result:
            messagebox.showwarning("Warning", "No ASCII art generated yet")
            return
            
        # Get format
        format_type = self.format_var.get()
        
        # Get file path
        file_extensions = {
            "txt": "*.txt",
            "html": "*.html",
            "png": "*.png",
            "jpg": "*.jpg"
        }
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{format_type}",
            filetypes=[(f"{format_type.upper()} files", file_extensions[format_type]), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Initialize formatter if needed
            if not self.output_formatter:
                from core.output_formatter import OutputFormatter
                self.output_formatter = OutputFormatter()
                
            # Prepare output based on format
            if format_type == "txt":
                output = self.output_formatter.to_string(self.ascii_result)
                self.output_formatter.save_to_file(output, file_path, format_type)
                
            elif format_type == "html":
                output = self.output_formatter.to_html(self.ascii_result)
                self.output_formatter.save_to_file(output, file_path, format_type)
                
            elif format_type in ["png", "jpg"]:
                # For image output we need to reformat data
                self.ascii_converter.color_handler.set_output_mode("image")
                image_data = self.ascii_converter.image_to_ascii(
                    self.image_processor.to_array(),
                    colored=True
                )
                image = self.output_formatter.to_image(image_data)
                self.output_formatter.save_to_file(image, file_path, format_type)
                
            messagebox.showinfo("Success", f"Saved to {file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
    
    def run(self):
        """Start the GUI application"""
        # Bind event for window resize
        self.root.bind("<Configure>", lambda e: self.update_image_preview())
        
        # Start main loop
        self.root.mainloop()