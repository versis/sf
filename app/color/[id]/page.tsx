import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { headers } from 'next/headers';
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

// Fetch postcard data server-side
async function fetchCardData(id: string): Promise<CardDetailsFromAPI | null> {
  try {
    // Construct the base URL more reliably
    let baseUrl: string;
    
    if (process.env.NODE_ENV === 'development') {
      // Development mode - use the port where Next.js is running (requests will be proxied to FastAPI)
      baseUrl = 'http://localhost:3000';
    } else {
      // Production - always use custom domain to avoid Vercel authentication on auto-generated URLs
      baseUrl = process.env.NEXT_PUBLIC_API_URL!;
    }
    
    const fetchUrl = `${baseUrl}/api/retrieve-card-by-extended-id/${id}`;
    console.log(`[Server] Fetching postcard data from: ${fetchUrl}`);
    
    const response = await fetch(fetchUrl, {
      cache: 'no-store', // Ensure fresh data for metadata generation
      headers: {
        'User-Agent': 'NextJS-Server',
      },
    });

    console.log(`[Server] Fetch response status: ${response.status}`);

    if (!response.ok) {
      console.error(`[Server] Failed to fetch postcard data: ${response.status} ${response.statusText}`);
      const errorText = await response.text();
      console.error(`[Server] Error response body: ${errorText}`);
      return null;
    }

    const data = await response.json();
    console.log(`[Server] Raw response from FastAPI:`, data);

    console.log(`[Server] Successfully fetched postcard data:`, {
      id: data.id,
      extendedId: data.extendedId,
      hasImages: {
        horizontal: !!data.frontHorizontalImageUrl,
        vertical: !!data.frontVerticalImageUrl
      }
    });

    return data;
  } catch (error) {
    console.error('[Server] Error fetching postcard data:', error);
    return null;
  }
}

// Convert API response to client component props
function transformCardData(apiData: CardDetailsFromAPI): any {
  console.log('[Server] Transforming postcard data for client:', {
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

// Add mobile detection utility function
function isMobileUserAgent(userAgent: string): boolean {
  const mobileKeywords = [
    'Mobile', 'Android', 'iPhone', 'iPad', 'iPod',
    'BlackBerry', 'Windows Phone', 'Opera Mini',
    'IEMobile', 'Mobile Safari'
  ];
  
  return mobileKeywords.some(keyword => 
    userAgent.includes(keyword)
  );
}

// Generate dynamic metadata for each postcard
export async function generateMetadata(
  { params }: { params: { id: string } }
): Promise<Metadata> {
  const cardData = await fetchCardData(params.id);
  
  if (!cardData) {
    return {
      title: 'Postcard Not Found - shadefreude',
      description: 'The requested color postcard could not be found.',
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
    // Include EXIF data from direct database fields
    photo_location: cardData.photo_location,
    photo_date: cardData.photo_date,
  });

  const cardName = cardData.card_name || 'Color Postcard';
  const baseUrl = process.env.NEXT_PUBLIC_API_URL!;
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
          alt: `${cardName} - shadefreude Postcard`,
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
  console.log(`[Server] Processing postcard page for ID: ${params.id}`);
  
  // Get server-side mobile detection
  const headersList = headers();
  const userAgent = headersList.get('user-agent') || '';
  const serverDetectedMobile = isMobileUserAgent(userAgent);
  
  console.log(`[Server] User-Agent: ${userAgent.substring(0, 100)}...`);
  console.log(`[Server] Detected mobile: ${serverDetectedMobile}`);
  
  const cardData = await fetchCardData(params.id);

  if (!cardData) {
    console.log(`[Server] No postcard data found for ID: ${params.id}, calling notFound()`);
    notFound();
  }

  // Transform the API data to match client component expectations
  const clientCardData = transformCardData(cardData);
  
  // Determine initial orientation based on server-side mobile detection
  let initialOrientation: 'horizontal' | 'vertical' = 'horizontal';
  if (serverDetectedMobile && clientCardData?.frontVerticalImageUrl) {
    initialOrientation = 'vertical';
  } else if (clientCardData?.frontHorizontalImageUrl) {
    initialOrientation = 'horizontal';
  } else if (clientCardData?.frontVerticalImageUrl) {
    initialOrientation = 'vertical';
  }
  
  console.log(`[Server] Initial orientation for ${serverDetectedMobile ? 'mobile' : 'desktop'}: ${initialOrientation}`);
  
  console.log(`[Server] Final client data:`, {
    hasData: !!clientCardData,
    extendedId: clientCardData?.extendedId,
    frontHorizontalImageUrl: clientCardData?.frontHorizontalImageUrl?.substring(0, 50) + '...',
    frontVerticalImageUrl: clientCardData?.frontVerticalImageUrl?.substring(0, 50) + '...',
    initialOrientation,
    serverDetectedMobile
  });

  return (
    <>
      <ClientCardPage
        cardData={clientCardData}
        cardId={params.id}
        loading={false}
        error={null}
        initialMobile={serverDetectedMobile}
        initialOrientation={initialOrientation}
      />
    </>
  );
} 