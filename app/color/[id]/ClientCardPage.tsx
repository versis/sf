'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import CardDisplay from '@/components/CardDisplay';
import { useSwipeable, type SwipeableHandlers } from 'react-swipeable';
import { copyTextToClipboard } from '@/lib/clipboardUtils';
import { shareOrCopy } from '@/lib/shareUtils';
import { COPY_SUCCESS_MESSAGE } from '@/lib/constants';
import { ImagePlus } from 'lucide-react';

interface CardDetails {
  extendedId?: string;
  hexColor?: string;
  card_name?: string;
  status?: string;
  frontHorizontalImageUrl?: string;
  frontVerticalImageUrl?: string;
  noteText?: string;
  hasNote?: boolean;
  backHorizontalImageUrl?: string;
  backVerticalImageUrl?: string;
  aiName?: string;
  aiPhonetic?: string;
  aiArticle?: string;
  aiDescription?: string;
  createdAt?: string;
  updatedAt?: string;
  // New fields for EXIF data
  photoDate?: string;
  photoLocation?: string;
  metadata?: any;
}

interface ClientCardPageProps {
  cardData: CardDetails | null;
  cardId: string;
  loading?: boolean;
  error?: string | null;
  initialMobile?: boolean;
  initialOrientation?: 'horizontal' | 'vertical';
}

export default function ClientCardPage({ 
  cardData, 
  cardId, 
  loading = false, 
  error = null,
  initialMobile = false,
  initialOrientation = 'horizontal'
}: ClientCardPageProps) {
  const router = useRouter();
  const [isMobile, setIsMobile] = useState<boolean>(initialMobile);
  const [currentDisplayOrientation, setCurrentDisplayOrientation] = useState<'horizontal' | 'vertical'>(initialOrientation);
  const [shareFeedback, setShareFeedback] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [copyUrlFeedback, setCopyUrlFeedback] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const cardDisplaySectionRef = useRef<HTMLDivElement>(null);
  const [isFlipped, setIsFlipped] = useState(false);
  const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | null>(null);

  const handleFlip = () => {
    if (cardData?.hasNote === false || cardData?.backHorizontalImageUrl || cardData?.backVerticalImageUrl) {
      setIsFlipped(!isFlipped);
    }
  };

  const swipeableElementRef = useRef<HTMLDivElement>(null);

  // Get all handlers from useSwipeable, including its ref callback
  const allSwipeableHandlers: SwipeableHandlers = useSwipeable({
    onSwipedLeft: () => {
      setSwipeDirection('left');
      handleFlip();
    },
    onSwipedRight: () => {
      setSwipeDirection('right');
      handleFlip();
    },
    preventScrollOnSwipe: true,
    trackMouse: true,
  });

  // Separate the ref callback from the other event handlers
  const { ref: swipeableHookRef, ...eventHandlersToSpread } = allSwipeableHandlers;

  // Custom ref callback to assign the node to both our local ref and react-swipeable's ref
  const combinedRefCallback = (node: HTMLDivElement | null) => {
    if (typeof swipeableHookRef === 'function') {
      swipeableHookRef(node);
    }
    (swipeableElementRef as React.MutableRefObject<HTMLDivElement | null>).current = node;
  };
  
  // Detect if user is on mobile for initial orientation
  useEffect(() => {
    const checkIfMobile = () => {
      const newIsMobile = window.innerWidth < 768;
      // Only update if different from server detection to avoid unnecessary re-renders
      if (newIsMobile !== isMobile) {
        setIsMobile(newIsMobile);
      }
    };
    
    checkIfMobile();
    window.addEventListener('resize', checkIfMobile);
    return () => window.removeEventListener('resize', checkIfMobile);
  }, [isMobile]);

  // Set initial orientation when card data loads or mobile state changes
  useEffect(() => {
    if (cardData) {
      let newOrientation: 'horizontal' | 'vertical';
      if (isMobile && cardData.frontVerticalImageUrl) {
        newOrientation = 'vertical';
      } else if (cardData.frontHorizontalImageUrl) {
        newOrientation = 'horizontal';
      } else if (cardData.frontVerticalImageUrl) {
        newOrientation = 'vertical';
      } else {
        newOrientation = 'horizontal'; // Default
      }
      
      // Only update if orientation actually needs to change
      if (newOrientation !== currentDisplayOrientation) {
        setCurrentDisplayOrientation(newOrientation);
      }
    }
  }, [cardData, isMobile, currentDisplayOrientation]);

  // handleDownload function to be passed to CardDisplay
  const handleDownloadImage = (orientation: 'vertical' | 'horizontal') => {
    const imageUrl = orientation === 'horizontal' 
      ? cardData?.frontHorizontalImageUrl 
      : cardData?.frontVerticalImageUrl;
    
    if (!imageUrl || !cardData) return;

    const filename = `shadefreude-${orientation}-${cardData.hexColor?.substring(1) || 'color'}-${cardData.card_name?.toLowerCase().replace(/\s+/g, '-') || 'card'}.png`;
    const downloadApiUrl = `/api/download-image?url=${encodeURIComponent(imageUrl)}&filename=${encodeURIComponent(filename)}`;
    window.location.href = downloadApiUrl;
  };

  // handleShare function to be passed to CardDisplay
  const handleShareAction = async () => {
    if (!cardId) {
        setShareFeedback({ message: 'Card ID not available for sharing.', type: 'error' });
        setTimeout(() => setShareFeedback(null), 3000);
        return;
    }
    const shareUrl = `https://sf.tinker.institute/color/${cardId}`;
    const shareData = {
      title: cardData?.card_name ? `shadefreude: ${cardData.card_name}` : 'shadefreude postcard',
      text: cardData?.card_name ? `Check out this shadefreude postcard: ${cardData.card_name}` : 'Check out this shadefreude postcard',
      url: shareUrl,
    };

    await shareOrCopy(shareData, shareUrl, {
      onShareSuccess: (message) => setShareFeedback({ message, type: 'success' }),
      onCopySuccess: (message) => setShareFeedback({ message, type: 'success' }),
      onShareError: (message) => setShareFeedback({ message, type: 'error' }),
      onCopyError: (message) => setShareFeedback({ message, type: 'error' }),
      shareSuccessMessage: "Your postcard sent successfully!",
      copySuccessMessage: "Postcard link copied! Go on, share it.",
      shareErrorMessage: "Sending postcard failed. Attempting to copy link.",
      copyErrorMessage: "Failed to copy postcard link."
    });
    setTimeout(() => setShareFeedback(null), 3000);
    setCopyUrlFeedback(null);
  };

  // handleCopyPageUrl function to be passed to CardDisplay as handleCopyGeneratedUrl
  const handleCopyLinkAction = async () => {
    if (!cardId) {
      setCopyUrlFeedback({ message: 'Cannot copy URL: Card ID missing.', type: 'error' });
      setTimeout(() => setCopyUrlFeedback(null), 3000);
      return;
    }
    const urlToCopy = window.location.href;
    await copyTextToClipboard(urlToCopy, {
        onSuccess: (message) => setCopyUrlFeedback({ message, type: 'success' }),
        onError: (message) => setCopyUrlFeedback({ message, type: 'error' }),
        successMessage: COPY_SUCCESS_MESSAGE,
        errorMessage: "Failed to copy postcard link."
    });
    setTimeout(() => setCopyUrlFeedback(null), 3000);
    setShareFeedback(null);
  };

  // New handler for the "Create New Card" button from CardDisplay
  const navigateToHome = () => {
    router.push('/?create=true');
  };

  if (loading) {
    return <div className="flex justify-center items-center min-h-screen">Loading card...</div>;
  }

  if (error) {
    return <div className="flex justify-center items-center min-h-screen text-red-500">Error: {error}</div>;
  }

  if (!cardData) {
    return <div className="flex justify-center items-center min-h-screen">Card not found.</div>;
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-start pt-1 px-6 pb-6 md:pt-3 md:px-12 md:pb-12 bg-background text-foreground">
      <div className="w-full max-w-6xl">
        <header className="py-6 border-b-2 border-foreground">
          <div className="flex items-center justify-between">
            {/* Logo on the left */}
            <div className="flex flex-col">
              <h1 className="text-2xl md:text-3xl font-bold flex items-center">
                <Link href="/" className="flex items-center cursor-pointer">
                  <span className="mr-1 ml-1">
                    <img src="/sf-icon.png" alt="SF Icon" className="inline h-5 w-5 md:h-6 md:w-6 mr-1" />
                    shade
                  </span>
                  <span className="inline-block bg-card text-foreground border-2 border-blue-700 shadow-[5px_5px_0_0_theme(colors.blue.700)] px-2 py-0.5 mr-1">
                    freude
                  </span>
                </Link>
              </h1>
            </div>
            
            {/* Create button on the right - centered with logo block */}
            <button
              onClick={navigateToHome}
              className="flex px-3 py-2 md:px-4 md:py-3 font-medium text-xs md:text-sm bg-black text-white border border-[#374151] shadow-[2px_2px_0_0_#374151] hover:shadow-[1px_1px_0_0_#374151] active:shadow-none active:translate-x-[1px] active:translate-y-[1px] transition-all duration-100 ease-in-out items-center justify-center ml-4"
            >
              <ImagePlus size={12} className="mr-1" />
              <span className="hidden md:inline">Create Your Postcard</span>
              <span className="md:hidden">Create</span>
            </button>
          </div>
        </header>
        
        {/* Use a flex container with explicit order to ensure consistent layout */}
        <div className="flex flex-col items-center w-full mt-6">
          <div 
            ref={combinedRefCallback}
            {...eventHandlersToSpread}
            className={`${isMobile ? 'w-10/12 mx-auto' : 'w-full'} flex flex-col items-center justify-center order-1 cursor-grab active:cursor-grabbing ${!isMobile && currentDisplayOrientation === 'vertical' ? 'md:max-w-xs lg:max-w-sm' : ''}`}
          >
            <CardDisplay
              isVisible={!loading && !error && !!cardData}
              frontHorizontalImageUrl={cardData?.frontHorizontalImageUrl || null}
              frontVerticalImageUrl={cardData?.frontVerticalImageUrl || null}
              backHorizontalImageUrl={cardData?.backHorizontalImageUrl || null}
              backVerticalImageUrl={cardData?.backVerticalImageUrl || null}
              noteText={cardData?.noteText || null}
              hasNote={cardData?.hasNote || false}
              isFlippable={true}
              isFlipped={isFlipped}
              onFlip={handleFlip}
              currentDisplayOrientation={currentDisplayOrientation}
              setCurrentDisplayOrientation={setCurrentDisplayOrientation}
              handleShare={handleShareAction} 
              handleCopyGeneratedUrl={handleCopyLinkAction}
              handleDownloadImage={handleDownloadImage}
              handleCreateNew={navigateToHome}
              isGenerating={false}
              generatedExtendedId={cardId}
              shareFeedback={shareFeedback}
              copyUrlFeedback={copyUrlFeedback}
              disableScrollOnLoad={true}
              swipeDirection={swipeDirection}
              hexColor={cardData?.hexColor}
              createdAt={cardData?.createdAt}
              isMobile={isMobile}
            />
          </div>

          {/* Text added below the CardDisplay component block, now with order-2 */}
          <div className="w-full text-center py-4 mt-4 md:mt-8 order-2">
            <p className="text-sm md:text-lg text-muted-foreground">
              Delivered by <i>shadefreude</i>,<br />
              <strong className="text-lg md:text-2xl">The Digital Postcard Service</strong>
            </p>
          </div>

        </div>
      </div>
    </main>
  );
} 