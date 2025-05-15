'use client';

import React, { useState, ChangeEvent, useRef, useEffect, MouseEvent } from 'react';

interface ColorToolsProps {
  initialHex?: string;
  initialName?: string;
  onHexChange: (hex: string) => void;
  onNameChange: (name: string) => void;
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
  initialName = '',
  onHexChange,
  onNameChange,
  croppedImageDataUrl,
}) => {
  const [hexColor, setHexColor] = useState<string>(initialHex);
  const [colorName, setColorName] = useState<string>(initialName);
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

  const handleNameInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const newName = event.target.value;
    setColorName(newName);
    onNameChange(newName);
  };

  const handleCanvasClick = (event: MouseEvent<HTMLCanvasElement>) => {
    if (!imageCanvasRef.current) return;
    const canvas = imageCanvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const ctx = canvas.getContext('2d');
    if (ctx) {
      const pixel = ctx.getImageData(x, y, 1, 1).data;
      const hex = rgbToHex(pixel[0], pixel[1], pixel[2]);
      setHexColor(hex); // Update local state for immediate feedback in input
      onHexChange(hex); // Propagate to parent
      setHexError(''); // Clear any previous hex error
    }
  };

  return (
    <div className="space-y-6 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
      <h3 className="text-lg font-medium text-gray-800 dark:text-gray-100">Color Details:</h3>
      
      {croppedImageDataUrl && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Pick color from image (click below):
          </p>
          <canvas 
            ref={imageCanvasRef} 
            onClick={handleCanvasClick} 
            className="border border-gray-300 dark:border-gray-600 rounded-md cursor-crosshair max-w-full h-auto"
            // Style to ensure canvas is not larger than its container if image is big
            style={{ maxWidth: '100%', height: 'auto'}}
          />
        </div>
      )}

      <div>
        <label htmlFor="hexColorInput" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          HEX Color Code
        </label>
        <input
          type="text"
          id="hexColorInput"
          value={hexColor} // Controlled by local state, updated by picker or input
          onChange={handleHexInputChange}
          placeholder="#RRGGBB"
          className={`block w-full sm:w-1/2 p-2 border rounded-md shadow-sm 
                      ${hexError ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} 
                      focus:ring-blue-500 focus:border-blue-500 
                      dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400`}
        />
        {hexError && <p className="mt-1 text-xs text-red-600 dark:text-red-400">{hexError}</p>}
        <div 
            className="mt-2 w-10 h-10 rounded border border-gray-400 dark:border-gray-500"
            style={{ backgroundColor: /^#[0-9A-F]{6}$/i.test(hexColor) || /^#[0-9A-F]{3}$/i.test(hexColor) ? hexColor : 'transparent' }}
            title="Current color preview"
        ></div>
      </div>

      <div>
        <label htmlFor="colorNameInput" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Color Name
        </label>
        <input
          type="text"
          id="colorNameInput"
          value={colorName}
          onChange={handleNameInputChange}
          placeholder="e.g., Deep Cerulean"
          className="block w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm 
                     focus:ring-blue-500 focus:border-blue-500 
                     dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
        />
      </div>
    </div>
  );
};

export default ColorTools; 