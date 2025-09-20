# Video to Comic Generator - Replit Project

## Overview
This is a Flask-based web application that transforms videos into comic-style storyboards. The project was imported from GitHub and configured to run in the Replit environment.

## Project Status
- ✅ Successfully imported and configured for Replit
- ✅ Running in mock mode (AI dependencies disabled due to storage constraints)
- ✅ Frontend working with file upload interface
- ✅ Workflow configured and running on port 5000
- ✅ Deployment configuration set up for autoscale
- ✅ Flask app properly configured for host binding (0.0.0.0:5000)
- ✅ Debug mode configured for development/production safety

## Architecture
- **Backend**: Flask web server (Python 3.11)
- **Frontend**: HTML templates with CSS/JS
- **Running Mode**: Mock mode - generates placeholder comic panels
- **Port**: 5000 (configured for Replit environment)

## Recent Changes (September 20, 2025)
- Installed Python 3.11 and Flask dependencies
- Resolved disk quota issues by clearing pip cache
- Created missing directories (static/uploads, static/styles)
- Modified Flask app to bind to 0.0.0.0:5000 for Replit proxy compatibility
- Configured workflow to run Flask development server
- Set up deployment configuration for autoscale

## Key Features (Mock Mode)
- Video file upload interface (supports MP4, AVI, MOV, WMV, MKV)
- Style selection options
- Generates mock comic panels with placeholder content
- Results page displaying generated panels
- Download functionality for comic panels

## Technical Notes
- The app automatically detects missing AI dependencies and runs in mock mode
- Mock mode generates sample comic panels without requiring TensorFlow, OpenCV, or Whisper
- All file uploads and processing work through the web interface
- Static assets (CSS, JS, fonts) are properly served

## File Structure
- `/app.py` - Main Flask application
- `/utils.py` - Comic generation utilities (not loaded in mock mode)
- `/templates/` - HTML templates (index.html, results.html)
- `/static/` - Static assets (CSS, JS, fonts, generated output)
- `/static/output/` - Generated comic panels storage
- `/static/uploads/` - Temporary video upload storage