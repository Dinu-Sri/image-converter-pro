"""
Create a simple icon for the Image Converter app
"""
from PIL import Image, ImageDraw, ImageFont

# Create a 256x256 icon
size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Background circle gradient (blue to green)
for i in range(size//2):
    alpha = int(255 * (1 - i / (size//2)))
    color = (76, 175, 80, 255)  # Green color
    draw.ellipse([i, i, size-i, size-i], fill=color)

# Draw a stylized image icon
# Photo frame
frame_margin = 40
draw.rectangle([frame_margin, frame_margin, size-frame_margin, size-frame_margin], 
               fill=(255, 255, 255, 255), outline=(100, 100, 100, 255), width=4)

# Mountain icon inside (simplified image representation)
mountain_color = (100, 150, 255, 255)
draw.polygon([
    (frame_margin + 30, size - frame_margin - 20),
    (size//2, frame_margin + 60),
    (size - frame_margin - 30, size - frame_margin - 20)
], fill=mountain_color)

# Sun/circle
sun_x = size - frame_margin - 50
sun_y = frame_margin + 50
draw.ellipse([sun_x - 20, sun_y - 20, sun_x + 20, sun_y + 20], 
             fill=(255, 200, 0, 255))

# Add "WP" text for WebP at bottom
try:
    font = ImageFont.truetype("arial.ttf", 40)
except:
    font = ImageFont.load_default()

text = "IMG"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_x = (size - text_width) // 2
text_y = size - frame_margin - 10
draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)

# Save as ICO (Windows icon) and PNG
img.save('app_icon.png', 'PNG')
print("✓ Created app_icon.png")

# For ICO, we need multiple sizes
icon_sizes = [(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)]
icons = []
for icon_size in icon_sizes:
    icons.append(img.resize(icon_size, Image.Resampling.LANCZOS))

icons[0].save('app_icon.ico', format='ICO', sizes=[(s[0], s[1]) for s in icon_sizes])
print("✓ Created app_icon.ico")
print("\nIcon files created successfully!")
