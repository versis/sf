'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import { copyTextToClipboard } from '@/lib/clipboardUtils';
import CardDisplay from '@/components/CardDisplay';

interface Generation {
  id: number;
  extended_id: string | null; // Kept in interface for data integrity, but not displayed
  hex_color: string; // Kept in interface, not displayed
  status: string; // Kept in interface, not displayed
  metadata: any | null; 
  front_horizontal_image_url: string | null;
  front_vertical_image_url: string | null;
  back_horizontal_image_url: string | null;
  back_vertical_image_url: string | null;
  note_text: string | null;
  has_note: boolean | null;
  created_at: string | null; 
  updated_at: string | null;
}

const ITEMS_PER_PAGE = 30;

// Type for individual item orientation preferences
interface ItemOrientations {
  [key: number]: 'horizontal' | 'vertical';
}

// Type for individual item flipped states
interface ItemFlippedStates {
  [key: number]: boolean;
}

// SVG Icons for buttons
const IconHorizontal = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 mr-1.5 flex-shrink-0">
    <path d="M21 6H3C2.45 6 2 6.45 2 7V17C2 17.55 2.45 18 3 18H21C21.55 18 22 17.55 22 17V7C22 6.45 21.55 6 21 6ZM20 16H4V8H20V16Z"></path>
  </svg>
);

const IconVertical = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 mr-1.5 flex-shrink-0">
    <path d="M18 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V4C20 2.9 19.1 2 18 2ZM18 20H6V4H18V20Z"></path>
  </svg>
);

const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}`;
};

export default function ReviewPage() {
  const [generations, setGenerations] = useState<Generation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const observer = useRef<IntersectionObserver | null>(null);
  const [itemOrientations, setItemOrientations] = useState<ItemOrientations>({});
  const [itemFlippedStates, setItemFlippedStates] = useState<ItemFlippedStates>({});
  const [copyIdFeedback, setCopyIdFeedback] = useState<{ id: number | null; message: string }>({ id: null, message: '' });

  const fetchGenerations = useCallback(async (currentOffset: number) => {
    if (isLoading || !hasMore) return;
    setIsLoading(true);
    try {
      const response = await fetch(`/api/generations?limit=${ITEMS_PER_PAGE}&offset=${currentOffset}`);
      if (!response.ok) {
        throw new Error('Failed to fetch generations');
      }
      const newGenerations: Generation[] = await response.json();
      
      setGenerations(prev => [...prev, ...newGenerations]);
      setOffset(prevOffset => prevOffset + newGenerations.length);
      setHasMore(newGenerations.length === ITEMS_PER_PAGE);

      const newOrientations: ItemOrientations = {};
      const newFlippedStates: ItemFlippedStates = {};
      newGenerations.forEach(gen => {
        // Default orientation logic: prefer horizontal, then vertical.
        if (gen.front_horizontal_image_url) {
          newOrientations[gen.id] = 'horizontal';
        } else if (gen.front_vertical_image_url) {
          newOrientations[gen.id] = 'vertical';
        } else {
          // If neither front image is available, default to horizontal
          // CardDisplay will show a placeholder if the preferred image is missing.
          newOrientations[gen.id] = 'horizontal'; 
        }
        newFlippedStates[gen.id] = false; 
      });
      setItemOrientations(prev => ({ ...prev, ...newOrientations }));
      setItemFlippedStates(prev => ({ ...prev, ...newFlippedStates }));

    } catch (error) {
      console.error('Error fetching generations:', error);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, hasMore]);

  useEffect(() => {
    fetchGenerations(0);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); 

  const lastElementRef = useCallback((node: HTMLElement | null) => {
    if (isLoading) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        fetchGenerations(offset);
      }
    });
    if (node) observer.current.observe(node);
  }, [isLoading, hasMore, fetchGenerations, offset]);

  const handleOrientationChange = (id: number, orientation: 'horizontal' | 'vertical') => {
    setItemOrientations(prev => ({
      ...prev,
      [id]: orientation
    }));
    // When orientation changes, ensure we are showing the front of the card
    setItemFlippedStates(prev => ({ ...prev, [id]: false }));
  };

  const handleCardClick = (id: number) => {
    setItemFlippedStates(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const getButtonClasses = (isActive: boolean, isDisabled: boolean) => {
    const baseClasses = "flex items-center justify-center p-2 rounded border text-sm transition-colors duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-300";

    if (isDisabled) {
      return `${baseClasses} bg-gray-100 text-gray-400 border-gray-300 cursor-not-allowed opacity-75`;
    }

    if (isActive) {
      // Active button style based on the image provided (blue border, light blue background)
      return `${baseClasses} bg-blue-50 text-blue-700 border-2 border-blue-600 hover:bg-blue-100`;
    }
    
    // Inactive button style (light gray border, white background)
    return `${baseClasses} bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400`;
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6 text-center md:text-left">Review Generations</h1>
      
      {generations.length === 0 && !isLoading && (
        <p className="text-center text-gray-500">No generations found.</p>
      )}
      <div>
        {generations.map((gen, index) => {
          const currentOrientation = itemOrientations[gen.id] || 'horizontal'; // Default to horizontal if not set
          const isFlipped = itemFlippedStates[gen.id] || false;

          // Dummy handlers for CardDisplay props not used in this list view
          const dummyShare = async () => console.log("Share action from review page");
          const dummyCopyUrl = async () => console.log("Copy URL action from review page");
          const dummyDownload = () => console.log("Download action from review page");

          const itemContent = (
            <article 
              key={gen.id} 
              className="py-6"
              ref={index === generations.length - 1 ? lastElementRef : null}
            >
              <div className="flex flex-col md:flex-row md:items-start">
                
                <div className="w-full md:order-2 flex-grow mb-6 md:mb-0 md:ml-10">
                  <p className="mb-3 text-sm text-gray-600">
                    <span className="font-semibold">{offset - generations.length + index + 1}.</span> Created: {formatDate(gen.created_at)}
                  </p>
                  
                  <div className="flex space-x-3 mb-2">
                    <button 
                      onClick={() => handleOrientationChange(gen.id, 'horizontal')} 
                      disabled={!gen.front_horizontal_image_url && !gen.back_horizontal_image_url}
                      className={getButtonClasses(currentOrientation === 'horizontal', !gen.front_horizontal_image_url && !gen.back_horizontal_image_url)}>
                      <IconHorizontal />
                      Horizontal
                    </button>
                    <button 
                      onClick={() => handleOrientationChange(gen.id, 'vertical')} 
                      disabled={!gen.front_vertical_image_url && !gen.back_vertical_image_url}
                      className={getButtonClasses(currentOrientation === 'vertical', !gen.front_vertical_image_url && !gen.back_vertical_image_url)}>
                      <IconVertical />
                      Vertical
                    </button>
                  </div>

                  {gen.extended_id && (
                    <div className="mt-3 space-y-2">
                      <div>
                        <span className="text-sm font-medium text-gray-700">Card ID: </span>
                        <span className="text-sm text-gray-600 font-mono mr-2">{gen.extended_id}</span>
                        <button 
                          onClick={async () => {
                            await copyTextToClipboard(gen.extended_id!, {
                              onSuccess: (msg) => setCopyIdFeedback({ id: gen.id, message: msg }),
                              onError: (msg) => setCopyIdFeedback({ id: gen.id, message: msg }),
                            });
                            setTimeout(() => setCopyIdFeedback({ id: null, message: '' }), 2000);
                          }}
                          className="text-xs text-blue-600 hover:text-blue-800 underline focus:outline-none"
                        >
                          Copy ID
                        </button>
                        {copyIdFeedback.id === gen.id && copyIdFeedback.message && (
                          <span className="ml-2 text-xs text-blue-600">{copyIdFeedback.message}</span>
                        )}
                      </div>
                      <div>
                        <Link href={`/color/${gen.extended_id.replace(/\s+/g, '-').toLowerCase()}`} legacyBehavior>
                          <a className="text-sm text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">
                            View Full Card Details
                          </a>
                        </Link>
                      </div>
                    </div>
                  )}
                </div>

                <div className="w-full md:order-1 md:w-1/2 lg:w-2/5 flex-shrink-0">
                  <CardDisplay
                    frontHorizontalImageUrl={gen.front_horizontal_image_url}
                    frontVerticalImageUrl={gen.front_vertical_image_url}
                    backHorizontalImageUrl={gen.back_horizontal_image_url}
                    backVerticalImageUrl={gen.back_vertical_image_url}
                    noteText={gen.note_text}
                    hasNote={gen.has_note}
                    isFlippable={true}
                    isFlipped={isFlipped}
                    onFlip={() => handleCardClick(gen.id)}
                    currentDisplayOrientation={currentOrientation}
                    setCurrentDisplayOrientation={(orientation) => handleOrientationChange(gen.id, orientation)}
                    // Pass dummy or no-op handlers for actions not relevant in list view
                    handleShare={dummyShare}
                    handleCopyGeneratedUrl={dummyCopyUrl}
                    handleDownloadImage={dummyDownload}
                    isGenerating={false} 
                    generatedExtendedId={gen.extended_id}
                    isVisible={true}
                    disableScrollOnLoad={true} // Prevent CardDisplay's own scroll effect
                    // hexColor and createdAt could be passed if CardDisplay uses them on the back for non-note cards
                    hexColor={gen.hex_color}
                    createdAt={gen.created_at}
                  />
                </div>

              </div>
            </article>
          );
          return (
            <React.Fragment key={gen.id}>
              {itemContent}
              {index < generations.length - 1 && <hr className="w-full border-t-2 border-foreground my-6" />}
            </React.Fragment>
          );
        })}
      </div>
      {isLoading && (
        <div className="text-center py-10">
          <p className="text-gray-500">Loading more generations...</p>
        </div>
      )}
      {!hasMore && generations.length > 0 && (
         <div className="text-center py-10">
          <p className="text-gray-500">You&apos;ve reached the end!</p>
        </div>
      )}
    </div>
  );
} 