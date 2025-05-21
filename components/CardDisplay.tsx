'use client';

import React, { useEffect, useState, useRef } from 'react';
import { 
  MoreHorizontal, Share2, Link2, Download, RectangleHorizontal, RectangleVertical
} from 'lucide-react';

interface CardDisplayProps {
  frontHorizontalImageUrl: string | null;
  frontVerticalImageUrl: string | null;
  backHorizontalImageUrl?: string | null;
  backVerticalImageUrl?: string | null;
  noteText?: string | null;
  hasNote?: boolean;
  isFlippable?: boolean;
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
  isFlippable,
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
}) => {
  // RE-ADD DEBUG LOGS FOR PROPS
  console.log("[CardDisplay Props] isVisible:", isVisible);
  console.log("[CardDisplay Props] currentDisplayOrientation:", currentDisplayOrientation);
  console.log("[CardDisplay Props] frontHorizontalImageUrl:", frontHorizontalImageUrl);
  console.log("[CardDisplay Props] frontVerticalImageUrl:", frontVerticalImageUrl);
  console.log("[CardDisplay Props] backHorizontalImageUrl:", backHorizontalImageUrl);
  console.log("[CardDisplay Props] backVerticalImageUrl:", backVerticalImageUrl);
  console.log("[CardDisplay Props] isFlippable:", isFlippable);
  console.log("[CardDisplay Props] hasNote:", hasNote);

  const [isActionsMenuOpen, setIsActionsMenuOpen] = useState(false);
  const actionsMenuRef = useRef<HTMLDivElement>(null);
  const [isFlipped, setIsFlipped] = useState<boolean>(false);

  useEffect(() => {
    if (!disableScrollOnLoad && isVisible && cardDisplayControlsRef?.current) {
      setTimeout(() => {
        cardDisplayControlsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [currentDisplayOrientation, isVisible, cardDisplayControlsRef, frontHorizontalImageUrl, frontVerticalImageUrl]);

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

  if (!isVisible) {
    return null;
  }

  const commonButtonStyles = "px-4 py-2 md:px-6 md:py-3 bg-input text-foreground font-semibold border-2 border-foreground shadow-[4px_4px_0_0_theme(colors.foreground)] hover:shadow-[2px_2px_0_0_theme(colors.foreground)] active:shadow-[1px_1px_0_0_theme(colors.foreground)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center justify-center gap-2";
  const dropdownItemStyles = "w-full px-4 py-2 text-left text-sm text-foreground hover:bg-muted flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed";
  const activeDropdownItemStyles = "w-full px-4 py-2 text-left text-sm text-blue-700 bg-blue-50 font-semibold flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed";
  const createNewButtonStyles = "text-sm text-foreground hover:text-muted-foreground underline flex items-center justify-center gap-2 mt-4 sm:mt-0";

  const downloadButtonText = () => {
    let text = "Download";
    const dimensions = KNOWN_DIMENSIONS[currentDisplayOrientation];
    const orientationLabel = currentDisplayOrientation === 'horizontal' ? "Horizontal" : "Vertical";
    text += ` (${orientationLabel} ${dimensions.width}x${dimensions.height}px)`;
    return text;
  };

  return (
    <section ref={cardDisplayControlsRef} className="w-full px-1 py-2 md:px-2 md:py-2 mt-0 flex flex-col items-center scroll-target-with-offset">
      <div className="space-y-6 flex flex-col items-center w-full max-w-2xl lg:max-w-4xl">
        <div className={`w-full perspective-container ${isFlippable ? 'flippable-card-wrapper' : ''}`}>
          <div className={`card-flipper ${isFlippable && isFlipped ? 'is-flipped' : ''}`}>
            {/* FRONT OF CARD */}
            <div className="card-face card-front">
              {(currentDisplayOrientation === 'horizontal' && frontHorizontalImageUrl) ? (
                <img src={frontHorizontalImageUrl} alt="Generated horizontal card (front)" className="max-w-full rounded-md md:max-w-2xl lg:max-w-4xl h-auto cursor-pointer" onClick={() => isFlippable && setIsFlipped(!isFlipped)} />
              ) : (currentDisplayOrientation === 'vertical' && frontVerticalImageUrl) ? (
                <img src={frontVerticalImageUrl} alt="Generated vertical card (front)" className="max-w-full rounded-md md:max-w-sm lg:max-w-md max-h-[85vh] h-auto cursor-pointer" onClick={() => isFlippable && setIsFlipped(!isFlipped)} />
              ) : (
                <div className="flex justify-center items-center w-full aspect-[16/9] md:aspect-[4/3] lg:aspect-[3/2] bg-muted rounded-md">
                  <p className="text-muted-foreground text-center p-4">Image not available or selected orientation has no image.</p>
                </div>
              )}
            </div>

            {/* BACK OF CARD */}
            <div className="card-face card-back">
              {(currentDisplayOrientation === 'horizontal' && backHorizontalImageUrl) ? (
                <img src={backHorizontalImageUrl} alt="Generated horizontal card (back)" className="max-w-full rounded-md md:max-w-2xl lg:max-w-4xl h-auto cursor-pointer" onClick={() => isFlippable && setIsFlipped(!isFlipped)} />
              ) : (currentDisplayOrientation === 'vertical' && backVerticalImageUrl) ? (
                <img src={backVerticalImageUrl} alt="Generated vertical card (back)" className="max-w-full rounded-md md:max-w-sm lg:max-w-md max-h-[85vh] h-auto cursor-pointer" onClick={() => isFlippable && setIsFlipped(!isFlipped)} />
              ) : (
                <div className="flex justify-center items-center w-full aspect-[16/9] md:aspect-[4/3] lg:aspect-[3/2] bg-muted rounded-md">
                  <p className="text-muted-foreground text-center p-4">Card back not available.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-col justify-center items-center gap-4 mt-6 w-full">
          {isFlippable && (backHorizontalImageUrl || backVerticalImageUrl) && (
             <button
                onClick={() => setIsFlipped(!isFlipped)}
                className={`${commonButtonStyles} mb-2`}
                title={isFlipped ? "Show Front" : "Reveal Note"}
              >
                {isFlipped ? "Show Front" : (hasNote ? "Reveal Note" : "Show Back")}
              </button>
          )}
          <div className="relative" ref={actionsMenuRef}>
            <button
              onClick={() => setIsActionsMenuOpen(!isActionsMenuOpen)}
              className={`${commonButtonStyles}`}
              title="More actions"
            >
              <MoreHorizontal size={20} />
              <span className="ml-2">More Actions</span>
            </button>
            {isActionsMenuOpen && (
              <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 bg-card border-2 border-foreground shadow-lg rounded-md py-1 w-auto z-10 whitespace-nowrap">
                 <button
                  onClick={() => { setCurrentDisplayOrientation('horizontal'); setIsActionsMenuOpen(false); setIsFlipped(false); }}
                  disabled={!frontHorizontalImageUrl}
                  className={currentDisplayOrientation === 'horizontal' ? activeDropdownItemStyles : dropdownItemStyles}
                >
                  <RectangleHorizontal size={16} className="mr-2" /> View Horizontal
                </button>
                <button
                  onClick={() => { setCurrentDisplayOrientation('vertical'); setIsActionsMenuOpen(false); setIsFlipped(false); }}
                  disabled={!frontVerticalImageUrl}
                  className={currentDisplayOrientation === 'vertical' ? activeDropdownItemStyles : dropdownItemStyles}
                >
                  <RectangleVertical size={16} className="mr-2" /> View Vertical
                </button>
                <div className="h-px bg-border my-1 mx-2"></div>
                <button
                  onClick={() => { handleShare(); setIsActionsMenuOpen(false); }}
                  disabled={isGenerating || !(frontHorizontalImageUrl || frontVerticalImageUrl) || !generatedExtendedId}
                  className={dropdownItemStyles}
                >
                  <Share2 size={16} className="mr-2" /> Share
                </button>
                <button
                  onClick={() => { handleCopyGeneratedUrl(); setIsActionsMenuOpen(false); }}
                  disabled={isGenerating || !generatedExtendedId}
                  className={dropdownItemStyles}
                >
                  <Link2 size={16} className="mr-2" /> Copy URL
                </button>
                <button
                  onClick={() => { handleDownloadImage(currentDisplayOrientation); setIsActionsMenuOpen(false); }}
                  disabled={isGenerating || (currentDisplayOrientation === 'horizontal' ? !frontHorizontalImageUrl : !frontVerticalImageUrl)}
                  className={dropdownItemStyles}
                >
                  <Download size={16} className="mr-2" /> {downloadButtonText()}
                </button>
              </div>
            )}
          </div>

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
        
        {(shareFeedback && !copyUrlFeedback) && (
          <p className="text-sm text-blue-700 mt-2 text-center h-5">{shareFeedback}</p>
        )}
        {copyUrlFeedback && (
          <p className="text-sm text-green-700 mt-2 text-center h-5">{copyUrlFeedback}</p>
        )}
      </div>
    </section>
  );
};

export default CardDisplay; 