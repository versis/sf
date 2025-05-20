'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation'; // Correct hook for App Router

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
    if (id && loading) { // Only fetch if we have a valid id and are in a loading state for it
      const fetchCardDetails = async () => {
        try {
          const response = await fetch(`/api/retrieve-card-by-extended-id/${id}`);
          if (!response.ok) {
            let errorMsg = `Error fetching card details: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.detail || errorMsg;
            } catch (jsonError) {
                // Stick with status error if JSON parsing fails
            }
            throw new Error(errorMsg);
          }
          const data: CardDetails = await response.json();
          setCardDetails(data);
          setError(null); // Clear any previous error on success
        } catch (err) {
          setError(err instanceof Error ? err.message : 'An unknown error occurred');
          setCardDetails(null); // Clear card details on error
        }
        setLoading(false); // Set loading to false once fetch attempt is complete
      };
      fetchCardDetails();
    }
    // If id is null, loading might have been set to false by the previous effect's 'else' block.
  }, [id, loading]); // Depend on 'id' (our stable internal id) and 'loading' state

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
    return <div className="flex justify-center items-center min-h-screen">Card not found. (Or still loading initial data)</div>;
  }

  // Basic display - you'll want to style this nicely
  return (
    <div className="container mx-auto p-4 min-h-screen flex flex-col items-center justify-center">
      <h1 className="text-3xl font-bold mb-2">Color Card: {cardDetails.colorName || 'Unnamed Color'}</h1>
      <p className="mb-1">Extended ID: {cardDetails.extendedId}</p>
      <p className="mb-4">Hex: {cardDetails.hexColor}</p>
      
      {cardDetails.horizontalImageUrl && (
        <img src={cardDetails.horizontalImageUrl} alt={`Color card ${cardDetails.colorName} - horizontal`} className="max-w-md mb-4 border" />
      )}
      {cardDetails.verticalImageUrl && (
        <img src={cardDetails.verticalImageUrl} alt={`Color card ${cardDetails.colorName} - vertical`} className="max-w-xs mb-4 border" />
      )}
      
      <div className="text-center max-w-md">
        <p className="text-lg italic mb-1">{cardDetails.phoneticName} {cardDetails.article}</p>
        <p>{cardDetails.description}</p>
      </div>
      
      <a href="/" className="mt-8 text-blue-600 hover:underline">Create your own card</a>
    </div>
  );
} 