const captureButton = document.getElementById('capture');
const predictButton = document.getElementById('predict');
const resultText = document.getElementById('result');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

// Capture the image from the video stream
captureButton.addEventListener('click', () => {
    const videoStream = document.getElementById('video-stream');
    ctx.drawImage(videoStream, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas image to data URL and send it to server to save as test.jpg
    const imageData = canvas.toDataURL('image/png');

    fetch('/capture', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image: imageData }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Image saved as:', data.path);
    })
    .catch(error => {
        console.log('Error:', error);
    });
});

// Send saved image path to server for prediction
predictButton.addEventListener('click', () => {
    fetch('/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: 'test.jpg' }),
    })
    .then(response => response.json())
    .then(data => {
        const resultText = document.getElementById('result');
        resultText.textContent = 'Prediction Result:  ' + data.result;
        // Add a class to trigger animation
        resultText.classList.add('celebration');
    })
    .catch(error => {
        console.log('Error:', error);
    });
});


captureButton.addEventListener('click', () => {
    // Clear the prediction result
    const resultText = document.getElementById('result');
    resultText.textContent = ''; // Clear the text content
    resultText.classList.remove('celebration'); // Remove the animation class

    // Capture functionality code (existing code here)
    fetch('/capture', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image: capturedImageData }), // Replace `capturedImageData` with your actual image data
    })
    .then(response => response.json())
    .then(data => {
        console.log('Image captured:', data.path);
    })
    .catch(error => {
        console.log('Error capturing image:', error);
    });
});
