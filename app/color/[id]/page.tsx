'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation'; // Added useRouter
import Link from 'next/link'; // Re-added Link import for the header
import CardDisplay from '@/components/CardDisplay'; // Import the new component
import { copyTextToClipboard } from '@/lib/clipboardUtils';
import { shareOrCopy } from '@/lib/shareUtils';
import { COPY_SUCCESS_MESSAGE } from '@/lib/constants';

interface CardDetails {
  extendedId?: string;
  hexColor?: string;
  card_name?: string;
  status?: string;
  front_horizontal_image_url?: string;
  front_vertical_image_url?: string;
  note_text?: string;
  has_note?: boolean;
  back_horizontal_image_url?: string;
  back_vertical_image_url?: string;
  ai_name?: string;
  ai_phonetic?: string;
  ai_article?: string;
  ai_description?: string;
  created_at?: string;
  updated_at?: string;
}

export default function ColorCardPage() {
  const params = useParams();
  const router = useRouter(); // Initialize router
  const idFromUrl = params && typeof params.id === 'string' ? params.id : null;

  const [id, setId] = useState<string | null>(null);
  const [cardDetails, setCardDetails] = useState<CardDetails | null>(null);
  const [loading, setLoading] = useState(true); // Start loading true
  const [error, setError] = useState<string | null>(null);
  const [isMobile, setIsMobile] = useState<boolean>(false);
  const [currentDisplayOrientation, setCurrentDisplayOrientation] = useState<'horizontal' | 'vertical'>('horizontal');
  const [shareFeedback, setShareFeedback] = useState<string>('');
  const [copyUrlFeedback, setCopyUrlFeedback] = useState<string>(''); // State for copy URL feedback
  const cardDisplaySectionRef = useRef<HTMLDivElement>(null); // Ref for scrolling to the card display

  // Detect if user is on mobile for initial orientation
  useEffect(() => {
    const checkIfMobile = () => setIsMobile(window.innerWidth < 768);
    checkIfMobile();
    window.addEventListener('resize', checkIfMobile);
    return () => window.removeEventListener('resize', checkIfMobile);
  }, []);

  // Effect to update 'id' state and reset dependent states when idFromUrl (from router) changes
  useEffect(() => {
    if (idFromUrl) {
      setId(idFromUrl);
      setCardDetails(null); // Clear previous card details
      setError(null);       // Clear previous error
      setLoading(true);     // Set loading for the new ID
    } else {
      // Handle case where idFromUrl is not valid (e.g., bad URL directly accessed)
      setId(null);
      setError("Invalid card ID in URL.");
      setLoading(false);
    }
  }, [idFromUrl]); // Depend only on idFromUrl from the router

  // Effect to fetch data when 'id' state is set and valid
  useEffect(() => {
    if (id && loading) {
      const fetchCardDetails = async () => {
        setLoading(true); // Ensure loading is true at the start of fetch
        try {
          const response = await fetch(`/api/retrieve-card-by-extended-id/${id}`);
          if (!response.ok) {
            let errorMsg = `Error fetching card details: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.detail || errorMsg;
            } catch (jsonError) { /* Stick with status error */ }
            throw new Error(errorMsg);
          }
          const data: CardDetails = await response.json();
          // CRUCIAL LOG: Inspect the raw data object here
          console.log("RAW DATA FROM API (response.json()):", JSON.stringify(data, null, 2)); 
          setCardDetails(data);
          
          let initialOrientation: 'horizontal' | 'vertical';
          if (isMobile && data.front_vertical_image_url) {
            initialOrientation = 'vertical';
          } else if (data.front_horizontal_image_url) {
            initialOrientation = 'horizontal';
          } else if (data.front_vertical_image_url) {
            initialOrientation = 'vertical';
          } else {
            initialOrientation = 'horizontal'; // Default
          }
          setCurrentDisplayOrientation(initialOrientation);
          setError(null);
          // Scroll to card display after data is loaded and orientation set
          // Ensure this happens after the DOM has a chance to update with the CardDisplay component
          // setTimeout(() => {
          //   cardDisplaySectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
          // }, 150); // Small delay - REMOVED

        } catch (err) {
          setError(err instanceof Error ? err.message : 'An unknown error occurred');
          setCardDetails(null);
        } finally {
            setLoading(false);
        }
      };
      fetchCardDetails();
    }
  }, [id, loading, isMobile]);

  // handleDownload function to be passed to CardDisplay
  const handleDownloadImage = (orientation: 'vertical' | 'horizontal') => {
    const imageUrl = orientation === 'horizontal' 
      ? cardDetails?.front_horizontal_image_url 
      : cardDetails?.front_vertical_image_url;
    
    if (!imageUrl || !cardDetails) return;

    const filename = `shadefreude-${orientation}-${cardDetails.hexColor?.substring(1) || 'color'}-${cardDetails.card_name?.toLowerCase().replace(/\s+/g, '-') || 'card'}.png`;
    const downloadApiUrl = `/api/download-image?url=${encodeURIComponent(imageUrl)}&filename=${encodeURIComponent(filename)}`;
    window.location.href = downloadApiUrl;
  };

  // handleShare function to be passed to CardDisplay
  const handleShareAction = async () => {
    if (!idFromUrl) {
        setShareFeedback('Card ID not available for sharing.');
        setTimeout(() => setShareFeedback(''), 3000);
        return;
    }
    const shareUrl = `https://sf.tinker.institute/color/${idFromUrl}`;
    const shareMessage = `Check this out. This is my own unique color card: ${shareUrl}`;
    const shareData = {
      title: cardDetails?.card_name ? `Shadefreude: ${cardDetails.card_name}` : 'Shadefreude Color Card',
      text: shareMessage,
      url: shareUrl,
    };

    await shareOrCopy(shareData, shareMessage, {
      onShareSuccess: (message) => setShareFeedback(message),
      onCopySuccess: (message) => setShareFeedback(message), // Use setShareFeedback for copy fallback as well
      onShareError: (message) => setShareFeedback(message),
      onCopyError: (message) => setShareFeedback(message),
      copySuccessMessage: 'Share message with link copied to clipboard!',
    });
    setTimeout(() => setShareFeedback(''), 3000);
    setCopyUrlFeedback(''); // Clear other feedback
  };

  // handleCopyPageUrl function to be passed to CardDisplay as handleCopyGeneratedUrl
  const handleCopyLinkAction = async () => {
    if (!idFromUrl) {
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
    setShareFeedback(''); // Clear other feedback
  };

  // New handler for the "Create New Card" button from CardDisplay
  const navigateToHome = () => {
    router.push('/');
  };

  if (!idFromUrl && !loading && !error) { // If idFromUrl is null and we are not in an initial loading/error state for it
    return <div className="flex justify-center items-center min-h-screen text-red-500">Invalid URL or Card ID.</div>;
  }

  if (loading) {
    return <div className="flex justify-center items-center min-h-screen">Loading card...</div>;
  }

  if (error) {
    return <div className="flex justify-center items-center min-h-screen text-red-500">Error: {error}</div>;
  }

  if (!cardDetails) {
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
          <div ref={cardDisplaySectionRef} className="w-full flex flex-col items-center justify-center order-1">
            <CardDisplay
              isVisible={!loading && !error && !!cardDetails}
              frontHorizontalImageUrl={cardDetails.front_horizontal_image_url || null}
              frontVerticalImageUrl={cardDetails.front_vertical_image_url || null}
              backHorizontalImageUrl={cardDetails.back_horizontal_image_url || null}
              backVerticalImageUrl={cardDetails.back_vertical_image_url || null}
              noteText={cardDetails.note_text || null}
              hasNote={cardDetails.has_note || false}
              isFlippable={true}
              currentDisplayOrientation={currentDisplayOrientation}
              setCurrentDisplayOrientation={setCurrentDisplayOrientation}
              handleShare={handleShareAction} 
              handleCopyGeneratedUrl={handleCopyLinkAction}
              handleDownloadImage={handleDownloadImage}
              handleCreateNew={navigateToHome}
              isGenerating={false}
              generatedExtendedId={id}
              shareFeedback={shareFeedback}
              copyUrlFeedback={copyUrlFeedback}
              disableScrollOnLoad={true}
            />
          </div>
          
          <hr className="w-full border-t-2 border-foreground my-6 order-3" />

          <div className="w-full order-4 mt-4">
            <div className="max-w-4xl mx-auto">
              <h3 className="text-xl font-semibold mb-3 text-left">What is it?</h3>
              <div className="text-md text-muted-foreground space-y-3">
                <p>
                  You&apos;ve landed on a unique shadefreude creation
                  {cardDetails && (cardDetails.card_name || cardDetails.hexColor) && (
                    <span className="font-mono text-xs">
                      {' '}({cardDetails.card_name ? `${cardDetails.card_name}, ` : ''}{cardDetails.hexColor || 'N/A'})
                    </span>
                  )}
                  , where a color from a personal photo has been given its own AI-crafted name and poetic tale. Discover its unique voice, then see what stories your own colors might tell!
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
} 