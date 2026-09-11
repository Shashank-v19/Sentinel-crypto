document.addEventListener('DOMContentLoaded', () => {
    const imageInput = document.getElementById('imageInput');
    const uploadArea = document.getElementById('dropZone');
    const previewArea = document.getElementById('previewArea');
    const imagePreview = document.getElementById('imagePreview');
    const encryptBtn = document.getElementById('encryptBtn');

    const resultCard = document.getElementById('resultCard');
    const uploadCard = document.getElementById('uploadCard');
    const encryptedImage = document.getElementById('encryptedImage');
    const downloadEncrypted = document.getElementById('downloadEncrypted');
    const sessionIdDisplay = document.getElementById('sessionIdDisplay');
    const copySessionBtn = document.getElementById('copySessionBtn');

    // Metrics
    const valEntropy = document.getElementById('valEntropy');
    const valNpcr = document.getElementById('valNpcr');
    const valUaci = document.getElementById('valUaci');

    let selectedFile = null;

    // Handle drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = 'var(--primary)';
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
                uploadCard.classList.remove('full-width');
            };
            reader.readAsDataURL(selectedFile);
        }
    }

    encryptBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        const originalText = encryptBtn.innerHTML;
        encryptBtn.innerHTML = '⏳ Encrypting…';
        encryptBtn.disabled = true;

        const formData = new FormData();
        formData.append('image', selectedFile);

        try {
            const response = await fetch('/api/encrypt', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.error) {
                alert(data.error);
                return;
            }

            // Update UI with encrypted data
            encryptedImage.src = data.encryptedUrl;
            downloadEncrypted.href = data.encryptedUrl;
            sessionIdDisplay.textContent = data.sessionId;

            valEntropy.textContent = data.metrics.entropy;
            valNpcr.textContent = data.metrics.npcr + '%';
            valUaci.textContent = data.metrics.uaci + '%';

            // Calculate similarity to ideal values
            const entropyMatch = (data.metrics.entropy / 8.0) * 100;
            const npcrMatch = 100 - Math.abs(data.metrics.npcr - 99.6094);
            const uaciMatch = 100 - Math.abs(data.metrics.uaci - 33.4635);

            document.getElementById('matchEntropy').textContent = `${entropyMatch.toFixed(2)}% Match`;
            document.getElementById('matchNpcr').textContent = `${npcrMatch.toFixed(2)}% Match`;
            document.getElementById('matchUaci').textContent = `${uaciMatch.toFixed(2)}% Match`;

            document.getElementById('formulaX0').textContent = data.formulaData.x0;

            resultCard.classList.remove('hidden');
            resultCard.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during encryption.');
        } finally {
            encryptBtn.innerHTML = originalText;
            encryptBtn.disabled = false;
        }
    });

    copySessionBtn.addEventListener('click', () => {
        const text = sessionIdDisplay.textContent;
        navigator.clipboard.writeText(text).then(() => {
            const originalText = copySessionBtn.textContent;
            copySessionBtn.textContent = 'Copied!';
            setTimeout(() => {
                copySessionBtn.textContent = originalText;
            }, 2000);
        });
    });
});
