// Utility functions for generating card metadata

/**
 * Formats an ISO timestamp to the required display format: "YYYY/MM/DD HH:MM"
 */
export function formatCardDate(isoString: string): string {
  try {
    const date = new Date(isoString);
    // Use Swedish locale format which gives us YYYY-MM-DD HH:MM, then replace - with /
    return date.toLocaleString('sv-SE', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit',
      hour: '2-digit', 
      minute: '2-digit'
    }).replace(/(\d{4})-(\d{2})-(\d{2}) (\d{2}:\d{2})/, '$1/$2/$3 $4');
  } catch (error) {
    console.error('Error formatting date:', error);
    return new Date().toLocaleString('sv-SE').replace(/(\d{4})-(\d{2})-(\d{2}) (\d{2}:\d{2})/, '$1/$2/$3 $4');
  }
}

/**
 * Generates a personalized title for the card page
 */
export function generateCardTitle(location?: string, createdAt?: string, noteText?: string): string {
  let title = 'shadefreude:';
  
  if (location) {
    title += ` You have a new postcard from ${location}!`;
  } else {
    title += ` You have a new postcard!`;
  }
  
  // Add first 10 characters of note if available
  if (noteText && noteText.trim()) {
    const notePreview = noteText.length > 10 
      ? noteText.substring(0, 10) + '...'
      : noteText;
    title += ` — ${notePreview}`;
  }
  
  return title;
}

/**
 * Generates a description for the card, prioritizing posted timestamp
 */
export function generateCardDescription(extendedId: string, noteText?: string, createdAt?: string): string {
  let description = '';
  
  if (createdAt) {
    const formattedDate = formatCardDate(createdAt);
    description = `Posted: ${formattedDate} | shadefreude`;
  } else {
    description = 'shadefreude';
  }
  
  return description;
}

/**
 * Extracts location from EXIF metadata
 */
export function extractLocation(metadata?: any): string | undefined {
  return metadata?.exif_data_extracted?.photo_location_country;
}

/**
 * Extracts photo date from EXIF metadata  
 */
export function extractPhotoDate(metadata?: any): string | undefined {
  return metadata?.exif_data_extracted?.photo_date;
}

/**
 * Gets the best available image URL for Open Graph (prefers horizontal)
 */
export function getOpenGraphImageUrl(frontHorizontalUrl?: string, frontVerticalUrl?: string): string | undefined {
  return frontHorizontalUrl || frontVerticalUrl;
}

export interface CardMetadata {
  title: string;
  description: string;
  imageUrl?: string;
  location?: string;
  photoDate?: string;
  createdAt?: string;
}

/**
 * Generates complete metadata for a card
 */
export function generateCardMetadata(cardData: {
  extended_id: string;
  note_text?: string;
  front_horizontal_image_url?: string;
  front_vertical_image_url?: string;
  created_at: string;
  metadata?: any;
  // New direct database fields for EXIF data
  photo_location?: string;
  photo_date?: string;
}): CardMetadata {
  // Prefer direct database fields over metadata extraction
  const location = cardData.photo_location || extractLocation(cardData.metadata);
  const photoDate = cardData.photo_date || extractPhotoDate(cardData.metadata);
  
  return {
    title: generateCardTitle(location, cardData.created_at, cardData.note_text),
    description: generateCardDescription(cardData.extended_id, cardData.note_text, cardData.created_at),
    imageUrl: getOpenGraphImageUrl(cardData.front_horizontal_image_url, cardData.front_vertical_image_url),
    location,
    photoDate,
    createdAt: cardData.created_at
  };
} 