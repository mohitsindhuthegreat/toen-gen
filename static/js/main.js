// Global variables
let currentTokens = [];
let processingState = false;

// Initialize the application
function initializeApp() {
    initializeSingleTokenForm();
    initializeFileUpload();
    initializeBulkProcessing();
    initializeDownloadButtons();
    initializeLikeFeature();
}

// Single token form handling
function initializeSingleTokenForm() {
    const form = document.getElementById('singleTokenForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const uid = document.getElementById('uid').value.trim();
        const password = document.getElementById('password').value.trim();
        
        if (!uid || !password) {
            showError('Please enter both UID and password');
            return;
        }
        
        await generateSingleToken(uid, password);
    });
}

// Generate single token
async function generateSingleToken(uid, password) {
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    const singleResult = document.getElementById('singleResult');
    
    try {
        // Show loading
        loadingModal.show();
        
        const response = await fetch('/api/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ uid, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Display success result
            displaySingleTokenResult(result.data);
            singleResult.style.display = 'block';
            singleResult.scrollIntoView({ behavior: 'smooth' });
        } else {
            showError(result.error || 'Failed to generate token');
        }
    } catch (error) {
        showError('Network error. Please try again.');
        console.error('Error:', error);
    } finally {
        // Force hide the modal
        loadingModal.hide();
        // Additional cleanup to ensure modal is properly hidden
        setTimeout(() => {
            const modalElement = document.getElementById('loadingModal');
            if (modalElement) {
                modalElement.classList.remove('show');
                modalElement.style.display = 'none';
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }
                document.body.classList.remove('modal-open');
                document.body.style.removeProperty('padding-right');
            }
        }, 100);
    }
}

// Display single token result
function displaySingleTokenResult(data) {
    document.getElementById('resultUid').textContent = data.uid;
    document.getElementById('resultStatus').textContent = data.status;
    document.getElementById('resultStatus').className = `badge ${data.status === 'success' ? 'bg-success' : 'bg-danger'}`;
    document.getElementById('resultTime').textContent = formatDateTime(data.generated_at);
    document.getElementById('resultToken').textContent = data.token || 'N/A';
    
    // Display validation result
    const validationElement = document.getElementById('resultValidation');
    if (data.validation && validationElement) {
        if (data.validation.valid) {
            validationElement.innerHTML = `<span class="badge bg-success">✓ Valid</span> <small>${data.validation.message}</small>`;
        } else {
            validationElement.innerHTML = `<span class="badge bg-warning">⚠ Unverified</span> <small>${data.validation.message}</small>`;
        }
        validationElement.style.display = 'block';
    }
}

// File upload handling
function initializeFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    const fileInfo = document.getElementById('fileInfo');
    
    if (!fileInput || !uploadArea) return;

    // File input change handler
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop handlers
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('click', (e) => {
        // Prevent multiple clicks
        if (e.detail === 1) {
            fileInput.click();
        }
    });
}

// Handle file selection
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        processUploadedFile(file);
    }
}

// Drag and drop handlers
function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        document.getElementById('fileInput').files = files;
        processUploadedFile(files[0]);
    }
}

// Process uploaded file
async function processUploadedFile(file) {
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const credCount = document.getElementById('credCount');
    
    try {
        // Validate file type
        if (!file.name.match(/\.(txt|json)$/i)) {
            showError('Please upload a .txt or .json file');
            return;
        }
        
        // Read file content
        const content = await readFileContent(file);
        
        // Extract credentials (client-side preview)
        const credentials = extractCredentialsFromContent(content);
        
        if (credentials.length === 0) {
            showError('No valid credentials found in the file');
            return;
        }
        
        // Display file info
        fileName.textContent = file.name;
        credCount.textContent = credentials.length;
        fileInfo.style.display = 'block';
        
        // Store credentials for processing
        window.uploadedCredentials = credentials;
        
    } catch (error) {
        showError('Error reading file: ' + error.message);
        console.error('File processing error:', error);
    }
}

// Read file content
function readFileContent(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(new Error('Failed to read file'));
        reader.readAsText(file);
    });
}

// Extract credentials from content (client-side preview)
function extractCredentialsFromContent(content) {
    const credentials = [];
    
    // Try JSON format first
    try {
        const jsonData = JSON.parse(content);
        if (Array.isArray(jsonData)) {
            jsonData.forEach(item => {
                if (item.guest_account_info) {
                    const uid = item.guest_account_info['com.garena.msdk.guest_uid'];
                    const password = item.guest_account_info['com.garena.msdk.guest_password'];
                    if (uid && password) {
                        credentials.push({ uid, password });
                    }
                }
            });
        }
    } catch (e) {
        // Not valid JSON, try text patterns
        
        // JSON pattern in text
        const jsonPattern = /\{"guest_account_info":\s*\{\s*"com\.garena\.msdk\.guest_uid":\s*"([^"]+)",\s*"com\.garena\.msdk\.guest_password":\s*"([^"]+)"\s*\}\s*\}/g;
        let match;
        while ((match = jsonPattern.exec(content)) !== null) {
            credentials.push({ uid: match[1], password: match[2] });
        }
        
        // Simple UID:PASSWORD pattern
        const simplePattern = /(\d{10,})[:\s|,;]+([A-F0-9]{64})/g;
        while ((match = simplePattern.exec(content)) !== null) {
            credentials.push({ uid: match[1], password: match[2] });
        }
    }
    
    return credentials;
}

// Initialize bulk processing
function initializeBulkProcessing() {
    const processBulkBtn = document.getElementById('processBulk');
    if (!processBulkBtn) return;

    processBulkBtn.addEventListener('click', async () => {
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];
        
        if (!file) {
            showError('Please select a file first');
            return;
        }
        
        await processBulkTokens(file);
    });
}

// Process bulk tokens
async function processBulkTokens(file) {
    const bulkProgress = document.getElementById('bulkProgress');
    const bulkResult = document.getElementById('bulkResult');
    
    try {
        // Show progress
        bulkProgress.style.display = 'block';
        bulkResult.style.display = 'none';
        processingState = true;
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        
        // Send request
        const response = await fetch('/api/bulk-token', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentTokens = result.data;
            displayBulkResults(result.data);
            
            // Hide progress, show results
            bulkProgress.style.display = 'none';
            bulkResult.style.display = 'block';
            bulkResult.scrollIntoView({ behavior: 'smooth' });
        } else {
            showError(result.error || 'Failed to process bulk tokens');
        }
    } catch (error) {
        showError('Network error. Please try again.');
        console.error('Bulk processing error:', error);
    } finally {
        processingState = false;
        bulkProgress.style.display = 'none';
    }
}

// Display bulk results
function displayBulkResults(data) {
    // Update summary
    document.getElementById('totalProcessed').textContent = data.total_processed;
    document.getElementById('finalSuccess').textContent = data.successful;
    document.getElementById('finalFailed').textContent = data.failed;
    
    // Update processing time and speed (if available)
    if (data.processing_time) {
        const processingTimeEl = document.getElementById('processingTime');
        if (processingTimeEl) {
            processingTimeEl.textContent = data.processing_time;
        }
    }
    
    if (data.processing_speed) {
        const processingSpeedEl = document.getElementById('processingSpeed');
        if (processingSpeedEl) {
            processingSpeedEl.textContent = data.processing_speed;
        }
    }
    
    // Update results table
    const resultsTable = document.getElementById('resultsTable');
    resultsTable.innerHTML = '';
    
    data.results.forEach((result, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${result.uid}</td>
            <td>
                <span class="badge ${result.status === 'success' ? 'bg-success' : 'bg-danger'}">
                    ${result.status}
                </span>
            </td>
            <td>
                ${result.token ? `<code>${truncateToken(result.token)}</code>` : 'N/A'}
            </td>
            <td>
                ${result.token ? `
                    <button class="btn btn-sm btn-outline-primary copy-btn" 
                            onclick="copyToClipboard('token-${index}', '${result.token}')">
                        <i class="fas fa-copy"></i>
                    </button>
                ` : ''}
            </td>
        `;
        resultsTable.appendChild(row);
    });
}

// Initialize download buttons
function initializeDownloadButtons() {
    const downloadJsonBtn = document.getElementById('downloadJson');
    const downloadTxtBtn = document.getElementById('downloadTxt');
    
    if (downloadJsonBtn) {
        downloadJsonBtn.addEventListener('click', () => downloadTokens('json'));
    }
    
    if (downloadTxtBtn) {
        downloadTxtBtn.addEventListener('click', () => downloadTokens('txt'));
    }
}

// Download tokens
async function downloadTokens(format) {
    if (!currentTokens || !currentTokens.results) {
        showError('No tokens to download');
        return;
    }
    
    try {
        // Use direct download without URL parameters
        const url = `/api/download/${format}`;
        
        // Create temporary link and click it
        const link = document.createElement('a');
        link.href = url;
        link.download = `phantoms_tokens_${new Date().toISOString().slice(0, 10)}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
    } catch (error) {
        showError('Failed to download tokens');
        console.error('Download error:', error);
    }
}

// Utility functions
function showError(message) {
    const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
    document.getElementById('errorMessage').textContent = message;
    errorModal.show();
}

function copyToClipboard(elementId, text = null) {
    const textToCopy = text || document.getElementById(elementId).textContent;
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(textToCopy).then(() => {
            showToast('Copied to clipboard!', 'success');
        }).catch(() => {
            fallbackCopyToClipboard(textToCopy);
        });
    } else {
        fallbackCopyToClipboard(textToCopy);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showToast('Copied to clipboard!', 'success');
    } catch (err) {
        showToast('Failed to copy to clipboard', 'error');
    }
    
    document.body.removeChild(textArea);
}

function showToast(message, type = 'info') {
    // Create toast element
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // Add to toast container
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }
    
    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    toastContainer.appendChild(toastElement.firstElementChild);
    
    // Show toast
    const toast = new bootstrap.Toast(toastContainer.lastElementChild);
    toast.show();
    
    // Remove toast after it's hidden
    toastContainer.lastElementChild.addEventListener('hidden.bs.toast', () => {
        toastContainer.removeChild(toastContainer.lastElementChild);
    });
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function truncateToken(token) {
    if (!token) return 'N/A';
    return token.length > 50 ? token.substring(0, 50) + '...' : token;
}

// Handle rate limiting
function handleRateLimit() {
    showError('Rate limit exceeded. Please wait before making another request.');
}

// Handle network errors
function handleNetworkError() {
    showError('Network error. Please check your connection and try again.');
}

// Handle form validation
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Auto-resize textareas
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Initialize like feature
function initializeLikeFeature() {
    const likeForm = document.getElementById('likeForm');
    if (!likeForm) return;

    likeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const targetUid = document.getElementById('targetUid').value.trim();
        const serverName = document.getElementById('serverName').value;
        
        if (!targetUid || !serverName) {
            showError('Please enter target UID and select server region');
            return;
        }
        
        await sendLikes(targetUid, serverName);
    });
}

// Send likes to player
async function sendLikes(uid, serverName) {
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    const likeResult = document.getElementById('likeResult');
    
    try {
        // Show loading
        loadingModal.show();
        
        const response = await fetch('/api/like', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ uid, server_name: serverName })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Display like result
            displayLikeResult(result.data);
            likeResult.style.display = 'block';
            likeResult.scrollIntoView({ behavior: 'smooth' });
            showToast('✅ Likes sent successfully!', 'success');
        } else {
            showError(result.error || 'Failed to send likes');
        }
    } catch (error) {
        showError('Network error. Please try again.');
        console.error('Error:', error);
    } finally {
        loadingModal.hide();
    }
}

// Display like operation result
function displayLikeResult(data) {
    document.getElementById('likePlayerUid').textContent = data.player.uid;
    document.getElementById('likePlayerName').textContent = data.player.nickname;
    document.getElementById('likesBefore').textContent = data.likes.before;
    document.getElementById('likesAfter').textContent = data.likes.after;
    document.getElementById('likesAdded').textContent = data.likes.added_by_api;
    
    const statusElement = document.getElementById('likeStatus');
    if (data.status === 1) {
        statusElement.className = 'alert alert-success mt-2';
        statusElement.textContent = data.message;
    } else {
        statusElement.className = 'alert alert-warning mt-2';
        statusElement.textContent = data.message;
    }
}

// Export functions for global access
window.copyToClipboard = copyToClipboard;
window.showError = showError;
window.showToast = showToast;
