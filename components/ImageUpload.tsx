'use client';

import React, { useState, ChangeEvent, useRef, useEffect } from 'react';
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

// Adaptively compress an image to target size
const compressImageToTargetSize = async (
  dataUrl: string, 
  targetSizeMB: number = 2, 
  initialQuality: number = 0.9,
  maxAttempts: number = 5
): Promise<string> => {
  // Function to get size in MB from a data URL
  const getSizeInMB = (dataUrl: string): number => {
    // base64 string is ~4/3 the size of the actual bytes
    return (dataUrl.length * 0.75) / (1024 * 1024);
  };

  let currentDataUrl = dataUrl;
  let currentSize = getSizeInMB(currentDataUrl);
  let attempt = 0;
  let quality = initialQuality;

  // Log initial size
  console.log(`Initial image size: ${currentSize.toFixed(2)}MB`);

  // If image is already under target size, return it
  if (currentSize <= targetSizeMB) {
    console.log(`Image already under ${targetSizeMB}MB (${currentSize.toFixed(2)}MB), no compression needed`);
    return currentDataUrl;
  }

  // Try compressing with increasingly lower quality until we hit target size
  while (currentSize > targetSizeMB && attempt < maxAttempts) {
    attempt++;
    
    // Lower quality based on how far we are from target and how many attempts we've made
    const sizeRatio = currentSize / targetSizeMB;
    quality = Math.max(0.5, quality * (1 / Math.min(sizeRatio, 1.5)));
    
    // Apply compression
    const img = new Image();
    await new Promise((resolve, reject) => {
      img.onload = resolve;
      img.onerror = reject;
      img.src = currentDataUrl;
    });
    
    const canvas = document.createElement('canvas');
    canvas.width = img.width;
    canvas.height = img.height;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Failed to get canvas context');
    
    ctx.drawImage(img, 0, 0);
    currentDataUrl = canvas.toDataURL('image/jpeg', quality);
    currentSize = getSizeInMB(currentDataUrl);
    
    console.log(`Attempt ${attempt}: Compressed to quality ${quality.toFixed(2)}, new size: ${currentSize.toFixed(2)}MB`);
  }

  return currentDataUrl;
};

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  onImageCropped: (croppedImageDataUrl: string | null) => void;
  showUploader: boolean;
  showCropper: boolean;
  initialPreviewUrl?: string | null;
}

const ASPECT_RATIO = 1;
const MIN_DIMENSION = 150;
const TARGET_SIZE_MB = 2; // Target size in MB

const ImageUpload: React.FC<ImageUploadProps> = ({ 
  onImageSelect, 
  onImageCropped, 
  showUploader, 
  showCropper, 
  initialPreviewUrl 
}) => {
  const imgRef = useRef<HTMLImageElement | null>(null);
  const previewCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [crop, setCrop] = useState<Crop>();
  const [completedCrop, setCompletedCrop] = useState<PixelCrop>();
  const [isCompressing, setIsCompressing] = useState<boolean>(false);
  const [processingMessage, setProcessingMessage] = useState<string | null>(null);

  useEffect(() => {
    if (showCropper && initialPreviewUrl && initialPreviewUrl !== previewUrl) {
      setPreviewUrl(initialPreviewUrl);
      setCrop(undefined);
      setCompletedCrop(undefined);
    }
  }, [initialPreviewUrl, showCropper, previewUrl]);

  const internalHandleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onImageSelect(file);
    }
  };

  const onImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const { width, height } = e.currentTarget;
    const currentCrop = centerAspectCrop(width, height, ASPECT_RATIO);
    setCrop(currentCrop);
  };

  const getCroppedImg = async () => {
    if (!completedCrop || !imgRef.current || !previewCanvasRef.current) {
      console.error('Crop, image reference, or canvas reference is not available.');
      onImageCropped(null);
      return;
    }

    try {
      setIsCompressing(true);
      setProcessingMessage('Processing image...');
      
      const image = imgRef.current;
      const canvas = previewCanvasRef.current;
      const cropData = completedCrop;

      const scaleX = image.naturalWidth / image.width;
      const scaleY = image.naturalHeight / image.height;

      // Limit the maximum dimensions of the cropped image
      const maxDimension = 1200; // Reasonable size to prevent huge images
      const cropWidth = cropData.width * scaleX;
      const cropHeight = cropData.height * scaleY;
      
      // Calculate scaled dimensions if needed
      let canvasWidth = cropWidth;
      let canvasHeight = cropHeight;
      
      if (cropWidth > maxDimension || cropHeight > maxDimension) {
        const ratio = Math.min(maxDimension / cropWidth, maxDimension / cropHeight);
        canvasWidth = cropWidth * ratio;
        canvasHeight = cropHeight * ratio;
        console.log(`Image cropped area rescaled from ${cropWidth}x${cropHeight} to ${canvasWidth}x${canvasHeight}`);
      }
      
      canvas.width = canvasWidth;
      canvas.height = canvasHeight;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        console.error('Failed to get 2D context from canvas');
        onImageCropped(null);
        return;
      }

      ctx.drawImage(
        image,
        cropData.x * scaleX,
        cropData.y * scaleY,
        cropWidth,
        cropHeight,
        0,
        0,
        canvasWidth,
        canvasHeight
      );

      // Use JPEG with high quality as initial output
      const base64Image = canvas.toDataURL('image/jpeg', 0.95);
      
      // Estimate size in MB
      const initialSizeMB = (base64Image.length * 0.75) / (1024 * 1024);
      console.log(`Initial cropped image size: ${initialSizeMB.toFixed(2)} MB`);
      
      // Apply adaptive compression if image is over target size
      let finalImage = base64Image;
      if (initialSizeMB > TARGET_SIZE_MB) {
        setProcessingMessage(`Optimizing image... (${initialSizeMB.toFixed(1)}MB → targeting ${TARGET_SIZE_MB}MB)`);
        finalImage = await compressImageToTargetSize(base64Image, TARGET_SIZE_MB);
        const finalSizeMB = (finalImage.length * 0.75) / (1024 * 1024);
        console.log(`Final image size after compression: ${finalSizeMB.toFixed(2)} MB`);
        setProcessingMessage(`Image optimized: ${finalSizeMB.toFixed(1)}MB (${Math.round((finalSizeMB / initialSizeMB) * 100)}% of original)`);
      }
      
      onImageCropped(finalImage);
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

  return (
    <div className="space-y-6">
      {showUploader && (
        <div>
          <input
            type="file"
            id="imageUpload"
            name="imageUpload"
            accept="image/*"
            onChange={internalHandleFileChange}
            className="block w-full text-sm text-muted-foreground border border-foreground file:mr-4 file:py-2 file:px-4 file:border-0 file:text-sm file:font-semibold file:bg-secondary file:text-secondary-foreground hover:file:bg-opacity-80 focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      )}

      {showCropper && previewUrl && (
        <div className="space-y-4 flex flex-col items-center">
          <div className="w-full max-w-[38.4rem]">
            <ReactCrop
              crop={crop}
              onChange={(_, percentCrop) => setCrop(percentCrop)}
              onComplete={(c) => setCompletedCrop(c)}
              aspect={ASPECT_RATIO}
              minWidth={MIN_DIMENSION}
              minHeight={MIN_DIMENSION}
            >
              <img
                ref={imgRef}
                src={previewUrl}
                alt="Selected preview for cropping"
                onLoad={onImageLoad}
                style={{ maxHeight: '65vh', display: previewUrl ? 'block' : 'none' }}
                className="border border-foreground block mx-auto"
              />
            </ReactCrop>
          </div>
          
          {processingMessage && (
            <div className="text-sm mt-2 p-2 border border-foreground rounded bg-secondary">
              {processingMessage}
            </div>
          )}
          
          {completedCrop && imgRef.current && (
            <div className="mt-4 flex justify-center">
              <button
                type="button"
                onClick={getCroppedImg}
                disabled={isCompressing}
                className="px-6 py-3 bg-input text-black font-semibold border-2 border-black shadow-[4px_4px_0_0_#000000] hover:shadow-[2px_2px_0_0_#000000] active:shadow-[1px_1px_0_0_#000000] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center gap-2"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                {isCompressing ? 'Processing...' : 'Confirm Crop'}
              </button>
            </div>
          )}
        </div>
      )}
      <canvas ref={previewCanvasRef} style={{ display: 'none' }} />
    </div>
  );
};

export default ImageUpload; 