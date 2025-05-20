'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';

interface Generation {
  id: number;
  extended_id: string | null; // Kept in interface for data integrity, but not displayed
  hex_color: string; // Kept in interface, not displayed
  status: string; // Kept in interface, not displayed
  metadata: any | null; 
  horizontal_image_url: string | null;
  vertical_image_url: string | null;
  created_at: string | null; 
  updated_at: string | null;
}

const ITEMS_PER_PAGE = 30;

// Type for individual item orientation preferences
interface ItemOrientations {
  [key: number]: 'horizontal' | 'vertical';
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

      // Initialize orientation for new items (default to horizontal if available, else vertical)
      const newOrientations: ItemOrientations = {};
      newGenerations.forEach(gen => {
        if (gen.horizontal_image_url) {
          newOrientations[gen.id] = 'horizontal';
        } else if (gen.vertical_image_url) {
          newOrientations[gen.id] = 'vertical';
        } 
        // If neither, it won't be set, and buttons will be disabled / no image shown
      });
      setItemOrientations(prev => ({ ...prev, ...newOrientations }));

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
          const currentOrientation = itemOrientations[gen.id];
          let imageUrlToShow: string | null = null;
          let altText = '';

          if (currentOrientation === 'horizontal' && gen.horizontal_image_url) {
            imageUrlToShow = gen.horizontal_image_url;
            altText = `Horizontal ${gen.extended_id || gen.id}`;
          } else if (currentOrientation === 'vertical' && gen.vertical_image_url) {
            imageUrlToShow = gen.vertical_image_url;
            altText = `Vertical ${gen.extended_id || gen.id}`;
          } else if (gen.horizontal_image_url) {
            imageUrlToShow = gen.horizontal_image_url;
            altText = `Horizontal (fallback) ${gen.extended_id || gen.id}`;
            if (!currentOrientation) setTimeout(() => handleOrientationChange(gen.id, 'horizontal'), 0); 
          } else if (gen.vertical_image_url) {
            imageUrlToShow = gen.vertical_image_url;
            altText = `Vertical (fallback) ${gen.extended_id || gen.id}`;
            if (!currentOrientation) setTimeout(() => handleOrientationChange(gen.id, 'vertical'), 0); 
          }

          const itemContent = (
            <article key={gen.id} className="py-6">
              {/* Main flex container: column on small, row on medium+ */}
              <div className="flex flex-col md:flex-row md:items-start">
                
                {/* Info and Controls Area - DOM first, order-2 on medium+ (right side) */}
                <div className="w-full md:order-2 flex-grow mb-6 md:mb-0 md:ml-10">
                  <p className="mb-3 text-sm text-gray-600">
                    <span className="font-semibold">{offset - generations.length + index + 1}.</span> Created: {formatDate(gen.created_at)}
                  </p>
                  
                  <div className="flex space-x-3 mb-2">
                    <button 
                      onClick={() => handleOrientationChange(gen.id, 'horizontal')} 
                      disabled={!gen.horizontal_image_url}
                      className={getButtonClasses(currentOrientation === 'horizontal' && !!gen.horizontal_image_url, !gen.horizontal_image_url)}>
                      <IconHorizontal />
                      Horizontal
                    </button>
                    <button 
                      onClick={() => handleOrientationChange(gen.id, 'vertical')} 
                      disabled={!gen.vertical_image_url}
                      className={getButtonClasses(currentOrientation === 'vertical' && !!gen.vertical_image_url, !gen.vertical_image_url)}>
                      <IconVertical />
                      Vertical
                    </button>
                  </div>
                </div>

                {/* Image Area - DOM second, order-1 on medium+ (left side) */}
                <div className="w-full md:order-1 md:w-1/2 lg:w-2/5 flex-shrink-0">
                  {imageUrlToShow ? (
                    <img src={imageUrlToShow} alt={altText} className="w-full h-auto rounded-lg"/>
                  ) : (
                    <div className="w-full aspect-video bg-gray-100 rounded-lg flex items-center justify-center text-gray-400">
                      <p>No image available for this selection.</p>
                    </div>
                  )}
                </div>

              </div>
              {index < generations.length - 1 && <hr className="mt-6 border-gray-300" />}
            </article>
          );

          if (generations.length === index + 1) {
            return React.cloneElement(itemContent, { ref: lastElementRef });
          }
          return itemContent;
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