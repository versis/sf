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

// Type for individual item flipped states
interface ItemFlippedStates {
  [key: number]: boolean;
}

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

      const newFlippedStates: ItemFlippedStates = {};
      newGenerations.forEach(gen => {
        newFlippedStates[gen.id] = false; 
      });
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

  const handleCardClick = (id: number) => {
    setItemFlippedStates(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6 text-center md:text-left">Review Generations</h1>
      
      {generations.length === 0 && !isLoading && (
        <p className="text-center text-gray-500">No generations found.</p>
      )}
      <div>
        {generations.map((gen, index) => {
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
                  
                  {gen.extended_id && (
                    <div className="mt-3 space-y-2">
                      <div>
                        <span className="text-sm font-medium text-gray-700">Postcard ID: </span>
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
                            View Full Postcard Details
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
                    currentDisplayOrientation={"horizontal"} // Default to horizontal, CardDisplay will handle its own state
                    setCurrentDisplayOrientation={() => {}} // No-op since CardDisplay handles this
                    // Pass dummy or no-op handlers for actions not relevant in list view
                    handleShare={dummyShare}
                    handleCopyGeneratedUrl={dummyCopyUrl}
                    handleDownloadImage={dummyDownload}
                    isGenerating={false} 
                    generatedExtendedId={gen.extended_id}
                    isVisible={true}
                    disableScrollOnLoad={true} // Prevent CardDisplay's own scroll effect
                    // hexColor and createdAt could be passed if CardDisplay uses them on the back for non-note postcards
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