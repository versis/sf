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

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  onImageCropped: (croppedImageDataUrl: string | null) => void;
  showUploader: boolean;
  showCropper: boolean;
  initialPreviewUrl?: string | null;
  currentFileName?: string | null;
  aspectRatio?: number;
}

const MIN_DIMENSION = 150;
const RECOMMENDED_MIN_DIMENSION = 512; // Recommended minimum size for better AI processing
const TARGET_SIZE_MB = 2; // Target size in MB

const ImageUpload: React.FC<ImageUploadProps> = ({ 
  onImageSelect, 
  onImageCropped, 
  showUploader, 
  showCropper, 
  initialPreviewUrl, 
  currentFileName,
  aspectRatio = 1/1 // Changed to 1:1 square aspect ratio
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
    if (aspectRatio) {
        const currentCrop = centerAspectCrop(width, height, aspectRatio);
        setCrop(currentCrop);
    } else {
        // Default to 1:1 aspect ratio (square) for the image panel
        const defaultAspect = 1/1;
        const currentCrop = centerAspectCrop(width, height, defaultAspect);
        setCrop(currentCrop);
    }
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

      // Get the original cropped dimensions
      const cropWidth = cropData.width * scaleX;
      const cropHeight = cropData.height * scaleY;
      
      // Calculate dimensions, ensuring we meet minimum recommended size
      // If the cropped area is small, we'll upscale it
      let canvasWidth = Math.max(cropWidth, RECOMMENDED_MIN_DIMENSION);
      let canvasHeight = Math.max(cropHeight, RECOMMENDED_MIN_DIMENSION);
      
      // For extremely small crops, log that we're upscaling
      if (cropWidth < RECOMMENDED_MIN_DIMENSION || cropHeight < RECOMMENDED_MIN_DIMENSION) {
        console.log(`Upscaling small crop from ${cropWidth}x${cropHeight} to ${canvasWidth}x${canvasHeight} for better AI processing`);
        setProcessingMessage(`Optimizing small image (${Math.round(cropWidth)}x${Math.round(cropHeight)}) for best results...`);
      }
      
      // Limit maximum dimensions for very large crops
      const maxDimension = 1200;
      if (canvasWidth > maxDimension || canvasHeight > maxDimension) {
        const ratio = Math.min(maxDimension / canvasWidth, maxDimension / canvasHeight);
        canvasWidth = canvasWidth * ratio;
        canvasHeight = canvasHeight * ratio;
        console.log(`Large image cropped area rescaled from ${cropWidth}x${cropHeight} to ${canvasWidth}x${canvasHeight}`);
      }
      
      // Set the canvas dimensions to our calculated values
      canvas.width = canvasWidth;
      canvas.height = canvasHeight;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        console.error('Failed to get 2D context from canvas');
        onImageCropped(null);
        return;
      }

      // Enable image smoothing for better upscaling quality
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';

      // Draw the image, potentially upscaling small crops
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

      // Output as PNG for lossless representation of the crop for the color picker
      const base64ImagePNG = canvas.toDataURL('image/png');
      const pngSizeMB = (base64ImagePNG.length * 0.75) / (1024 * 1024);
      console.log(`Cropped image (PNG for color picker) size: ${pngSizeMB.toFixed(2)} MB`);
      
      // No more forced compression to target size here.
      // The backend will handle final image compression and format.
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
            />
          </div>
        </div>
      )}

      {showCropper && previewUrl && (
        <div className="space-y-4 flex flex-col items-center">
          <div className="w-full flex justify-center">
            <div className="max-w-[38.4rem] overflow-visible">
              <ReactCrop
                crop={crop}
                onChange={(_, percentCrop) => setCrop(percentCrop)}
                onComplete={(c) => setCompletedCrop(c)}
                aspect={aspectRatio}
                minWidth={MIN_DIMENSION}
                minHeight={MIN_DIMENSION}
              >
                <img
                  ref={imgRef}
                  src={previewUrl}
                  alt="Selected preview for cropping"
                  onLoad={onImageLoad}
                  style={{ 
                    maxWidth: '100%', 
                    maxHeight: '70vh', 
                    objectFit: 'contain'
                  }}
                  className="border border-foreground" 
                />
              </ReactCrop>
            </div>
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