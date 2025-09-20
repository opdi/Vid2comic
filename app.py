from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
import time
import random
import shutil
import zipfile
from io import BytesIO

# Import our ComicGenerator class - comment out if you want to test frontend only
try:
    from utils import ComicGenerator
    UTILS_AVAILABLE = True
except ImportError:
    print("Warning: ComicGenerator class not available. Running in mock mode.")
    UTILS_AVAILABLE = False

app = Flask(__name__)
app.secret_key = "comic_generator_secret_key"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/output'
app.config['STYLES_FOLDER'] = 'static/styles'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'wmv', 'mkv'}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['STYLES_FOLDER'], exist_ok=True)

# Set to True to force mock mode even if utils is available
FORCE_MOCK_MODE = False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    # Check if we're in mock mode
    mock_mode = FORCE_MOCK_MODE or not UTILS_AVAILABLE
    return render_template('index.html', mock_mode=mock_mode)

@app.route('/upload_file', methods=['POST'])
def upload_file():
    # Check if the post request has the file part
    if 'video' not in request.files:
        if request.accept_mimetypes.accept_json:
            return jsonify({'error': 'No video file uploaded'}), 400
        flash('No video file uploaded')
        return redirect(url_for('index'))
    
    file = request.files['video']
    
    if file.filename == '':
        if request.accept_mimetypes.accept_json:
            return jsonify({'error': 'No file selected'}), 400
        flash('No file selected')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        error_msg = f'Invalid file type. Allowed types: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
        if request.accept_mimetypes.accept_json:
            return jsonify({'error': error_msg}), 400
        flash(error_msg)
        return redirect(url_for('index'))
    
    try:
        # Generate unique ID for this job
        job_id = str(uuid.uuid4())
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
        file.save(video_path)
        
        # Get style image selection
        style_image = request.form.get('style_image', 'static/styles/comic_style.jpg')
        
        # Check if we should use mock processing
        use_mock = FORCE_MOCK_MODE or not UTILS_AVAILABLE
        
        if use_mock:
            # Mock processing
            message = 'Processing video in MOCK MODE... Demo panels will be generated.'
            if not request.accept_mimetypes.accept_json:
                flash(message)
            time.sleep(2)  # Simulate processing delay
            output_images = generate_mock_panels(job_id, 6)
        else:
            # Real processing with ComicGenerator
            message = 'Processing video... This may take a while.'
            if not request.accept_mimetypes.accept_json:
                flash(message)
            
            # Create comic generator instance with selected style
            comic_gen = ComicGenerator(style_path=style_image)
            
            # Generate comic panels
            try:
                panel_paths = comic_gen.generate_comic_from_video(video_path, output_dir)
                output_images = [f"{job_id}/{os.path.basename(path)}" for path in panel_paths]
            except Exception as e:
                error_msg = f"Comic generation failed: {str(e)}"
                if not request.accept_mimetypes.accept_json:
                    flash(error_msg)
                # Fall back to mock panels if real processing fails
                output_images = generate_mock_panels(job_id, 4)
        
        # Clean up uploaded video
        if os.path.exists(video_path):
            os.remove(video_path)
        
        # Handle AJAX requests differently than regular form submissions
        if request.accept_mimetypes.accept_json:
            return jsonify({
                'success': True,
                'redirect': url_for('results', job_id=job_id),
                'message': message,
                'mock_mode': use_mock
            })
        
        return redirect(url_for('results', job_id=job_id))
    
    except Exception as e:
        error_msg = f'Error processing video: {str(e)}'
        if request.accept_mimetypes.accept_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg)
        return redirect(url_for('index'))

def generate_mock_panels(job_id, num_panels):
    """Generate mock comic panels for testing the frontend"""
    output_images = []
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
    
    # Create sample panels with colored rectangles and placeholder text
    for i in range(num_panels):
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a blank image with random pastel background
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
        
        # Add some mock dialogue
        dialogue_options = [
            f"This is a mock speech bubble.\nPanel {i+1} of {num_panels}",
            "Hello there! This is just a placeholder.",
            "Comic generation would normally happen here!",
            "In real mode, this would be real dialogue from your video!",
            "Speech bubbles will contain transcribed audio."
        ]
        
        draw.text(
            (70, 120),
            random.choice(dialogue_options),
            fill=(0, 0, 0),
            font=font
        )
        
        # Save the image
        panel_path = os.path.join(output_dir, f"panel_{i:03d}.jpg")
        img.save(panel_path)
        
        # Add to output list
        output_images.append(f"{job_id}/panel_{i:03d}.jpg")
    
    return output_images

@app.route('/results/<job_id>')
def results(job_id):
    """Display the results page for a specific job"""
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
    
    if not os.path.exists(output_dir):
        flash("Results not found")
        return redirect(url_for('index'))
    
    # Get all image files in the job output directory
    images = []
    for filename in os.listdir(output_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            images.append(f"{job_id}/{filename}")
    
    # Sort the images by panel number
    images.sort()
    
    use_mock = FORCE_MOCK_MODE or not UTILS_AVAILABLE
    
    return render_template('results.html', 
                          images=images, 
                          job_id=job_id, 
                          mock_mode=use_mock)

@app.route('/output/<path:filename>')
def get_output(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/download_zip/<job_id>')
def download_zip(job_id):
    """Create a ZIP file with all panels for a job and send it to the user"""
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
    
    if not os.path.exists(output_dir):
        flash("Results not found")
        return redirect(url_for('index'))
    
    # Create a ZIP file in memory
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for filename in os.listdir(output_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(output_dir, filename)
                zf.write(file_path, filename)
    
    # Seek to the beginning of the stream
    memory_file.seek(0)
    
    # Set the appropriate headers
    return send_from_directory(
        app.config['OUTPUT_FOLDER'],
        f"{job_id}/panels.zip",
        as_attachment=True,
        download_name=f"comic_panels_{job_id}.zip",
        attachment_filename=f"comic_panels_{job_id}.zip"
    )

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
    # Check if we're in mock mode
    if FORCE_MOCK_MODE or not UTILS_AVAILABLE:
        print("Running in MOCK MODE - no real video processing will be performed")
    # Use debug mode only in development
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)