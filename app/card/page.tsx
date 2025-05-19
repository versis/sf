'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

// Dynamic metadata for this page will be handled by the root layout
// since this is a client component and can't export metadata directly

export default function CardPage() {
  const [orientation, setOrientation] = useState<'horizontal' | 'vertical'>('horizontal');
  const [hexColor, setHexColor] = useState<string>('#000000');
  const [colorName, setColorName] = useState<string>('');
  const [cardUrl, setCardUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMobile, setIsMobile] = useState<boolean>(false);
  
  // Detect if user is on mobile
  useEffect(() => {
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkIfMobile();
    window.addEventListener('resize', checkIfMobile);
    
    return () => {
      window.removeEventListener('resize', checkIfMobile);
    };
  }, []);
  
  useEffect(() => {
    // Parse URL parameters
    const searchParams = new URLSearchParams(window.location.search);
    const orientationParam = searchParams.get('orientation') as 'horizontal' | 'vertical';
    const colorParam = searchParams.get('color');
    const colorNameParam = searchParams.get('colorName');
    
    // Set orientation based on device type
    const preferredOrientation = isMobile ? 'vertical' : 'horizontal';
    setOrientation(preferredOrientation);
    
    if (colorParam) {
      setHexColor(colorParam);
    }
    
    if (colorNameParam) {
      setColorName(colorNameParam);
    }
    
    // Try to get card URLs from sessionStorage
    const horizontalUrl = sessionStorage.getItem('horizontalCardUrl');
    const verticalUrl = sessionStorage.getItem('verticalCardUrl');
    
    if ((preferredOrientation === 'horizontal' && horizontalUrl) || 
        (preferredOrientation === 'vertical' && verticalUrl)) {
      setCardUrl(preferredOrientation === 'horizontal' ? horizontalUrl : verticalUrl);
      setLoading(false);
    } else {
      // Fallback: Use API endpoint to get or generate the card
      fetchCardFromApi(preferredOrientation, colorParam);
    }
  }, [isMobile]);

  // Add a new effect to handle orientation changes
  useEffect(() => {
    const horizontalUrl = sessionStorage.getItem('horizontalCardUrl');
    const verticalUrl = sessionStorage.getItem('verticalCardUrl');
    
    if (orientation === 'horizontal' && horizontalUrl) {
      setCardUrl(horizontalUrl);
    } else if (orientation === 'vertical' && verticalUrl) {
      setCardUrl(verticalUrl);
    } else {
      fetchCardFromApi(orientation, hexColor);
    }
  }, [orientation, hexColor]);
  
  const fetchCardFromApi = async (orientationParam: string | null, colorParam: string | null) => {
    try {
      setLoading(true);
      
      // Use URL from query params or construct a fetch for the server-stored image
      const imageUrl = `${window.location.origin}/api/get-card?orientation=${orientationParam}&color=${encodeURIComponent(colorParam || '#000000')}`;
      
      setCardUrl(imageUrl);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching card:', err);
      setError('Failed to load the card. Please try again.');
      setLoading(false);
    }
  };
  
  const handleDownload = () => {
    if (!cardUrl) return;
    
    const link = document.createElement('a');
    link.href = cardUrl;
    link.download = `shadefreude-${orientation}-${colorName.toLowerCase().replace(/\s+/g, '-')}-${new Date().getTime()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
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
        
        <div className="mt-6 text-center text-sm text-muted-foreground">
          <p>A personalized color card created with shadefreude - capturing the perfect hue from your image.</p>
          <p>Use it for inspiration, color matching, or as a reference for your design projects.</p>
        </div>

        <hr className="my-8 border-t-2 border-foreground w-full" />
        
        <div className="mt-8 flex flex-col items-center justify-center">
          {loading ? (
            <div className="p-8 text-center">
              <p>Loading card...</p>
            </div>
          ) : error ? (
            <div className="p-8 text-center text-red-500">
              <p>{error}</p>
              <Link href="/" className="mt-4 underline text-blue-700">
                Return to card creator
              </Link>
            </div>
          ) : (
            <>
              <div className="flex justify-center gap-6 mb-4">
                <button 
                  onClick={() => setOrientation('horizontal')}
                  className={`p-2 border-2 rounded-md ${orientation === 'horizontal' ? 'border-blue-700 bg-blue-50' : 'border-gray-300 hover:bg-gray-50'} flex flex-col items-center transition-all duration-200`}
                  title="Display Horizontal Card"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="5" width="18" height="14" rx="2" ry="2" /></svg>
                  <span className="text-xs mt-1">Horizontal</span>
                </button>
                <button
                  onClick={() => setOrientation('vertical')}
                  className={`p-2 border-2 rounded-md ${orientation === 'vertical' ? 'border-blue-700 bg-blue-50' : 'border-gray-300 hover:bg-gray-50'} flex flex-col items-center transition-all duration-200`}
                  title="Display Vertical Card"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="5" y="3" width="14" height="18" rx="2" ry="2" /></svg>
                  <span className="text-xs mt-1">Vertical</span>
                </button>
              </div>
              
              <div className="flex justify-center w-full">
                {cardUrl && (
                  <img 
                    src={cardUrl} 
                    alt={`${colorName} color card`} 
                    className={`max-w-full rounded-md ${orientation === 'horizontal' ? 'md:max-w-2xl' : 'md:max-w-sm max-h-[80vh]'} h-auto`} 
                  />
                )}
              </div>
              
              <div className="flex flex-col md:flex-row justify-center gap-3 md:gap-4 mt-8 w-full max-w-sm md:max-w-none px-4 md:px-0">
                <button
                  onClick={handleDownload}
                  className="w-full md:w-auto px-4 py-2 md:px-6 md:py-3 bg-input text-foreground font-semibold border-2 border-foreground shadow-[4px_4px_0_0_theme(colors.foreground)] hover:shadow-[2px_2px_0_0_theme(colors.foreground)] active:shadow-[1px_1px_0_0_theme(colors.foreground)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center justify-center gap-2"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                  Download
                </button>
                <button
                  onClick={() => {
                    // Try using the Web Share API if available (mobile devices)
                    const shareUrl = window.location.href;
                    if (navigator.share) {
                      navigator.share({
                        title: `${colorName} - Shadefreude Color Card`,
                        text: 'Check out this color card I created with shadefreude!',
                        url: shareUrl
                      })
                      .catch(err => {
                        console.error('Error sharing:', err);
                      });
                    } else {
                      // Copy to clipboard on desktop
                      navigator.clipboard.writeText(shareUrl)
                        .then(() => {
                          alert('Share link copied to clipboard!');
                        })
                        .catch(err => {
                          console.error('Failed to copy:', err);
                        });
                    }
                  }}
                  className="w-full md:w-auto px-4 py-2 md:px-6 md:py-3 bg-input text-foreground font-semibold border-2 border-foreground shadow-[4px_4px_0_0_theme(colors.foreground)] hover:shadow-[2px_2px_0_0_theme(colors.foreground)] active:shadow-[1px_1px_0_0_theme(colors.foreground)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center justify-center gap-2"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
                  Share
                </button>
                <Link
                  href="/"
                  className="w-full md:w-auto px-4 py-2 md:px-6 md:py-3 bg-input text-blue-700 font-semibold border-2 border-blue-700 shadow-[4px_4px_0_0_theme(colors.blue.700)] hover:shadow-[2px_2px_0_0_theme(colors.blue.700)] active:shadow-[1px_1px_0_0_theme(colors.blue.700)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center justify-center gap-2"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                  Create Your Own Unique Card
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
} 