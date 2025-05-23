'use client';

import React, { useEffect, useState, useRef } from 'react';
import { 
  MoreHorizontal, Share2, Link2, Download, RectangleHorizontal, RectangleVertical,
  Undo2, BookOpenText
} from 'lucide-react';
import { getContrastTextColor } from '@/lib/colorUtils';

interface CardDisplayProps {
  frontHorizontalImageUrl: string | null;
  frontVerticalImageUrl: string | null;
  backHorizontalImageUrl?: string | null;
  backVerticalImageUrl?: string | null;
  noteText?: string | null;
  hasNote?: boolean | null;
  isFlippable?: boolean;
  isFlipped: boolean;
  onFlip: () => void;
  currentDisplayOrientation: 'horizontal' | 'vertical';
  setCurrentDisplayOrientation: (orientation: 'horizontal' | 'vertical') => void;
  handleShare: () => Promise<void>;
  handleCopyGeneratedUrl: () => Promise<void>;
  handleDownloadImage: (orientation: 'horizontal' | 'vertical') => void;
  handleCreateNew?: () => void;
  isGenerating: boolean;
  generatedExtendedId: string | null;
  cardDisplayControlsRef?: React.RefObject<HTMLDivElement>;
  shareFeedback?: string;
  copyUrlFeedback?: string;
  isVisible: boolean;
  disableScrollOnLoad?: boolean;
  swipeDirection?: 'left' | 'right' | null;
  hexColor?: string | null;
  createdAt?: string | null;
}

// Define known dimensions (assuming these are correct, adjust if needed)
const KNOWN_DIMENSIONS = {
  horizontal: { width: 1400, height: 700 },
  vertical: { width: 700, height: 1400 },
};

const CardDisplay: React.FC<CardDisplayProps> = ({
  frontHorizontalImageUrl,
  frontVerticalImageUrl,
  backHorizontalImageUrl,
  backVerticalImageUrl,
  noteText,
  hasNote,
  isFlippable = false,
  isFlipped,
  onFlip,
  currentDisplayOrientation,
  setCurrentDisplayOrientation,
  handleShare,
  handleCopyGeneratedUrl,
  handleDownloadImage,
  handleCreateNew,
  isGenerating,
  generatedExtendedId,
  cardDisplayControlsRef,
  shareFeedback,
  copyUrlFeedback,
  isVisible,
  disableScrollOnLoad,
  swipeDirection,
  hexColor,
  createdAt,
}) => {
  const [isActionsMenuOpen, setIsActionsMenuOpen] = useState(false);
  const actionsMenuRef = useRef<HTMLDivElement>(null);
  const [currentOrientation, setCurrentOrientation] = useState<"horizontal" | "vertical">(currentDisplayOrientation);

  const flipperBaseClasses = "card-flipper";
  // const flipperAspectRatio = currentOrientation === 'horizontal' ? 'aspect-[2/1]' : 'aspect-[1/2]'; // REMOVED
  // const verticalMaxHeightClass = currentOrientation === 'vertical' ? 'max-h-[80vh]' : ''; // Intentionally commented out

  const cardImageUrl = currentOrientation === "horizontal" ? frontHorizontalImageUrl : frontVerticalImageUrl;
  const backCardImageUrl = currentOrientation === "horizontal" ? backHorizontalImageUrl : backVerticalImageUrl;

  // For the "post stamp" area, if its background is always page white, text will be black (or determined by contrast with white)
  const postStampBackgroundColor = 'hsl(0, 0%, 98%)'; // Use specific off-white from globals.css
  const postStampTextColor = getContrastTextColor('hsl(0, 0%, 98%)'); // Text color for this background

  const handleSetOrientation = (newOrientation: "horizontal" | "vertical") => {
    setCurrentOrientation(newOrientation);
    if (isFlipped) {
      onFlip();
    }
    setIsActionsMenuOpen(false);
  };

  const handleFlipCard = () => {
    if (isFlippable) {
      onFlip();
    }
  };

  useEffect(() => {
    if (!disableScrollOnLoad && isVisible && cardDisplayControlsRef?.current) {
      setTimeout(() => {
        cardDisplayControlsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [currentOrientation, isVisible, cardDisplayControlsRef, frontHorizontalImageUrl, frontVerticalImageUrl]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (actionsMenuRef.current && !actionsMenuRef.current.contains(event.target as Node)) {
        setIsActionsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    if (!isFlippable && isFlipped) {
      onFlip();
    }
  }, [isFlippable, isFlipped, onFlip]);

  if (!isVisible) {
    return null;
  }

  const commonButtonStyles = "px-6 py-3 bg-input text-foreground font-semibold border-2 border-foreground shadow-[4px_4px_0_0_theme(colors.foreground)] hover:shadow-[2px_2px_0_0_theme(colors.foreground)] active:shadow-[1px_1px_0_0_theme(colors.foreground)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center justify-center";
  const dropdownItemStyles = "w-full px-4 py-2 text-sm text-foreground hover:bg-muted flex items-center justify-start gap-2 disabled:opacity-60 disabled:cursor-not-allowed";
  const activeDropdownItemStyles = "w-full px-4 py-2 text-sm text-blue-700 bg-blue-50 font-semibold flex items-center justify-start gap-2 disabled:opacity-60 disabled:cursor-not-allowed";
  const createNewButtonStyles = "text-sm text-foreground hover:text-muted-foreground underline flex items-center justify-center gap-2";

  const revealButtonStyle = "px-6 py-3 font-semibold bg-black text-white border-2 border-[#374151] shadow-[4px_4px_0_0_#374151] hover:shadow-[2px_2px_0_0_#374151] active:shadow-[1px_1px_0_0_#374151] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center justify-center disabled:opacity-70 disabled:bg-[#1F2937] disabled:text-[#9CA3AF] disabled:border-[#4B5563] disabled:shadow-none disabled:cursor-not-allowed";

  const downloadButtonText = () => {
    let text = "Download";
    const dimensions = KNOWN_DIMENSIONS[currentOrientation];
    text += ` (${dimensions.width}x${dimensions.height}px)`;
    return text;
  };

  return (
    <section ref={cardDisplayControlsRef} className="w-full px-1 py-2 md:px-2 md:py-2 mt-0 flex flex-col items-center scroll-target-with-offset">
      <style jsx global>{`
        .perspective-container {
          perspective: 1200px; /* Increased perspective for a more pronounced 3D effect */
          display: flex;
          justify-content: center;
          align-items: center;
          width: 100%; /* Ensure it takes width for aspect ratio calculation */
        }

        /* This is the div that will have the dynamic Tailwind aspect ratio class */
        .flippable-card-wrapper .card-flipper {
          position: relative; /* Children will be absolute to this */
          width: 100%; /* Takes full width of its column in the grid/flex parent */
          height: 0; /* ADDED for padding-bottom trick */
          /* padding-bottom will be set dynamically inline */
          transform-style: preserve-3d;
          transition: transform 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275); /* Smoother, slightly bouncy flip */
        }

        .flippable-card-wrapper .card-flipper.is-flipped.swipe-left {
          transform: rotateY(-180deg);
        }

        .flippable-card-wrapper .card-flipper.is-flipped.swipe-right {
          transform: rotateY(180deg);
        }

        .flippable-card-wrapper .card-face {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          backface-visibility: hidden;
          display: flex; /* For aligning content (like placeholders) within the face */
          justify-content: center;
          align-items: center;
          overflow: hidden; /* Prevent content spill, especially from rotated children */
          border-radius: inherit; /* Inherit border-radius from parent if any */
        }

        .flippable-card-wrapper .card-face img {
          display: block; /* Remove extra space below image */
          width: 100%;    /* Make image fill the face */
          height: 100%;   /* Make image fill the face */
          object-fit: contain; /* Or 'cover'; 'contain' ensures whole image is visible */
          border-radius: inherit; /* Ensure image corners match face corners if rounded */
        }
        
        .flippable-card-wrapper .card-front {
          /* z-index: 2; /* Usually not needed with backface-visibility */
        }

        .flippable-card-wrapper .card-back {
          transform: rotateY(180deg);
        }
      `}</style>

      <div className="space-y-6 flex flex-col items-center w-full max-w-2xl lg:max-w-4xl">
        <div className={`w-full perspective-container ${isFlippable ? 'flippable-card-wrapper' : ''}`}>
          <div 
            className={`${flipperBaseClasses} ${ 
              isFlippable && isFlipped
                ? swipeDirection === 'left'
                  ? 'is-flipped swipe-left'
                  : 'is-flipped swipe-right'
                : ''
            }`.trim()}
            style={{
              paddingBottom: currentOrientation === 'horizontal' ? '50%' : '200%',
            }}
          >
            {/* FRONT OF CARD */}
            <div className="card-face card-front">
              {(currentOrientation === 'horizontal' && frontHorizontalImageUrl) ? (
                <img src={frontHorizontalImageUrl} alt="Generated horizontal card (front)" className="w-full h-full object-contain rounded-md cursor-pointer" onClick={handleFlipCard} />
              ) : (currentOrientation === 'vertical' && frontVerticalImageUrl) ? (
                <img src={frontVerticalImageUrl} alt="Generated vertical card (front)" className="w-full h-full object-contain rounded-md cursor-pointer" onClick={handleFlipCard} />
              ) : (
                <div className="w-full h-full flex justify-center items-center bg-muted rounded-md">
                  <p className="text-muted-foreground text-center p-4">Image not available or selected orientation has no image.</p>
                </div>
              )}
            </div>

            {/* BACK OF CARD */}
            <div className="card-face card-back">
              {(currentOrientation === 'horizontal' && backHorizontalImageUrl) ? (
                <img src={backHorizontalImageUrl} alt="Generated horizontal card (back)" className="w-full h-full object-contain rounded-md cursor-pointer" onClick={handleFlipCard} />
              ) : (currentOrientation === 'vertical' && backVerticalImageUrl) ? (
                <img src={backVerticalImageUrl} alt="Generated vertical card (back)" className="w-full h-full object-contain rounded-md cursor-pointer" onClick={handleFlipCard} />
              ) : noteText ? (
                <div 
                  className="w-full h-full flex flex-col justify-center items-center p-6 rounded-md overflow-auto"
                  style={{
                    backgroundColor: postStampBackgroundColor,
                    color: postStampTextColor,
                  }}
                >
                  <p className="text-sm text-center whitespace-pre-wrap">{noteText}</p>
                  {createdAt && (
                    <p className="text-xs text-center whitespace-pre-wrap mt-4">Created: {new Date(createdAt).toLocaleDateString()}</p>
                  )}
                </div>
              ) : createdAt ? (
                <div 
                  className="w-full h-full flex flex-col justify-center items-center p-6 rounded-md"
                  style={{
                    backgroundColor: postStampBackgroundColor,
                    color: postStampTextColor,
                  }}
                >
                  <p className="text-sm text-center whitespace-pre-wrap">Created: {new Date(createdAt).toLocaleDateString()}</p>
                </div>
              ) : (
                <div className="w-full h-full flex justify-center items-center bg-muted rounded-md">
                  <p className="text-muted-foreground text-center p-4">Card back not available.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-col justify-center items-center gap-4 mt-6 w-full">
          {isFlippable && (backCardImageUrl || (hasNote === false)) && (
            <div className="flex flex-col items-center mb-2">
              <div className="flex items-center justify-center gap-4">
                <button
                  onClick={handleFlipCard}
                  className={`${revealButtonStyle} min-w-[200px]`}
                  title={isFlipped ? "Show Front" : "Reveal the Note"}
                >
                  {isFlipped ? <Undo2 size={20} className="mr-1.5" /> : <BookOpenText size={20} className="mr-1.5" />}
                  <span className="text-sm">{isFlipped ? "Show Front" : "Reveal the Note"}</span>
                </button>

                <div className="relative" ref={actionsMenuRef}>
                  <button
                    onClick={() => setIsActionsMenuOpen(!isActionsMenuOpen)}
                    className={`${commonButtonStyles}`}
                    title="More actions"
                  >
                    <MoreHorizontal size={20} />
                  </button>
                  {isActionsMenuOpen && (
                    <div className="absolute top-full mt-2 right-0 bg-card border-2 border-foreground shadow-lg rounded-md py-1 z-10 flex flex-col min-w-[240px]">
                      <button
                        onClick={() => handleSetOrientation('horizontal')}
                        disabled={!frontHorizontalImageUrl}
                        className={currentOrientation === 'horizontal' ? activeDropdownItemStyles : dropdownItemStyles}
                      >
                        <RectangleHorizontal size={16} /> View Horizontal
                      </button>
                      <button
                        onClick={() => handleSetOrientation('vertical')}
                        disabled={!frontVerticalImageUrl}
                        className={currentOrientation === 'vertical' ? activeDropdownItemStyles : dropdownItemStyles}
                      >
                        <RectangleVertical size={16} /> View Vertical
                      </button>
                      <div className="h-px bg-border my-1 mx-2"></div>
                      <button
                        onClick={() => { handleShare(); setIsActionsMenuOpen(false); }}
                        disabled={isGenerating || !(frontHorizontalImageUrl || frontVerticalImageUrl) || !generatedExtendedId}
                        className={dropdownItemStyles}
                      >
                        <Share2 size={16} /> Share
                      </button>
                      <button
                        onClick={() => { handleCopyGeneratedUrl(); setIsActionsMenuOpen(false); }}
                        disabled={isGenerating || !generatedExtendedId}
                        className={dropdownItemStyles}
                      >
                        <Link2 size={16} /> Copy URL
                      </button>
                      <button
                        onClick={() => { handleDownloadImage(currentOrientation); setIsActionsMenuOpen(false); }}
                        disabled={isGenerating || (currentOrientation === 'horizontal' ? !frontHorizontalImageUrl : !frontVerticalImageUrl)}
                        className={dropdownItemStyles}
                      >
                        <Download size={16} /> {downloadButtonText()}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
        
        {(shareFeedback && !copyUrlFeedback) && (
          <p className="text-sm text-blue-700 mt-2 text-center h-5">{shareFeedback}</p>
        )}
        {copyUrlFeedback && (
          <p className="text-sm text-green-700 mt-2 text-center h-5">{copyUrlFeedback}</p>
        )}

        {handleCreateNew && (
          <button
            onClick={handleCreateNew}
            className={createNewButtonStyles}
            title="Create New Card"
          >
            + Create New Card
          </button>
        )}
      </div>
    </section>
  );
};

export default CardDisplay; 