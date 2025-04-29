import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageEnhance
import os
import logging
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any
import tifffile


class TiffViewer16Bit:
    def __init__(self, master):
        self.master = master
        master.title("MXA Acquired Image")
        self.setup_logging()
        self.initialize_variables()
        self.create_ui()
        self.bind_events()

    def setup_logging(self):
        """Configure logging for the application"""
        logging.basicConfig(
            filename='tiff_viewer.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def initialize_variables(self):
        """Initialize all instance variables"""
        self.file_path = None
        self.image = None
        self.photo = None
        self.original_image = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0
        self.brightness = 1.0
        self.contrast = 1.0
        self.metadata_window = None

    def create_ui(self):
        """Create the user interface"""
        # File Path Label
        self.file_label = ttk.Label(self.master, text="No file selected")
        self.file_label.pack(pady=5)

        # Main Frame
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas Frame (Left Side)
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Canvas for Image Display
        self.canvas = tk.Canvas(self.canvas_frame, width=800, height=600, bg='gray90')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Controls Frame (Right Side)
        self.controls_frame = ttk.Frame(self.main_frame, padding="5 5 5 5")
        self.controls_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        self.create_buttons()
        self.create_adjustment_controls()

        # Status Bar
        self.status_bar = ttk.Label(self.master, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Menu Bar
        self.create_menu()

    def create_buttons(self):
        """Create control buttons"""
        button_frame = ttk.Frame(self.controls_frame)
        button_frame.pack(fill=tk.X, pady=5)

        # Search Button
        self.search_button = ttk.Button(
            button_frame,
            text="Search",
            command=self.search_file
        )
        self.search_button.pack(fill=tk.X, pady=2)

        # Metadata Button
        self.metadata_button = ttk.Button(
            button_frame,
            text="Show Metadata",
            command=self.show_metadata_window
        )
        self.metadata_button.pack(fill=tk.X, pady=2)

    def create_adjustment_controls(self):
        """Create image adjustment controls"""
        # Brightness control
        ttk.Label(self.controls_frame, text="Brightness:").pack(fill=tk.X, pady=(10, 0))
        self.brightness_scale = ttk.Scale(
            self.controls_frame,
            from_=0.1, to=2.0,
            value=1.0,
            orient=tk.HORIZONTAL,
            command=self.update_brightness
        )
        self.brightness_scale.pack(fill=tk.X)

        # Contrast control
        ttk.Label(self.controls_frame, text="Contrast:").pack(fill=tk.X, pady=(10, 0))
        self.contrast_scale = ttk.Scale(
            self.controls_frame,
            from_=0.1, to=2.0,
            value=1.0,
            orient=tk.HORIZONTAL,
            command=self.update_contrast
        )
        self.contrast_scale.pack(fill=tk.X)

        # Image info frame
        self.info_frame = ttk.LabelFrame(self.controls_frame, text="Image Info", padding=5)
        self.info_frame.pack(fill=tk.X, pady=5)
        self.info_label = ttk.Label(self.info_frame, text="No image loaded")
        self.info_label.pack(fill=tk.X)

    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.master)

        # File Menu
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        filemenu.add_command(label="Save View", command=self.save_current_view)
        filemenu.add_separator()
        filemenu.add_command(label="Show Metadata", command=self.show_metadata_window)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        self.master.config(menu=menubar)

    def bind_events(self):
        """Bind keyboard and mouse events"""
        self.master.bind('<Control-o>', lambda e: self.open_file())
        self.canvas.bind('<MouseWheel>', self.handle_zoom)
        self.canvas.bind('<Button-1>', self.start_pan)
        self.canvas.bind('<B1-Motion>', self.pan_image)

    def extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata from TIFF file"""
        try:
            with tifffile.TiffFile(self.file_path) as tif:
                metadata = {}
                for page in tif.pages:
                    for tag in page.tags.values():
                        if tag.name == "ImageDescription":
                            description = tag.value
                            try:
                                root = ET.fromstring(description)
                                for prop in root.findall('.//prop'):
                                    prop_id = prop.get('id')
                                    prop_type = prop.get('type')
                                    prop_value = prop.get('value')
                                    try:
                                        if prop_type == "int":
                                            prop_value = int(prop_value)
                                        elif prop_type == "float":
                                            prop_value = float(prop_value)
                                        metadata[prop_id] = prop_value
                                    except (ValueError, TypeError):
                                        self.logger.warning(
                                            f"Could not convert value '{prop_value}' to type '{prop_type}' for id '{prop_id}'"
                                        )
                            except ET.ParseError as e:
                                self.logger.error(f"XML Parse Error: {e}")
                return metadata
        except Exception as e:
            self.logger.error(f"Error reading TIFF metadata: {e}")
            return {}

    def show_metadata_window(self):
        """Display metadata in a new window"""
        if not self.file_path:
            messagebox.showwarning("Warning", "Please open a TIFF file first.")
            return

        # Create new window or focus existing
        if self.metadata_window and self.metadata_window.winfo_exists():
            self.metadata_window.lift()
            return

        self.metadata_window = tk.Toplevel(self.master)
        self.metadata_window.title("Image Metadata")
        self.metadata_window.geometry("600x400")

        # Create text widget with scrollbar
        frame = ttk.Frame(self.metadata_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text_widget.pack(fill=tk.BOTH, expand=True)

        scrollbar.config(command=text_widget.yview)

        # Extract and display metadata
        metadata = self.extract_metadata()
        if metadata:
            text_widget.insert(tk.END, "Image Metadata:\n\n")
            for key, value in metadata.items():
                text_widget.insert(tk.END, f"{key}: {value}\n")
        else:
            text_widget.insert(tk.END, "No metadata found or error extracting metadata.")

        text_widget.config(state=tk.DISABLED)

    def open_file(self, file_path=None):
        """Open and load a TIFF file"""
        try:
            if not file_path:
                file_path = filedialog.askopenfilename(
                    defaultextension=".tif",
                    filetypes=[("TIFF files", "*.tif;*.tiff"), ("All files", "*.*")]
                )

            if file_path:
                self.file_path = file_path
                self.image = Image.open(self.file_path)
                self.original_image = self.image.copy()

                if self.image.mode not in ("I;16", "I;16B", "I;16L", "I"):
                    self.logger.warning(f"Non-16-bit image opened: {self.image.mode}")
                    messagebox.showwarning(
                        "Warning",
                        "This is not a 16-bit image. It will be displayed, but unexpected results may occur."
                    )

                self.total_pages = getattr(self.image, "n_frames", 1)
                self.current_page = 0
                self.show_image()
                self.update_image_info()
                self.file_label.config(text=os.path.basename(file_path))
                self.status_bar.config(text=f"Loaded: {os.path.basename(file_path)}")

        except Exception as e:
            self.logger.error(f"Error opening file: {str(e)}")
            messagebox.showerror("Error", f"Failed to open TIFF file:\n{str(e)}")

    def show_image(self):
        """Display the current image on the canvas"""
        if not self.image:
            return

        try:
            # Process image
            working_image = self.image
            if self.image.mode == "I;16":
                working_image = working_image.point(lambda i: i * (1. / 256)).convert('L')

            # Apply adjustments
            working_image = ImageEnhance.Brightness(working_image).enhance(self.brightness)
            working_image = ImageEnhance.Contrast(working_image).enhance(self.contrast)

            # Convert to RGB if necessary
            if working_image.mode != "RGB":
                working_image = working_image.convert("RGB")

            # Calculate dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            image_width, image_height = working_image.size

            # Apply zoom
            new_width = int(image_width * self.zoom_level)
            new_height = int(image_height * self.zoom_level)

            resized_image = working_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(resized_image)

            # Clear and update canvas
            self.canvas.delete("all")
            self.canvas.create_image(
                canvas_width // 2, canvas_height // 2,
                anchor=tk.CENTER, image=self.photo
            )

        except Exception as e:
            self.logger.error(f"Error displaying image: {str(e)}")
            messagebox.showerror("Error", f"Failed to display the image:\n{str(e)}")

    def search_file(self):
        """Search for a file by name"""
        keyword = simpledialog.askstring("Search", "Enter the exact file name:")
        if keyword:
            file_path = self.find_file(keyword)
            if file_path:
                self.open_file(file_path)
            else:
                messagebox.showinfo(
                    "Not Found",
                    f"No file named '{keyword}' found in D: or C: drives."
                )

    def find_file(self, filename):
        """Find a file in the specified drives"""
        # First, search in D drive
        for root, _, files in os.walk("D:\\"):
            if filename in files:
                return os.path.join(root, filename)

        # If not found in D, search in C drive
        for root, _, files in os.walk("C:\\"):
            if filename in files:
                return os.path.join(root, filename)

        return None

    def update_image_info(self):
        """Update image information display"""
        if self.image:
            info_text = (
                f"Size: {self.image.size}\n"
                f"Mode: {self.image.mode}\n"
                f"Format: {self.image.format}\n"
                f"Pages: {self.total_pages}"
            )
            self.info_label.config(text=info_text)

    def handle_zoom(self, event):
        """Handle mouse wheel zoom events"""
        if event.delta > 0:
            self.zoom_level *= 1.1
        else:
            self.zoom_level /= 1.1
        self.zoom_level = max(0.1, min(5.0, self.zoom_level))
        self.show_image()

    def start_pan(self, event):
        """Start image panning"""
        self.canvas.scan_mark(event.x, event.y)

    def pan_image(self, event):
        """Continue image panning"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def update_brightness(self, value):
        """Update image brightness"""
        self.brightness = float(value)
        self.show_image()

    def update_contrast(self, value):
        """Update image contrast"""
        self.contrast = float(value)
        self.show_image()

    def save_current_view(self):
        """Save the current view of the image"""
        if not self.photo:
            return

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
            )
            if file_path:
                self.photo._PhotoImage__photo.write(file_path, format="png")
                self.status_bar.config(text=f"Saved view as: {os.path.basename(file_path)}")
        except Exception as e:
            self.logger.error(f"Error saving view: {str(e)}")
            messagebox.showerror("Error", f"Failed to save the current view:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TiffViewer16Bit(root)
    root.mainloop()