'use client';

import React, { useState, ChangeEvent, useRef, useEffect, MouseEvent } from 'react';

interface ColorToolsProps {
  initialHex?: string;
  onHexChange: (hex: string) => void;
  croppedImageDataUrl?: string | null; // For the color picker
  onColorPickedFromCanvas?: () => void; // New callback prop
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
  onColorPickedFromCanvas
}) => {
  const [hexColor, setHexColor] = useState<string>(initialHex);
  const [hexError, setHexError] = useState<string>('');
  const imageCanvasRef = useRef<HTMLCanvasElement | null>(null); // This will be the visible 42/58 preview
  const sourceImageCanvasRef = useRef<HTMLCanvasElement | null>(null); // Hidden canvas for original image data

  // Update internal hexColor state if initialHex prop changes from parent (e.g., after color picking)
  useEffect(() => {
    setHexColor(initialHex);
  }, [initialHex]);

  useEffect(() => {
    // Update the visible preview canvas (imageCanvasRef)
    const previewCanvas = imageCanvasRef.current;
    const sourceCanvas = sourceImageCanvasRef.current; // For original image data

    if (previewCanvas) {
      const prevCtx = previewCanvas.getContext('2d');
      if (prevCtx) {
        // Set fixed dimensions for the preview canvas (matching card aspect ratio)
        previewCanvas.width = 500; // Example width, aspect ratio 1000/600 = 500/300
        previewCanvas.height = 300;

        const swatchWidth = previewCanvas.width * 0.50;
        const imagePanelXStart = swatchWidth;
        const imagePanelWidth = previewCanvas.width - swatchWidth;

        // Draw color swatch
        prevCtx.fillStyle = hexColor;
        prevCtx.fillRect(0, 0, swatchWidth, previewCanvas.height);

        const img = new Image();
        img.onload = () => {
          // Draw image on the right panel of the preview canvas
          prevCtx.drawImage(img, imagePanelXStart, 0, imagePanelWidth, previewCanvas.height);

          // Also draw the original image to the hidden source canvas for accurate color picking
          if (sourceCanvas) {
            const sourceCtx = sourceCanvas.getContext('2d');
            if (sourceCtx) {
              sourceCanvas.width = img.naturalWidth;
              sourceCanvas.height = img.naturalHeight;
              sourceCtx.drawImage(img, 0, 0);
            }
          }
        };
        img.onerror = () => {
          console.error('Failed to load image for color picker.');
        };

        if (croppedImageDataUrl) {
          img.src = croppedImageDataUrl;
        } else {
          // Clear preview if no image
          prevCtx.clearRect(imagePanelXStart, 0, imagePanelWidth, previewCanvas.height);
          if (sourceCanvas) { // Clear source canvas too
            const sourceCtx = sourceCanvas.getContext('2d');
            if (sourceCtx) sourceCtx.clearRect(0, 0, sourceCanvas.width, sourceCanvas.height);
          }
        }
      }
    }
  }, [croppedImageDataUrl, hexColor]); // Redraw preview if hexColor (swatch) or image changes

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
    if (!imageCanvasRef.current || !sourceImageCanvasRef.current || !croppedImageDataUrl) return;

    const previewCanvas = imageCanvasRef.current;
    const sourceCanvas = sourceImageCanvasRef.current;
    const rect = previewCanvas.getBoundingClientRect(); // Dimensions of the displayed canvas

    // Click coordinates relative to the displayed canvas element
    const displayedClickX = event.clientX - rect.left;
    const displayedClickY = event.clientY - rect.top;

    // Scale click coordinates to the canvas's internal drawing dimensions (500x300)
    const displayToCanvasScaleX = previewCanvas.width / rect.width;
    const displayToCanvasScaleY = previewCanvas.height / rect.height;
    const canvasClickX = displayedClickX * displayToCanvasScaleX;
    const canvasClickY = displayedClickY * displayToCanvasScaleY;

    // Define the image panel dimensions within the internal canvas drawing
    const imagePanelXStartDrawn = previewCanvas.width * 0.50;
    const imagePanelWidthDrawn = previewCanvas.width * 0.50;
    const imagePanelHeightDrawn = previewCanvas.height;

    // Check if the (scaled) click is within the image panel on the internal canvas
    if (canvasClickX >= imagePanelXStartDrawn && canvasClickX < previewCanvas.width) {
      // Calculate click coordinates relative to the image panel on the internal canvas
      const localXDrawn = canvasClickX - imagePanelXStartDrawn;
      const localYDrawn = canvasClickY;

      // Scale these coordinates to the original source image dimensions
      const sourceImgWidth = sourceCanvas.width;
      const sourceImgHeight = sourceCanvas.height;

      const pickX = Math.floor((localXDrawn / (previewCanvas.width * 0.50)) * sourceImgWidth);
      const pickY = Math.floor((localYDrawn / imagePanelHeightDrawn) * sourceImgHeight);

      const sourceCtx = sourceCanvas.getContext('2d');
      if (sourceCtx) {
        const finalPickX = Math.min(Math.max(pickX, 0), sourceImgWidth - 1);
        const finalPickY = Math.min(Math.max(pickY, 0), sourceImgHeight - 1);
        const pixel = sourceCtx.getImageData(finalPickX, finalPickY, 1, 1).data;
        const hex = rgbToHex(pixel[0], pixel[1], pixel[2]);
        setHexColor(hex); 
        onHexChange(hex); 
        setHexError(''); 
        if (onColorPickedFromCanvas) {
          onColorPickedFromCanvas(); // Call the callback
        }
      }
    }
  };

  return (
    <div className="space-y-4">
      {croppedImageDataUrl && (
        <>
          <canvas 
            ref={imageCanvasRef} 
            onClick={handleCanvasClick} 
            className="cursor-crosshair w-full max-w-[38.4rem] h-auto rounded-lg block mx-auto" 
            style={{ aspectRatio: '1000 / 600' }} 
          />
          {/* Hidden canvas for source image data */}
          <canvas ref={sourceImageCanvasRef} style={{ display: 'none' }} />
        </>
      )}
    </div>
  );
};

export default ColorTools; 