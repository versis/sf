import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import ClientCardPage from './ClientCardPage';
import { generateCardMetadata } from './utils';

interface CardDetailsFromAPI {
  id?: number;
  extended_id?: string;
  hex_color?: string;
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
  photo_date?: string;
  photo_location?: string;
  metadata?: any;
}

// Fetch card data server-side
async function fetchCardData(id: string): Promise<CardDetailsFromAPI | null> {
  try {
    const baseUrl = process.env.NEXT_PUBLIC_VERCEL_URL 
      ? `https://${process.env.NEXT_PUBLIC_VERCEL_URL}`
      : process.env.NODE_ENV === 'development' 
        ? 'http://localhost:3000'
        : 'https://sf.tinker.institute';
    
    const response = await fetch(`${baseUrl}/api/retrieve-card-by-extended-id/${id}`, {
      cache: 'no-store', // Ensure fresh data for metadata generation
    });

    if (!response.ok) {
      console.error(`Failed to fetch card data: ${response.status} ${response.statusText}`);
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching card data:', error);
    return null;
  }
}

// Convert API response to client component props
function transformCardData(apiData: CardDetailsFromAPI): any {
  return {
    extendedId: apiData.extended_id,
    hexColor: apiData.hex_color,
    card_name: apiData.card_name,
    status: apiData.status,
    frontHorizontalImageUrl: apiData.front_horizontal_image_url,
    frontVerticalImageUrl: apiData.front_vertical_image_url,
    noteText: apiData.note_text,
    hasNote: apiData.has_note,
    backHorizontalImageUrl: apiData.back_horizontal_image_url,
    backVerticalImageUrl: apiData.back_vertical_image_url,
    aiName: apiData.ai_name,
    aiPhonetic: apiData.ai_phonetic,
    aiArticle: apiData.ai_article,
    aiDescription: apiData.ai_description,
    createdAt: apiData.created_at,
    updatedAt: apiData.updated_at,
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
    extended_id: cardData.extended_id || params.id,
    note_text: cardData.note_text,
    front_horizontal_image_url: cardData.front_horizontal_image_url,
    front_vertical_image_url: cardData.front_vertical_image_url,
    created_at: cardData.created_at || new Date().toISOString(),
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
  const cardData = await fetchCardData(params.id);

  if (!cardData) {
    notFound();
  }

  // Transform the API data to match client component expectations
  const clientCardData = transformCardData(cardData);

  return (
    <ClientCardPage
      cardData={clientCardData}
      cardId={params.id}
      loading={false}
      error={null}
    />
  );
} 