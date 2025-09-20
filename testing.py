from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename
import time
import random
import shutil

app = Flask(__name__)
app.secret_key = "comic_generator_secret_key"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/output'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'wmv', 'mkv'}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Flag to enable/disable actual processing
MOCK_PROCESSING = True

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        flash('No video file uploaded')
        return redirect(request.url)
    
    file = request.files['video']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if not allowed_file(file.filename):
        flash(f'Invalid file type. Allowed types: {", ".join(app.config["ALLOWED_EXTENSIONS"])}')
        return redirect(request.url)
    
    try:
        # Generate unique ID for this job
        job_id = str(uuid.uuid4())
        os.makedirs(os.path.join(app.config['OUTPUT_FOLDER'], job_id), exist_ok=True)
        
        # Save the uploaded file (for demo purposes)
        filename = secure_filename(file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
        file.save(video_path)
        
        if MOCK_PROCESSING:
            # Mock processing - simulate delay
            flash('Processing video... (MOCK MODE)')
            time.sleep(2)  # Simulate processing time
            
            # Generate mock panels (copy sample images or create placeholders)
            output_images = generate_mock_panels(job_id, 6)  # Generate 6 mock panels
        else:
            # TODO: Real processing goes here when utils is properly implemented
            # This would use the ComicGenerator class from utils.py
            flash('Processing video... This may take a while.')
            # You would import and use the ComicGenerator class here
            output_images = []  # Replace with actual processing results
        
        # Clean up uploaded video
        if os.path.exists(video_path):
            os.remove(video_path)
        
        return render_template('results.html', images=output_images, job_id=job_id)
    
    except Exception as e:
        flash(f'Error processing video: {str(e)}')
        return redirect(url_for('index'))

def generate_mock_panels(job_id, num_panels):
    """Generate mock comic panels for testing the frontend"""
    output_images = []
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
    
    # Create sample panels with colored rectangles and placeholder text
    for i in range(num_panels):
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a blank image
        img = Image.new('RGB', (512, 288), color=(
            random.randint(200, 255), 
            random.randint(200, 255), 
            random.randint(200, 255)
        ))
        
        draw = ImageDraw.Draw(img)
        
        # Draw a frame
        draw.rectangle(
            [(10, 10), (502, 278)],
            outline=(0, 0, 0),
            width=2
        )
        
        # Add some text
        try:
            font = ImageFont.truetype("Arial", 16)
        except:
            font = ImageFont.load_default()
            
        draw.text(
            (50, 50),
            f"Mock Comic Panel {i+1}",
            fill=(0, 0, 0),
            font=font
        )
        
        # Add a speech bubble
        draw.rounded_rectangle(
            [50, 100, 350, 170],
            radius=10,
            fill=(255, 255, 255),
            outline=(0, 0, 0),
            width=2
        )
        
        draw.text(
            (70, 120),
            f"This is a mock speech bubble.\nPanel {i+1} of {num_panels}",
            fill=(0, 0, 0),
            font=font
        )
        
        # Save the image
        panel_path = os.path.join(output_dir, f"panel_{i:03d}.jpg")
        img.save(panel_path)
        
        # Add to output list
        output_images.append(f"{job_id}/panel_{i:03d}.jpg")
    
    return output_images

@app.route('/output/<path:filename>')
def get_output(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/cleanup')
def cleanup():
    """Clean up temporary files (for development)"""
    try:
        for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
            for root, dirs, files in os.walk(folder):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))
        flash('All temporary files cleaned up')
    except Exception as e:
        flash(f'Error during cleanup: {str(e)}')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)