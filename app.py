from flask import Flask, request, send_from_directory, render_template, jsonify
from PIL import Image, ImageOps
import os
import pillow_heif  # Required for HEIC support
import logging
import time
import threading
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths for uploads, watermarked outputs, and logo
UPLOAD_FOLDER = 'Uploads'  # Storage for staged (pre-watermarked) images
WATERMARKED_FOLDER = 'watermarked'  # Storage for watermarked images
LOGO_PATH = 'logo.png'  # Update if logo is named differently (e.g., 'dance_logo.png')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'heic', 'heif'}  # Added HEIC/HEIF support

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(WATERMARKED_FOLDER, exist_ok=True)

# Register HEIC/HEIF support with Pillow
pillow_heif.register_heif_opener()

# Check if uploaded file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to add watermark to an image
def add_watermark(image_path, output_path):
    logging.debug(f"Adding watermark to {image_path}, saving to {output_path}")
    # Open the uploaded image and logo
    base_image = Image.open(image_path)
    
    # Correct orientation based on EXIF data
    base_image = ImageOps.exif_transpose(base_image)
    
    watermark = Image.open(LOGO_PATH).convert("RGBA")  # Convert logo to RGBA for transparency
    
    # Make logo semi-transparent (50% opacity)
    alpha = watermark.split()[3]  # Get alpha channel
    alpha = alpha.point(lambda p: int(p * 0.5))  # Reduce opacity to 50%
    watermark.putalpha(alpha)  # Apply modified alpha channel
    
    # Resize watermark to 20% of base image width (adjustable)
    watermark_width = int(base_image.width * 0.2)
    watermark_height = int(watermark_width * (watermark.height / watermark.width))
    watermark = watermark.resize((watermark_width, watermark_height), Image.Resampling.LANCZOS)
    
    # Position watermark in bottom-right corner with 20px padding (adjustable)
    position = (base_image.width - watermark_width - 20, base_image.height - watermark_height - 20)
    
    # Convert base image to RGBA if needed for transparency support
    if base_image.mode != 'RGBA':
        base_image = base_image.convert('RGBA')
    
    # Overlay watermark
    base_image.paste(watermark, position, watermark)  # Use watermark as mask for transparency
    
    # Convert to RGB for output (output as JPEG for consistency)
    base_image = base_image.convert('RGB')
    
    # Save as JPEG (regardless of input format) to ensure compatibility
    output_path = os.path.splitext(output_path)[0] + '.jpg'
    base_image.save(output_path, quality=95)  # Save with high quality

# Function to delete files older than 24 hours
def cleanup_old_files():
    while True:
        logging.debug("Running cleanup for old files")
        now = datetime.now()
        cutoff = now - timedelta(hours=24)
        
        # Clean uploads folder
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if mtime < cutoff:
                    try:
                        os.remove(file_path)
                        logging.debug(f"Deleted old staged file: {filename}")
                    except Exception as e:
                        logging.error(f"Error deleting old staged file {filename}: {str(e)}")
        
        # Clean watermarked folder
        for filename in os.listdir(WATERMARKED_FOLDER):
            file_path = os.path.join(WATERMARKED_FOLDER, filename)
            if os.path.isfile(file_path):
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if mtime < cutoff:
                    try:
                        os.remove(file_path)
                        logging.debug(f"Deleted old watermarked file: {filename}")
                    except Exception as e:
                        logging.error(f"Error deleting old watermarked file {filename}: {str(e)}")
        
        time.sleep(3600)  # Check every hour

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

# Route to stage files
@app.route('/stage', methods=['POST'])
def stage_files():
    logging.debug(f"Received stage request from {request.remote_addr}")
    if 'file' not in request.files:
        logging.error("No file part in request")
        return jsonify({'success': False, 'error': 'No file part'}), 400
    
    files = request.files.getlist('file')
    if not files or all(file.filename == '' for file in files):
        logging.error("No valid files selected")
        return jsonify({'success': False, 'error': 'No selected files'}), 400
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = file.filename
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                file.save(input_path)
                logging.debug(f"Staged file: {filename}")
            except Exception as e:
                logging.error(f"Error staging {filename}: {str(e)}")
                return jsonify({'success': False, 'error': f'Error staging {filename}: {str(e)}'}), 500
    
    return jsonify({'success': True}), 200

# Route for the main page
@app.route('/', methods=['GET'])
def main_page():
    logging.debug(f"Rendering main page for {request.remote_addr}")
    # Get list of pre-watermarked (staged) files
    original_files = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
    
    # Get list of watermarked files
    watermarked_files = [f for f in os.listdir(WATERMARKED_FOLDER) if allowed_file(f)]
    
    # Render HTML template
    return render_template('index.html', original_files=original_files, watermarked_files=watermarked_files)

# Route to process all staged files
@app.route('/process', methods=['POST'])
def process_files():
    logging.debug(f"Processing files for {request.remote_addr}")
    original_files = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
    if not original_files:
        logging.error("No files to process")
        return jsonify({'success': False, 'error': 'No files to process'}), 400
    
    download_links = []
    for filename in original_files:
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_filename = f"watermarked_{filename.rsplit('.', 1)[0]}.jpg"  # Output as JPEG
        output_path = os.path.join(WATERMARKED_FOLDER, output_filename)
        
        try:
            add_watermark(input_path, output_path)
            os.remove(input_path)  # Delete original after successful watermarking
            download_links.append({'filename': output_filename, 'url': f'/download/{output_filename}'})
            logging.debug(f"Processed {filename} to {output_filename}")
        except Exception as e:
            logging.error(f"Error processing {filename}: {str(e)}")
            return jsonify({'success': False, 'error': f'Error processing {filename}: {str(e)}'}), 500
    
    return jsonify({'success': True, 'links': download_links}), 200

# Route to serve watermarked files for download
@app.route('/download/<filename>')
def download_file(filename):
    logging.debug(f"Downloading watermarked file: {filename}")
    return send_from_directory(WATERMARKED_FOLDER, filename, as_attachment=True)

# Route to delete a watermarked file
@app.route('/delete/<filename>', methods=['GET'])
def delete_file(filename):
    logging.debug(f"Deleting watermarked file: {filename}")
    file_path = os.path.join(WATERMARKED_FOLDER, filename)
    if os.path.exists(file_path) and allowed_file(filename):
        try:
            os.remove(file_path)
            return jsonify({'success': True}), 200
        except Exception as e:
            logging.error(f"Error deleting {filename}: {str(e)}")
            return jsonify({'success': False, 'error': f'Error deleting {filename}: {str(e)}'}), 500
    logging.error(f"File not found: {filename}")
    return jsonify({'success': False, 'error': 'File not found'}), 404

# Route to serve pre-watermarked (staged) files for download
@app.route('/download_original/<filename>')
def download_original_file(filename):
    logging.debug(f"Downloading staged file: {filename}")
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# Route to delete a pre-watermarked (staged) file
@app.route('/delete_original/<filename>', methods=['GET'])
def delete_original_file(filename):
    logging.debug(f"Deleting staged file: {filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path) and allowed_file(filename):
        try:
            os.remove(file_path)
            return jsonify({'success': True}), 200
        except Exception as e:
            logging.error(f"Error deleting {filename}: {str(e)}")
            return jsonify({'success': False, 'error': f'Error deleting {filename}: {str(e)}'}), 500
    logging.error(f"File not found: {filename}")
    return jsonify({'success': False, 'error': 'File not found'}), 404

# Run the server on all interfaces, port 5000, with debug mode
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)