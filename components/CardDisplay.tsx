'use client';

import React, { useEffect } from 'react';

interface CardDisplayProps {
  generatedHorizontalImageUrl: string | null;
  generatedVerticalImageUrl: string | null;
  currentDisplayOrientation: 'horizontal' | 'vertical';
  setCurrentDisplayOrientation: (orientation: 'horizontal' | 'vertical') => void;
  handleShare: () => Promise<void>;
  handleCopyGeneratedUrl: () => Promise<void>;
  handleDownloadImage: (orientation: 'horizontal' | 'vertical') => void;
  resetWizard?: () => void;
  isGenerating: boolean;
  generatedExtendedId: string | null;
  cardDisplayControlsRef?: React.RefObject<HTMLDivElement>;
  shareFeedback?: string;
  copyUrlFeedback?: string;
  // Add a prop to control visibility, as the parent page might have slightly different logic
  isVisible: boolean;
}

const CardDisplay: React.FC<CardDisplayProps> = ({
  generatedHorizontalImageUrl,
  generatedVerticalImageUrl,
  currentDisplayOrientation,
  setCurrentDisplayOrientation,
  handleShare,
  handleCopyGeneratedUrl,
  handleDownloadImage,
  resetWizard,
  isGenerating,
  generatedExtendedId,
  cardDisplayControlsRef,
  shareFeedback,
  copyUrlFeedback,
  isVisible,
}) => {
  // Effect to scroll to controls when orientation changes and ref is available
  useEffect(() => {
    if (isVisible && cardDisplayControlsRef?.current) {
      // Slight delay to ensure the content is rendered and dimensions are stable
      // This might be needed if the image loading itself causes layout shifts
      // that weren't fully accounted for in the parent's preloading logic.
      setTimeout(() => {
        cardDisplayControlsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [currentDisplayOrientation, isVisible, cardDisplayControlsRef, generatedHorizontalImageUrl, generatedVerticalImageUrl]);


  if (!isVisible) {
    return null;
  }

  return (
    <section ref={cardDisplayControlsRef} className="w-full px-1 py-2 md:px-2 md:py-2 mt-0 flex flex-col items-center scroll-target-with-offset">
      <div className="space-y-6 flex flex-col items-center w-full max-w-2xl lg:max-w-4xl">
        <div className="flex justify-center gap-6 mb-4">
          <button
            onClick={() => setCurrentDisplayOrientation('horizontal')}
            className={`p-2 border-2 rounded-md ${currentDisplayOrientation === 'horizontal' ? 'border-blue-700 bg-blue-50' : 'border-gray-300 hover:bg-gray-50'} flex flex-col items-center transition-all duration-200`}
            title="Display Horizontal Card"
            disabled={!generatedHorizontalImageUrl}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="5" width="18" height="14" rx="2" ry="2" /></svg>
            <span className="text-xs mt-1">Horizontal</span>
          </button>
          <button
            onClick={() => setCurrentDisplayOrientation('vertical')}
            className={`p-2 border-2 rounded-md ${currentDisplayOrientation === 'vertical' ? 'border-blue-700 bg-blue-50' : 'border-gray-300 hover:bg-gray-50'} flex flex-col items-center transition-all duration-200`}
            title="Display Vertical Card"
            disabled={!generatedVerticalImageUrl}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="5" y="3" width="14" height="18" rx="2" ry="2" /></svg>
            <span className="text-xs mt-1">Vertical</span>
          </button>
        </div>

        <div className="flex justify-center w-full">
          {(currentDisplayOrientation === 'horizontal' && generatedHorizontalImageUrl) ? (
            <img src={generatedHorizontalImageUrl} alt="Generated horizontal card" className="max-w-full rounded-md md:max-w-2xl lg:max-w-4xl h-auto" />
          ) : (currentDisplayOrientation === 'vertical' && generatedVerticalImageUrl) ? (
            <img src={generatedVerticalImageUrl} alt="Generated vertical card" className="max-w-full rounded-md md:max-w-sm lg:max-w-md max-h-[70vh] sm:max-h-[80vh] h-auto" />
          ) : (
            <p className="text-muted-foreground py-10">Select an orientation to view your card.</p>
          )}
        </div>

        <div className="flex flex-col sm:flex-row justify-center items-center gap-4 mt-6 w-full">
          <button
            onClick={handleShare}
            disabled={isGenerating || !(generatedHorizontalImageUrl || generatedVerticalImageUrl) || !generatedExtendedId}
            className="w-full sm:w-auto px-4 py-2 md:px-6 md:py-3 bg-input text-foreground font-semibold border-2 border-foreground shadow-[4px_4px_0_0_theme(colors.foreground)] hover:shadow-[2px_2px_0_0_theme(colors.foreground)] active:shadow-[1px_1px_0_0_theme(colors.foreground)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center justify-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>
            Share
          </button>
          <button
            onClick={handleCopyGeneratedUrl}
            disabled={isGenerating || !generatedExtendedId}
            className="w-full sm:w-auto px-4 py-2 md:px-6 md:py-3 bg-input text-foreground font-semibold border-2 border-foreground shadow-[4px_4px_0_0_theme(colors.foreground)] hover:shadow-[2px_2px_0_0_theme(colors.foreground)] active:shadow-[1px_1px_0_0_theme(colors.foreground)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center justify-center gap-2 whitespace-nowrap"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2" /><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" /></svg>
            Copy URL
          </button>
          <button
            onClick={() => handleDownloadImage(currentDisplayOrientation)}
            disabled={isGenerating || (currentDisplayOrientation === 'horizontal' ? !generatedHorizontalImageUrl : !generatedVerticalImageUrl)}
            className="w-full sm:w-auto px-4 py-2 md:px-6 md:py-3 bg-input text-foreground font-semibold border-2 border-foreground shadow-[4px_4px_0_0_theme(colors.foreground)] hover:shadow-[2px_2px_0_0_theme(colors.foreground)] active:shadow-[1px_1px_0_0_theme(colors.foreground)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center justify-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Download
          </button>
        </div>
        {(shareFeedback && !copyUrlFeedback) && (
          <p className="text-sm text-blue-700 mt-2 text-center h-5">{shareFeedback}</p>
        )}
        {copyUrlFeedback && (
          <p className="text-sm text-green-700 mt-2 text-center h-5">{copyUrlFeedback}</p>
        )}
        
        {resetWizard && (
          <button
            onClick={resetWizard}
            className="mt-8 px-4 py-2 text-sm text-muted-foreground hover:text-foreground underline"
          >
            Create New Card
          </button>
        )}
      </div>
    </section>
  );
};

export default CardDisplay; 