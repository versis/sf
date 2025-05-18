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
        // Match the final card dimensions with a 50/50 split
        previewCanvas.width = 500; // Scaled down version for better display
        previewCanvas.height = 300; // Height for proper display

        const swatchWidth = previewCanvas.width * 0.50; // 50% for swatch (250px)
        const imagePanelXStart = swatchWidth;
        const imagePanelWidth = previewCanvas.width - swatchWidth; // 50% for image (250px)
        const imagePanelHeight = previewCanvas.height;

        // Draw color swatch
        prevCtx.fillStyle = hexColor;
        prevCtx.fillRect(0, 0, swatchWidth, previewCanvas.height);

        // Fill the image panel with black to avoid any transparency issues
        prevCtx.fillStyle = '#000000';
        prevCtx.fillRect(imagePanelXStart, 0, imagePanelWidth, imagePanelHeight);

        const img = new Image();
        img.onload = () => {
          // Calculate dimensions to cover the panel while maintaining aspect ratio
          const imgAspectRatio = img.width / img.height;
          const panelAspectRatio = imagePanelWidth / imagePanelHeight;
          
          let drawWidth, drawHeight, offsetX, offsetY;
          
          if (imgAspectRatio > panelAspectRatio) {
            // Image is wider than panel (relative to height)
            drawHeight = imagePanelHeight;
            drawWidth = drawHeight * imgAspectRatio;
            offsetX = imagePanelXStart + (imagePanelWidth - drawWidth) / 2;
            offsetY = 0;
          } else {
            // Image is taller than panel (relative to width)
            drawWidth = imagePanelWidth;
            drawHeight = drawWidth / imgAspectRatio;
            offsetX = imagePanelXStart;
            offsetY = (imagePanelHeight - drawHeight) / 2;
          }
          
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
    const swatchWidth = previewCanvas.width * 0.50;
    const imagePanelXStart = swatchWidth;
    const imagePanelWidth = previewCanvas.width - swatchWidth;
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
      const imgAspectRatio = sourceImgWidth / sourceImgHeight;
      const panelAspectRatio = imagePanelWidth / imagePanelHeight;
      
      let drawWidth, drawHeight, offsetX, offsetY;
      
      if (imgAspectRatio > panelAspectRatio) {
        // Image is wider than panel (relative to height)
        drawHeight = imagePanelHeight;
        drawWidth = drawHeight * imgAspectRatio;
        offsetX = imagePanelXStart + (imagePanelWidth - drawWidth) / 2;
        offsetY = 0;
      } else {
        // Image is taller than panel (relative to width)
        drawWidth = imagePanelWidth;
        drawHeight = drawWidth / imgAspectRatio;
        offsetX = imagePanelXStart;
        offsetY = (imagePanelHeight - drawHeight) / 2;
      }
      
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
            style={{ aspectRatio: '5 / 3' }} // Keep 5/3 ratio for the preview canvas (still shows half color/half image)
          />
          {/* Hidden canvas for source image data */}
          <canvas ref={sourceImageCanvasRef} style={{ display: 'none' }} />
        </>
      )}
    </div>
  );
};

export default ColorTools; 