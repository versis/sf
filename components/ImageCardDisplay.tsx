'use client';

import { useState, useEffect } from 'react';

interface CardImage {
  h?: string; // URL for horizontal image
  v?: string; // URL for vertical image
  altText?: string;
}

interface ImageCardDisplayProps {
  cardSet: CardImage[]; // Array of card image objects
  isMobile: boolean;
  initialIndex?: number;
  enableImageSwitching?: boolean; // To control if prev/next is shown when multiple cards
  className?: string; // Optional additional class names for the wrapper
  defaultOrientation?: 'horizontal' | 'vertical';
}

const SWIPE_THRESHOLD = 50;

const ImageCardDisplay: React.FC<ImageCardDisplayProps> = ({
  cardSet,
  isMobile,
  initialIndex = 0,
  enableImageSwitching = true, // Default to true if cardSet has more than 1 item
  className = '',
  defaultOrientation = 'horizontal',
}) => {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [touchStartX, setTouchStartX] = useState<number | null>(null);
  const [currentOrientation, setCurrentOrientation] = useState<'horizontal' | 'vertical'>(defaultOrientation);

  const getContainerClasses = (orientation: 'horizontal' | 'vertical', mobile: boolean) => {
    let aspectRatioContainer = 'aspect-video max-w-xl'; // Default to desktop horizontal
    if (mobile) {
      aspectRatioContainer = orientation === 'horizontal' ? 'w-full max-w-md aspect-video' : 'w-full max-w-sm aspect-[3/4]';
    } else { // Desktop
      aspectRatioContainer = orientation === 'horizontal' ? 'max-w-xl aspect-video mx-auto' : 'max-w-sm aspect-[3/4] mx-auto'; 
    }
    return { aspectRatioContainer }; 
  };

  useEffect(() => {
    if (isMobile) {
      if (cardSet[currentIndex]?.v) {
        setCurrentOrientation('vertical');
      } else if (cardSet[currentIndex]?.h) {
        setCurrentOrientation('horizontal');
      } else {
        setCurrentOrientation(defaultOrientation);
      }
    } else {
        if (cardSet[currentIndex]?.h) {
            setCurrentOrientation('horizontal');
        } else if (cardSet[currentIndex]?.v) {
            setCurrentOrientation('vertical');
        } else {
            setCurrentOrientation(defaultOrientation);
        }
    }
  }, [isMobile, currentIndex, cardSet, defaultOrientation]);

  const handleNextCard = () => {
    if (!actualEnableImageSwitching) return;
    setCurrentIndex((prevIndex) => (prevIndex + 1) % cardSet.length);
  };

  const handlePrevCard = () => {
    if (!actualEnableImageSwitching) return;
    setCurrentIndex((prevIndex) => (prevIndex - 1 + cardSet.length) % cardSet.length);
  };

  const currentCard = cardSet[currentIndex];
  const { aspectRatioContainer } = getContainerClasses(currentOrientation, isMobile);

  if (!cardSet || cardSet.length === 0 || !currentCard) {
    return <div className={`flex items-center justify-center text-muted-foreground bg-muted rounded-md ${aspectRatioContainer}`}>Image data not available.</div>;
  }

  const imageUrl = currentOrientation === 'vertical' ? currentCard.v : currentCard.h;
  const actualEnableImageSwitching = enableImageSwitching && cardSet.length > 1;

  if (!imageUrl) {
    return (
        <div className={`flex flex-col items-center w-full ${className}`}>
            <div className={`relative w-full mb-2 ${aspectRatioContainer} flex items-center justify-center text-muted-foreground bg-muted rounded-md`}>
                Orientation not available for this card.
            </div>
        </div>
    );
  }

  return (
    <div className={`flex flex-col items-center w-full ${className}`}>
      {/* Image Container */}
      <div 
        className={`relative w-full mb-2 cursor-grab active:cursor-grabbing ${aspectRatioContainer}`}
        onTouchStart={(e) => setTouchStartX(e.touches[0].clientX)}
        onTouchEnd={(e) => {
          if (touchStartX === null) return;
          const touchEndX = e.changedTouches[0].clientX;
          const deltaX = touchEndX - touchStartX;
          if (Math.abs(deltaX) > SWIPE_THRESHOLD) {
            if (deltaX > 0) { if (actualEnableImageSwitching) handlePrevCard(); }
            else { if (actualEnableImageSwitching) handleNextCard(); }
          }
          setTouchStartX(null);
        }}
      >
        <img 
          src={imageUrl}
          alt={currentCard.altText || `Card image ${currentIndex + 1} - ${currentOrientation}`}
          className="w-full h-full rounded-lg object-contain"
          draggable="false"
        />

        {/* Desktop Overlay/Side Buttons - Conditionally Rendered */}
        {!isMobile && actualEnableImageSwitching && (
          <>
            {currentIndex > 0 && (
              <button 
                onClick={handlePrevCard} 
                className="absolute top-1/2 -left-4 md:-left-8 transform -translate-y-1/2 text-muted-foreground hover:text-foreground z-10 transition-colors"
                aria-label="Previous card"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
              </button>
            )}
            {currentIndex < cardSet.length - 1 && (
              <button 
                onClick={handleNextCard} 
                className="absolute top-1/2 -right-4 md:-right-8 transform -translate-y-1/2 text-muted-foreground hover:text-foreground z-10 transition-colors"
                aria-label="Next card"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
              </button>
            )}
          </>
        )}
      </div>

      {/* Mobile Dot Indicators - Conditionally Rendered */}
      {isMobile && actualEnableImageSwitching && (
        <div className="flex justify-center items-center space-x-2 mt-1 mb-1">
            {cardSet.map((_, index) => (
                <button
                key={index}
                onClick={() => setCurrentIndex(index)}
                className={`w-2.5 h-2.5 rounded-full transition-colors ${currentIndex === index ? 'bg-foreground' : 'bg-muted hover:bg-muted-foreground/50'}`}
                aria-label={`Go to card ${index + 1}`}
                />
            ))}
        </div>
      )}
      
      {/* Toggle H/V buttons - specific to single card view on color page, handled outside for now */}
      {/* Or, could be added here if we pass a prop to enable them for single card display */}

    </div>
  );
};

export default ImageCardDisplay; 