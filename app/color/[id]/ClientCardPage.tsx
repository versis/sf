'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import CardDisplay from '@/components/CardDisplay';
import { useSwipeable, type SwipeableHandlers } from 'react-swipeable';
import { copyTextToClipboard } from '@/lib/clipboardUtils';
import { shareOrCopy } from '@/lib/shareUtils';
import { COPY_SUCCESS_MESSAGE } from '@/lib/constants';

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
}

export default function ClientCardPage({ cardData, cardId, loading = false, error = null }: ClientCardPageProps) {
  const router = useRouter();
  const [isMobile, setIsMobile] = useState<boolean>(false);
  const [currentDisplayOrientation, setCurrentDisplayOrientation] = useState<'horizontal' | 'vertical'>('horizontal');
  const [shareFeedback, setShareFeedback] = useState<string>('');
  const [copyUrlFeedback, setCopyUrlFeedback] = useState<string>('');
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
    const checkIfMobile = () => setIsMobile(window.innerWidth < 768);
    checkIfMobile();
    window.addEventListener('resize', checkIfMobile);
    return () => window.removeEventListener('resize', checkIfMobile);
  }, []);

  // Set initial orientation when card data loads
  useEffect(() => {
    if (cardData) {
      let initialOrientation: 'horizontal' | 'vertical';
      if (isMobile && cardData.frontVerticalImageUrl) {
        initialOrientation = 'vertical';
      } else if (cardData.frontHorizontalImageUrl) {
        initialOrientation = 'horizontal';
      } else if (cardData.frontVerticalImageUrl) {
        initialOrientation = 'vertical';
      } else {
        initialOrientation = 'horizontal'; // Default
      }
      setCurrentDisplayOrientation(initialOrientation);
    }
  }, [cardData, isMobile]);

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
        setShareFeedback('Card ID not available for sharing.');
        setTimeout(() => setShareFeedback(''), 3000);
        return;
    }
    const shareUrl = `https://sf.tinker.institute/color/${cardId}`;
    const shareData = {
      title: cardData?.card_name ? `shadefreude: ${cardData.card_name}` : 'shadefreude Color Card',
      url: shareUrl,
    };

    await shareOrCopy(shareData, shareUrl, {
      onShareSuccess: (message) => setShareFeedback(message),
      onCopySuccess: (message) => setShareFeedback(message),
      onShareError: (message) => setShareFeedback(message),
      onCopyError: (message) => setShareFeedback(message),
      copySuccessMessage: 'URL copied to clipboard!',
    });
    setTimeout(() => setShareFeedback(''), 3000);
    setCopyUrlFeedback('');
  };

  // handleCopyPageUrl function to be passed to CardDisplay as handleCopyGeneratedUrl
  const handleCopyLinkAction = async () => {
    if (!cardId) {
      setCopyUrlFeedback('Cannot copy URL: Card ID missing.');
      setTimeout(() => setCopyUrlFeedback(''), 3000);
      return;
    }
    const urlToCopy = window.location.href;
    await copyTextToClipboard(urlToCopy, {
        onSuccess: (message) => setCopyUrlFeedback(message),
        onError: (message) => setCopyUrlFeedback(message),
        successMessage: COPY_SUCCESS_MESSAGE,
    });
    setTimeout(() => setCopyUrlFeedback(''), 3000);
    setShareFeedback('');
  };

  // New handler for the "Create New Card" button from CardDisplay
  const navigateToHome = () => {
    router.push('/');
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
          <h1 className="text-4xl md:text-5xl font-bold text-center flex items-center justify-center">
            <Link href="/" className="flex items-center justify-center cursor-pointer">
              <span className="mr-1 ml-1">
                <img src="/sf-icon.png" alt="SF Icon" className="inline h-8 w-8 md:h-12 md:w-12 mr-1" />
                shade
              </span>
              <span className="inline-block bg-card text-foreground border-2 border-blue-700 shadow-[5px_5px_0_0_theme(colors.blue.700)] px-2 py-0.5 mr-1">
                freude
              </span>
            </Link>
          </h1>
          <p className="text-center text-sm text-muted-foreground mt-2">
            part of <a href="https://tinker.institute" target="_blank" rel="noopener noreferrer" className="underline hover:text-foreground">tinker.institute</a>
          </p>
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
          
          <hr className="w-full border-t-2 border-foreground my-6 order-3" />

          <div className="w-full order-4 mt-4">
            <div className="max-w-4xl mx-auto">
              <h3 className="text-xl font-semibold mb-3 text-left">
                First time here?
              </h3>

              <div className="text-md text-muted-foreground space-y-3">
                <p>
                  You&apos;re looking at an AI-crafted postcard from <i>shadefreude</i>&nbsp;
                  titled:&nbsp;
                  {cardData && (cardData.card_name || cardData.hexColor) && (
                    <span className="font-mono">
                      {cardData.card_name ? `${cardData.card_name} ` : ''}
                      {cardData.hexColor && `(${cardData.hexColor})`}
                    </span>
                  )}
                  .
                  <br />
                  It began with an everyday photo. A standout colour was tapped, our fine-tuned AI studied the scene, named the shade, and served a tiny story on the card. If there&apos;s a note on the back, that&apos;s the creator&apos;s personal
                  touch.
                </p>

                <p>
                  <Link href="/" className="underline hover:text-foreground">
                    Make your own AI postcard&nbsp;→
                  </Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
} 