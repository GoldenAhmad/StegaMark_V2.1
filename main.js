// main.js
document.addEventListener('DOMContentLoaded', () => {
    // ---------- Theme Toggle ----------
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const sunIcon = document.getElementById('theme-icon-sun');
    const moonIcon = document.getElementById('theme-icon-moon');

    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        body.classList.add('dark');
        sunIcon.classList.add('hidden');
        moonIcon.classList.remove('hidden');
    } else {
        sunIcon.classList.remove('hidden');
        moonIcon.classList.add('hidden');
    }

    themeToggle.addEventListener('click', () => {
        body.classList.toggle('dark');
        const isDark = body.classList.contains('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        sunIcon.classList.toggle('hidden', isDark);
        moonIcon.classList.toggle('hidden', !isDark);
    });

     window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
        const isOsDark = event.matches;
        if (!localStorage.getItem('theme')) {
             body.classList.toggle('dark', isOsDark);
             sunIcon.classList.toggle('hidden', isOsDark);
             moonIcon.classList.toggle('hidden', !isOsDark);
        }
     });

    // ---------- Tab Switching ----------
    const tabs = document.querySelectorAll('.tab');
    const sections = document.querySelectorAll('.section');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const sectionId = tab.id.replace('tab-', 'section-');
            sections.forEach(s => s.classList.add('hidden'));
            document.getElementById(sectionId)?.classList.remove('hidden');
        });
     });

    // ---------- DOM Elements Caching ----------
    // Common Elements
    const imageUpload = document.getElementById('imageUpload');
    const applyWatermarkBtn = document.getElementById('apply-watermark');
    const downloadBtn = document.getElementById('download-btn');
    const resetBtn = document.getElementById('reset-btn');
    const previewImage = document.getElementById('preview-image');
    const noImageMessage = document.getElementById('no-image-message');
    const previewWrapper = document.getElementById('watermark-preview-wrapper');
    const previewContainer = document.getElementById('preview-container');
    const processingOverlay = document.getElementById('processing-overlay');
    const applyStatus = document.getElementById('apply-status');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar-fill');

    // Watermark Specific Controls
    const logoUpload = document.getElementById('logoUpload');
    const watermarkText = document.getElementById('watermarkText');
    const textColor = document.getElementById('textColor');
    const opacity = document.getElementById('opacity');
    const opacityValue = document.getElementById('opacityValue');
    const positionBtns = document.querySelectorAll('.position-btn');
    const watermarkTypeBtns = document.querySelectorAll('[data-wm-type]');
    const visibleOptions = document.getElementById('visible-watermark-options');
    const invisibleOptions = document.getElementById('invisible-watermark-options');
    const textOptions = document.getElementById('watermark-text-options');
    const logoOptions = document.getElementById('watermark-logo-options');
    const textColorOption = document.getElementById('text-color-option');
    const positionControls= document.getElementById('position-controls');
    // Add Tiling Checkbox
    const tileWatermarkCheckbox = document.getElementById('tileWatermark');
    const tilingOptionContainer = document.getElementById('tiling-option-container');

    // Tiling Controls (NEW - Add these lines)
    const tileStyleSelect = document.getElementById('tileStyle');
    const tileSettingsContainer = document.getElementById('tile-settings');
    const tileSpacingSlider = document.getElementById('tileSpacing');
    const tileSpacingValue = document.getElementById('tileSpacingValue');
    const tileAngleOption = document.getElementById('tile-angle-option');
    const tileAngleSlider = document.getElementById('tileAngle');
    const tileAngleValue = document.getElementById('tileAngleValue');

    // Invisible Specific Controls
    const secretMessage = document.getElementById('secretMessage');
    const encodingStrength = document.getElementById('encodingStrength');
    const encodingStrengthValue = document.getElementById('encodingStrengthValue');
    const lsbBitsValue = document.getElementById('lsbBitsValue');
    const invisibleLogoUpload = document.getElementById('invisibleLogoUpload');
    const invTypeBtns = document.querySelectorAll('[data-inv-type]');
    const invTextOptions = document.getElementById('invisible-text-options');
    const invLogoOptions = document.getElementById('invisible-logo-options');

    // Extraction Specific Controls
    const extractImageUpload = document.getElementById('extractImageUpload');
    const extractionStrength = document.getElementById('extractionStrength');
    const extractionStrengthValue = document.getElementById('extractionStrengthValue');
    const extractLsbBitsValue = document.getElementById('extractLsbBitsValue');
    const extractWatermarkBtn = document.getElementById('extract-watermark-btn');
    const extractionResult = document.getElementById('extraction-result');
    const extractedContent = document.getElementById('extracted-content');
    const extractedMessage = document.getElementById('extracted-message');
    const extractedImage = document.getElementById('extracted-image');
    const extractedPlaceholder = document.getElementById('extracted-placeholder');
    const extractedError = document.getElementById('extracted-error');
    const extractStatus = document.getElementById('extract-status');
    const extractProgressContainer = document.getElementById('extract-progress-container');
    const extractProgressBar = document.getElementById('extract-progress-bar-fill');

    // Code Section Elements (Assuming Python code loading logic is separate or static)
    const pythonCodeElement = document.getElementById('python-code');

    // ---------- State Variables ----------
    let originalImageFile = null;
    let originalImageDataUrl = null;
    let logoImageFile = null; // For visible logo
    let logoImageDataUrl = null; // For visible logo preview
    let watermarkedBlobUrl = null; // Holds the Blob URL of the result for download
    let lastDownloadFilename = 'watermarked_image.png'; // Store filename from backend
    let currentWatermarkType = 'visible-text';
    let currentInvisibleType = 'text'; // Still used for UI toggle
    let currentPosition = 'center'; // For visible watermark
    let isTilingEnabled = false; // Track tiling state
    let isProcessingApply = false; // Prevent concurrent applies
    let isProcessingExtract = false; // Prevent concurrent extracts

    // ---------- Helper Functions ----------
    const getLsbBits = (strength) => Math.min(8, Math.max(1, Math.ceil(parseInt(strength) * 8 / 5)));

    const setStatus = (element, message, type = 'info', duration = 3000) => {
        const typeClasses = {
            info: 'text-gray-500 dark:text-gray-400',
            success: 'text-green-600 dark:text-green-400',
            error: 'text-red-600 dark:text-red-400',
            processing: 'text-blue-600 dark:text-blue-400'
        };
        element.className = `text-xs text-center mt-2 h-4 font-medium ${typeClasses[type] || typeClasses['info']}`;
        element.textContent = message;
        if (duration > 0 && type !== 'processing') {
            setTimeout(() => {
                if (element.textContent === message) {
                    element.textContent = '';
                    element.className = 'text-xs text-center mt-2 h-4';
                }
            }, duration);
        }
    };

    const setButtonLoading = (button, isLoading) => {
        const textSpan = button.querySelector('.btn-text');
        const loadingIcon = button.querySelector('.btn-loading');
        if (isLoading) {
            button.disabled = true;
            textSpan?.classList.add('hidden');
            loadingIcon?.classList.remove('hidden');
        } else {
            button.disabled = false;
            textSpan?.classList.remove('hidden');
            loadingIcon?.classList.add('hidden');
        }
    };

    const setProgress = (barElement, containerElement, value, status = null) => {
        if (!containerElement || !barElement) return;
        containerElement.classList.remove('hidden');
        barElement.style.width = `${Math.max(0, Math.min(100, value))}%`;
        barElement.className = 'progress-bar-fill';
        if (status === 'success') barElement.classList.add('success');
        if (status === 'error') barElement.classList.add('error');

        if (value >= 100 || status === 'error') {
            setTimeout(() => {
                containerElement.classList.add('hidden');
                setTimeout(() => { barElement.style.width = `0%`; }, 300);
            }, 2000);
        } else if (value <= 0) {
            containerElement.classList.add('hidden');
            barElement.style.width = `0%`;
        }
    };

    const resetPreviewArea = () => {
        previewImage.src = '';
        previewImage.removeAttribute('style');
        previewWrapper.classList.add('hidden');
        noImageMessage.classList.remove('hidden');
        downloadBtn.disabled = true;
        if (watermarkedBlobUrl) { URL.revokeObjectURL(watermarkedBlobUrl); }
        watermarkedBlobUrl = null;
        applyStatus.textContent = '';
        const existingOverlays = previewWrapper.querySelectorAll('.visual-watermark-overlay');
        existingOverlays.forEach(el => el.remove());
        setProgress(progressBar, progressContainer, 0);
    };

    // NEW: Updates tiling controls based on selected style
    function updateTilingUI() {
        if (!tileStyleSelect || !positionControls || !tileSettingsContainer || !tileAngleOption) return; // Guard against missing elements

        const selectedStyle = tileStyleSelect.value;
        const isTiling = selectedStyle !== 'none';

        positionControls.classList.toggle('hidden', isTiling);
        tileSettingsContainer.classList.toggle('hidden', !isTiling);
        tileAngleOption.classList.toggle('hidden', selectedStyle !== 'diagonal');
    }

    const resetAll = () => {
        imageUpload.value = '';
        logoUpload.value = '';
        invisibleLogoUpload.value = '';
        extractImageUpload.value = '';
        originalImageFile = null;
        originalImageDataUrl = null;
        logoImageFile = null; logoImageDataUrl = null;
        if (watermarkedBlobUrl) { URL.revokeObjectURL(watermarkedBlobUrl); }
        watermarkedBlobUrl = null; lastDownloadFilename = 'watermarked_image.png';
        isProcessingApply = false;
        isProcessingExtract = false;
        resetPreviewArea();
        applyWatermarkBtn.disabled = true;
        extractWatermarkBtn.disabled = true;
        watermarkText.value = '© StegaMark';
        secretMessage.value = 'StegaMark Hidden Message';
        opacity.value = 50; opacityValue.textContent = '50%';
        textColor.value = '#ffffff';
        encodingStrength.value = 3; encodingStrengthValue.textContent = '3'; lsbBitsValue.textContent = getLsbBits(3);
        extractionStrength.value = 3; extractionStrengthValue.textContent = '3';
        extractLsbBitsValue.textContent = getLsbBits(3);
        positionBtns.forEach(b => b.classList.remove('active'));
        const centerBtn = document.querySelector('.position-btn[data-position="center"]');
        if (centerBtn) centerBtn.classList.add('active');
        currentPosition = 'center';

        // Reset Tiling Controls (NEW - Add these)
        if (tileStyleSelect) tileStyleSelect.value = 'none';
        if (tileSpacingSlider) tileSpacingSlider.value = 10;
        if (tileSpacingValue) tileSpacingValue.textContent = '10%';
        if (tileAngleSlider) tileAngleSlider.value = 45;
        if (tileAngleValue) tileAngleValue.textContent = '45°';

        extractionResult.classList.add('hidden');
        extractedContent.querySelectorAll(':scope > *').forEach(el => el.classList.add('hidden'));
        extractedPlaceholder.classList.remove('hidden');
        extractedPlaceholder.textContent = 'No data extracted yet.'; // Reset placeholder text
        extractStatus.textContent = '';
        setProgress(extractProgressBar, extractProgressContainer, 0);
        currentWatermarkType = 'visible-text';
        watermarkTypeBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.wmType === currentWatermarkType));
        currentInvisibleType = 'text';
        invTypeBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.invType === currentInvisibleType));
        updateWatermarkTypeUI();
        console.log("UI Reset");
    };

    const updatePreviewWatermark = () => { // VISUAL preview ONLY
        if (!previewWrapper || previewWrapper.classList.contains('hidden')) return;
        const existingOverlays = previewWrapper.querySelectorAll('.visual-watermark-overlay');
        existingOverlays.forEach(el => el.remove());
        if (!originalImageDataUrl || currentWatermarkType === 'invisible') {
            return;
        }
        if (currentWatermarkType === 'visible-logo' && !logoImageDataUrl) {
             return;
        }

        const imgElement = previewImage;
        const container = previewWrapper;

         if (imgElement.naturalWidth === 0 && imgElement.src) {
             imgElement.onload = () => { updatePreviewWatermark(); imgElement.onload = null; };
             return;
         } else if (!imgElement.src){
             return;
         }

        const imgRect = imgElement.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();

        if (imgRect.width <= 0 || imgRect.height <= 0) {
            console.warn("Preview image has zero dimensions.");
            return;
        }

        const overlay = document.createElement('div');
        overlay.classList.add('visual-watermark-overlay');
        overlay.style.position = 'absolute';
        overlay.style.pointerEvents = 'none';
        overlay.style.opacity = opacity.value / 100;
        overlay.style.visibility = 'hidden';
        let watermarkWidth = 0, watermarkHeight = 0;
        const padding = 10 * (imgRect.width / imgElement.naturalWidth);

        if (currentWatermarkType === 'visible-text') {
            overlay.textContent = watermarkText.value || '© StegaMark';
            overlay.style.color = textColor.value;
            const baseFontSize = Math.max(10, imgRect.height * 0.05);
            overlay.style.fontSize = `${baseFontSize}px`;
            overlay.style.fontFamily = 'Poppins, Arial, sans-serif';
            overlay.style.fontWeight = '600';
            overlay.style.whiteSpace = 'nowrap';
            overlay.style.textShadow = '1px 1px 2px rgba(0,0,0,0.6)';
            previewWrapper.appendChild(overlay);
            watermarkWidth = overlay.offsetWidth;
            watermarkHeight = overlay.offsetHeight;
            positionAndShowOverlay(overlay, watermarkWidth, watermarkHeight, imgRect, containerRect, padding);

        } else if (currentWatermarkType === 'visible-logo' && logoImageDataUrl) {
            const logoImg = new Image();
            logoImg.onload = () => {
                const targetWidth = imgRect.width * 0.15;
                const aspectRatio = logoImg.naturalHeight / logoImg.naturalWidth;
                const targetHeight = targetWidth * aspectRatio;
                overlay.style.width = `${targetWidth}px`;
                overlay.style.height = `${targetHeight}px`;
                overlay.style.backgroundImage = `url(${logoImageDataUrl})`;
                overlay.style.backgroundSize = 'contain';
                overlay.style.backgroundRepeat = 'no-repeat';
                watermarkWidth = targetWidth;
                watermarkHeight = targetHeight;
                previewWrapper.appendChild(overlay);
                positionAndShowOverlay(overlay, watermarkWidth, watermarkHeight, imgRect, containerRect, padding);
            };
            logoImg.onerror = () => console.error("Failed to load logo for preview overlay.");
            logoImg.src = logoImageDataUrl;
        }
    };

     function positionAndShowOverlay(overlay, wmWidth, wmHeight, imgRect, containerRect, padding) {
         const offsetX = (containerRect.width - imgRect.width) / 2;
         const offsetY = (containerRect.height - imgRect.height) / 2;
         let left, top;
         if (currentPosition.includes('left')) left = offsetX + padding;
         else if (currentPosition.includes('right')) left = offsetX + imgRect.width - wmWidth - padding;
         else left = offsetX + (imgRect.width - wmWidth) / 2;
         if (currentPosition.includes('top')) top = offsetY + padding;
         else if (currentPosition.includes('bottom')) top = offsetY + imgRect.height - wmHeight - padding;
         else top = offsetY + (imgRect.height - wmHeight) / 2;
         left = Math.max(0, Math.min(left, containerRect.width - wmWidth));
         top = Math.max(0, Math.min(top, containerRect.height - wmHeight));
         overlay.style.left = `${left}px`;
         overlay.style.top = `${top}px`;
         overlay.style.visibility = 'visible';
     }

    // ---------- Event Listeners Setup ----------

    imageUpload.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0] && e.target.files[0].type.match('image.*')) {
            originalImageFile = e.target.files[0];
            const reader = new FileReader();
            reader.onload = (ev) => {
                originalImageDataUrl = ev.target.result;
                 const imgElement = previewImage;
                 imgElement.onload = () => {
                     noImageMessage.classList.add('hidden');
                     previewWrapper.classList.remove('hidden');
                     updatePreviewWatermark();
                     imgElement.onload = null;
                     applyWatermarkBtn.disabled = false;
                     if (watermarkedBlobUrl) { URL.revokeObjectURL(watermarkedBlobUrl); watermarkedBlobUrl = null; }
                     downloadBtn.disabled = true;
                     setStatus(applyStatus, 'Image loaded.', 'info', 1500);
                 };
                 imgElement.onerror = () => {
                     setStatus(applyStatus, 'Error loading image preview.', 'error');
                     resetPreviewArea();
                 };
                 imgElement.src = originalImageDataUrl;
            };
            reader.onerror = () => {
                 setStatus(applyStatus, 'Error reading image file.', 'error');
                 resetPreviewArea();
            };
            reader.readAsDataURL(originalImageFile);
        } else {
            originalImageFile = null;
            originalImageDataUrl = null;
            resetPreviewArea();
            applyWatermarkBtn.disabled = true;
            if(e.target.files && e.target.files[0]) {
                setStatus(applyStatus, 'Please select a valid image file (PNG or JPG).', 'error');
            }
        }
    });

    logoUpload.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0] && e.target.files[0].type.startsWith('image/')) { // Allow more logo types
            logoImageFile = e.target.files[0];
            const reader = new FileReader();
            reader.onload = (ev) => {
                logoImageDataUrl = ev.target.result;
                if (currentWatermarkType === 'visible-logo') updatePreviewWatermark();
                setStatus(applyStatus, `Logo loaded.`, 'info', 1500);
            };
            reader.onerror = () => setStatus(applyStatus, `Error reading logo file.`, 'error');
            reader.readAsDataURL(logoImageFile);
        } else {
            logoImageFile = null;
            logoImageDataUrl = null;
            if (currentWatermarkType === 'visible-logo') updatePreviewWatermark();
            if(e.target.files && e.target.files[0]) {
                setStatus(applyStatus, `Please select a valid image file for the logo.`, 'error');
            }
        }
    });

    invisibleLogoUpload.addEventListener('change', (e) => {
         if (e.target.files && e.target.files[0] && e.target.files[0].type === 'image/png') {
             setStatus(applyStatus, 'Invisible logo selected (backend support pending).', 'info', 2000);
         } else {
             if (e.target.files && e.target.files[0]){
                 setStatus(applyStatus, 'Please select a PNG file for the invisible logo.', 'error');
             }
         }
         if (watermarkedBlobUrl) { URL.revokeObjectURL(watermarkedBlobUrl); watermarkedBlobUrl = null; }
         downloadBtn.disabled = true;
    });


    watermarkTypeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
             watermarkTypeBtns.forEach(b => b.classList.remove('active'));
             btn.classList.add('active');
             currentWatermarkType = btn.dataset.wmType;
             updateWatermarkTypeUI();
         });
    });
     invTypeBtns.forEach(btn => {
         btn.addEventListener('click', () => {
             invTypeBtns.forEach(b => b.classList.remove('active'));
             btn.classList.add('active');
             currentInvisibleType = btn.dataset.invType;
             updateInvisibleTypeUI();
         });
     });

    function updateWatermarkTypeUI() {
        const isVisible = currentWatermarkType.startsWith('visible');
        visibleOptions.classList.toggle('hidden', !isVisible);
        invisibleOptions.classList.toggle('hidden', isVisible);

         if (isVisible) {
             logoOptions.classList.toggle('hidden', currentWatermarkType !== 'visible-logo');
             textOptions.classList.toggle('hidden', currentWatermarkType !== 'visible-text');
             textColorOption.classList.toggle('hidden', currentWatermarkType !== 'visible-text');
             updateTilingUI(); // Call the new function here
         } else {
             // Explicitly hide position/tiling controls when invisible
             if (positionControls) positionControls.classList.add('hidden');
             if (tileSettingsContainer) tileSettingsContainer.classList.add('hidden');
             updateInvisibleTypeUI();
         }
         updatePreviewWatermark(); // Keep this
         if (watermarkedBlobUrl) { URL.revokeObjectURL(watermarkedBlobUrl); watermarkedBlobUrl = null; } // Keep this
         downloadBtn.disabled = true; // Keep this
    }

     function updateInvisibleTypeUI() {
        if (currentWatermarkType === 'invisible') {
             invTextOptions.classList.toggle('hidden', currentInvisibleType !== 'text');
             invLogoOptions.classList.toggle('hidden', currentInvisibleType !== 'logo');
             if(currentInvisibleType === 'logo' && applyStatus){
                 setStatus(applyStatus, 'Note: LSB Logo encoding is not supported by the backend yet.', 'info', 5000);
             }
        }
        if (watermarkedBlobUrl) { URL.revokeObjectURL(watermarkedBlobUrl); watermarkedBlobUrl = null; }
        downloadBtn.disabled = true;
     }

    [watermarkText, textColor, opacity].forEach(el => {
        el?.addEventListener('input', () => {
            if (watermarkedBlobUrl) { URL.revokeObjectURL(watermarkedBlobUrl); watermarkedBlobUrl = null; }
            downloadBtn.disabled = true;
            if (el.id === 'opacity') opacityValue.textContent = `${opacity.value}%`;
            updatePreviewWatermark();
        });
    });

    // Tiling Controls Listeners (NEW - Add these)
    if (tileStyleSelect) {
        tileStyleSelect.addEventListener('change', () => {
            updateTilingUI();
            // Invalidate backend result if tiling style changes
            if (watermarkedBlobUrl) { URL.revokeObjectURL(watermarkedBlobUrl); watermarkedBlobUrl = null; }
            downloadBtn.disabled = true;
            // Note: Live preview for tiling/angle/spacing is complex and not implemented here.
            // updatePreviewWatermark(); // Optionally update preview, but it won't reflect tiling changes
        });
    }

    if (tileSpacingSlider) {
        tileSpacingSlider.addEventListener('input', (e) => {
            if (tileSpacingValue) tileSpacingValue.textContent = `${e.target.value}%`;
            // Invalidate backend result if spacing changes
            if (watermarkedBlobUrl) { URL.revokeObjectURL(watermarkedBlobUrl); watermarkedBlobUrl = null; }
            downloadBtn.disabled = true;
        });
    }

    if (tileAngleSlider) {
        tileAngleSlider.addEventListener('input', (e) => {
            if (tileAngleValue) tileAngleValue.textContent = `${e.target.value}°`;
            // Invalidate backend result if angle changes
            if (watermarkedBlobUrl) { URL.revokeObjectURL(watermarkedBlobUrl); watermarkedBlobUrl = null; }
            downloadBtn.disabled = true;
        });
    }

    [encodingStrength, extractionStrength].forEach(el => {
        el.addEventListener('input', () => {
            const value = el.value;
            const bits = getLsbBits(value);
            if (el.id === 'encodingStrength') {
                encodingStrengthValue.textContent = value;
                lsbBitsValue.textContent = bits;
                if (watermarkedBlobUrl) { URL.revokeObjectURL(watermarkedBlobUrl); watermarkedBlobUrl = null; }
                downloadBtn.disabled = true;
            } else {
                extractionStrengthValue.textContent = value;
                extractLsbBitsValue.textContent = bits;
            }
        });
    });

    positionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            positionBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentPosition = btn.dataset.position;
             if (watermarkedBlobUrl) { URL.revokeObjectURL(watermarkedBlobUrl); watermarkedBlobUrl = null; }
             downloadBtn.disabled = true;
             updatePreviewWatermark();
        });
    });

    // --- Apply Watermark - ACTUAL Fetch Call ---
    applyWatermarkBtn.addEventListener('click', async () => {
        if (isProcessingApply || !originalImageFile) return;

        if (currentWatermarkType === 'visible-logo' && !logoImageFile) {
            setStatus(applyStatus, 'Please upload a logo image.', 'error'); return;
        }
        if (currentWatermarkType === 'invisible' && currentInvisibleType === 'text' && !secretMessage.value.trim()) {
            setStatus(applyStatus, 'Please enter text to hide.', 'error'); return;
        }
        if (currentWatermarkType === 'invisible' && currentInvisibleType === 'logo') {
             setStatus(applyStatus, 'LSB encoding for logos is not supported yet.', 'error'); return;
        }

        isProcessingApply = true;
        setButtonLoading(applyWatermarkBtn, true);
        processingOverlay.classList.remove('hidden');
        setStatus(applyStatus, 'Processing...', 'processing', 0);
        setProgress(progressBar, progressContainer, 10);
        if (watermarkedBlobUrl) { URL.revokeObjectURL(watermarkedBlobUrl); watermarkedBlobUrl = null; }
        downloadBtn.disabled = true;

        const formData = new FormData();
        formData.append('image', originalImageFile);
        formData.append('visibility', currentWatermarkType === 'invisible' ? 'invisible' : 'visible');

        // Determine watermark_type based on visibility and specific type
        let wmTypeParam = 'text'; // Default
        if (currentWatermarkType === 'visible-logo') {
            wmTypeParam = 'logo';
        } else if (currentWatermarkType === 'invisible') {
            wmTypeParam = currentInvisibleType; // 'text' or 'logo' for invisible
        }
        formData.append('watermark_type', wmTypeParam);


        if (currentWatermarkType === 'invisible') {
            // --- Keep existing invisible logic ---
            formData.append('watermark_text', secretMessage.value); // Assuming 'watermark_text' is used for invisible too
            formData.append('strength', encodingStrength.value);
            // Add invisible logo handling here if/when supported by backend
            // if (currentInvisibleType === 'logo' && invisibleLogoFile) {
            //     formData.append('watermark_logo', invisibleLogoFile);
            // }
        } else { // Visible Watermark Logic
            formData.append('opacity', (parseFloat(opacity.value) / 100.0).toFixed(2));
            // formData.append('position', currentPosition); // Only send position if not tiling (handled below)

            if (currentWatermarkType === 'visible-text') {
                 formData.append('watermark_text', watermarkText.value);
                 formData.append('text_color', textColor.value);
            } else if (currentWatermarkType === 'visible-logo' && logoImageFile) {
                 formData.append('watermark_logo', logoImageFile);
                 // Send logo scale (assuming slider exists and is referenced as logoScaleSlider)
                 const logoScaleSlider = document.getElementById('logoScale'); // Get ref if not cached
                 if (logoScaleSlider) {
                    formData.append('logo_scale', (parseFloat(logoScaleSlider.value) / 100.0).toFixed(2));
                 }
            }

            // --- Add Tiling Data (NEW/UPDATED) ---
            const currentTileStyle = tileStyleSelect ? tileStyleSelect.value : 'none';
            formData.append('tile_style', currentTileStyle);

            if (currentTileStyle === 'none') {
                formData.append('position', currentPosition); // Send position only if not tiling
            } else {
                // Send spacing (convert 0-100% to 0.0-1.0)
                if (tileSpacingSlider) {
                    formData.append('tile_spacing', (parseFloat(tileSpacingSlider.value) / 100.0).toFixed(2));
                }
                // Send angle only if style is diagonal
                if (currentTileStyle === 'diagonal' && tileAngleSlider) {
                    formData.append('tile_angle', tileAngleSlider.value);
                }
            }
            // --- End Tiling Data ---

            // Remove old 'tile' boolean if it exists in the original code
            // formData.append('tile', isTilingEnabled); // <-- REMOVE THIS LINE
        }

        try {
            await new Promise(resolve => setTimeout(resolve, 300));
            setProgress(progressBar, progressContainer, 40);

            const response = await fetch('/watermark', {
                method: 'POST',
                body: formData,
            });

            await new Promise(resolve => setTimeout(resolve, 300));
            setProgress(progressBar, progressContainer, 80);

            if (response.ok) {
                const blob = await response.blob();
                watermarkedBlobUrl = URL.createObjectURL(blob);

                const disposition = response.headers.get('Content-Disposition');
                if (disposition && disposition.includes('filename=')) {
                    const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    const matches = filenameRegex.exec(disposition);
                    if (matches?.[1]) {
                        lastDownloadFilename = matches[1].replace(/['"]/g, '');
                    }
                } else {
                    const baseName = originalImageFile.name.replace(/\.[^/.]+$/, "");
                     const extension = currentWatermarkType === 'invisible' ? 'png' : (originalImageFile.type === 'image/jpeg' ? 'jpg' : 'png');
                     lastDownloadFilename = `${baseName}_stegamark.${extension}`;
                }

                previewImage.src = watermarkedBlobUrl;
                setStatus(applyStatus, 'Watermark applied successfully!', 'success');
                setProgress(progressBar, progressContainer, 100, 'success');
                downloadBtn.disabled = false;
            } else {
                const errorData = await response.json();
                setStatus(applyStatus, `Error: ${errorData.error || response.statusText}`, 'error');
                setProgress(progressBar, progressContainer, 100, 'error');
            }
        } catch (error) {
            console.error("Apply Watermark Fetch Error:", error);
            setStatus(applyStatus, `Network or server error: ${error.message}`, 'error');
            setProgress(progressBar, progressContainer, 100, 'error');
        } finally {
            isProcessingApply = false;
            setButtonLoading(applyWatermarkBtn, false);
            processingOverlay.classList.add('hidden');
        }
    });


    // Download Button Listener - Uses Blob URL
    downloadBtn.addEventListener('click', () => {
        if (!watermarkedBlobUrl) return;
        const link = document.createElement('a');
        link.download = lastDownloadFilename;
        link.href = watermarkedBlobUrl;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setStatus(applyStatus, 'Download started.', 'info', 1500);
    });

     // Reset Button Listener
    resetBtn.addEventListener('click', resetAll);

    // --- Extraction Section Listeners ---

    extractImageUpload.addEventListener('change', (e) => {
         const file = e.target.files?.[0];
         // Enable button only for PNG files
         extractWatermarkBtn.disabled = !(file && file.type === 'image/png');
         extractionResult.classList.add('hidden');
         extractedContent.querySelectorAll(':scope > *').forEach(el => el.classList.add('hidden'));
         extractedPlaceholder.classList.remove('hidden');
         extractedPlaceholder.textContent = 'No data extracted yet.'; // Reset placeholder text
         extractStatus.textContent = '';
         setProgress(extractProgressBar, extractProgressContainer, 0);
         if (file && file.type !== 'image/png') {
            setStatus(extractStatus, 'Please upload a PNG file for extraction.', 'error');
         }
     });

    // --- Extract Watermark - ACTUAL Fetch Call ---
    extractWatermarkBtn.addEventListener('click', async () => {
        const file = extractImageUpload.files?.[0];
        if (isProcessingExtract || !file || file.type !== 'image/png') { // Double check file type
             setStatus(extractStatus, 'Please upload a valid PNG file.', 'error');
             return;
        }

        isProcessingExtract = true;
        setButtonLoading(extractWatermarkBtn, true);
        extractStatus.textContent = '';
        setStatus(extractStatus, 'Extracting...', 'processing', 0);
        setProgress(extractProgressBar, extractProgressContainer, 10);
        extractionResult.classList.add('hidden');
        extractedContent.querySelectorAll(':scope > *').forEach(el => el.classList.add('hidden')); // Clear previous results visually


        const formData = new FormData();
        // Field name 'image' matches the HTML input and backend expectation
        formData.append('image', file);
         // Field name 'strength' matches the HTML input and backend expectation
        formData.append('strength', extractionStrength.value);

        try {
            await new Promise(resolve => setTimeout(resolve, 300));
            setProgress(extractProgressBar, extractProgressContainer, 40);

            const response = await fetch('/extract', { // Call backend API
                method: 'POST',
                body: formData,
            });

            await new Promise(resolve => setTimeout(resolve, 300));
            setProgress(extractProgressBar, extractProgressContainer, 80);

            const resultData = await response.json();

            extractionResult.classList.remove('hidden'); // Show result area
            extractedPlaceholder.classList.add('hidden'); // Hide placeholder initially

            if (response.ok) {
                // --- SUCCESSFUL EXTRACTION ---
                setStatus(extractStatus, 'Extraction complete.', 'success');
                setProgress(extractProgressBar, extractProgressContainer, 100, 'success');

                // Explicitly check the type and content of extracted_text
                if (typeof resultData.extracted_text === 'string') {
                    // It's a string, display it, even if empty
                    extractedMessage.textContent = resultData.extracted_text;
                    extractedMessage.classList.remove('hidden');
                    // If it's an empty string, maybe show placeholder text instead of just blank space
                    if (resultData.extracted_text === "") {
                        extractedPlaceholder.textContent = "Extracted an empty text message.";
                        extractedPlaceholder.classList.remove('hidden');
                        extractedMessage.classList.add('hidden'); // Hide the empty message field itself
                    } else {
                         extractedPlaceholder.classList.add('hidden'); // Hide placeholder if text has content
                    }
                } else if (resultData.is_image && resultData.image_data) {
                     // Handle extracted image data (assuming backend sends base64 PNG)
                     extractedMessage.textContent = "Extracted Image Watermark:";
                     extractedImage.src = `data:image/png;base64,${resultData.image_data}`;
                     extractedMessage.classList.remove('hidden');
                     extractedImage.classList.remove('hidden');
                } else if (resultData.is_binary) {
                     // Handle binary data indication (backend sends info string in extracted_text)
                     extractedMessage.textContent = resultData.extracted_text; // Display "Extracted X bytes..."
                     extractedMessage.classList.remove('hidden');
                } else {
                    // Fallback if extracted_text is missing or not a string/binary/image
                    extractedPlaceholder.textContent = "Backend returned success but no recognized content found.";
                    extractedPlaceholder.classList.remove('hidden');
                    extractedMessage.classList.add('hidden');
                    extractedImage.classList.add('hidden');
                }
                extractedError.classList.add('hidden'); // Ensure error field is hidden

            } else {
                // --- EXTRACTION FAILED or Backend Error ---
                const errorMessage = resultData.error || response.statusText || 'Unknown extraction error';
                setStatus(extractStatus, `Error: ${errorMessage}`, 'error');
                setProgress(extractProgressBar, extractProgressContainer, 100, 'error');

                // Display the error message from the backend
                extractedError.textContent = errorMessage;
                extractedError.classList.remove('hidden');
                extractedMessage.classList.add('hidden'); // Ensure message field is hidden
                extractedImage.classList.add('hidden'); // Ensure image field is hidden
                extractedPlaceholder.classList.add('hidden'); // Hide placeholder on error
            }

        } catch (error) {
            // --- NETWORK or other JS Error ---
            console.error("Extract Watermark Fetch Error:", error);
            setStatus(extractStatus, `Network or script error: ${error.message}`, 'error');
            setProgress(extractProgressBar, extractProgressContainer, 100, 'error');
            extractionResult.classList.remove('hidden'); // Show result area
            extractedPlaceholder.classList.add('hidden'); // Hide placeholder
            extractedError.textContent = `Network error: ${error.message}`; // Display network error
            extractedError.classList.remove('hidden');
            extractedMessage.classList.add('hidden');
        } finally {
            isProcessingExtract = false;
            setButtonLoading(extractWatermarkBtn, false);
        }
    });

    // --- Initialize ---
    resetAll(); // Set initial state on load
    updateWatermarkTypeUI(); // Ensure correct UI visibility

}); // End DOMContentLoaded