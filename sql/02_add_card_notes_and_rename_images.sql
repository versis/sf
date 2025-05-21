-- Migration script to add card note functionality and rename image URL columns

-- Rename existing columns for front images
ALTER TABLE public.card_generations
RENAME COLUMN horizontal_image_url TO front_horizontal_image_url;

ALTER TABLE public.card_generations
RENAME COLUMN vertical_image_url TO front_vertical_image_url;

-- Add new columns for notes and back images
ALTER TABLE public.card_generations
ADD COLUMN note_text TEXT DEFAULT NULL,
ADD COLUMN has_note BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN back_horizontal_image_url TEXT DEFAULT NULL,
ADD COLUMN back_vertical_image_url TEXT DEFAULT NULL;

-- It's good practice to comment the migration script with its purpose and date
-- Deployed: YYYY-MM-DD
-- Description: Adds fields for card notes (note_text, has_note) and back image URLs (back_horizontal_image_url, back_vertical_image_url). Renames existing image URLs to include 'front_'. 