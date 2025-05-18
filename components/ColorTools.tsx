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
    const sourceCanvas = sourceImageCanvasRef.current;

    if (previewCanvas) {
      const prevCtx = previewCanvas.getContext('2d');
      if (prevCtx) {
        // Set dimensions to match card proportions (horizontal orientation)
        previewCanvas.width = 600; 
        previewCanvas.height = 300; // 2:1 aspect ratio to match card
        
        // Split the canvas 50/50 for color and image
        const swatchWidth = previewCanvas.width * 0.5; // 50% for color swatch
        const imagePanelXStart = swatchWidth;
        const imagePanelWidth = previewCanvas.width - swatchWidth; // 50% for image
        const imagePanelHeight = previewCanvas.height;

        // Draw color swatch
        prevCtx.fillStyle = hexColor;
        prevCtx.fillRect(0, 0, swatchWidth, previewCanvas.height);

        // Fill the image panel with black to avoid any transparency issues
        prevCtx.fillStyle = '#000000';
        prevCtx.fillRect(imagePanelXStart, 0, imagePanelWidth, imagePanelHeight);

        const img = new Image();
        img.onload = () => {
          // We know the image is a square (1:1 ratio) from the cropping step
          // For a square image in a rectangular panel, we need to fit it properly
          
          // Calculate dimensions to fit the panel fully while maintaining aspect ratio
          const imgAspectRatio = img.width / img.height;
          const panelAspectRatio = imagePanelWidth / imagePanelHeight;
          
          let drawWidth, drawHeight, offsetX, offsetY;
          
          // Since we're using a square cropped image (1:1) in a rectangular panel:
          // The panel is likely wider than tall, so we'll fit to height and center horizontally
          drawHeight = imagePanelHeight;
          drawWidth = drawHeight; // Keep square aspect ratio (1:1)
          
          // Center the image in the panel
          offsetX = imagePanelXStart + (imagePanelWidth - drawWidth) / 2;
          offsetY = 0;
          
          // Draw image centered in the right panel of the preview canvas
          prevCtx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight);

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
  }, [croppedImageDataUrl, hexColor]);

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

    // Scale click coordinates to the canvas's internal drawing dimensions
    const displayToCanvasScaleX = previewCanvas.width / rect.width;
    const displayToCanvasScaleY = previewCanvas.height / rect.height;
    const canvasClickX = displayedClickX * displayToCanvasScaleX;
    const canvasClickY = displayedClickY * displayToCanvasScaleY;

    // Define the image panel dimensions within the internal canvas drawing
    const swatchWidth = previewCanvas.width * 0.5; // 50% for color swatch
    const imagePanelXStart = swatchWidth;
    const imagePanelWidth = previewCanvas.width - swatchWidth; // 50% for image
    const imagePanelHeight = previewCanvas.height;

    // Check if the click is within the image panel
    if (canvasClickX >= imagePanelXStart && canvasClickX < previewCanvas.width) {
      // Need to recalculate the image dimensions to know where the actual image is drawn
      // This must match the exact logic in the useEffect draw function
      const img = new Image();
      img.src = croppedImageDataUrl;
      
      // We need to convert from click on display to click on source image
      const sourceImgWidth = sourceCanvas.width;
      const sourceImgHeight = sourceCanvas.height;
      
      // Since we know the image is a square (1:1) from cropping
      let drawWidth, drawHeight, offsetX, offsetY;
      
      // Use the same layout logic as in the rendering code
      drawHeight = imagePanelHeight;
      drawWidth = drawHeight; // Keep square aspect ratio (1:1)
      
      // Center the image in the panel
      offsetX = imagePanelXStart + (imagePanelWidth - drawWidth) / 2;
      offsetY = 0;
      
      // Check if click is within the actual image area
      if (
        canvasClickX >= offsetX && 
        canvasClickX < offsetX + drawWidth && 
        canvasClickY >= offsetY && 
        canvasClickY < offsetY + drawHeight
      ) {
        // Convert canvas click position to source image coordinates
        const relativeX = (canvasClickX - offsetX) / drawWidth;
        const relativeY = (canvasClickY - offsetY) / drawHeight;
        
        const pickX = Math.floor(relativeX * sourceImgWidth);
        const pickY = Math.floor(relativeY * sourceImgHeight);
        
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
            style={{ aspectRatio: '2 / 1' }} // 2:1 ratio to match horizontal card layout
          />
          {/* Hidden canvas for source image data */}
          <canvas ref={sourceImageCanvasRef} style={{ display: 'none' }} />
        </>
      )}
    </div>
  );
};

export default ColorTools; 