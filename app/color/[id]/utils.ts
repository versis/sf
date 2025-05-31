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
export function generateCardTitle(location?: string, createdAt?: string): string {
  const formattedDate = createdAt ? formatCardDate(createdAt) : '';
  const fromLocation = location || 'an unknown location';
  
  let title = 'shadefreude: You have a new postcard';
  if (location) {
    title += ` from ${fromLocation}!`;
  }
  if (createdAt) {
    title += ` Posted: ${formattedDate}`;
  }
  
  return title;
}

/**
 * Generates a description for the card, prioritizing personal notes
 */
export function generateCardDescription(extendedId: string, noteText?: string): string {
  if (noteText && noteText.trim()) {
    // Truncate note to 30 characters max
    const truncatedNote = noteText.length > 30 
      ? noteText.substring(0, 27) + "..."
      : noteText;
    return `Card ID ${extendedId}: ${truncatedNote}`;
  }
  
  // Fallback description for users unfamiliar with the app
  return "A unique AI-generated color postcard that turns everyday photos into shareable moments with custom color names and insights.";
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
}): CardMetadata {
  const location = extractLocation(cardData.metadata);
  const photoDate = extractPhotoDate(cardData.metadata);
  
  return {
    title: generateCardTitle(location, cardData.created_at),
    description: generateCardDescription(cardData.extended_id, cardData.note_text),
    imageUrl: getOpenGraphImageUrl(cardData.front_horizontal_image_url, cardData.front_vertical_image_url),
    location,
    photoDate,
    createdAt: cardData.created_at
  };
} 