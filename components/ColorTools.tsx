'use client';

import React, { useState, ChangeEvent, useRef, useEffect, MouseEvent } from 'react';

interface ColorToolsProps {
  initialHex?: string;
  onHexChange: (hex: string) => void;
  croppedImageDataUrl?: string | null; // For the color picker
}

// Helper to convert RGB to HEX
const rgbToHex = (r: number, g: number, b: number): string => {
  return (
    '#' +
    [r, g, b]
      .map((x) => {
        const hex = x.toString(16);
        return hex.length === 1 ? '0' + hex : hex;
      })
      .join('')
      .toUpperCase()
  );
};

const ColorTools: React.FC<ColorToolsProps> = ({
  initialHex = '#000000',
  onHexChange,
  croppedImageDataUrl,
}) => {
  const [hexColor, setHexColor] = useState<string>(initialHex);
  const [hexError, setHexError] = useState<string>('');
  const imageCanvasRef = useRef<HTMLCanvasElement | null>(null);

  // Update internal hexColor state if initialHex prop changes from parent (e.g., after color picking)
  useEffect(() => {
    setHexColor(initialHex);
  }, [initialHex]);

  useEffect(() => {
    if (croppedImageDataUrl && imageCanvasRef.current) {
      const canvas = imageCanvasRef.current;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        const img = new Image();
        img.onload = () => {
          // Set canvas dimensions to image dimensions to avoid scaling issues with pixel picking
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.drawImage(img, 0, 0);
        };
        img.onerror = () => {
          console.error('Failed to load image for color picker.');
        };
        img.src = croppedImageDataUrl;
      }
    } else if (imageCanvasRef.current) {
      // Clear canvas if no image
      const canvas = imageCanvasRef.current;
      const ctx = canvas.getContext('2d');
      if(ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
  }, [croppedImageDataUrl]);

  const handleHexInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    let newHex = event.target.value.toUpperCase();
    if (!newHex.startsWith('#')) {
      newHex = '#' + newHex;
    }
    setHexColor(newHex);

    if (/^#[0-9A-F]{6}$/i.test(newHex) || /^#[0-9A-F]{3}$/i.test(newHex)) {
      onHexChange(newHex);
      setHexError('');
    } else if (newHex.length > 1 && newHex.length <= 7) {
      setHexError('Invalid HEX (e.g., #RRGGBB).');
    } else if (newHex.length > 7) {
        setHexError('HEX code is too long.');
    } else {
      setHexError('');
    }
  };

  const handleCanvasClick = (event: MouseEvent<HTMLCanvasElement>) => {
    if (!imageCanvasRef.current) return;
    const canvas = imageCanvasRef.current;
    const rect = canvas.getBoundingClientRect();

    // Calculate click coordinates relative to the canvas element
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Adjust coordinates for canvas scaling (due to CSS or browser zoom)
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const canvasX = x * scaleX;
    const canvasY = y * scaleY;

    const ctx = canvas.getContext('2d');
    if (ctx) {
      // Ensure coordinates are within canvas bounds before getting image data
      const finalX = Math.min(Math.max(canvasX, 0), canvas.width - 1);
      const finalY = Math.min(Math.max(canvasY, 0), canvas.height - 1);
      const pixel = ctx.getImageData(finalX, finalY, 1, 1).data;
      const hex = rgbToHex(pixel[0], pixel[1], pixel[2]);
      setHexColor(hex); // Update local state for immediate feedback in input
      onHexChange(hex); // Propagate to parent
      setHexError(''); // Clear any previous hex error
    }
  };

  return (
    <div className="space-y-6">
      {croppedImageDataUrl && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-foreground">
            Pick color from image (click below):
          </p>
          <canvas 
            ref={imageCanvasRef} 
            onClick={handleCanvasClick} 
            className="cursor-crosshair max-w-full h-auto"
            style={{ maxWidth: '100%', height: 'auto'}}
          />
        </div>
      )}
    </div>
  );
};

export default ColorTools; 