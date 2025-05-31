import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import ClientCardPage from './ClientCardPage';
import { generateCardMetadata } from './utils';

// This matches the actual FastAPI response format (camelCase from the API response)
interface CardDetailsFromAPI {
  id?: number;
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
  // EXIF fields from FastAPI (might be missing)
  photo_date?: string;
  photo_location?: string;
  metadata?: any;
}

// Fetch card data server-side
async function fetchCardData(id: string): Promise<CardDetailsFromAPI | null> {
  try {
    // Construct the base URL more reliably
    let baseUrl: string;
    
    if (process.env.VERCEL_URL) {
      // Vercel production/preview
      baseUrl = `https://${process.env.VERCEL_URL}`;
    } else if (process.env.NODE_ENV === 'development') {
      // Development mode - use the port where Next.js is running (requests will be proxied to FastAPI)
      baseUrl = 'http://localhost:3000'; // The server is on 3000 now
    } else {
      // Fallback for production
      baseUrl = 'https://sf.tinker.institute';
    }
    
    const fetchUrl = `${baseUrl}/api/retrieve-card-by-extended-id/${id}`;
    console.log(`[Server] Fetching card data from: ${fetchUrl}`);
    
    const response = await fetch(fetchUrl, {
      cache: 'no-store', // Ensure fresh data for metadata generation
      headers: {
        'User-Agent': 'NextJS-Server',
      },
    });

    console.log(`[Server] Fetch response status: ${response.status}`);

    if (!response.ok) {
      console.error(`[Server] Failed to fetch card data: ${response.status} ${response.statusText}`);
      const errorText = await response.text();
      console.error(`[Server] Error response body: ${errorText}`);
      return null;
    }

    const data = await response.json();
    console.log(`[Server] Raw response from FastAPI:`, data);

    console.log(`[Server] Successfully fetched card data:`, {
      id: data.id,
      extendedId: data.extendedId,
      hasImages: {
        horizontal: !!data.frontHorizontalImageUrl,
        vertical: !!data.frontVerticalImageUrl
      }
    });

    return data;
  } catch (error) {
    console.error('[Server] Error fetching card data:', error);
    return null;
  }
}

// Convert API response to client component props
function transformCardData(apiData: CardDetailsFromAPI): any {
  console.log('[Server] Transforming card data for client:', {
    hasHorizontalImage: !!apiData.frontHorizontalImageUrl,
    hasVerticalImage: !!apiData.frontVerticalImageUrl,
    extendedId: apiData.extendedId,
  });

  return {
    extendedId: apiData.extendedId,
    hexColor: apiData.hexColor,
    card_name: apiData.card_name,
    status: apiData.status,
    frontHorizontalImageUrl: apiData.frontHorizontalImageUrl,
    frontVerticalImageUrl: apiData.frontVerticalImageUrl,
    noteText: apiData.noteText,
    hasNote: apiData.hasNote,
    backHorizontalImageUrl: apiData.backHorizontalImageUrl,
    backVerticalImageUrl: apiData.backVerticalImageUrl,
    aiName: apiData.aiName,
    aiPhonetic: apiData.aiPhonetic,
    aiArticle: apiData.aiArticle,
    aiDescription: apiData.aiDescription,
    createdAt: apiData.createdAt,
    updatedAt: apiData.updatedAt,
    photoDate: apiData.photo_date,
    photoLocation: apiData.photo_location,
    metadata: apiData.metadata,
  };
}

// Generate dynamic metadata for each card
export async function generateMetadata(
  { params }: { params: { id: string } }
): Promise<Metadata> {
  const cardData = await fetchCardData(params.id);
  
  if (!cardData) {
    return {
      title: 'Card Not Found - shadefreude',
      description: 'The requested color card could not be found.',
    };
  }

  // Generate dynamic metadata using our utility functions
  const metadata = generateCardMetadata({
    extended_id: cardData.extendedId || params.id,
    note_text: cardData.noteText,
    front_horizontal_image_url: cardData.frontHorizontalImageUrl,
    front_vertical_image_url: cardData.frontVerticalImageUrl,
    created_at: cardData.createdAt || new Date().toISOString(),
    metadata: cardData.metadata,
  });

  const cardName = cardData.card_name || 'Color Card';
  const baseUrl = 'https://sf.tinker.institute';
  const cardUrl = `${baseUrl}/color/${params.id}`;

  return {
    title: metadata.title,
    description: metadata.description,
    openGraph: {
      title: metadata.title,
      description: metadata.description,
      url: cardUrl,
      siteName: 'shadefreude',
      images: metadata.imageUrl ? [
        {
          url: metadata.imageUrl,
          width: 1400,
          height: 700,
          alt: `${cardName} - shadefreude Color Card`,
        }
      ] : [],
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: metadata.title,
      description: metadata.description,
      images: metadata.imageUrl ? [metadata.imageUrl] : [],
    },
    alternates: {
      canonical: cardUrl,
    },
  };
}

// Server component
export default async function ColorCardPage({ params }: { params: { id: string } }) {
  console.log(`[Server] Processing card page for ID: ${params.id}`);
  
  const cardData = await fetchCardData(params.id);

  if (!cardData) {
    console.log(`[Server] No card data found for ID: ${params.id}, calling notFound()`);
    notFound();
  }

  // Transform the API data to match client component expectations
  const clientCardData = transformCardData(cardData);
  
  console.log(`[Server] Final client data:`, {
    hasData: !!clientCardData,
    extendedId: clientCardData?.extendedId,
    frontHorizontalImageUrl: clientCardData?.frontHorizontalImageUrl?.substring(0, 50) + '...',
    frontVerticalImageUrl: clientCardData?.frontVerticalImageUrl?.substring(0, 50) + '...'
  });

  return (
    <ClientCardPage
      cardData={clientCardData}
      cardId={params.id}
      loading={false}
      error={null}
    />
  );
} 