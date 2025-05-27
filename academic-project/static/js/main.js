// Video elements and constraints
let videoStream = null;
let capturedImageData = null;
let attendanceCapturedImageData = null;

const videoConstraints = {
    video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: "user"
    },
    audio: false
};

// Initialize video streams for different tabs
async function initializeVideo(videoElement) {
    try {
        // Stop any existing stream
        if (videoStream) {
            videoStream.getTracks().forEach(track => track.stop());
        }

        // Request camera permissions explicitly
        const stream = await navigator.mediaDevices.getUserMedia(videoConstraints);
        videoStream = stream;
        videoElement.srcObject = stream;
        
        // Ensure video is playing
        try {
            await videoElement.play();
            console.log('Video started playing');
        } catch (playError) {
            console.error('Error playing video:', playError);
            alert('Error starting video stream. Please check your camera permissions.');
        }
    } catch (err) {
        console.error('Error accessing camera:', err);
        if (err.name === 'NotAllowedError') {
            alert('Camera access was denied. Please allow camera access in your browser settings and refresh the page.');
        } else if (err.name === 'NotFoundError') {
            alert('No camera found. Please connect a camera and refresh the page.');
        } else {
            alert('Error accessing camera: ' + err.message);
        }
    }
}

// Stop video stream
function stopVideoStream() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => {
            track.stop();
        });
        videoStream = null;
    }
}

// Initialize videos when tabs are shown
document.getElementById('register-tab').addEventListener('click', async () => {
    document.getElementById('registerForm').reset();
    document.getElementById('capturedImage').style.display = 'none';
    document.getElementById('videoElement').style.display = 'block';
    document.getElementById('captureBtn').style.display = 'block';
    document.getElementById('retakeBtn').style.display = 'none';
    capturedImageData = null;
    
    // Initialize video after UI is updated
    await initializeVideo(document.getElementById('videoElement'));
});

document.getElementById('attendance-tab').addEventListener('click', async () => {
    document.getElementById('attendanceCapturedImage').style.display = 'none';
    document.getElementById('attendanceVideo').style.display = 'block';
    document.getElementById('attendanceCaptureBtn').style.display = 'block';
    document.getElementById('attendanceRetakeBtn').style.display = 'none';
    document.getElementById('markAttendanceBtn').disabled = true;
    document.getElementById('attendanceResult').style.display = 'none';
    attendanceCapturedImageData = null;
    
    // Initialize video after UI is updated
    await initializeVideo(document.getElementById('attendanceVideo'));
});

// Stop video when switching away from video tabs
document.getElementById('view-tab').addEventListener('click', stopVideoStream);

// Helper function to capture image from video
function captureImage(videoElement) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    // Set canvas size to match video dimensions
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    
    // Draw the video frame to canvas
    context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    
    // Convert to base64
    return canvas.toDataURL('image/jpeg', 0.8);
}

// Registration capture button
document.getElementById('captureBtn').addEventListener('click', () => {
    const video = document.getElementById('videoElement');
    
    if (!video.srcObject || !video.srcObject.active) {
        alert('Camera is not ready. Please wait or refresh the page.');
        return;
    }
    
    capturedImageData = captureImage(video);
    
    // Show captured image and switch buttons
    const capturedImage = document.getElementById('capturedImage');
    capturedImage.src = capturedImageData;
    video.style.display = 'none';
    capturedImage.style.display = 'block';
    document.getElementById('captureBtn').style.display = 'none';
    document.getElementById('retakeBtn').style.display = 'block';
});

// Registration retake button
document.getElementById('retakeBtn').addEventListener('click', async () => {
    const video = document.getElementById('videoElement');
    const capturedImage = document.getElementById('capturedImage');
    
    // Show video and switch buttons
    video.style.display = 'block';
    capturedImage.style.display = 'none';
    document.getElementById('captureBtn').style.display = 'block';
    document.getElementById('retakeBtn').style.display = 'none';
    capturedImageData = null;
    
    // Reinitialize video if needed
    if (!video.srcObject || !video.srcObject.active) {
        await initializeVideo(video);
    }
});

// Attendance capture button
document.getElementById('attendanceCaptureBtn').addEventListener('click', () => {
    const video = document.getElementById('attendanceVideo');
    
    if (!video.srcObject || !video.srcObject.active) {
        alert('Camera is not ready. Please wait or refresh the page.');
        return;
    }
    
    attendanceCapturedImageData = captureImage(video);
    
    // Show captured image and switch buttons
    const capturedImage = document.getElementById('attendanceCapturedImage');
    capturedImage.src = attendanceCapturedImageData;
    video.style.display = 'none';
    capturedImage.style.display = 'block';
    document.getElementById('attendanceCaptureBtn').style.display = 'none';
    document.getElementById('attendanceRetakeBtn').style.display = 'block';
    document.getElementById('markAttendanceBtn').disabled = false;
});

// Attendance retake button
document.getElementById('attendanceRetakeBtn').addEventListener('click', async () => {
    const video = document.getElementById('attendanceVideo');
    const capturedImage = document.getElementById('attendanceCapturedImage');
    
    // Show video and switch buttons
    video.style.display = 'block';
    capturedImage.style.display = 'none';
    document.getElementById('attendanceCaptureBtn').style.display = 'block';
    document.getElementById('attendanceRetakeBtn').style.display = 'none';
    document.getElementById('markAttendanceBtn').disabled = true;
    attendanceCapturedImageData = null;
    
    // Reinitialize video if needed
    if (!video.srcObject || !video.srcObject.active) {
        await initializeVideo(video);
    }
});

// Start camera when the page loads
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize camera for the registration tab since it's active by default
    await initializeVideo(document.getElementById('videoElement'));
});

// Register student form submission
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!capturedImageData) {
        alert('Please capture a photo first');
        return;
    }
    
    const name = document.getElementById('name').value;
    const rollNumber = document.getElementById('rollNumber').value;
    
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                roll_number: rollNumber,
                face_image: capturedImageData
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Student registered successfully!');
            document.getElementById('registerForm').reset();
            // Reset capture UI
            document.getElementById('capturedImage').style.display = 'none';
            document.getElementById('videoElement').style.display = 'block';
            document.getElementById('captureBtn').style.display = 'block';
            document.getElementById('retakeBtn').style.display = 'none';
            capturedImageData = null;
            // Reinitialize video
            await initializeVideo(document.getElementById('videoElement'));
        } else {
            if (data.error === 'Face already registered') {
                alert(`Error: ${data.error}\n${data.details}`);
            } else {
                alert('Error: ' + (data.error || 'Failed to register student'));
            }
        }
    } catch (err) {
        console.error('Error:', err);
        alert('Error registering student. Please try again.');
    }
});

// Mark attendance button click
document.getElementById('markAttendanceBtn').addEventListener('click', async () => {
    if (!attendanceCapturedImageData) {
        alert('Please capture a photo first');
        return;
    }
    
    const rollNumber = document.getElementById('attendanceRollNumber').value;
    if (!rollNumber) {
        alert('Please enter a roll number');
        return;
    }
    
    const subject = document.getElementById('subject').value;
    const resultDiv = document.getElementById('attendanceResult');
    
    try {
        const response = await fetch('/mark-attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                face_image: attendanceCapturedImageData,
                subject: subject,
                roll_number: rollNumber
            })
        });
        
        const data = await response.json();
        resultDiv.style.display = 'block';
        
        if (response.ok) {
            // Face matched and attendance marked
            Swal.fire({
                icon: 'success',
                title: 'Face Matched!',
                text: `Successfully verified identity for Roll Number: ${rollNumber}`,
                confirmButtonColor: '#4CAF50'
            }).then(() => {
                resultDiv.className = 'alert alert-success';
                resultDiv.textContent = `Attendance marked successfully for ${data.student_name}`;
            });
        } else {
            if (data.already_marked) {
                // Face matched but attendance already marked
                Swal.fire({
                    icon: 'success',
                    title: 'Face Matched!',
                    text: `Successfully verified identity for Roll Number: ${rollNumber}`,
                    confirmButtonColor: '#4CAF50'
                }).then(() => {
                    resultDiv.className = 'alert alert-warning';
                    resultDiv.textContent = `Attendance already marked for ${data.student_name}`;
                });
            } else if (!data.face_matched) {
                // Face not recognized
                Swal.fire({
                    icon: 'error',
                    title: 'Face Not Matched',
                    text: 'The captured face does not match with the registered student',
                    confirmButtonColor: '#dc3545'
                });
                resultDiv.className = 'alert alert-danger';
                resultDiv.textContent = data.error || 'Face not recognized. Please try again.';
            } else {
                // Other errors
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.error || 'Failed to mark attendance',
                    confirmButtonColor: '#dc3545'
                });
                resultDiv.className = 'alert alert-danger';
                resultDiv.textContent = data.error || 'Failed to mark attendance';
            }
        }
        
        // Reset capture UI
        document.getElementById('attendanceCapturedImage').style.display = 'none';
        document.getElementById('attendanceVideo').style.display = 'block';
        document.getElementById('attendanceCaptureBtn').style.display = 'block';
        document.getElementById('attendanceRetakeBtn').style.display = 'none';
        document.getElementById('markAttendanceBtn').disabled = true;
        attendanceCapturedImageData = null;
        // Reinitialize video
        await initializeVideo(document.getElementById('attendanceVideo'));
        
    } catch (err) {
        console.error('Error:', err);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Error marking attendance. Please try again.',
            confirmButtonColor: '#dc3545'
        });
        resultDiv.style.display = 'block';
        resultDiv.className = 'alert alert-danger';
        resultDiv.textContent = 'Error marking attendance. Please try again.';
    }
});

// View attendance button click
document.getElementById('viewAttendanceBtn').addEventListener('click', async () => {
    const subject = document.getElementById('viewSubject').value;
    const date = document.getElementById('viewDate').value;
    
    if (!date) {
        alert('Please select a date');
        return;
    }
    
    try {
        const response = await fetch(`/get-attendance?subject=${encodeURIComponent(subject)}&date=${encodeURIComponent(date)}`);
        const data = await response.json();
        
        const tableBody = document.getElementById('attendanceTableBody');
        tableBody.innerHTML = '';
        
        if (data.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="3" class="text-center">No attendance records found</td></tr>';
            return;
        }
        
        data.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.name}</td>
                <td>${record.roll_number}</td>
                <td>${record.present ? '<span class="text-success">Present</span>' : '<span class="text-danger">Absent</span>'}</td>
            `;
            tableBody.appendChild(row);
        });
    } catch (err) {
        console.error('Error:', err);
        alert('Error fetching attendance records. Please try again.');
    }
});
