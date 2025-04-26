#!/usr/bin/env python3
# filepath: c:\Users\DELL\Documents\StegaMarkStart-V2.0\app.py
import argparse
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
import io
import os
import sys
import math
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import base64 # Potentially useful for returning small images/data
import traceback # Import traceback at the top

# --- Helper: Data Conversion ---

def to_binary(data):
    """Convert data (string or bytes) to a binary string."""
    if isinstance(data, str):
        # Encode string to bytes using UTF-8, then convert bytes to binary
        return ''.join(format(byte, '08b') for byte in data.encode('utf-8'))
    elif isinstance(data, bytes):
        # Convert bytes directly to binary
        return ''.join(format(byte, '08b') for byte in data)
    else:
        raise TypeError("Input must be a string or bytes for binary conversion.")

def binary_to_bytes(binary_string):
    """Convert binary string back to bytes."""
    # Ensure the string length is a multiple of 8
    byte_len = len(binary_string) // 8
    actual_binary = binary_string[:byte_len*8] # Trim excess bits that don't form a full byte

    byte_list = bytearray()
    for i in range(0, len(actual_binary), 8):
        byte = actual_binary[i:i+8]
        try:
            byte_list.append(int(byte, 2))
        except ValueError:
            # This might happen if non-binary characters are present
            print(f"Warning: Skipping invalid binary sequence '{byte}' during conversion.", file=sys.stderr)
            continue # Or raise an error depending on desired strictness
    return bytes(byte_list)

# --- Helper: Color Conversion ---

def hex_to_rgb(hex_color):
    """Converts a hex color string (e.g., '#ffffff') to an RGB tuple (255, 255, 255)."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return (255, 255, 255) # Default to white on error
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return (255, 255, 255) # Default to white on error

# --- LSB Steganography Core (Refactored for PIL Image objects) ---

class LSBSteganography:
    """Handles LSB encoding and decoding in PIL Image objects."""

    # Using a more robust sequence that's less likely to appear naturally
    DELIMITER = b"<\x01STG\x02MRK\x03END>"
    DELIMITER_BIN = to_binary(DELIMITER)
    DELIMITER_LEN_BITS = len(DELIMITER_BIN)

    def __init__(self, strength=3):
        """
        Initialize LSB handler.
        Args:
            strength (int): Encoding strength (1-5). Higher uses more LSB bits.
        """
        # Map strength 1-5 to LSB bits 1-8 more granularly
        # Using ceil ensures strength 1 uses at least 1 bit.
        self.bits_to_use = min(8, max(1, math.ceil(strength * 8 / 5)))
        if strength == 5: self.bits_to_use = 8 # Max out bits at max strength
        # print(f"LSB Steganography Initialized: Using {self.bits_to_use} LSB bit(s) per channel value.")
        self.clear_mask = 0xFF << self.bits_to_use & 0xFF # e.g., for 3 bits: 11111000
        self.write_mask = (1 << self.bits_to_use) - 1   # e.g., for 3 bits: 00000111

    def _get_max_bytes(self, image):
        """Calculate the maximum number of bytes that can be hidden in a PIL Image."""
        if not isinstance(image, Image.Image):
             raise TypeError("Input must be a Pillow Image object.")
        width, height = image.size
        # Assuming RGBA conversion happens before calling this
        channels = 4
        available_bits = width * height * channels * self.bits_to_use
        # Subtract bits needed for delimiter
        if available_bits <= self.DELIMITER_LEN_BITS:
             return 0
        max_bits = available_bits - self.DELIMITER_LEN_BITS
        return max_bits // 8 # Convert bits to bytes

    def encode_image(self, image, data_to_hide):
        """
        Encodes data (bytes) into a PIL Image object using LSB.

        Args:
            image (Image.Image): Input PIL Image object.
            data_to_hide (bytes): The raw bytes of the data to hide.

        Returns:
            Image.Image: The encoded PIL Image object (always RGBA).

        Raises:
            ValueError: If data is too large for the image.
            TypeError: If input is not a PIL Image or data is not bytes.
        """
        if not isinstance(image, Image.Image):
            raise TypeError("Input 'image' must be a Pillow Image object.")
        if not isinstance(data_to_hide, bytes):
             raise TypeError("Input 'data_to_hide' must be bytes.")

        img_rgba = image.convert("RGBA") # Ensure RGBA for 4 channels
        max_bytes = self._get_max_bytes(img_rgba)

        if len(data_to_hide) > max_bytes:
            raise ValueError(f"Data too large ({len(data_to_hide)} bytes) to hide. Max capacity: {max_bytes} bytes (using {self.bits_to_use} LSB bits).")

        binary_data_to_hide = to_binary(data_to_hide) + self.DELIMITER_BIN
        data_index = 0
        n_bits_total = len(binary_data_to_hide)

        # Use image.load() for efficient pixel access
        pixels = img_rgba.load()
        width, height = img_rgba.size

        encoded_image = img_rgba.copy() # Work on a copy
        encoded_pixels = encoded_image.load()

        # print(f"Encoding {len(data_to_hide)} bytes ({n_bits_total} bits including delimiter)...")

        for y in range(height):
            for x in range(width):
                if data_index >= n_bits_total:
                     # print(f"Finished encoding after {y*width + x} pixels.")
                     return encoded_image # All data encoded

                pixel = list(pixels[x, y]) # Get original pixel as list [R, G, B, A]

                for channel_index in range(4): # R, G, B, A
                    if data_index < n_bits_total:
                        # Get the next bits_to_use bits
                        start = data_index
                        end = min(data_index + self.bits_to_use, n_bits_total)
                        bits_to_encode = binary_data_to_hide[start:end]

                        # Pad with zeros if needed for the last group
                        bits_to_encode = bits_to_encode.ljust(self.bits_to_use, '0')

                        # Convert to decimal
                        bits_value = int(bits_to_encode, 2)

                        # Clear the LSBs and set new ones
                        pixel[channel_index] = (pixel[channel_index] & self.clear_mask) | bits_value

                        data_index = end # Move to next group of bits

                encoded_pixels[x, y] = tuple(pixel) # Update pixel in the copied image

        # If loop finishes, check if all data was encoded (should be caught earlier by size check)
        if data_index < n_bits_total:
            raise RuntimeError(f"Could not encode all data despite size check. Encoded {data_index}/{n_bits_total} bits. This indicates a bug.")

        return encoded_image # Should have returned earlier if successful

    def decode_image(self, image):
        """
        Decodes hidden data from a PIL Image object using LSB.

        Args:
            image (Image.Image): The encoded PIL Image object.

        Returns:
            bytes: The extracted data if found.

        Raises:
            ValueError: If no hidden data (delimiter) is found.
            TypeError: If input is not a PIL Image.
        """
        if not isinstance(image, Image.Image):
            raise TypeError("Input must be a Pillow Image object.")

        img_rgba = image.convert("RGBA")
        pixels = img_rgba.load()
        width, height = img_rgba.size
        binary_result = ""

        # print(f"Decoding using {self.bits_to_use} LSB bits...")

        # Iterate through pixels and channels to extract LSBs
        for y in range(height):
            for x in range(width):
                pixel = pixels[x, y]
                for channel_value in pixel: # R, G, B, A
                    # Extract the specified number of LSB bits
                    lsb_bits = channel_value & self.write_mask # Use write_mask to get only LSBs
                    binary_result += format(lsb_bits, f'0{self.bits_to_use}b')

                    # Check frequently if the delimiter suffix is found (more efficient than searching full string)
                    if len(binary_result) >= self.DELIMITER_LEN_BITS and binary_result.endswith(self.DELIMITER_BIN):
                        # Found delimiter, extract data up to this point
                        # print(f"Delimiter found after extracting approx {len(binary_result)} bits.")
                        data_part = binary_result[:-self.DELIMITER_LEN_BITS]
                        return binary_to_bytes(data_part)

        # If we've searched the entire image and not found the delimiter
        raise ValueError(f"Delimiter not found in image. No hidden data detected or incorrect strength used (Expected strength corresponding to {self.bits_to_use} bits).")

# --- Visible Watermarking Core ---

def _calculate_position(img_width, img_height, wm_width, wm_height, position_keyword, padding=10):
    """Calculates (x, y) coordinates based on keywords."""
    if position_keyword == "top-left":
        x = padding
        y = padding
    elif position_keyword == "top-center":
        x = (img_width - wm_width) // 2
        y = padding
    elif position_keyword == "top-right":
        x = img_width - wm_width - padding
        y = padding
    elif position_keyword == "center-left":
        x = padding
        y = (img_height - wm_height) // 2
    elif position_keyword == "center":
        x = (img_width - wm_width) // 2
        y = (img_height - wm_height) // 2
    elif position_keyword == "center-right":
        x = img_width - wm_width - padding
        y = (img_height - wm_height) // 2
    elif position_keyword == "bottom-left":
        x = padding
        y = img_height - wm_height - padding
    elif position_keyword == "bottom-center":
        x = (img_width - wm_width) // 2
        y = img_height - wm_height - padding
    elif position_keyword == "bottom-right":
        x = img_width - wm_width - padding
        y = img_height - wm_height - padding
    else: # Default to center if keyword is unknown
        x = (img_width - wm_width) // 2
        y = (img_height - wm_height) // 2

    # Ensure position is within bounds
    x = max(0, min(x, img_width - wm_width))
    y = max(0, min(y, img_height - wm_height))
    return int(x), int(y)

def add_visible_watermark(image, text=None, logo_image=None, position="center", opacity=0.5,
                          font_path=None, font_size=None, text_color=(255, 255, 255), logo_scale=0.15,
                          tile_style="none", tile_spacing=0.1, tile_angle=45): # Added tile_style, tile_spacing, tile_angle
    """
    Adds a visible text or logo watermark to a PIL Image object. Can tile the watermark with various styles.

    Args:
        image (Image.Image): Base image.
        text (str, optional): Text for the watermark. Defaults to None.
        logo_image (Image.Image, optional): Logo image for the watermark. Defaults to None.
        position (str, optional): Position keyword. Used only if tile_style='none'. Defaults to "center".
        opacity (float, optional): Opacity from 0.0 (transparent) to 1.0 (opaque). Defaults to 0.5.
        font_path (str, optional): Path to a .ttf font file for text. Defaults to None (uses PIL default).
        font_size (int, optional): Font size for text. Calculated if None. Defaults to None.
        text_color (tuple, optional): RGB color for text (0-255). Defaults to (255, 255, 255).
        logo_scale (float, optional): Scale factor for logo based on base image width. Defaults to 0.15.
        tile_style (str, optional): Tiling style ('none', 'grid', 'staggered', 'diagonal'). Defaults to "none".
        tile_spacing (float, optional): Spacing between tiles as a fraction of watermark dimension (width/height). Defaults to 0.1.
        tile_angle (int, optional): Angle (degrees) to rotate the watermark element for 'diagonal' style. Defaults to 45.

    Returns:
        Image.Image: Image with watermark applied.

    Raises:
        ValueError: If neither text nor logo is provided, or logo_image is not a PIL Image.
        TypeError: If base image is not a PIL Image.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("Base image must be a Pillow Image object.")
    if text is None and logo_image is None:
        raise ValueError("Either text or logo_image must be provided for visible watermark.")
    if logo_image is not None and not isinstance(logo_image, Image.Image):
         raise TypeError("logo_image must be a Pillow Image object.")

    base_image = image.convert("RGBA")
    width, height = base_image.size
    watermark_layer = Image.new("RGBA", base_image.size, (255, 255, 255, 0)) # Main transparent layer

    alpha = int(opacity * 255) # Convert opacity float (0-1) to int (0-255)

    # --- Prepare the base watermark element (text or logo) onto its own transparent image ---
    wm_element_img = None
    original_wm_width, original_wm_height = 0, 0
    bbox = [0, 0, 0, 0] # To handle text positioning

    if text:
        if font_size is None: font_size = max(10, int(height * 0.05))
        try:
            # Load font (simplified fallback logic)
            try: font = ImageFont.truetype(font_path or "arial.ttf", font_size)
            except IOError: font = ImageFont.load_default()
        except Exception as e:
            print(f"Warning: Font loading error ({e}). Using default font.", file=sys.stderr)
            font = ImageFont.load_default()

        # Get text dimensions accurately using textbbox
        try:
            temp_draw = ImageDraw.Draw(Image.new("RGBA", (1,1)))
            bbox = temp_draw.textbbox((0, 0), text, font=font) # (left, top, right, bottom)
            original_wm_width = bbox[2] - bbox[0]
            original_wm_height = bbox[3] - bbox[1]
        except AttributeError: # Fallback for older PIL / default font
             # Use the main layer's draw temporarily for measurement
             temp_draw = ImageDraw.Draw(watermark_layer)
             text_length = temp_draw.textlength(text, font=font)
             original_wm_width = int(text_length)
             original_wm_height = int(font_size * 1.2) # Crude estimate
             bbox = [0, 0, original_wm_width, original_wm_height] # Approximate bbox

        if original_wm_width <= 0 or original_wm_height <= 0:
             print(f"Warning: Calculated text dimensions invalid ({original_wm_width}x{original_wm_height}). Skipping.", file=sys.stderr)
             return image.convert("RGB")

        # Create a correctly sized transparent image for the text
        text_img = Image.new('RGBA', (original_wm_width, original_wm_height), (255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_img)
        # Draw text onto the temporary image, adjusting for negative bbox offsets
        text_draw.text((-bbox[0], -bbox[1]), text, font=font, fill=text_color + (alpha,))
        wm_element_img = text_img

    elif logo_image:
        logo = logo_image.convert("RGBA")
        base_width = int(width * logo_scale)
        if logo.size[0] > 0:
            w_percent = (base_width / float(logo.size[0]))
            h_size = int((float(logo.size[1]) * float(w_percent))) if logo.size[1] > 0 and w_percent > 0 else 0
        else: w_percent = 0; h_size = 0

        if base_width <= 0 or h_size <= 0:
             print(f"Warning: Calculated logo size invalid ({base_width}x{h_size}). Skipping.", file=sys.stderr)
             return image.convert("RGB")

        logo = logo.resize((base_width, h_size), Image.Resampling.LANCZOS)
        original_wm_width, original_wm_height = logo.size

        # Apply opacity to the logo's alpha channel
        try:
            logo_alpha = logo.split()[3]
            logo_alpha = logo_alpha.point(lambda p: int(p * opacity))
            logo.putalpha(logo_alpha)
        except IndexError: # Handle images without an alpha channel (e.g. JPEG logo)
             logo.putalpha(Image.new('L', logo.size, alpha)) # Create an alpha channel

        wm_element_img = logo

    if not wm_element_img or original_wm_width <= 0 or original_wm_height <= 0:
        print("Warning: Watermark element could not be prepared. Returning original.", file=sys.stderr)
        return image.convert("RGB")

    # --- Handle Rotation for Diagonal Style ---
    rotated_wm_img = wm_element_img
    if tile_style == "diagonal" and tile_angle != 0:
        try:
            # Rotate the element image, expanding the canvas to fit, use transparent fill
            rotated_wm_img = wm_element_img.rotate(tile_angle, resample=Image.Resampling.BICUBIC, expand=True)
            # The background created by rotate might not be fully transparent, ensure it is
            # This is tricky, might need a mask - let's assume rotate handles transparency well enough for now
            # or paste the rotated image onto a new transparent background of the same expanded size.
        except Exception as e:
            print(f"Warning: Could not rotate watermark element: {e}. Using unrotated.", file=sys.stderr)
            rotated_wm_img = wm_element_img # Fallback to unrotated

    # Use dimensions of the (potentially rotated) element for tiling calculations
    wm_width, wm_height = rotated_wm_img.size
    if wm_width <= 0 or wm_height <= 0:
        print(f"Warning: Watermark dimensions invalid after potential rotation ({wm_width}x{wm_height}). Skipping.", file=sys.stderr)
        return image.convert("RGB")


    # --- Apply Watermark (Single or Tiled) ---
    if tile_style == "none":
        # Place single watermark using the potentially rotated element
        pos_x, pos_y = _calculate_position(width, height, wm_width, wm_height, position)
        # Paste using the element's alpha channel as the mask
        watermark_layer.paste(rotated_wm_img, (pos_x, pos_y), rotated_wm_img)
    else:
        # --- Tiling Logic ---
        # Calculate spacing in pixels based on the potentially rotated dimensions
        spacing_x = int(wm_width * tile_spacing)
        spacing_y = int(wm_height * tile_spacing)
        step_x = wm_width + spacing_x
        step_y = wm_height + spacing_y

        if step_x <= 0 or step_y <= 0: # Prevent infinite loop / division by zero
             print("Warning: Invalid tile step size (<= 0). Applying single watermark instead.", file=sys.stderr)
             pos_x, pos_y = _calculate_position(width, height, wm_width, wm_height, position)
             watermark_layer.paste(rotated_wm_img, (pos_x, pos_y), rotated_wm_img)
        else:
            # Calculate starting points to ensure coverage even with rotation/staggering
            # These are approximate starting points off-canvas
            start_y = -wm_height # Start further up
            start_x = -wm_width  # Start further left

            row_count = 0
            # Loop well beyond the bottom edge
            for y in range(start_y, height + wm_height, step_y):
                 current_start_x = start_x
                 # Apply stagger offset for 'staggered' and 'diagonal' styles
                 if tile_style == "staggered" or tile_style == "diagonal":
                     if row_count % 2 != 0:
                         current_start_x -= (step_x // 2) # Offset alternate rows leftwards

                 # Loop well beyond the right edge
                 for x in range(current_start_x, width + wm_width, step_x):
                     pos_x = x
                     pos_y = y
                     # Paste the (potentially rotated) watermark element image
                     # Use the element's alpha channel as the mask for proper transparency
                     watermark_layer.paste(rotated_wm_img, (pos_x, pos_y), rotated_wm_img)
                 row_count += 1

    # Composite the watermark layer onto the base image
    watermarked_image = Image.alpha_composite(base_image, watermark_layer)
    # Return RGB. If original was PNG and transparency is desired, more complex handling needed.
    return watermarked_image.convert("RGB")

# --- Flask Web Application ---
app = Flask(__name__, static_folder='.') # Serve static files from root for simplicity
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Max upload size 16MB
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', os.urandom(24)) # Use env var or random

# --- NEW: Global Error Handler ---
@app.errorhandler(Exception) # Catch all unhandled exceptions
def handle_exception(e):
    """Handles unexpected errors and ensures a JSON response."""
    # Log the full error traceback to the server console/logs for debugging
    print(f"--- Unhandled Exception Caught by Global Handler ---", file=sys.stderr)
    traceback.print_exc()
    print(f"--- End Traceback ---", file=sys.stderr)

    # For all other exceptions (likely causing 500 Internal Server Error)
    # Return a generic JSON error response
    response = jsonify({"error": "An internal server error occurred on the server."})
    response.status_code = 500 # Set the status code to 500
    return response
# --- End NEW Error Handler ---

@app.route('/')
def index():
    # Serve index.html from the root directory
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
     # Serve other static files (CSS, JS) from the root directory
     # Be cautious with this in production - might expose unintended files
     return send_from_directory('.', path)

@app.route('/watermark', methods=['POST'])
def handle_watermark_request():
    """Flask route to apply visible or invisible watermarks."""
    # --- (Keep existing file checks) ---
    if 'image' not in request.files: return jsonify({"error": "No image file provided"}), 400
    image_file = request.files['image']
    if image_file.filename == '': return jsonify({"error": "No selected image file"}), 400

    # --- Get Parameters ---
    visibility = request.form.get('visibility', 'visible')
    watermark_type = request.form.get('watermark_type', 'text') # 'text' or 'logo'
    text = request.form.get('watermark_text', '')

    # Parameters for Invisible
    strength = request.form.get('strength', default=3, type=int)

    # Parameters for Visible
    position = request.form.get('position', 'center') # Used if tile_style is 'none'
    opacity = request.form.get('opacity', default=0.5, type=float)
    logo_scale = request.form.get('logo_scale', default=0.15, type=float)
    hex_color_str = request.form.get('text_color', '#ffffff')
    rgb_color = hex_to_rgb(hex_color_str)

    # --- Tiling Parameters (NEW/UPDATED) ---
    tile_style = request.form.get('tile_style', 'none').lower() # Get style: 'none', 'grid', 'staggered', 'diagonal'
    tile_spacing = request.form.get('tile_spacing', default=0.1, type=float) # Get spacing factor (e.g., 0.1 = 10%)
    tile_angle = request.form.get('tile_angle', default=45, type=int) # Get angle for diagonal style

    # Validate tile_style
    allowed_styles = ['none', 'grid', 'staggered', 'diagonal']
    if tile_style not in allowed_styles:
        print(f"Warning: Invalid tile_style '{tile_style}' received. Defaulting to 'none'.", file=sys.stderr)
        tile_style = 'none'
    # Basic validation for spacing (prevent negative values)
    if tile_spacing < 0:
        print(f"Warning: Invalid negative tile_spacing '{tile_spacing}' received. Using 0.", file=sys.stderr)
        tile_spacing = 0

    # --- (Keep existing file extension validation) ---
    file_ext = os.path.splitext(image_file.filename)[1].lower()
    if file_ext not in app.config['UPLOAD_EXTENSIONS']:
         return jsonify({"error": f"Invalid image file type: {file_ext}"}), 400

    # --- (Keep existing image opening try/except block) ---
    try:
        base_image = Image.open(image_file.stream)
        original_format = base_image.format or 'PNG'
        result_image = None
        output_format = 'PNG'
    except UnidentifiedImageError: return jsonify({"error": "Cannot identify image file."}), 400
    except Exception as e: return jsonify({"error": f"Error opening image: {str(e)}"}), 500

    try:
        if visibility == 'visible':
            logo_image = None
            if watermark_type == 'logo':
                # --- (Keep existing logo loading logic) ---
                if 'watermark_logo' not in request.files or request.files['watermark_logo'].filename == '':
                    return jsonify({"error": "Logo file required for visible logo watermark"}), 400
                logo_file = request.files['watermark_logo']
                logo_ext = os.path.splitext(logo_file.filename)[1].lower()
                if logo_ext not in app.config['UPLOAD_EXTENSIONS']:
                     return jsonify({"error": f"Invalid logo file type: {logo_ext}"}), 400
                try:
                    logo_image = Image.open(logo_file.stream)
                except UnidentifiedImageError: return jsonify({"error": "Cannot identify logo file."}), 400
                except Exception as e: return jsonify({"error": f"Error opening logo: {str(e)}"}), 500
            elif watermark_type == 'text' and not text:
                 return jsonify({"error": "Watermark text cannot be empty for text type"}), 400

            # Call the updated function with new tiling parameters
            result_image = add_visible_watermark(
                base_image,
                text=text if watermark_type == 'text' else None,
                logo_image=logo_image,
                position=position,      # Used only if tile_style='none'
                opacity=opacity,
                logo_scale=logo_scale,
                text_color=rgb_color,
                tile_style=tile_style,    # Pass the chosen style
                tile_spacing=tile_spacing,# Pass the spacing factor
                tile_angle=tile_angle     # Pass the angle for diagonal
                # font_path/font_size could be added here if needed from form
            )
            # --- (Keep existing output format determination logic) ---
            if original_format.upper() in ['JPEG', 'JPG']: output_format = 'JPEG'
            else: output_format = 'PNG'

        elif visibility == 'invisible':
            # --- (Keep ALL existing invisible logic untouched) ---
            # ... (invisible encoding logic using LSBSteganography) ...
            # This section remains exactly as it was before.
            if watermark_type == 'text':
                if not text: return jsonify({"error": "Text message required for invisible"}), 400
                import json
                metadata = {"watermark_type": "text", "content": text}
                secret_data = json.dumps(metadata).encode('utf-8')
            elif watermark_type == 'logo':
                if 'watermark_logo' not in request.files or request.files['watermark_logo'].filename == '':
                    return jsonify({"error": "Logo file required for invisible logo"}), 400
                logo_file = request.files['watermark_logo']
                # ... (rest of invisible logo loading/validation/conversion) ...
                try:
                    logo_image_inv = Image.open(logo_file.stream)
                    logo_bytes_io = io.BytesIO()
                    logo_image_inv.save(logo_bytes_io, format='PNG')
                    logo_bytes = logo_bytes_io.getvalue()
                    import json
                    metadata = {
                        "watermark_type": "image", "format": "png",
                        "content": base64.b64encode(logo_bytes).decode('ascii')
                    }
                    secret_data = json.dumps(metadata).encode('utf-8')
                except UnidentifiedImageError: return jsonify({"error": "Cannot identify logo file."}), 400
                except Exception as e: return jsonify({"error": f"Error processing logo for invisible: {str(e)}"}), 500
            else: return jsonify({"error": "Invalid type for invisible watermark"}), 400

            if not 1 <= strength <= 5: return jsonify({"error": "Strength must be 1-5"}), 400
            steg = LSBSteganography(strength)
            result_image = steg.encode_image(base_image, secret_data)
            output_format = 'PNG' # MUST be PNG for LSB

        else:
            return jsonify({"error": "Invalid visibility option"}), 400

        # --- (Keep existing response preparation and sending logic) ---
        if result_image:
            byte_io = io.BytesIO()
            save_kwargs = {}
            if output_format == 'JPEG':
                 save_kwargs['quality'] = 95
                 if result_image.mode == 'RGBA': result_image = result_image.convert('RGB')
            elif output_format == 'PNG':
                 save_kwargs['compress_level'] = 1

            result_image.save(byte_io, format=output_format, **save_kwargs)
            byte_io.seek(0)
            mime_type = f'image/{output_format.lower()}'
            download_filename = f"watermarked_{os.path.splitext(image_file.filename)[0]}.{output_format.lower()}"
            return send_file(byte_io, mimetype=mime_type, as_attachment=True, download_name=download_filename)
        else:
             return jsonify({"error": "Watermarking process failed unexpectedly."}), 500

    except ValueError as e:
        # This specific handler is still useful for clear client messages
        print(f"ValueError in /watermark: {e}", file=sys.stderr) # Optional: Log specific catches too
        return jsonify({"error": str(e)}), 400
    except UnidentifiedImageError as e:
        # Keep specific handlers if they exist or add them
        print(f"UnidentifiedImageError in /watermark: {e}", file=sys.stderr)
        return jsonify({"error": f"Cannot identify image file: {e}"}), 400
    except Exception as e:
        # This will now likely be caught by the global handler,
        # but keeping it doesn't hurt (global handler runs if this re-raises or isn't caught)
        print(f"Generic Exception in /watermark: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        # Let the global handler manage the final JSON response for unexpected errors
        # Or explicitly return JSON here too as a safeguard:
        return jsonify({"error": "An internal server error occurred during watermarking."}), 500

@app.route('/extract', methods=['POST'])
def handle_extract_request():
    """Flask route to extract invisible watermarks."""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided for extraction"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No selected image file"}), 400

    strength = request.form.get('strength', default=3, type=int)

    if not 1 <= strength <= 5:
        return jsonify({"error": "Strength must be between 1 and 5"}), 400

    # Check if the uploaded file appears to be PNG based on filename/content type
    is_likely_png = image_file.filename.lower().endswith('.png') or image_file.mimetype == 'image/png'
    if not is_likely_png:
         print(f"Warning: Extraction attempted on non-PNG file: {image_file.filename} ({image_file.mimetype})", file=sys.stderr)

    try:
        encoded_image = Image.open(image_file.stream)
    except UnidentifiedImageError:
        return jsonify({"error": "Cannot identify image file. Corrupted or unsupported?"}), 400
    except Exception as e:
        return jsonify({"error": f"Error opening image: {str(e)}"}), 500

    try:
        steg = LSBSteganography(strength)
        extracted_data_bytes = steg.decode_image(encoded_image)
        print(f"DEBUG: Extracted {len(extracted_data_bytes)} bytes.") # Add log

        try:
            extracted_text = extracted_data_bytes.decode('utf-8')
            print(f"DEBUG: Decoded as UTF-8: '{extracted_text[:100]}...'") # Add log

            # Try to parse as JSON (for metadata structure)
            try:
                import json
                metadata = json.loads(extracted_text)
                print("DEBUG: Parsed as JSON successfully.") # Add log

                if isinstance(metadata, dict) and "content" in metadata:
                    content = metadata["content"] # Get the content
                    watermark_type = metadata.get("watermark_type")
                    print(f"DEBUG: Found metadata - type: {watermark_type}") # Add log

                    if watermark_type == "text":
                        extracted_string = str(content) if content is not None else ""
                        print(f"DEBUG: Returning text content: '{extracted_string[:100]}...'") # Add log
                        return jsonify({"extracted_text": extracted_string})

                    elif watermark_type == "image":
                        if isinstance(content, str):
                            print("DEBUG: Returning image watermark data.") # Add log
                            return jsonify({
                                "extracted_text": "Image watermark detected",
                                "is_image": True,
                                "image_data": content
                            })
                        else:
                            print("DEBUG: Returning image watermark with invalid content format.") # Add log
                            return jsonify({
                                "extracted_text": "Image watermark detected, but content data format is invalid.",
                                "is_binary": True
                            })
                    else:
                        # Known JSON structure but unknown watermark_type
                        print(f"DEBUG: JSON parsed, but unknown watermark_type ('{watermark_type}'). Treating as plain text.") # Add log
                        # Fall through to return the raw text (which is the JSON string itself)
                        pass

                else:
                     # JSON parsed, but not the expected dict structure with 'content'
                     print("DEBUG: JSON parsed, but not the expected metadata structure. Treating as plain text.") # Add log
                     # Fall through to return the raw text (which is the JSON string itself)
                     pass


            except (json.JSONDecodeError, TypeError) as json_err:
                # Not valid JSON, treat as plain text
                print(f"DEBUG: Not valid JSON ({json_err}). Returning as plain text.") # Add log
                # Fall through to return the raw decoded text below

            # --- Fall-through cases ---
            # If JSON parsing failed OR it parsed but wasn't the expected structure/type,
            # return the raw decoded text. The frontend should display this.
            print(f"DEBUG: Falling through JSON handling. Returning raw decoded text: '{extracted_text[:100]}...'") # Add log
            return jsonify({"extracted_text": extracted_text})

        except UnicodeDecodeError:
            # Handle non-UTF8 data
            extracted_info = f"Extracted {len(extracted_data_bytes)} bytes (non-UTF8 data)"
            print("DEBUG: Data is not valid UTF-8. Returning binary info.") # Add log
            return jsonify({"extracted_text": extracted_info, "is_binary": True})

    except ValueError as e:
        # Specific error from decode (delimiter not found)
        error_message = (
            f"{e}. Possible causes: "
            "1) Incorrect 'Strength' setting (must match encoding strength). "
            "2) Image was modified after encoding (e.g., re-saved, compressed, edited). "
            "3) No watermark exists with the specified strength. "
            "Please use the original, unmodified PNG file."
        )
        print(f"ERROR: ValueError during decode: {e}") # Add log
        return jsonify({"error": error_message}), 400
    except Exception as e:
        print(f"ERROR: Unexpected error during extraction process: {e}", file=sys.stderr) # Add log
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An internal server error occurred during extraction."}), 500

# --- Command Line Interface Functions (Updated) ---

def cli_encode_visible(args):
    print("Encoding visible watermark via CLI")
    try:
        base_image = Image.open(args.input)
        logo_img = None
        
        # Add logic to load logo if --logo path is provided
        if hasattr(args, 'logo') and args.logo:
            try:
                logo_img = Image.open(args.logo)
                print(f"Loaded logo from {args.logo}")
            except FileNotFoundError:
                print(f"Warning: Logo file not found: {args.logo}", file=sys.stderr)
                print("Continuing with text-only watermark")
            except UnidentifiedImageError:
                print(f"Warning: Cannot identify logo file: {args.logo}", file=sys.stderr)
                print("Continuing with text-only watermark")
            except Exception as e:
                print(f"Warning: Error loading logo: {e}", file=sys.stderr)
                print("Continuing with text-only watermark")

        result_image = add_visible_watermark(
            base_image,
            text=args.text,
            logo_image=logo_img,
            position=args.position,
            opacity=args.opacity,
            # Add args for font_path, font_size, text_color if needed
        )
        # Determine output format (keep original if JPEG?)
        output_format = "PNG" # Default safe choice
        if base_image.format and base_image.format.upper() in ['JPEG', 'JPG']:
            output_format = 'JPEG'
            if result_image.mode == 'RGBA': result_image = result_image.convert('RGB')

        save_kwargs = {'quality': 95} if output_format == 'JPEG' else {}
        result_image.save(args.output, format=output_format, **save_kwargs)
        print(f"Visible watermark added and saved to {args.output}")

    except FileNotFoundError as e:
        print(f"Error: Input file not found - {e}", file=sys.stderr)
        sys.exit(1)
    except UnidentifiedImageError:
        print(f"Error: Cannot identify input image file: {args.input}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during visible encoding: {e}", file=sys.stderr)
        sys.exit(1)


def cli_encode_invisible(args):
    print("Encoding invisible watermark using LSB steganography via CLI")

    # Read the secret data as bytes
    secret_data = None
    if args.message:
        secret_data = args.message.encode('utf-8')
    elif args.file:
        try:
            with open(args.file, 'rb') as f:
                secret_data = f.read()
        except FileNotFoundError:
             print(f"Error: Secret data file not found: {args.file}", file=sys.stderr)
             sys.exit(1)
        except IOError as e:
             print(f"Error reading secret data file {args.file}: {e}", file=sys.stderr)
             sys.exit(1)
    else:
        print("Error: Either --message or --file must be specified for invisible encoding", file=sys.stderr)
        sys.exit(1)

    if not args.output.lower().endswith(".png"):
        print("Warning: Output file for LSB encoding should ideally be .png to ensure data preservation.", file=sys.stderr)
        # Continue anyway, but warn user

    steg = LSBSteganography(args.strength)
    try:
        base_image = Image.open(args.input)
        encoded_image = steg.encode_image(base_image, secret_data)
        encoded_image.save(args.output, "PNG") # Force PNG for saving LSB
        print(f"Successfully encoded data into {args.output}")
    except FileNotFoundError:
        print(f"Error: Input image file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except UnidentifiedImageError:
         print(f"Error: Cannot identify input image file: {args.input}", file=sys.stderr)
         sys.exit(1)
    except ValueError as e: # e.g., data too large
         print(f"Error encoding data: {e}", file=sys.stderr)
         sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during encoding: {e}", file=sys.stderr)
        sys.exit(1)

def cli_decode(args):
    print("Decoding hidden data from image via CLI")
    steg = LSBSteganography(args.strength)
    try:
        encoded_image = Image.open(args.input)
        extracted_data = steg.decode_image(encoded_image)

        if args.output:
            # Write to file in binary mode
            try:
                with open(args.output, 'wb') as f:
                    f.write(extracted_data)
                print(f"Extracted data saved to {args.output}")
            except IOError as e:
                print(f"Error writing extracted data to {args.output}: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            # Try to display as text if no output file specified
            try:
                text = extracted_data.decode('utf-8')
                print("--- Extracted Text ---")
                print(text)
                print("----------------------")
            except UnicodeDecodeError:
                print("Extracted binary data (cannot display as text):")
                print(f" - Byte length: {len(extracted_data)} bytes")
                # Optionally print hex representation for inspection
                # print(f" - Hex sample: {extracted_data[:32].hex()}...")
    except FileNotFoundError:
        print(f"Error: Input image file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except UnidentifiedImageError:
         print(f"Error: Cannot identify input image file: {args.input}", file=sys.stderr)
         sys.exit(1)
    except ValueError as e: # Delimiter not found
         print(f"Error decoding data: {e}", file=sys.stderr)
         sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during decoding: {e}", file=sys.stderr)
        sys.exit(1)

def run_web_server(args):
     """Starts the Flask web server."""
     print("Starting Flask web server...")
     # Use host='0.0.0.0' to make it accessible on the network
     # Use debug=True only for development
     is_debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
     app.run(host='0.0.0.0', port=5000, debug=is_debug)


# --- Main Execution & CLI Parser ---

def main():
    parser = argparse.ArgumentParser(
        description="StegaMark - Image Watermarking Tool (CLI & Web)",
        formatter_class=argparse.RawTextHelpFormatter # Preserve newline formatting in help
        )
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode", required=True)

    # --- Visible watermark arguments ---
    visible_parser = subparsers.add_parser("encode-visible", help="Add visible watermark to image.")
    visible_parser.add_argument("input", help="Input image file path.")
    visible_parser.add_argument("output", help="Output image file path.")
    visible_parser.add_argument("--text", default="© StegaMark", help="Watermark text (default: '%(default)s').")
    visible_parser.add_argument("--logo", help="Path to logo image file for visible watermark.")
    visible_parser.add_argument("--position", default="center",
                                choices=["top-left", "top-center", "top-right",
                                         "center-left", "center", "center-right",
                                         "bottom-left", "bottom-center", "bottom-right"],
                                help="Position of watermark (default: '%(default)s').")
    visible_parser.add_argument("--opacity", type=float, default=0.5,
                                help="Watermark opacity (0.0=transparent, 1.0=opaque, default: %(default)s).")
    visible_parser.set_defaults(func=cli_encode_visible)

    # --- Invisible watermark arguments ---
    invisible_parser = subparsers.add_parser("encode-invisible", help="Add invisible watermark to image using LSB.")
    invisible_parser.add_argument("input", help="Input image file path.")
    invisible_parser.add_argument("output", help="Output image file path (should be PNG).")
    invisible_parser.add_argument("--message", help="Secret text message to encode.")
    invisible_parser.add_argument("--file", help="Path to file containing data to encode.")
    invisible_parser.add_argument("--strength", type=int, default=3, choices=range(1, 6),
                                help="Encoding strength (1-5). Higher values use more bits. Default: %(default)s")
    invisible_parser.set_defaults(func=cli_encode_invisible)

    # --- Decode watermark arguments ---
    decode_parser = subparsers.add_parser("decode", help="Extract hidden data from watermarked image.")
    decode_parser.add_argument("input", help="Input watermarked image file path.")
    decode_parser.add_argument("--output", help="Output file path for extracted data. If omitted, displays as text.")
    decode_parser.add_argument("--strength", type=int, default=3, choices=range(1, 6),
                              help="Decoding strength (1-5). Must match encoding strength. Default: %(default)s")
    decode_parser.set_defaults(func=cli_decode)

    # --- Web server arguments ---
    web_parser = subparsers.add_parser("web", help="Start web server interface.")
    web_parser.set_defaults(func=run_web_server)
    
    args = parser.parse_args()

    # Execute the function associated with the chosen sub-command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        # This should not happen if subparsers are required, but good practice
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()