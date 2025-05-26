'use client';

import React, { useState, ChangeEvent, useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import ReactCrop, { type Crop, PixelCrop, centerCrop, makeAspectCrop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';

// Helper function to center the crop
function centerAspectCrop(
  mediaWidth: number,
  mediaHeight: number,
  aspect: number,
) {
  return centerCrop(
    makeAspectCrop(
      {
        unit: '%',
        width: 90,
      },
      aspect,
      mediaWidth,
      mediaHeight,
    ),
    mediaWidth,
    mediaHeight,
  );
}

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  onImageCropped: (croppedImageDataUrl: string | null) => void;
  showUploader: boolean;
  showCropper: boolean;
  initialPreviewUrl?: string | null;
  currentFileName?: string | null;
  aspectRatio?: number;
}

// Exact minimum dimension in pixels
const REQUIRED_MIN_DIMENSION = 900; // Required for the AI processing
const MAX_DIMENSION = 1200; // Maximum for very large crops

const ImageUpload = forwardRef<HTMLInputElement, ImageUploadProps>(({
  onImageSelect,
  onImageCropped,
  showUploader,
  showCropper,
  initialPreviewUrl,
  currentFileName,
  aspectRatio = 1/1
}, ref) => {
  const imgRef = useRef<HTMLImageElement | null>(null);
  const previewCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [crop, setCrop] = useState<Crop>();
  const [pixelCrop, setPixelCrop] = useState<PixelCrop>();
  const [isCompressing, setIsCompressing] = useState<boolean>(false);
  const [processingMessage, setProcessingMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [imageDimensions, setImageDimensions] = useState<{width: number, height: number} | null>(null);

  const localInputRef = useRef<HTMLInputElement>(null);

  // Expose the localInputRef to the parent component via the passed ref
  useImperativeHandle(ref, () => localInputRef.current as HTMLInputElement);

  // Reset states when initial preview URL changes
  useEffect(() => {
    if (showCropper && initialPreviewUrl && initialPreviewUrl !== previewUrl) {
      setPreviewUrl(initialPreviewUrl);
      setCrop(undefined);
      setPixelCrop(undefined);
      setErrorMessage(null);
    }
  }, [initialPreviewUrl, showCropper, previewUrl]);

  const internalHandleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Check file size first
      if (file.size > 15 * 1024 * 1024) { // 15MB limit
        setErrorMessage(`File too large (${(file.size / (1024 * 1024)).toFixed(1)}MB). Maximum size is 15MB.`);
        return;
      }
      
      // Create an offscreen image to check dimensions
      const img = new window.Image();
      img.onload = () => {
        URL.revokeObjectURL(img.src);
        
        // Check if image is too small in either dimension
        if (img.width < REQUIRED_MIN_DIMENSION || img.height < REQUIRED_MIN_DIMENSION) {
          setErrorMessage(
            `Image too small (${img.width}×${img.height}px). Minimum size required is ${REQUIRED_MIN_DIMENSION}×${REQUIRED_MIN_DIMENSION}px.`
          );
          return;
        }
        
        // Image is valid, proceed
        setErrorMessage(null);
        setImageDimensions({ width: img.width, height: img.height });
        onImageSelect(file);
      };
      
      img.onerror = () => {
        URL.revokeObjectURL(img.src);
        setErrorMessage('Cannot load image. Please try a different file format (JPEG, PNG recommended).');
      };
      
      img.src = URL.createObjectURL(file);
    }
  };

  const onImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const { width, height, naturalWidth, naturalHeight } = e.currentTarget;
    
    // Store natural dimensions for validation
    setImageDimensions({
      width: naturalWidth,
      height: naturalHeight
    });
    
    // Check if image is too small for processing
    if (naturalWidth < REQUIRED_MIN_DIMENSION || naturalHeight < REQUIRED_MIN_DIMENSION) {
      setErrorMessage(
        `Image too small (${naturalWidth}×${naturalHeight}px). Minimum size required is ${REQUIRED_MIN_DIMENSION}×${REQUIRED_MIN_DIMENSION}px.`
      );
      return;
    } else {
      setErrorMessage(null);
    }
    
    // Calculate initial crop
    if (aspectRatio) {
      const initialCrop = centerAspectCrop(width, height, aspectRatio);
      setCrop(initialCrop);
    } else {
      // For non-aspect ratio crops
      setCrop({
        unit: '%' as const,
        width: 80,
        height: 80,
        x: 10,
        y: 10
      });
    }
  };

  // Enforce minimum crop size in pixels directly
  const enforceMinimumCropSize = (newPixelCrop: PixelCrop): PixelCrop => {
    if (!imgRef.current) return newPixelCrop;
    
    const { naturalWidth, naturalHeight, width, height } = imgRef.current;
    const scaleX = naturalWidth / width;
    const scaleY = naturalHeight / height;
    
    // Calculate real size in pixels
    const realWidthPx = newPixelCrop.width * scaleX;
    const realHeightPx = newPixelCrop.height * scaleY;
    
    // Check if below minimum
    if (realWidthPx < REQUIRED_MIN_DIMENSION || realHeightPx < REQUIRED_MIN_DIMENSION) {
      // Create a new crop that meets minimum requirements
      const adjustedCrop = { ...newPixelCrop };
      
      // Calculate the minimum size in UI pixels
      const minUIWidth = Math.ceil(REQUIRED_MIN_DIMENSION / scaleX);
      const minUIHeight = Math.ceil(REQUIRED_MIN_DIMENSION / scaleY);
      
      // Apply the minimums
      if (realWidthPx < REQUIRED_MIN_DIMENSION) {
        adjustedCrop.width = minUIWidth;
      }
      
      if (realHeightPx < REQUIRED_MIN_DIMENSION) {
        adjustedCrop.height = minUIHeight;
      }
      
      // If we have an aspect ratio, ensure it's maintained
      if (aspectRatio) {
        // Determine which dimension is controlling
        if (adjustedCrop.width / adjustedCrop.height > aspectRatio) {
          // Width is controlling, adjust height
          adjustedCrop.height = adjustedCrop.width / aspectRatio;
        } else {
          // Height is controlling, adjust width
          adjustedCrop.width = adjustedCrop.height * aspectRatio;
        }
      }
      
      // Make sure we don't go out of bounds
      const maxX = width - adjustedCrop.width;
      const maxY = height - adjustedCrop.height;
      
      adjustedCrop.x = Math.max(0, Math.min(maxX, adjustedCrop.x));
      adjustedCrop.y = Math.max(0, Math.min(maxY, adjustedCrop.y));
      
      return adjustedCrop;
    }
    
    return newPixelCrop;
  };

  // Handle both crop changes and completion
  const handleCropChange = (newPixelCrop: PixelCrop, percentCrop: Crop) => {
    // Enforce minimum size
    const adjustedPixelCrop = enforceMinimumCropSize(newPixelCrop);
    
    // If the crop was adjusted, update both crops
    if (adjustedPixelCrop !== newPixelCrop) {
      setPixelCrop(adjustedPixelCrop);
      
      // We also need to update the percentage crop accordingly
      if (imgRef.current) {
        const { width, height } = imgRef.current;
        
        // Convert adjusted pixel crop back to percentage
        const adjustedPercentCrop = {
          unit: '%' as const,
          width: (adjustedPixelCrop.width / width) * 100,
          height: (adjustedPixelCrop.height / height) * 100,
          x: (adjustedPixelCrop.x / width) * 100,
          y: (adjustedPixelCrop.y / height) * 100
        };
        
        setCrop(adjustedPercentCrop);
      } else {
        setCrop(percentCrop);
      }
    } else {
      // No adjustments needed
      setPixelCrop(newPixelCrop);
      setCrop(percentCrop);
    }
    
    // Clear errors
    setErrorMessage(null);
  };
  
  // Special handler for completion to ensure final validation
  const handleCropComplete = (completedPixelCrop: PixelCrop) => {
    // Final validation
    let validatedCrop = enforceMinimumCropSize(completedPixelCrop);
    
    // Use Math.floor to ensure we're always above the minimum
    if (imgRef.current) {
      const { naturalWidth, naturalHeight, width, height } = imgRef.current;
      const scaleX = naturalWidth / width;
      const scaleY = naturalHeight / height;
      
      // Calculate actual pixels
      const exactWidth = Math.floor(validatedCrop.width * scaleX);
      const exactHeight = Math.floor(validatedCrop.height * scaleY);
      
      // If we're below minimum after flooring, add 1 pixel to ensure we're at least at minimum
      if (exactWidth < REQUIRED_MIN_DIMENSION || exactHeight < REQUIRED_MIN_DIMENSION) {
        // Adjust the crop to ensure minimum dimensions
        const adjustedCrop = { ...validatedCrop };
        
        if (exactWidth < REQUIRED_MIN_DIMENSION) {
          // Add pixels needed to meet minimum after rounding
          const pixelsNeeded = Math.ceil((REQUIRED_MIN_DIMENSION - exactWidth) / scaleX) + 1;
          adjustedCrop.width = validatedCrop.width + pixelsNeeded;
        }
        
        if (exactHeight < REQUIRED_MIN_DIMENSION) {
          // Add pixels needed to meet minimum after rounding
          const pixelsNeeded = Math.ceil((REQUIRED_MIN_DIMENSION - exactHeight) / scaleY) + 1;
          adjustedCrop.height = validatedCrop.height + pixelsNeeded;
        }
        
        // Update with the adjusted crop
        validatedCrop = adjustedCrop;
      }
    }
    
    // Set the final validated crop
    setPixelCrop(validatedCrop);
    
    // Log the final dimensions
    console.log(`Final crop dimensions: ${getCurrentCropDimensions()?.width}×${getCurrentCropDimensions()?.height}px`);
  };

  const getCroppedImg = async () => {
    if (!pixelCrop || !imgRef.current || !previewCanvasRef.current) {
      console.error('Crop, image reference, or canvas reference is not available.');
      onImageCropped(null);
      return;
    }

    try {
      setIsCompressing(true);
      setProcessingMessage('Processing image...');
      setErrorMessage(null);
      
      const image = imgRef.current;
      const canvas = previewCanvasRef.current;
      
      // Calculate the actual dimensions in the original image
      const scaleX = image.naturalWidth / image.width;
      const scaleY = image.naturalHeight / image.height;
      
      const cropX = pixelCrop.x * scaleX;
      const cropY = pixelCrop.y * scaleY;
      const cropWidth = pixelCrop.width * scaleX;
      const cropHeight = pixelCrop.height * scaleY;

      // One final validation
      if (cropWidth < REQUIRED_MIN_DIMENSION || cropHeight < REQUIRED_MIN_DIMENSION) {
        setErrorMessage(`The selected area is too small. Please select at least ${REQUIRED_MIN_DIMENSION}×${REQUIRED_MIN_DIMENSION}px.`);
        setIsCompressing(false);
        return;
      }
      
      console.log(`Processing crop: ${Math.round(cropWidth)}×${Math.round(cropHeight)}px`);
            
      // Use the exact cropped size
      let canvasWidth = cropWidth;
      let canvasHeight = cropHeight;
      
      // Limit maximum dimensions for very large crops
      if (canvasWidth > MAX_DIMENSION || canvasHeight > MAX_DIMENSION) {
        const ratio = Math.min(MAX_DIMENSION / canvasWidth, MAX_DIMENSION / canvasHeight);
        canvasWidth = canvasWidth * ratio;
        canvasHeight = canvasHeight * ratio;
        console.log(`Large image cropped area rescaled from ${cropWidth}×${cropHeight} to ${canvasWidth}×${canvasHeight}`);
      }
      
      // Set the canvas dimensions
      canvas.width = canvasWidth;
      canvas.height = canvasHeight;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        console.error('Failed to get 2D context from canvas');
        onImageCropped(null);
        return;
      }

      // Enable image smoothing for better quality
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';

      ctx.drawImage(
        image,
        cropX,
        cropY,
        cropWidth,
        cropHeight,
        0,
        0,
        canvasWidth,
        canvasHeight
      );

      // Output as PNG for lossless representation
      const base64ImagePNG = canvas.toDataURL('image/png');
      const pngSizeMB = (base64ImagePNG.length * 0.75) / (1024 * 1024);
      console.log(`Final cropped image: ${Math.round(canvasWidth)}×${Math.round(canvasHeight)}px, ${pngSizeMB.toFixed(2)}MB`);
      
      onImageCropped(base64ImagePNG);

    } catch (error) {
      console.error('Error processing image:', error);
      setProcessingMessage('Failed to process image. Please try again.');
      onImageCropped(null);
    } finally {
      setIsCompressing(false);
      // Clear message after a delay
      setTimeout(() => setProcessingMessage(null), 3000);
    }
  };

  // Get actual pixel dimensions for display
  const getCurrentCropDimensions = (): { width: number, height: number } | null => {
    if (!pixelCrop || !imgRef.current) return null;
    
    const { naturalWidth, naturalHeight, width, height } = imgRef.current;
    const scaleX = naturalWidth / width;
    const scaleY = naturalHeight / height;
    
    // Use Math.floor to ensure we never display larger than actual size
    const exactWidth = Math.floor(pixelCrop.width * scaleX);
    const exactHeight = Math.floor(pixelCrop.height * scaleY);
    
    // Always display exactly 512 if we're at the minimum enforced size
    // This ensures consistent UI presentation
    return {
      width: exactWidth <= REQUIRED_MIN_DIMENSION ? REQUIRED_MIN_DIMENSION : exactWidth,
      height: exactHeight <= REQUIRED_MIN_DIMENSION ? REQUIRED_MIN_DIMENSION : exactHeight
    };
  };

  return (
    <div className="space-y-6">
      {showUploader && (
        <div>
          <div className="flex items-center">
            <label htmlFor="imageUpload" className="cursor-pointer mr-2">
              <div className="py-2 px-4 bg-secondary border border-foreground text-sm font-semibold hover:bg-opacity-80">
                Browse...
              </div>
            </label>
            <div className="flex-grow overflow-hidden">
              <div className="block w-full text-sm text-muted-foreground border border-foreground py-2 px-3 truncate">
                {currentFileName || "No file selected"}
              </div>
            </div>
            <input
              type="file"
              id="imageUpload"
              name="imageUpload"
              accept="image/*"
              onChange={internalHandleFileChange}
              className="hidden"
              ref={localInputRef}
            />
          </div>
          
          {errorMessage && (
            <div className="mt-2 p-2 text-sm text-red-700 bg-red-50 border border-red-400 rounded">
              <svg xmlns="http://www.w3.org/2000/svg" className="inline-block mr-1 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              {errorMessage}
            </div>
          )}
        </div>
      )}

      {showCropper && previewUrl && (
        <div className="space-y-4 flex flex-col items-center">
          <div className="w-full flex justify-center">
            <div className="max-w-[38.4rem] overflow-visible">
              <ReactCrop
                crop={crop}
                onChange={(p, pc) => handleCropChange(p, pc)}
                onComplete={handleCropComplete}
                aspect={aspectRatio}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  ref={imgRef}
                  src={previewUrl!}
                  alt="Selected preview for cropping"
                  onLoad={onImageLoad}
                  style={{ 
                    maxWidth: '100%', 
                    maxHeight: '650px', 
                    objectFit: 'contain'
                  }}
                  className="border border-foreground" 
                />
              </ReactCrop>
            </div>
          </div>
          
          {errorMessage && (
            <div className="text-sm mt-2 p-2 border border-red-400 rounded bg-red-50 text-red-700">
              <svg xmlns="http://www.w3.org/2000/svg" className="inline-block mr-1 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              {errorMessage}
            </div>
          )}
          
          {processingMessage && !errorMessage && (
            <div className="text-sm mt-2 p-2 border border-foreground rounded bg-secondary">
              {processingMessage}
            </div>
          )}
          
          {pixelCrop && imgRef.current && (
            <div className="mt-4 flex justify-center">
              <button
                type="button"
                onClick={getCroppedImg}
                disabled={isCompressing || !!errorMessage}
                className="px-6 py-3 bg-input text-black font-semibold border-2 border-black shadow-[4px_4px_0_0_#000000] hover:shadow-[2px_2px_0_0_#000000] active:shadow-[1px_1px_0_0_#000000] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center gap-2"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                {isCompressing ? 'Processing...' : 'Continue with this square'}
              </button>
            </div>
          )}
        </div>
      )}
      <canvas ref={previewCanvasRef} style={{ display: 'none' }} />
    </div>
  );
});

ImageUpload.displayName = 'ImageUpload';

export default ImageUpload; 