-- Migration script to add EXIF location data and photo date fields

-- Add new columns for EXIF data
ALTER TABLE public.card_generations
ADD COLUMN photo_location_country TEXT DEFAULT NULL,
ADD COLUMN photo_location_coordinates JSONB DEFAULT NULL, -- Store {lat: number, lng: number}
ADD COLUMN photo_date TIMESTAMPTZ DEFAULT NULL;

-- Add indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_card_generations_photo_location_country ON public.card_generations(photo_location_country);
CREATE INDEX IF NOT EXISTS idx_card_generations_photo_date ON public.card_generations(photo_date);

-- Comments for documentation
COMMENT ON COLUMN public.card_generations.photo_location_country IS 'Country extracted from EXIF GPS data';
COMMENT ON COLUMN public.card_generations.photo_location_coordinates IS 'Latitude and longitude coordinates as JSON: {"lat": number, "lng": number}';
COMMENT ON COLUMN public.card_generations.photo_date IS 'Date when the photo was taken, extracted from EXIF data';

-- It's good practice to comment the migration script with its purpose and date
-- Deployed: 2024-12-22
-- Description: Adds fields for EXIF location data (photo_location_country, photo_location_coordinates) and photo date (photo_date) to enable personalized card sharing metadata. 