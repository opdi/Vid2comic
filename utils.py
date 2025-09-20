import whisper
import cv2
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from PIL import Image, ImageFont, ImageDraw
from fpdf import FPDF
import os
from moviepy.video.io.VideoFileClip import VideoFileClip
import shutil
import re
from tqdm import tqdm

class ComicGenerator:
    def __init__(self, style_path="static/styles/comic_style.jpg", model_type="tiny", frame_interval=30, target_size=(512, 288)):
        """
        Initialize the Comic Generator with configuration parameters
        
        Args:
            style_path (str): Path to the style image for transfer
            model_type (str): Whisper model type for audio transcription
            frame_interval (int): Interval for extracting frames from video
            target_size (tuple): Target size for output frames
        """
        self.style_path = style_path
        self.model_type = model_type
        self.frame_interval = frame_interval
        self.target_size = target_size
        self.style_model = None
        self.style_image = None
        
        os.environ['PATH'] += r';C:\ffmpeg\bin'
    
    def check_ffmpeg(self):
        """Check if ffmpeg is installed and available in PATH"""
        if not shutil.which("ffmpeg"):
            raise FileNotFoundError("ffmpeg not found. Please ensure it's installed and added to PATH.")
    
    def extract_audio_from_video(self, video_path):
        """
        Extract audio from a video file
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            audio object or None if extraction fails
        """
        try:
            video = VideoFileClip(video_path)
            audio = video.audio
            return audio
        except Exception as e:
            print(f"[Error] Audio extraction failed: {e}")
            return None
    
    def audio_to_text(self, audio):
        """
        Convert audio to text using Whisper model
        
        Args:
            audio: Audio object from extract_audio_from_video
            
        Returns:
            list: List of sentences from transcription
        """
        if not audio:
            return ["[Audio extraction failed]"]
        
        try:
            temp_audio_path = 'temp_audio.wav'
            audio.write_audiofile(temp_audio_path)
            
            model = whisper.load_model(self.model_type)
            result = model.transcribe(temp_audio_path, fp16=False)
            
            sentences = re.split(r'(?<=[.!?]) +', result['text'])
            
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            
            return sentences
        except Exception as e:
            print(f"[Error] Whisper transcription failed: {e}")
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            return ["[Transcription failed]"]
    
    def extract_frames(self, video_path):
        """
        Extract frames from a video at specified intervals
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            list: List of extracted frames as numpy arrays
        """
        cap = cv2.VideoCapture(video_path)
        frames = []
        count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if count % self.frame_interval == 0:
                resized_frame = cv2.resize(frame, self.target_size)
                frames.append(resized_frame)
            count += 1
        cap.release()
        print(f"[Info] Extracted {len(frames)} frames at size {self.target_size}.")
        return frames
    
    def load_style_model_and_image(self):
        """
        Load the style transfer model and prepare the style image
        
        Returns:
            tuple: (model, style_image) for style transfer
        """
        print("[Info] Loading style model and style image...")
        model = hub.load('https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2')
        
        style_image = cv2.imread(self.style_path)
        if style_image is None:
            raise FileNotFoundError(f"Style image '{self.style_path}' not found.")
        
        style_image = cv2.resize(style_image, (256, 256))
        style_image = tf.convert_to_tensor(style_image, dtype=tf.float32)[tf.newaxis, ...] / 255.0
        
        self.style_model = model
        self.style_image = style_image
        return model, style_image
    
    def apply_comic_filter(self, frame):
        """
        Apply the comic style filter to a frame
        
        Args:
            frame: Input frame as numpy array
            
        Returns:
            numpy.ndarray: Stylized frame
        """
        if self.style_model is None or self.style_image is None:
            self.load_style_model_and_image()
            
        content_image = tf.convert_to_tensor(frame, dtype=tf.float32)[tf.newaxis, ...] / 255.0
        stylized_image = self.style_model(content_image, self.style_image)[0]
        stylized_image = stylized_image.numpy().squeeze() * 255.0
        return cv2.convertScaleAbs(stylized_image)
    
    def trim_text(self, text, max_length=100):
        """Trim text to a maximum length"""
        return text if len(text) <= max_length else text[:max_length] + "..."
    
    def add_speech_bubble(self, image, text, position='top-right'):
        """
        Add a speech bubble with text to an image
        
        Args:
            image: Input image as numpy array
            text (str): Text to display in the speech bubble
            position (str): Position of the speech bubble (top-right, top-left, etc.)
            
        Returns:
            numpy.ndarray: Image with speech bubble added
        """
        text = self.trim_text(text)

        img = Image.fromarray(image)
        draw = ImageDraw.Draw(img, "RGBA")  # Allow transparency

        img_w, img_h = img.size

        # Dynamically scale bubble size based on image
        bubble_width = int(img_w * 0.5)   # 50% of image width
        bubble_height = int(img_h * 0.2)  # 20% of image height

        # Bubble positions with padding
        padding = 10
        positions = {
            'top-left': (padding, padding),
            'top-right': (img_w - bubble_width - padding, padding),
            'bottom-left': (padding, img_h - bubble_height - padding),
            'bottom-right': (img_w - bubble_width - padding, img_h - bubble_height - padding)
        }
        bubble_x, bubble_y = positions.get(position, (padding, padding))

        # Draw semi-transparent white bubble
        bubble_color = (255, 255, 255, 200)  # RGBA: last value 0-255 for transparency
        outline_color = (0, 0, 0, 255)  # black outline
        
        # Draw rounded rectangle for bubble
        radius = 10
        draw.rounded_rectangle(
            [bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height],
            radius=radius, 
            fill=bubble_color, 
            outline=outline_color
        )
        
        # Add text to bubble
        try:
            # Try to use a comic-style font if available
            font = ImageFont.truetype("Arial", 14)
        except IOError:
            font = ImageFont.load_default()
            
        text_color = (0, 0, 0, 255)  # Black text
        text_padding = 15
        
        # Draw text with word wrapping
        draw.text(
            (bubble_x + text_padding, bubble_y + text_padding),
            text,
            font=font,
            fill=text_color
        )
        
        return np.array(img)
    
    def generate_comic_from_video(self, video_path, output_dir):
        """
        Generate comic panels from a video file
        
        Args:
            video_path (str): Path to the video file
            output_dir (str): Directory to save output panels
            
        Returns:
            list: Paths to generated panel images
        """
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Check for FFmpeg
        self.check_ffmpeg()
        
        # Extract audio and convert to text
        audio = self.extract_audio_from_video(video_path)
        captions = self.audio_to_text(audio)
        
        # Extract frames
        frames = self.extract_frames(video_path)
        
        # Load style model
        self.load_style_model_and_image()
        
        # Generate panels
        output_paths = []
        for i, frame in enumerate(tqdm(frames, desc="Generating panels")):
            caption = captions[i] if i < len(captions) else ""
            
            # Apply comic filter
            stylized = self.apply_comic_filter(frame)
            
            # Add speech bubble
            position = 'top-right' if i % 2 == 0 else 'bottom-left'
            final_image = self.add_speech_bubble(stylized, caption, position)
            
            # Save panel
            panel_path = os.path.join(output_dir, f"panel_{i:03d}.jpg")
            Image.fromarray(final_image).save(panel_path)
            output_paths.append(panel_path)
        
        return output_paths

    def set_style_image(self, style_path):
        """
        Update the style image
        
        Args:
            style_path (str): Path to the new style image
        """
        self.style_path = style_path
        # Reset the loaded style image to force reload
        self.style_model = None
        self.style_image = None