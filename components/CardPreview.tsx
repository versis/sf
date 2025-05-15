'use client';

import React from 'react';

interface CardPreviewProps {
  imageDataUrl: string | null;
  backgroundColor: string;
  // width and height props are removed, will use Tailwind for responsive sizing
}

const CardPreview: React.FC<CardPreviewProps> = ({
  imageDataUrl,
  backgroundColor,
}) => {
  return (
    <div className="p-4 bg-card text-foreground">
      <h3 className="text-lg font-semibold mb-3">
        Live Preview
      </h3>
      {/* Card preview with rounded corners */}
      <div className="w-full aspect-[1000/600] rounded-lg overflow-hidden flex">
        {/* Left Panel (Color Swatch) */}
        <div 
          className="w-[42%] h-full"
          style={{ backgroundColor: backgroundColor }}
        />

        {/* Right Panel (Image) - Removed background colors */}
        <div className="w-[58%] h-full flex items-center justify-center overflow-hidden">
          {imageDataUrl ? (
            <img
              src={imageDataUrl}
              alt="Card Preview"
              className="w-full h-full object-cover" // Changed to object-cover to fill the panel
            />
          ) : (
            <div className="text-muted-foreground text-center p-2 text-sm">
              <p>Image will appear here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CardPreview; 