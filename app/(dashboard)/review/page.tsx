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

  // Consistent button styling
  const getButtonClasses = (isActive: boolean, isDisabled: boolean) => {
    let baseClasses = "px-3 py-1 text-sm rounded transition-colors duration-150 ease-in-out";
    if (isDisabled) {
      return `${baseClasses} bg-gray-100 text-gray-400 cursor-not-allowed`;
    }
    if (isActive) {
      return `${baseClasses} bg-blue-500 text-white hover:bg-blue-600`;
    }
    return `${baseClasses} bg-gray-200 text-gray-700 hover:bg-gray-300`;
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
              <div className="md:flex md:items-start md:space-x-6">
                {/* Image Area */} 
                <div className="flex-shrink-0 w-full md:w-1/2 lg:w-2/5 mb-4 md:mb-0">
                  {imageUrlToShow ? (
                    <img src={imageUrlToShow} alt={altText} className="w-full h-auto rounded-lg shadow-md"/>
                  ) : (
                    <div className="w-full aspect-video bg-gray-100 rounded-lg flex items-center justify-center text-gray-400 shadow-md">
                      <p>No image available for this selection.</p>
                    </div>
                  )}
                </div>

                {/* Info and Controls Area */} 
                <div className="flex-grow">
                  <p className="mb-2 text-sm text-gray-600">
                    <span className="font-semibold">{offset - generations.length + index + 1}.</span> Created: {gen.created_at ? new Date(gen.created_at).toLocaleString() : 'N/A'}
                  </p>
                  
                  <div className="flex space-x-2 mb-2">
                    <button 
                      onClick={() => handleOrientationChange(gen.id, 'horizontal')} 
                      disabled={!gen.horizontal_image_url}
                      className={getButtonClasses(currentOrientation === 'horizontal' && !!gen.horizontal_image_url, !gen.horizontal_image_url)}>
                      Horizontal
                    </button>
                    <button 
                      onClick={() => handleOrientationChange(gen.id, 'vertical')} 
                      disabled={!gen.vertical_image_url}
                      className={getButtonClasses(currentOrientation === 'vertical' && !!gen.vertical_image_url, !gen.vertical_image_url)}>
                      Vertical
                    </button>
                  </div>
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