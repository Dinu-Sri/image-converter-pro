"""
Image Converter & Cutter Tool
A fast, portable tool for converting images with advanced features for web and graphic designers.
"""

import sys
import os
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QSpinBox, QFileDialog, QListWidget,
    QGroupBox, QRadioButton, QProgressBar, QMessageBox, QTabWidget,
    QCheckBox, QComboBox, QLineEdit, QTextEdit, QSplitter, QFrame,
    QScrollArea, QListWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent, QFont
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS
import io


class ImageProcessor(QThread):
    """Thread for processing images without blocking the UI"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    stats_update = pyqtSignal(dict)
    
    def __init__(self, files, output_dir, settings):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.settings = settings
        self.total_original_size = 0
        self.total_new_size = 0
        
    def run(self):
        try:
            total = len(self.files)
            for idx, file_path in enumerate(self.files):
                self.process_image(file_path)
                self.progress.emit(int((idx + 1) / total * 100))
            
            # Send final statistics
            stats = {
                'total_files': total,
                'original_size': self.total_original_size,
                'new_size': self.total_new_size,
                'savings': self.total_original_size - self.total_new_size,
                'percentage': ((self.total_original_size - self.total_new_size) / self.total_original_size * 100) if self.total_original_size > 0 else 0
            }
            self.stats_update.emit(stats)
            self.finished.emit(f"Successfully processed {total} image(s)")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")
    
    def process_image(self, file_path):
        """Process a single image with all settings"""
        # Track original file size
        original_size = os.path.getsize(file_path)
        self.total_original_size += original_size
        
        img = Image.open(file_path)
        
        # Strip metadata if requested
        if self.settings.get('strip_metadata', False):
            # Remove EXIF data by creating new image
            img = img.copy()
        
        # Resize if requested
        if self.settings.get('resize_enabled', False):
            img = self.resize_image(img, self.settings)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Add watermark if requested
        if self.settings.get('watermark_enabled', False):
            img = self.add_watermark(img, self.settings)
        
        base_name = Path(file_path).stem
        output_format = self.settings.get('output_format', 'webp').lower()
        
        # Apply filename prefix/suffix
        prefix = self.settings.get('filename_prefix', '')
        suffix = self.settings.get('filename_suffix', '')
        base_name = f"{prefix}{base_name}{suffix}"
        
        cut_mode = self.settings.get('cut_mode', 'none')
        
        if cut_mode == 'none':
            # Just convert
            output_path = os.path.join(self.output_dir, f"{base_name}.{output_format}")
            self.save_image(img, output_path, self.settings)
        else:
            # Cut image in half
            width, height = img.size
            
            if cut_mode == 'horizontal':
                half_height = height // 2
                top_half = img.crop((0, 0, width, half_height))
                bottom_half = img.crop((0, half_height, width, height))
                
                top_path = os.path.join(self.output_dir, f"{base_name}_top.{output_format}")
                bottom_path = os.path.join(self.output_dir, f"{base_name}_bottom.{output_format}")
                
                self.save_image(top_half, top_path, self.settings)
                self.save_image(bottom_half, bottom_path, self.settings)
            
            elif cut_mode == 'vertical':
                half_width = width // 2
                left_half = img.crop((0, 0, half_width, height))
                right_half = img.crop((half_width, 0, width, height))
                
                left_path = os.path.join(self.output_dir, f"{base_name}_left.{output_format}")
                right_path = os.path.join(self.output_dir, f"{base_name}_right.{output_format}")
                
                self.save_image(left_half, left_path, self.settings)
                self.save_image(right_half, right_path, self.settings)
    
    def resize_image(self, img, settings):
        """Resize image based on settings"""
        resize_mode = settings.get('resize_mode', 'width')
        maintain_aspect = settings.get('maintain_aspect', True)
        
        if resize_mode == 'preset':
            target_width = settings.get('preset_width', 1920)
            if maintain_aspect:
                ratio = target_width / img.width
                target_height = int(img.height * ratio)
            else:
                target_height = img.height
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        elif resize_mode == 'custom':
            target_width = settings.get('custom_width', img.width)
            target_height = settings.get('custom_height', img.height)
            if maintain_aspect:
                img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
            else:
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        elif resize_mode == 'percentage':
            scale = settings.get('scale_percentage', 100) / 100
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return img
    
    def add_watermark(self, img, settings):
        """Add text watermark to image"""
        watermark_text = settings.get('watermark_text', '')
        if not watermark_text:
            return img
        
        # Create a copy to draw on
        img_copy = img.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # Try to use a better font, fall back to default
        font_size = settings.get('watermark_size', 36)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Get text size
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position
        position = settings.get('watermark_position', 'bottom-right')
        margin = 20
        
        if position == 'top-left':
            x, y = margin, margin
        elif position == 'top-right':
            x, y = img.width - text_width - margin, margin
        elif position == 'bottom-left':
            x, y = margin, img.height - text_height - margin
        elif position == 'bottom-right':
            x, y = img.width - text_width - margin, img.height - text_height - margin
        else:  # center
            x, y = (img.width - text_width) // 2, (img.height - text_height) // 2
        
        # Draw watermark with opacity
        opacity = settings.get('watermark_opacity', 128)
        watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw_watermark = ImageDraw.Draw(watermark)
        draw_watermark.text((x, y), watermark_text, font=font, fill=(255, 255, 255, opacity))
        
        # Composite
        img_copy = img_copy.convert('RGBA')
        img_copy = Image.alpha_composite(img_copy, watermark)
        img_copy = img_copy.convert('RGB')
        
        return img_copy
    
    def save_image(self, img, output_path, settings):
        """Save image with format-specific options and target file size"""
        output_format = settings.get('output_format', 'webp').lower()
        quality = settings.get('quality', 85)
        target_size_kb = settings.get('target_size_kb', 0)
        
        if target_size_kb > 0:
            # Iteratively adjust quality to meet target size
            quality = self.find_quality_for_target_size(img, output_format, target_size_kb * 1024)
        
        # Save with format-specific options
        if output_format == 'webp':
            img.save(output_path, 'WEBP', quality=quality, method=6)
        elif output_format in ['jpg', 'jpeg']:
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
        elif output_format == 'png':
            # PNG doesn't use quality, use optimize instead
            img.save(output_path, 'PNG', optimize=True)
        
        # Track new file size
        if os.path.exists(output_path):
            self.total_new_size += os.path.getsize(output_path)
    
    def find_quality_for_target_size(self, img, output_format, target_size_bytes):
        """Binary search to find the right quality for target file size"""
        low, high = 1, 100
        best_quality = 85
        
        for _ in range(10):  # Max 10 iterations
            mid = (low + high) // 2
            
            # Test save to memory
            buffer = io.BytesIO()
            if output_format == 'webp':
                img.save(buffer, 'WEBP', quality=mid, method=6)
            elif output_format in ['jpg', 'jpeg']:
                img.save(buffer, 'JPEG', quality=mid, optimize=True)
            else:
                return mid  # PNG doesn't support quality
            
            size = buffer.tell()
            
            if size <= target_size_bytes:
                best_quality = mid
                low = mid + 1
            else:
                high = mid - 1
        
        return best_quality


class ImageConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_files = []
        self.output_directory = ""
        self.setAcceptDrops(True)  # Enable drag and drop
        self.init_ui()
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp']
        
        for file in files:
            if Path(file).suffix.lower() in image_extensions and file not in self.selected_files:
                self.selected_files.append(file)
                item = QListWidgetItem(Path(file).name)
                item.setToolTip(file)
                self.file_list.addItem(item)
        
        self.update_status()
        if self.selected_files:
            self.update_preview()
        
    def init_ui(self):
        self.setWindowTitle("Image Converter & Cutter Pro")
        self.setGeometry(100, 100, 1000, 700)
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), 'app_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create tabs
        self.create_files_tab()
        self.create_convert_tab()
        self.create_resize_tab()
        self.create_advanced_tab()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # Process button
        self.btn_process = QPushButton("🚀 Process Images")
        self.btn_process.setStyleSheet("""
            QPushButton { 
                font-size: 16px; 
                padding: 12px; 
                background-color: #4CAF50; 
                color: white; 
                border-radius: 5px;
                font-weight: bold;
            } 
            QPushButton:hover { 
                background-color: #45a049; 
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.btn_process.clicked.connect(self.process_images)
        main_layout.addWidget(self.btn_process)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Statistics label
        self.stats_label = QLabel("")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        main_layout.addWidget(self.stats_label)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_left = QLabel("Made by Dr. Dinu Sri Madusanka")
        footer_left.setStyleSheet("color: gray; font-size: 10px;")
        footer_right = QLabel("Supported: PNG, JPG, JPEG, BMP, GIF, TIFF, WebP")
        footer_right.setStyleSheet("color: gray; font-size: 10px;")
        footer_right.setAlignment(Qt.AlignRight)
        footer_layout.addWidget(footer_left)
        footer_layout.addStretch()
        footer_layout.addWidget(footer_right)
        main_layout.addLayout(footer_layout)
        main_layout.addLayout(footer_layout)
    
    def create_files_tab(self):
        """Files and preview tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Left side - File list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        file_group = QGroupBox("📁 Image Selection (Drag & Drop or Click)")
        file_layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        self.btn_add_files = QPushButton("➕ Add Images")
        self.btn_add_files.clicked.connect(self.add_files)
        self.btn_clear = QPushButton("🗑️ Clear All")
        self.btn_clear.clicked.connect(self.clear_files)
        btn_layout.addWidget(self.btn_add_files)
        btn_layout.addWidget(self.btn_clear)
        file_layout.addLayout(btn_layout)
        
        self.file_list = QListWidget()
        self.file_list.currentItemChanged.connect(self.update_preview)
        file_layout.addWidget(self.file_list)
        
        # File info
        self.file_info_label = QLabel("No file selected")
        self.file_info_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        file_layout.addWidget(self.file_info_label)
        
        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)
        
        # Output directory
        output_group = QGroupBox("💾 Output Settings")
        output_layout = QVBoxLayout()
        
        dir_layout = QHBoxLayout()
        output_label = QLabel("Output Folder:")
        self.output_path_label = QLabel("(Auto: 'processed images' folder)")
        self.output_path_label.setStyleSheet("color: gray;")
        self.btn_output_dir = QPushButton("📂 Choose Folder")
        self.btn_output_dir.clicked.connect(self.choose_output_directory)
        self.btn_open_folder = QPushButton("📁 Open Folder")
        self.btn_open_folder.clicked.connect(self.open_output_folder)
        self.btn_open_folder.setEnabled(False)
        
        dir_layout.addWidget(output_label)
        dir_layout.addWidget(self.output_path_label, 1)
        dir_layout.addWidget(self.btn_output_dir)
        dir_layout.addWidget(self.btn_open_folder)
        output_layout.addLayout(dir_layout)
        
        # Filename options
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("Prefix:"))
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("e.g., web_")
        filename_layout.addWidget(self.prefix_input)
        filename_layout.addWidget(QLabel("Suffix:"))
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("e.g., _optimized")
        filename_layout.addWidget(self.suffix_input)
        output_layout.addLayout(filename_layout)
        
        output_group.setLayout(output_layout)
        left_layout.addWidget(output_group)
        
        # Right side - Preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        preview_group = QGroupBox("🖼️ Image Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel("Select an image to preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 400)
        self.preview_label.setStyleSheet("background-color: #f9f9f9; border: 2px dashed #ccc;")
        self.preview_label.setScaledContents(False)
        
        scroll = QScrollArea()
        scroll.setWidget(self.preview_label)
        scroll.setWidgetResizable(True)
        preview_layout.addWidget(scroll)
        
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        
        # Add to splitter for resizable sections
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
        self.tabs.addTab(tab, "📁 Files & Preview")
    
    def create_convert_tab(self):
        """Conversion settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Output format
        format_group = QGroupBox("🎨 Output Format")
        format_layout = QVBoxLayout()
        
        format_buttons = QHBoxLayout()
        self.format_webp = QRadioButton("WebP (Recommended)")
        self.format_jpg = QRadioButton("JPG/JPEG")
        self.format_png = QRadioButton("PNG")
        self.format_webp.setChecked(True)
        
        format_buttons.addWidget(self.format_webp)
        format_buttons.addWidget(self.format_jpg)
        format_buttons.addWidget(self.format_png)
        format_buttons.addStretch()
        format_layout.addLayout(format_buttons)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Quality settings
        quality_group = QGroupBox("⚙️ Quality Settings")
        quality_layout = QVBoxLayout()
        
        quality_control = QHBoxLayout()
        quality_label = QLabel("Quality:")
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(85)
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(10)
        
        self.quality_spinbox = QSpinBox()
        self.quality_spinbox.setMinimum(1)
        self.quality_spinbox.setMaximum(100)
        self.quality_spinbox.setValue(85)
        self.quality_spinbox.setSuffix("%")
        
        self.quality_slider.valueChanged.connect(self.quality_spinbox.setValue)
        self.quality_spinbox.valueChanged.connect(self.quality_slider.setValue)
        
        quality_control.addWidget(quality_label)
        quality_control.addWidget(self.quality_slider)
        quality_control.addWidget(self.quality_spinbox)
        quality_layout.addLayout(quality_control)
        
        # Quality presets
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Presets:")
        btn_low = QPushButton("Low (60%)")
        btn_medium = QPushButton("Medium (85%)")
        btn_high = QPushButton("High (95%)")
        
        btn_low.clicked.connect(lambda: self.quality_slider.setValue(60))
        btn_medium.clicked.connect(lambda: self.quality_slider.setValue(85))
        btn_high.clicked.connect(lambda: self.quality_slider.setValue(95))
        
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(btn_low)
        preset_layout.addWidget(btn_medium)
        preset_layout.addWidget(btn_high)
        preset_layout.addStretch()
        quality_layout.addLayout(preset_layout)
        
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)
        
        # Target file size
        target_group = QGroupBox("🎯 Target File Size (Optional)")
        target_layout = QHBoxLayout()
        
        self.target_size_check = QCheckBox("Compress to target size:")
        self.target_size_spinbox = QSpinBox()
        self.target_size_spinbox.setMinimum(10)
        self.target_size_spinbox.setMaximum(10000)
        self.target_size_spinbox.setValue(500)
        self.target_size_spinbox.setSuffix(" KB")
        self.target_size_spinbox.setEnabled(False)
        
        self.target_size_check.toggled.connect(self.target_size_spinbox.setEnabled)
        self.target_size_check.toggled.connect(lambda checked: self.quality_slider.setEnabled(not checked))
        self.target_size_check.toggled.connect(lambda checked: self.quality_spinbox.setEnabled(not checked))
        
        target_layout.addWidget(self.target_size_check)
        target_layout.addWidget(self.target_size_spinbox)
        target_layout.addStretch()
        
        info_label = QLabel("ℹ️ Quality will be automatically adjusted to meet target size")
        info_label.setStyleSheet("color: #666; font-size: 10px;")
        
        target_group_layout = QVBoxLayout()
        target_group_layout.addLayout(target_layout)
        target_group_layout.addWidget(info_label)
        target_group.setLayout(target_group_layout)
        layout.addWidget(target_group)
        
        # Cut mode
        cut_group = QGroupBox("✂️ Image Cutting Options")
        cut_layout = QVBoxLayout()
        
        self.radio_no_cut = QRadioButton("No cutting (convert only)")
        self.radio_horizontal = QRadioButton("Cut horizontally (top/bottom)")
        self.radio_vertical = QRadioButton("Cut vertically (left/right)")
        self.radio_no_cut.setChecked(True)
        
        cut_layout.addWidget(self.radio_no_cut)
        cut_layout.addWidget(self.radio_horizontal)
        cut_layout.addWidget(self.radio_vertical)
        
        cut_group.setLayout(cut_layout)
        layout.addWidget(cut_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "🎨 Convert & Quality")
    
    def create_resize_tab(self):
        """Resize settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Enable resize
        self.resize_enabled = QCheckBox("📐 Enable Image Resizing")
        self.resize_enabled.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.resize_enabled)
        
        # Resize options container
        self.resize_container = QWidget()
        resize_layout = QVBoxLayout(self.resize_container)
        
        # Resize presets
        preset_group = QGroupBox("📱 Common Web Sizes (Width-based)")
        preset_layout = QVBoxLayout()
        
        self.resize_preset = QRadioButton("Use preset width")
        self.resize_preset.setChecked(True)
        preset_layout.addWidget(self.resize_preset)
        
        preset_buttons = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "1920px (Full HD)",
            "1200px (Desktop)",
            "800px (Tablet)",
            "400px (Mobile)"
        ])
        preset_buttons.addWidget(QLabel("Select:"))
        preset_buttons.addWidget(self.preset_combo)
        preset_buttons.addStretch()
        preset_layout.addLayout(preset_buttons)
        
        preset_group.setLayout(preset_layout)
        resize_layout.addWidget(preset_group)
        
        # Custom dimensions
        custom_group = QGroupBox("✏️ Custom Dimensions")
        custom_layout = QVBoxLayout()
        
        self.resize_custom = QRadioButton("Use custom dimensions")
        custom_layout.addWidget(self.resize_custom)
        
        dims_layout = QHBoxLayout()
        dims_layout.addWidget(QLabel("Width:"))
        self.custom_width = QSpinBox()
        self.custom_width.setMinimum(1)
        self.custom_width.setMaximum(10000)
        self.custom_width.setValue(1920)
        self.custom_width.setSuffix(" px")
        dims_layout.addWidget(self.custom_width)
        
        dims_layout.addWidget(QLabel("Height:"))
        self.custom_height = QSpinBox()
        self.custom_height.setMinimum(1)
        self.custom_height.setMaximum(10000)
        self.custom_height.setValue(1080)
        self.custom_height.setSuffix(" px")
        dims_layout.addWidget(self.custom_height)
        dims_layout.addStretch()
        custom_layout.addLayout(dims_layout)
        
        custom_group.setLayout(custom_layout)
        resize_layout.addWidget(custom_group)
        
        # Percentage
        percentage_group = QGroupBox("📊 Scale by Percentage")
        percentage_layout = QVBoxLayout()
        
        self.resize_percentage = QRadioButton("Scale by percentage")
        percentage_layout.addWidget(self.resize_percentage)
        
        percent_layout = QHBoxLayout()
        percent_layout.addWidget(QLabel("Scale:"))
        self.scale_percentage = QSpinBox()
        self.scale_percentage.setMinimum(1)
        self.scale_percentage.setMaximum(500)
        self.scale_percentage.setValue(100)
        self.scale_percentage.setSuffix("%")
        percent_layout.addWidget(self.scale_percentage)
        percent_layout.addStretch()
        percentage_layout.addLayout(percent_layout)
        
        percentage_group.setLayout(percentage_layout)
        resize_layout.addWidget(percentage_group)
        
        # Aspect ratio
        self.maintain_aspect = QCheckBox("🔒 Maintain aspect ratio (recommended)")
        self.maintain_aspect.setChecked(True)
        self.maintain_aspect.setStyleSheet("font-weight: bold;")
        resize_layout.addWidget(self.maintain_aspect)
        
        self.resize_container.setEnabled(False)
        self.resize_enabled.toggled.connect(self.resize_container.setEnabled)
        
        layout.addWidget(self.resize_container)
        layout.addStretch()
        self.tabs.addTab(tab, "📐 Resize")
    
    def create_advanced_tab(self):
        """Advanced settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Watermark
        watermark_group = QGroupBox("💧 Watermark")
        watermark_layout = QVBoxLayout()
        
        self.watermark_enabled = QCheckBox("Add text watermark")
        watermark_layout.addWidget(self.watermark_enabled)
        
        self.watermark_container = QWidget()
        wm_layout = QVBoxLayout(self.watermark_container)
        
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Text:"))
        self.watermark_text = QLineEdit()
        self.watermark_text.setPlaceholderText("© Your Name 2025")
        text_layout.addWidget(self.watermark_text)
        wm_layout.addLayout(text_layout)
        
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Position:"))
        self.watermark_position = QComboBox()
        self.watermark_position.addItems([
            "bottom-right", "bottom-left", "top-right", "top-left", "center"
        ])
        pos_layout.addWidget(self.watermark_position)
        pos_layout.addStretch()
        wm_layout.addLayout(pos_layout)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))
        self.watermark_size = QSpinBox()
        self.watermark_size.setMinimum(10)
        self.watermark_size.setMaximum(200)
        self.watermark_size.setValue(36)
        self.watermark_size.setSuffix(" pt")
        size_layout.addWidget(self.watermark_size)
        
        size_layout.addWidget(QLabel("Opacity:"))
        self.watermark_opacity = QSpinBox()
        self.watermark_opacity.setMinimum(0)
        self.watermark_opacity.setMaximum(255)
        self.watermark_opacity.setValue(128)
        size_layout.addWidget(self.watermark_opacity)
        size_layout.addStretch()
        wm_layout.addLayout(size_layout)
        
        self.watermark_container.setEnabled(False)
        self.watermark_enabled.toggled.connect(self.watermark_container.setEnabled)
        
        watermark_layout.addWidget(self.watermark_container)
        watermark_group.setLayout(watermark_layout)
        layout.addWidget(watermark_group)
        
        # Metadata
        metadata_group = QGroupBox("🏷️ Metadata")
        metadata_layout = QVBoxLayout()
        
        self.strip_metadata = QCheckBox("Strip EXIF metadata (reduces file size)")
        self.strip_metadata.setChecked(True)
        metadata_layout.addWidget(self.strip_metadata)
        
        info = QLabel("ℹ️ Removes camera info, GPS data, and other metadata")
        info.setStyleSheet("color: #666; font-size: 10px;")
        metadata_layout.addWidget(info)
        
        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "⚡ Advanced")
    
    def update_preview(self):
        """Update preview when file is selected"""
        current_item = self.file_list.currentItem()
        if not current_item or not self.selected_files:
            return
        
        current_index = self.file_list.currentRow()
        if current_index < 0 or current_index >= len(self.selected_files):
            return
        
        file_path = self.selected_files[current_index]
        
        try:
            # Load and display image
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)
            
            # Update file info
            img = Image.open(file_path)
            file_size = os.path.getsize(file_path) / 1024  # KB
            info_text = f"{Path(file_path).name}\n"
            info_text += f"Size: {img.width}x{img.height} px\n"
            info_text += f"Format: {img.format}\n"
            info_text += f"File size: {file_size:.1f} KB"
            self.file_info_label.setText(info_text)
            
        except Exception as e:
            self.preview_label.setText(f"Error loading preview:\n{str(e)}")
            self.file_info_label.setText("Error loading file info")
        
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;All Files (*.*)"
        )
        
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                item = QListWidgetItem(Path(file).name)
                item.setToolTip(file)
                self.file_list.addItem(item)
        
        self.update_status()
        if self.selected_files:
            self.file_list.setCurrentRow(0)
            self.update_preview()
    
    def clear_files(self):
        self.selected_files.clear()
        self.file_list.clear()
        self.preview_label.clear()
        self.preview_label.setText("Select an image to preview")
        self.file_info_label.setText("No file selected")
        self.update_status()
    
    def choose_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_directory = directory
            # Truncate long paths for display
            display_path = directory if len(directory) < 50 else "..." + directory[-47:]
            self.output_path_label.setText(display_path)
            self.output_path_label.setToolTip(directory)
            self.output_path_label.setStyleSheet("color: black;")
            self.btn_open_folder.setEnabled(True)
    
    def open_output_folder(self):
        """Open the output folder in file explorer"""
        folder = self.output_directory
        
        # If no output directory set, use the auto-generated one
        if not folder and self.selected_files:
            first_file_dir = str(Path(self.selected_files[0]).parent)
            folder = os.path.join(first_file_dir, "processed images")
        
        if folder and os.path.exists(folder):
            try:
                if sys.platform == 'win32':
                    os.startfile(folder)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', folder])
                else:  # linux
                    subprocess.run(['xdg-open', folder])
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open folder: {str(e)}")
        else:
            QMessageBox.information(self, "Info", "Output folder doesn't exist yet. Process images first!")
    
    def get_cut_mode(self):
        if self.radio_horizontal.isChecked():
            return 'horizontal'
        elif self.radio_vertical.isChecked():
            return 'vertical'
        else:
            return 'none'
    
    def get_output_format(self):
        if self.format_jpg.isChecked():
            return 'jpg'
        elif self.format_png.isChecked():
            return 'png'
        else:
            return 'webp'
    
    def get_settings(self):
        """Gather all settings into a dictionary"""
        settings = {
            'quality': self.quality_slider.value(),
            'cut_mode': self.get_cut_mode(),
            'output_format': self.get_output_format(),
            'filename_prefix': self.prefix_input.text(),
            'filename_suffix': self.suffix_input.text(),
            'strip_metadata': self.strip_metadata.isChecked(),
        }
        
        # Target file size
        if self.target_size_check.isChecked():
            settings['target_size_kb'] = self.target_size_spinbox.value()
        else:
            settings['target_size_kb'] = 0
        
        # Resize settings
        settings['resize_enabled'] = self.resize_enabled.isChecked()
        if settings['resize_enabled']:
            settings['maintain_aspect'] = self.maintain_aspect.isChecked()
            
            if self.resize_preset.isChecked():
                settings['resize_mode'] = 'preset'
                preset_values = [1920, 1200, 800, 400]
                settings['preset_width'] = preset_values[self.preset_combo.currentIndex()]
            elif self.resize_custom.isChecked():
                settings['resize_mode'] = 'custom'
                settings['custom_width'] = self.custom_width.value()
                settings['custom_height'] = self.custom_height.value()
            else:  # percentage
                settings['resize_mode'] = 'percentage'
                settings['scale_percentage'] = self.scale_percentage.value()
        
        # Watermark settings
        settings['watermark_enabled'] = self.watermark_enabled.isChecked()
        if settings['watermark_enabled']:
            settings['watermark_text'] = self.watermark_text.text()
            settings['watermark_position'] = self.watermark_position.currentText()
            settings['watermark_size'] = self.watermark_size.value()
            settings['watermark_opacity'] = self.watermark_opacity.value()
        
        return settings
    
    def process_images(self):
        if not self.selected_files:
            QMessageBox.warning(self, "No Images", "Please add images first!")
            return
        
        # Validate watermark
        settings = self.get_settings()
        if settings['watermark_enabled'] and not settings['watermark_text']:
            QMessageBox.warning(self, "Watermark Text Required", "Please enter watermark text or disable watermark!")
            return
        
        # Determine output directory
        if not self.output_directory:
            # Auto-create "processed images" folder in the first image's directory
            first_file_dir = str(Path(self.selected_files[0]).parent)
            self.output_directory = os.path.join(first_file_dir, "processed images")
            
            # Create the directory if it doesn't exist
            os.makedirs(self.output_directory, exist_ok=True)
            
            # Update UI to show the auto-created path
            display_path = self.output_directory if len(self.output_directory) < 50 else "..." + self.output_directory[-47:]
            self.output_path_label.setText(display_path)
            self.output_path_label.setToolTip(self.output_directory)
            self.output_path_label.setStyleSheet("color: #2196F3;")
            self.btn_open_folder.setEnabled(True)
        
        # Disable UI during processing
        self.btn_process.setEnabled(False)
        self.btn_add_files.setEnabled(False)
        self.tabs.setEnabled(False)
        self.status_label.setText("Processing...")
        self.stats_label.setText("")
        
        # Start processing in separate thread
        self.processor = ImageProcessor(
            self.selected_files,
            self.output_directory,
            settings
        )
        
        self.processor.progress.connect(self.update_progress)
        self.processor.finished.connect(self.processing_finished)
        self.processor.error.connect(self.processing_error)
        self.processor.stats_update.connect(self.update_stats)
        self.processor.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def update_stats(self, stats):
        """Display compression statistics"""
        original_mb = stats['original_size'] / (1024 * 1024)
        new_mb = stats['new_size'] / (1024 * 1024)
        savings_mb = stats['savings'] / (1024 * 1024)
        
        stats_text = f"📊 Processed {stats['total_files']} files | "
        stats_text += f"Original: {original_mb:.2f} MB → New: {new_mb:.2f} MB | "
        stats_text += f"Saved: {savings_mb:.2f} MB ({stats['percentage']:.1f}%)"
        
        self.stats_label.setText(stats_text)
    
    def processing_finished(self, message):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.progress_bar.setValue(100)
        
        # Re-enable UI
        self.btn_process.setEnabled(True)
        self.btn_add_files.setEnabled(True)
        self.tabs.setEnabled(True)
        
        QMessageBox.information(self, "Success", f"{message}\n\nCheck the statistics below for details.")
    
    def processing_error(self, message):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        # Re-enable UI
        self.btn_process.setEnabled(True)
        self.btn_add_files.setEnabled(True)
        self.tabs.setEnabled(True)
        
        QMessageBox.critical(self, "Error", message)
    
    def update_status(self):
        count = len(self.selected_files)
        if count == 0:
            self.status_label.setText("No images selected - Drag & drop or click 'Add Images'")
            self.status_label.setStyleSheet("color: gray;")
        else:
            self.status_label.setText(f"✅ {count} image(s) ready to process")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern looking style
    window = ImageConverterApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
