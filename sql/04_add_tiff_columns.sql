-- Migration: Add TIFF URL columns for print-ready postcard system
-- Date: December 22, 2024
-- Phase 2, Step 2.1: Database Schema Updates

-- Add TIFF URL columns to store high-quality print versions alongside existing PNG URLs
ALTER TABLE card_generations ADD COLUMN front_horizontal_tiff_url TEXT;
ALTER TABLE card_generations ADD COLUMN front_vertical_tiff_url TEXT;
ALTER TABLE card_generations ADD COLUMN back_horizontal_tiff_url TEXT;
ALTER TABLE card_generations ADD COLUMN back_vertical_tiff_url TEXT;

-- Add comments for documentation
COMMENT ON COLUMN card_generations.front_horizontal_tiff_url IS 'URL to high-resolution TIFF version of horizontal front card (300 DPI, print-ready)';
COMMENT ON COLUMN card_generations.front_vertical_tiff_url IS 'URL to high-resolution TIFF version of vertical front card (300 DPI, print-ready)';
COMMENT ON COLUMN card_generations.back_horizontal_tiff_url IS 'URL to high-resolution TIFF version of horizontal back card (300 DPI, print-ready)';
COMMENT ON COLUMN card_generations.back_vertical_tiff_url IS 'URL to high-resolution TIFF version of vertical back card (300 DPI, print-ready)';

-- Optional: Add index for performance if querying by TIFF URLs becomes common
-- CREATE INDEX CONCURRENTLY idx_card_generations_tiff_urls ON card_generations 
-- (front_horizontal_tiff_url, front_vertical_tiff_url, back_horizontal_tiff_url, back_vertical_tiff_url)
-- WHERE front_horizontal_tiff_url IS NOT NULL; 