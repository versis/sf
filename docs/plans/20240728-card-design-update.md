# Plan: Card Design Update - EXIF Data and Layout Adjustments ✅ COMPLETED

**Date:** 2024-07-28

**Objective:** Modify the generated card images to update text rendering, replace metrics with EXIF-derived location (country) and date, and adjust the layout accordingly.

**SOLUTION IMPLEMENTED:** Client-side EXIF extraction using the `exifr` JavaScript library.

## Phase 1: Backend - Data Extraction & Preparation

- [X] **1.1. Locate Image Generation Code:**
    - [X] **Identified:** Image generation primarily occurs in `api/utils/card_utils.py`, within the `generate_card_image_bytes` function.
    - [X] **Calling Context:** This function is called by the `finalize_card_generation` endpoint in `api/routers/card_generation.py`.
    - [X] **Dependency Management:** Python dependencies are managed via `api/requirements.txt`.

- [X] **1.2. EXIF Data Extraction Implementation (Client-side):**
    - [X] **1.2.1.** Added `exifr` JavaScript library for client-side EXIF parsing that supports HEIC/HEIF files.
    - [X] **1.2.2.** Implemented `extractExifData()` function in the frontend to extract date and GPS coordinates from uploaded files.
    - [X] **1.2.3.** Implemented simple reverse geocoding using OpenStreetMap Nominatim API to convert GPS coordinates to country names.
    - [X] **1.2.4.** Added state management for storing extracted EXIF data (date, latitude, longitude, country).

- [X] **1.3. Modify Image Generation Service Interface:**
    - [X] **1.3.1.** Updated `finalize_card_generation` endpoint to accept optional `photo_date` and `photo_location` form fields.
    - [X] **1.3.2.** Modified frontend form submission to include extracted EXIF data as additional form fields.
    - [X] **1.3.3.** Removed server-side EXIF extraction code and dependencies (`reverse_geocoder`, `pillow-heif`).

## Phase 2: Frontend - Card Layout Adjustments

- [X] **2.1. Text Size Adjustment:**
    - [X] **2.1.1.** Modified "shadefreude" brand text to use the same font size as the unique ID (`f_brand` font size adjusted).
    - [X] **2.1.2.** Maintained consistent spacing between brand name and ID.

- [X] **2.2. Metrics Replacement:**
    - [X] **2.2.1.** Replaced the old 3-line metrics system with a 2-line system showing location and date.
    - [X] **2.2.2.** Implemented conditional rendering - only display metrics when data is available (no "Unknown" text).
    - [X] **2.2.3.** Adjusted layout calculations to accommodate the reduced number of metric lines.

## Phase 3: Testing & Validation

- [ ] **3.1. Test with various image formats (JPEG, PNG, HEIC)**
- [ ] **3.2. Test with images with and without EXIF data**
- [ ] **3.3. Verify layout adjustments work correctly**
- [ ] **3.4. Test deployment on Vercel**

## Phase 4: Code Cleanup ✅ COMPLETED

- [X] **4.1. Python Backend Cleanup:**
    - [X] **4.1.1.** Removed all commented-out old EXIF extraction code from `api/utils/card_utils.py`.
    - [X] **4.1.2.** Removed extensive commented-out old metrics logic (HEX, RGB, CMYK system).
    - [X] **4.1.3.** Cleaned up imports and removed unused debugging comments.
    - [X] **4.1.4.** Simplified font loading code and removed unnecessary inline comments.
    - [X] **4.1.5.** Updated "shadefreude" brand text to use same font size as ID (38pt scale).

- [X] **4.2. Router Cleanup:**
    - [X] **4.2.1.** Removed debugging code that saved images locally for testing.
    - [X] **4.2.2.** Cleaned up import comments and removed outdated inline comments.
    - [X] **4.2.3.** Simplified logging messages and removed redundant explanatory comments.

- [X] **4.3. Design Enhancement:**
    - [X] **4.3.1.** Replaced text labels "Location:" and "Date:" with symbols (📍 for location, 📅 for date).
    - [X] **4.3.2.** Updated metric line height calculations to use the new symbol format.

## Additional Notes

*   **Privacy-Conscious:** Only the country name is sent to the backend, not raw GPS coordinates.
*   **Graceful Degradation:** If EXIF extraction fails or data is not available, the card generation continues without metrics.
*   **Cross-Platform Compatibility:** The `exifr` library supports various image formats including HEIC files from modern smartphones.
*   **No External Dependencies:** Removed server-side dependencies that would complicate deployment on serverless platforms like Vercel. 