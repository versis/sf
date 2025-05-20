'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation'; // Correct hook for App Router
import Link from 'next/link'; // Added Link for navigation

interface CardDetails {
  // Define structure based on what your API will return
  extendedId?: string;
  hexColor?: string;
  colorName?: string;
  description?: string;
  phoneticName?: string;
  article?: string;
  horizontalImageUrl?: string;
  verticalImageUrl?: string;
  // Add other fields as necessary
}

export default function ColorCardPage() {
  const params = useParams();
  const idFromUrl = params && typeof params.id === 'string' ? params.id : null;

  const [id, setId] = useState<string | null>(null);
  const [cardDetails, setCardDetails] = useState<CardDetails | null>(null);
  const [loading, setLoading] = useState(true); // Start loading true
  const [error, setError] = useState<string | null>(null);
  const [isMobile, setIsMobile] = useState<boolean>(false);
  const [currentDisplayOrientation, setCurrentDisplayOrientation] = useState<'horizontal' | 'vertical'>('horizontal');
  const [shareFeedback, setShareFeedback] = useState<string>('');
  const [copyUrlFeedback, setCopyUrlFeedback] = useState<string>(''); // State for copy URL feedback

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
          // Set initial orientation after data is fetched
          if (isMobile && data.verticalImageUrl) {
            setCurrentDisplayOrientation('vertical');
          } else if (data.horizontalImageUrl) {
            setCurrentDisplayOrientation('horizontal');
          } else if (data.verticalImageUrl) { // Fallback if only vertical
            setCurrentDisplayOrientation('vertical');
          }
          setError(null);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'An unknown error occurred');
          setCardDetails(null);
        }
        setLoading(false);
      };
      fetchCardDetails();
    }
  }, [id, loading, isMobile]);

  const handleDownload = () => {
    const imageUrl = currentDisplayOrientation === 'horizontal' 
      ? cardDetails?.horizontalImageUrl 
      : cardDetails?.verticalImageUrl;
    
    if (!imageUrl || !cardDetails) return;

    const filename = `shadefreude-${currentDisplayOrientation}-${cardDetails.hexColor?.substring(1) || 'color'}-${cardDetails.colorName?.toLowerCase().replace(/\s+/g, '-') || 'card'}.png`;
    
    // Use the new API endpoint for robust downloads
    const downloadApiUrl = `/api/download-image?url=${encodeURIComponent(imageUrl)}&filename=${encodeURIComponent(filename)}`;
    window.location.href = downloadApiUrl;
  };

 const handleShare = async () => {
    if (!idFromUrl) {
        setShareFeedback('Card ID not available for sharing.');
        setTimeout(() => setShareFeedback(''), 3000);
        return;
    }
    const shareUrl = `https://sf.tinker.institute/color/${idFromUrl}`; // Use the clean URL
    const shareMessage = `Check this out. This is my own unique color card: ${shareUrl}`;

    const shareData = {
      title: cardDetails?.colorName ? `Shadefreude: ${cardDetails.colorName}` : 'Shadefreude Color Card',
      text: shareMessage,
      url: shareUrl,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
        setShareFeedback('Shared successfully!');
      } else {
        await navigator.clipboard.writeText(shareMessage);
        setShareFeedback('Share message with link copied to clipboard!');
      }
    } catch (err) {
      console.error('Share/Copy failed:', err);
      setShareFeedback('Failed to share or copy link.');
    } finally {
      setTimeout(() => setShareFeedback(''), 3000);
      setCopyUrlFeedback(''); // Clear copy feedback if share is used
    }
  };

  const handleCopyPageUrl = async () => {
    if (!idFromUrl) {
      setCopyUrlFeedback('Cannot copy URL: Card ID missing.');
      setTimeout(() => setCopyUrlFeedback(''), 3000);
      return;
    }
    const urlToCopy = window.location.href; // This page's URL is the nice URL
    try {
      await navigator.clipboard.writeText(urlToCopy);
      setCopyUrlFeedback('Page URL copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy page URL:', err);
      setCopyUrlFeedback('Failed to copy URL.');
    }
    setTimeout(() => setCopyUrlFeedback(''), 3000);
    setShareFeedback(''); // Clear share feedback if copy is used
  };

  if (!idFromUrl) { // Initial check before first useEffect sets 'id' or error
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

  const currentImageUrl = currentDisplayOrientation === 'horizontal' 
    ? cardDetails?.horizontalImageUrl
    : cardDetails?.verticalImageUrl;

  return (
    <main className="flex min-h-screen flex-col items-center justify-start pt-1 px-6 pb-6 md:pt-3 md:px-12 md:pb-12 bg-background text-foreground">
      <div className="w-full max-w-4xl">
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
        
        <div className="mt-6">
          <div className="text-md text-muted-foreground max-w-xl mx-auto mt-4 space-y-3">
            <p>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. 
              Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
            </p>
          </div>
        </div>

        <hr className="my-8 border-t-2 border-foreground w-full" />
        
        <div className="mt-2 flex flex-col items-center justify-center">
          <div className="flex justify-center gap-6 mb-4">
            <button 
              onClick={() => setCurrentDisplayOrientation('horizontal')}
              className={`p-2 border-2 rounded-md ${currentDisplayOrientation === 'horizontal' ? 'border-blue-700 bg-blue-50' : 'border-gray-300 hover:bg-gray-50'} flex flex-col items-center transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed`}
              title="Display Horizontal Card"
              disabled={!cardDetails.horizontalImageUrl}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="5" width="18" height="14" rx="2" ry="2" /></svg>
              <span className="text-xs mt-1">Horizontal</span>
            </button>
            <button
              onClick={() => setCurrentDisplayOrientation('vertical')}
              className={`p-2 border-2 rounded-md ${currentDisplayOrientation === 'vertical' ? 'border-blue-700 bg-blue-50' : 'border-gray-300 hover:bg-gray-50'} flex flex-col items-center transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed`}
              title="Display Vertical Card"
              disabled={!cardDetails.verticalImageUrl}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="5" y="3" width="14" height="18" rx="2" ry="2" /></svg>
              <span className="text-xs mt-1">Vertical</span>
            </button>
          </div>
          
          <div className="flex justify-center w-full min-h-[300px]">
            {cardDetails && currentImageUrl ? (
              <img 
                src={currentImageUrl} 
                alt={`${cardDetails.colorName || 'Color'} card - ${currentDisplayOrientation}`}
                className={`max-w-full rounded-md ${currentDisplayOrientation === 'horizontal' ? 'md:max-w-2xl lg:max-w-4xl' : 'md:max-w-2xl max-h-[80vh]'} h-auto`}
              />
            ) : cardDetails ? (
              <div className="text-muted-foreground flex items-center justify-center">
                Image not available for this orientation. (Debug: H:{cardDetails.horizontalImageUrl ? '✓' : '✗'}, V:{cardDetails.verticalImageUrl ? '✓' : '✗'}, Orientation: {currentDisplayOrientation})
              </div>
            ) : (
              <div className="text-muted-foreground flex items-center justify-center">Preparing image display... (No cardDetails yet)</div>
            )}
          </div>
          
          <div className="flex flex-col md:flex-row justify-center gap-3 md:gap-4 mt-8 w-full max-w-sm md:max-w-md">
            <button
              onClick={handleShare}
              disabled={!idFromUrl}
              className="w-full md:w-auto px-4 py-2 md:px-6 md:py-3 bg-input text-foreground font-semibold border-2 border-foreground shadow-[4px_4px_0_0_theme(colors.foreground)] hover:shadow-[2px_2px_0_0_theme(colors.foreground)] active:shadow-[1px_1px_0_0_theme(colors.foreground)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
              Share
            </button>
            <button
              onClick={handleCopyPageUrl}
              disabled={!idFromUrl}
              className="w-full md:w-auto px-4 py-2 md:px-6 md:py-3 bg-input text-foreground font-semibold border-2 border-foreground shadow-[4px_4px_0_0_theme(colors.foreground)] hover:shadow-[2px_2px_0_0_theme(colors.foreground)] active:shadow-[1px_1px_0_0_theme(colors.foreground)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none whitespace-nowrap"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2" /><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" /></svg>
              Copy URL
            </button>
            <button
              onClick={handleDownload}
              disabled={!currentImageUrl}
              className="w-full md:w-auto px-4 py-2 md:px-6 md:py-3 bg-input text-foreground font-semibold border-2 border-foreground shadow-[4px_4px_0_0_theme(colors.foreground)] hover:shadow-[2px_2px_0_0_theme(colors.foreground)] active:shadow-[1px_1px_0_0_theme(colors.foreground)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Download
            </button>
          </div>
           {shareFeedback && !copyUrlFeedback && (
             <p className="text-sm text-blue-700 mt-4 text-center h-5">{shareFeedback}</p>
           )}
           {copyUrlFeedback && (
             <p className="text-sm text-green-700 mt-4 text-center h-5">{copyUrlFeedback}</p> // Different color for copy feedback
           )}

          <Link
            href="/"
            className="mt-10 text-blue-700 font-semibold hover:underline flex items-center justify-center gap-2"
          >
             <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            Create Your Own Unique Card
          </Link>
        </div>
      </div>
    </main>
  );
} 