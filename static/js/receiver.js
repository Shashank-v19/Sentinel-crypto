document.addEventListener('DOMContentLoaded', () => {
    const imageInput = document.getElementById('imageInput');
    const uploadArea = document.getElementById('dropZone');
    const previewArea = document.getElementById('previewArea');
    const imagePreview = document.getElementById('imagePreview');
    const decryptBtn = document.getElementById('decryptBtn');

    const resultCard = document.getElementById('resultCard');
    const decryptedImage = document.getElementById('decryptedImage');
    const downloadDecrypted = document.getElementById('downloadDecrypted');
    const sessionKeyInput = document.getElementById('sessionKey');
    const errorMsg = document.getElementById('errorMsg');

    let selectedFile = null;

    // Handle drag and drop for receiver
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = 'var(--color-signal-blue)';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = '';
        }, false);
    });

    uploadArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }, false);

    imageInput.addEventListener('change', function () {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            selectedFile = files[0];
            const reader = new FileReader();
            reader.onload = function (e) {
                imagePreview.src = e.target.result;
                uploadArea.classList.add('hidden');
                previewArea.classList.remove('hidden');
                resultCard.classList.add('hidden'); // hide previous result if any
                errorMsg.classList.add('hidden');
            };
            reader.readAsDataURL(selectedFile);
        }
    }

    decryptBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        const sessionKey = sessionKeyInput.value.trim();
        if (!sessionKey) {
            errorMsg.textContent = 'Please enter the Session Key first.';
            errorMsg.classList.remove('hidden');
            return;
        }

        const originalText = decryptBtn.innerHTML;
        decryptBtn.innerHTML = '⏳ Decrypting…';
        decryptBtn.disabled = true;
        errorMsg.classList.add('hidden');

        const formData = new FormData();
        formData.append('image', selectedFile);
        formData.append('sessionId', sessionKey);

        try {
            const response = await fetch('/api/decrypt', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.error) {
                errorMsg.textContent = data.error;
                errorMsg.classList.remove('hidden');
                return;
            }

            // Update UI with decrypted data
            decryptedImage.src = data.decryptedUrl + "?t=" + new Date().getTime(); // cache busting 
            downloadDecrypted.href = data.decryptedUrl;

            resultCard.classList.remove('hidden');
            resultCard.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            console.error('Error:', error);
            errorMsg.textContent = 'An error occurred during decryption.';
            errorMsg.classList.remove('hidden');
        } finally {
            decryptBtn.innerHTML = originalText;
            decryptBtn.disabled = false;
        }
    });
});
