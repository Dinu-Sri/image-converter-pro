# Image Converter & Cutter Pro 🎨✂️

A fast, portable, professional-grade image processing tool designed for web and graphic designers. Convert, resize, optimize, and watermark images with an intuitive tabbed interface.

![Made with Python](https://img.shields.io/badge/Made%20with-Python-blue)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Features

### Core Features
- 🚀 **Fast Processing**: Multi-threaded image processing with progress tracking
- 📦 **Portable**: Standalone `.exe` for Windows or run from Python source
- 🖼️ **Multiple Format Support**: PNG, JPG, JPEG, BMP, GIF, TIFF, and WebP
- 🎯 **Drag & Drop**: Easily add images by dragging them into the application
- 📊 **Live Preview**: See your images before processing with detailed file info

### Conversion & Quality
- 🎨 **Multiple Output Formats**: Convert to WebP, JPG, or PNG
- 🎚️ **Quality Control**: Adjustable quality 1-100% with presets (Low 60%, Medium 85%, High 95%)
- 🎯 **Target File Size**: Auto-adjust quality to meet specific KB targets
- ✂️ **Image Cutting**: Cut images in half horizontally or vertically
- 📈 **Compression Statistics**: Real-time savings percentage and file size comparison

### Resizing Options
- 📱 **Web Size Presets**: Quick resize to 1920px, 1200px, 800px, or 400px width
- ✏️ **Custom Dimensions**: Set exact width and height
- 📊 **Percentage Scaling**: Scale by percentage (1-500%)
- 🔒 **Aspect Ratio Lock**: Maintain or ignore aspect ratio

### Advanced Features
- 💧 **Text Watermarking**: Customizable position, size (10-200pt), and opacity
- 🏷️ **Metadata Stripping**: Remove EXIF data to reduce file size
- 🔄 **Batch Rename**: Add prefix/suffix to output filenames
- 📁 **Auto Folder**: Creates "processed images" folder automatically
- 🚀 **Open Folder Button**: Quick access to output location

### Batch Processing
- 📁 **Multi-file Support**: Process hundreds of images simultaneously
- 🎯 **Smart Output**: Auto-generated folders or custom directory
- ⚡ **Non-blocking UI**: Responsive interface during processing

## 🚀 Quick Start

### Option 1: Windows Executable (Recommended)
1. Download `ImageConverterPro.exe` from [Releases](../../releases)
2. Double-click to run - no installation needed!
3. Start processing images immediately

### Option 2: Run from Source

**Requirements:**
- Python 3.8 or higher
- pip (Python package manager)

**Installation:**
```bash
# Clone the repository
git clone https://github.com/yourusername/image-converter-pro.git
cd image-converter-pro

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## 📖 Usage Guide

### Basic Workflow
1. **Add Images**: Drag & drop or click "Add Images"
2. **Choose Settings**: 
   - Format (WebP/JPG/PNG)
   - Quality or target file size
   - Optional: Resize, watermark, cut
3. **Process**: Click "Process Images"
4. **Access Files**: Click "Open Folder" to view results

### Tab Organization
- **📁 Tab 1 - Files & Preview**: File selection and live preview
- **🎨 Tab 2 - Convert & Quality**: Format, quality, cutting options
- **📐 Tab 3 - Resize**: Web presets and custom dimensions
- **⚡ Tab 4 - Advanced**: Watermarks and metadata

### Pro Tips for Web Designers

#### Recommended Settings by Use Case

**Hero Images / Headers:**
- Format: WebP
- Quality: 90-95%
- Resize: 1920px width
- Strip metadata: ✓

**Content Images:**
- Format: WebP
- Quality: 80-85%
- Resize: 1200px width
- Target: 200-300 KB

**Thumbnails:**
- Format: WebP
- Quality: 70-80%
- Resize: 400px width
- Target: 50-100 KB

**Product Photos:**
- Format: WebP
- Quality: 85-90%
- Resize: 800px width
- Watermark: Optional

## 🛠️ Building Executable

To create your own portable executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
python -m PyInstaller --onefile --windowed --name="ImageConverterPro" --icon="app_icon.ico" main.py

# Find executable in dist/ folder
```

## 📋 Requirements

```
PyQt5==5.15.10
Pillow==10.1.0
```

## 🎯 Why Use This Tool?

- **WebP Optimization**: Save 25-35% file size compared to JPEG
- **Responsive Design**: Presets match common breakpoints (1920, 1200, 800, 400px)
- **Batch Efficiency**: Process hundreds of images in minutes
- **Professional Quality**: Precise control over output quality
- **Client-Ready**: Add watermarks to protect your work
- **Portable**: No installation, works from USB drive

## 🔧 Technical Details

- **Framework**: PyQt5 for modern, native-looking GUI
- **Image Processing**: Pillow (PIL) with LANCZOS resampling for quality
- **Threading**: Non-blocking UI with QThread for smooth operation
- **Compression**: WebP method 6 for optimal balance
- **Platform**: Windows (executable), Cross-platform (Python script)

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## 📝 License

This project is free to use for personal and commercial projects.

## 👨‍💻 Author

**Made by Dr. Dinu Sri Madusanka**

## 🙏 Acknowledgments

- PyQt5 for the excellent GUI framework
- Pillow for powerful image processing
- The Python community for inspiration

## 📞 Support

If you find this tool useful, please ⭐ star the repository!

For issues or questions, please open an issue on GitHub.

---

**Made with ❤️ for web designers and graphic designers**
