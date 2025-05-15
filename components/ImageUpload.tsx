'use client';

import React, { useState, ChangeEvent, useRef } from 'react';
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
  onImageSelect: (file: File) => void; // Callback to pass the original selected file
  onImageCropped: (croppedImageDataUrl: string | null) => void; // Callback for the cropped image data
}

const ASPECT_RATIO = 1;
const MIN_DIMENSION = 150;

const ImageUpload: React.FC<ImageUploadProps> = ({ onImageSelect, onImageCropped }) => {
  const imgRef = useRef<HTMLImageElement | null>(null);
  const previewCanvasRef = useRef<HTMLCanvasElement | null>(null); // For drawing the cropped image
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [crop, setCrop] = useState<Crop>();
  const [completedCrop, setCompletedCrop] = useState<PixelCrop>();

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onImageSelect(file);
      setCrop(undefined);
      setCompletedCrop(undefined);
      onImageCropped(null); // Reset cropped image data on new file select

      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    } else {
      setPreviewUrl(null);
      setCompletedCrop(undefined);
      onImageCropped(null);
    }
  };

  const onImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const { width, height } = e.currentTarget;
    const crop = centerAspectCrop(width, height, ASPECT_RATIO);
    setCrop(crop);
  };

  const getCroppedImg = () => {
    if (!completedCrop || !imgRef.current || !previewCanvasRef.current) {
      console.error('Crop, image reference, or canvas reference is not available.');
      return;
    }

    const image = imgRef.current;
    const canvas = previewCanvasRef.current;
    const crop = completedCrop;

    const scaleX = image.naturalWidth / image.width;
    const scaleY = image.naturalHeight / image.height;

    canvas.width = crop.width * scaleX;
    canvas.height = crop.height * scaleY;

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      console.error('Failed to get 2D context from canvas');
      return;
    }

    ctx.drawImage(
      image,
      crop.x * scaleX,
      crop.y * scaleY,
      crop.width * scaleX,
      crop.height * scaleY,
      0,
      0,
      crop.width * scaleX,
      crop.height * scaleY
    );

    // Get the data URL of the cropped image
    const base64Image = canvas.toDataURL('image/png'); // Or 'image/jpeg'
    onImageCropped(base64Image);
    console.log('Cropped image data URL:', base64Image.substring(0, 100) + '...');
  };

  return (
    <div className="space-y-6">
      <div>
        <label htmlFor="imageUpload" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Upload Image
        </label>
        <input
          type="file"
          id="imageUpload"
          name="imageUpload"
          accept="image/*"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500 dark:text-gray-400
                     file:mr-4 file:py-2 file:px-4
                     file:rounded-md file:border-0
                     file:text-sm file:font-semibold
                     file:bg-blue-50 file:text-blue-700
                     hover:file:bg-blue-100
                     dark:file:bg-gray-700 dark:file:text-gray-200 dark:hover:file:bg-gray-600"
        />
      </div>

      {previewUrl && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-800 dark:text-gray-100 mb-2">Crop Image:</h3>
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
              style={{ maxHeight: '70vh', display: previewUrl ? 'block' : 'none' }}
              className="rounded-md border border-gray-300 dark:border-gray-600"
            />
          </ReactCrop>
        </div>
      )}

      {/* Hidden canvas for drawing cropped image */}
      <canvas ref={previewCanvasRef} style={{ display: 'none' }} />

      {completedCrop && imgRef.current && (
        <div className="mt-4 p-4 border border-dashed border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700/50">
          <h4 className="text-md font-semibold mb-1 text-gray-700 dark:text-gray-200">Crop Controls:</h4>
          {/* <pre className="text-xs text-gray-600 dark:text-gray-300 overflow-x-auto">
            {JSON.stringify(completedCrop, null, 2)}
          </pre> */}
          <button
            type="button"
            onClick={getCroppedImg}
            className="mt-2 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 dark:bg-green-500 dark:hover:bg-green-600"
          >
            Confirm Crop
          </button>
        </div>
      )}
    </div>
  );
};

export default ImageUpload; 