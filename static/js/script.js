document.addEventListener('DOMContentLoaded', function() {
    // Detect which page we're on
    const isIndexPage = document.querySelector('.upload-section') !== null;
    const isResultsPage = document.querySelector('.results-section') !== null;
    
    // Index page functionality (video upload)
    if (isIndexPage) {
        initializeUploadPage();
    }
    
    // Results page functionality
    if (isResultsPage) {
        initializeResultsPage();
    }
});

function initializeUploadPage() {
    const fileInput = document.getElementById('video');
    const uploadLabel = document.querySelector('.up-vid-txt');
    const inputDiv = document.querySelector('.input-div');
    const form = document.querySelector('form');
    const submitButton = document.querySelector('button.button');
    
    // Check if elements were found
    if (!fileInput || !uploadLabel || !inputDiv || !form || !submitButton) {
        console.error("Some required elements were not found on the upload page");
        return;
    }
    
    const originalLabelText = uploadLabel.textContent;
    
    // Create file name display element
    const fileNameDisplay = document.createElement('div');
    fileNameDisplay.className = 'file-name-display';
    fileNameDisplay.style.display = 'none';
    inputDiv.parentNode.insertBefore(fileNameDisplay, inputDiv.nextSibling);
    
    // Create progress elements
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-container';
    progressContainer.style.display = 'none';
    
    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';
    
    const progressText = document.createElement('div');
    progressText.className = 'progress-text';
    progressText.textContent = '0%';
    
    progressContainer.appendChild(progressBar);
    progressContainer.appendChild(progressText);
    
    // Insert progress container after file name display
    fileNameDisplay.parentNode.insertBefore(progressContainer, fileNameDisplay.nextSibling);
    
    // File selection handler
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            // Update upload label with filename
            uploadLabel.textContent = file.name;
            
            // Show filename below upload button
            fileNameDisplay.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
            fileNameDisplay.style.display = 'block';
            
            // Visual feedback that file is selected
            inputDiv.classList.add('file-selected');
            
            // Reset progress bar if it was previously used
            progressContainer.style.display = 'none';
            progressBar.style.width = '0%';
            progressText.textContent = '0%';
            progressBar.style.backgroundColor = 'rgb(241, 252, 35)';
        } else {
            // Reset to original state
            uploadLabel.textContent = originalLabelText;
            fileNameDisplay.style.display = 'none';
            progressContainer.style.display = 'none';
            inputDiv.classList.remove('file-selected');
        }
    });
    
    // Form submission with progress tracking
    form.addEventListener('submit', function(e) {
        const file = fileInput.files[0];
        
        if (!file) {
            e.preventDefault();
            alert('Please select a video file first.');
            return;
        }
        
        // Only use AJAX if the browser supports FormData and XHR2
        if (window.FormData && window.XMLHttpRequest && 'upload' in new XMLHttpRequest()) {
            e.preventDefault();
            
            const xhr = new XMLHttpRequest();
            const formData = new FormData(form);
            
            // Show progress container
            progressContainer.style.display = 'block';
            submitButton.disabled = true;
            
            // Progress event
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percentComplete + '%';
                    progressText.textContent = percentComplete + '%';
                }
            });
            
            // Load completed
            xhr.addEventListener('load', function() {
                if (xhr.status >= 200 && xhr.status < 400) {
                    progressBar.style.width = '100%';
                    progressText.textContent = 'Processing...';
                    
                    try {
                        const response = JSON.parse(xhr.responseText);
                        if (response.error) {
                            // Show error
                            progressText.textContent = 'Error: ' + response.error;
                            progressBar.style.backgroundColor = '#dc3545';
                            submitButton.disabled = false;
                        } else if (response.redirect) {
                            // Successful upload, redirect to results
                            progressText.textContent = 'Upload complete! Redirecting...';
                            setTimeout(function() {
                                window.location.href = response.redirect;
                            }, 1000);
                        }
                    } catch (e) {
                        // Handle non-JSON response (like an HTML page)
                        window.location.reload();
                    }
                } else {
                    // Error response
                    progressText.textContent = 'Error: ' + xhr.status;
                    progressBar.style.backgroundColor = '#dc3545';
                    submitButton.disabled = false;
                }
            });
            
            // Error handler
            xhr.addEventListener('error', function() {
                progressText.textContent = 'Upload failed';
                progressBar.style.backgroundColor = '#dc3545';
                submitButton.disabled = false;
            });
            
            // Abort handler
            xhr.addEventListener('abort', function() {
                progressText.textContent = 'Upload cancelled';
                progressBar.style.backgroundColor = '#dc3545';
                submitButton.disabled = false;
            });
            
            // Open the request first
            xhr.open('POST', form.action, true);
            
            // Set headers after opening the request
            xhr.setRequestHeader('Accept', 'application/json');
            
            // Send the request
            xhr.send(formData);
        }
        // If no AJAX support, let the form submit normally
    });
}

function initializeResultsPage() {
    const downloadAllBtn = document.querySelector('.download-all');
    
    if (downloadAllBtn) {
        downloadAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get the job ID from the URL
            const pathParts = window.location.pathname.split('/');
            const jobId = pathParts[pathParts.length - 1];
            
            // Redirect to a backend endpoint that will create and return the ZIP file
            window.location.href = '/download_zip/' + jobId;
        });
    }
}

// Helper function to format file size
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' bytes';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
}