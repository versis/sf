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
}

const ASPECT_RATIO = 1;
const MIN_DIMENSION = 150;

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

  const getCroppedImg = () => {
    if (!completedCrop || !imgRef.current || !previewCanvasRef.current) {
      console.error('Crop, image reference, or canvas reference is not available.');
      onImageCropped(null);
      return;
    }

    const image = imgRef.current;
    const canvas = previewCanvasRef.current;
    const cropData = completedCrop;

    const scaleX = image.naturalWidth / image.width;
    const scaleY = image.naturalHeight / image.height;

    canvas.width = cropData.width * scaleX;
    canvas.height = cropData.height * scaleY;

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
      cropData.width * scaleX,
      cropData.height * scaleY,
      0,
      0,
      cropData.width * scaleX,
      cropData.height * scaleY
    );

    const base64Image = canvas.toDataURL('image/png');
    onImageCropped(base64Image);
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
          {completedCrop && imgRef.current && (
            <div className="mt-4 flex justify-center">
              <button
                type="button"
                onClick={getCroppedImg}
                className="px-6 py-3 bg-input text-blue-700 font-semibold border-2 border-blue-700 shadow-[4px_4px_0_0_theme(colors.blue.700)] hover:shadow-[2px_2px_0_0_theme(colors.blue.700)] active:shadow-[1px_1px_0_0_theme(colors.blue.700)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground"
              >
                Confirm Crop
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