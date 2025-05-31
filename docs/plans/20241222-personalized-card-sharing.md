# Plan: Personalized Card Sharing Experience

**Date:** 2024-12-22

**Objective:** Implement personalized Open Graph metadata for color card pages to enhance social sharing experience with dynamic titles, descriptions, and preview images.

## Current State Analysis

### ✅ Available Data
- EXIF data: `metadata.exif_data_extracted.photo_date` and `metadata.exif_data_extracted.photo_location_country`
- Timestamps: `created_at`, `updated_at` 
- Personal notes: `note_text` field
- Card images: `front_horizontal_image_url`, `front_vertical_image_url`
- Card details: `extended_id`, `hex_color`, card name from AI/metadata

### ❓ To Verify
- GPS coordinates storage (currently only country name stored)
- Exact format of stored date/location data

### ⚠️ Missing
- Dynamic Open Graph metadata generation
- Fallback descriptions for cards without personal notes

## Feature Requirements

### 1. Open Graph Preview
- **Image:** Use `front_horizontal_image_url` as preview image
- **Title:** "shadefreude: You have a new postcard from {location}! Posted: {date}"
- **Description:** "Card ID {extended_id}: {personal_note}" (max 30 chars for note) OR fallback text

### 2. Date Format
- Target format: "2024/12/15 17:31"
- Parse from `created_at` timestamp

### 3. Location Detection  
- Use `photo_location_country` from EXIF data
- Fallback to "an unknown location" if not available

### 4. Description Fallback
- If no personal note: "A unique AI-generated color postcard that turns everyday photos into shareable moments with custom color names and insights."

## Technical Solution: Next.js generateMetadata

### Approach
Convert `app/color/[id]/page.tsx` to use:
1. **Server Component** with `generateMetadata` function for SEO/OG
2. **Client Component** for interactive features (swipe, flip, etc.)
3. **Shared data fetching** to avoid duplicate API calls

### Implementation Steps

#### Phase 1: Data Verification & API Enhancement

- [x] **1.1 Check Current Data Structure**
  - [x] Verify EXIF data format in database
  - [x] Check if GPS coordinates are stored separately
  - [x] Document current `created_at` timestamp format

- [x] **1.2 Enhance API Response (if needed)**
  - [x] Update card retrieval API to include formatted date/location for metadata
  - [x] Add utility functions for date formatting
  - [x] Ensure all required fields are exposed

#### Phase 2: Component Architecture Refactor

- [x] **2.1 Create Server Component Wrapper**
  - [x] New `app/color/[id]/page.tsx` as server component with `generateMetadata`
  - [x] Extract current client logic to separate `ClientCardPage` component
  - [x] Implement server-side data fetching

- [x] **2.2 Implement generateMetadata Function**
  - [x] Fetch card data server-side
  - [x] Generate dynamic Open Graph metadata
  - [x] Handle fallbacks for missing data
  - [x] Format date as "YYYY/MM/DD HH:MM"

- [x] **2.3 Create Client Component**
  - [x] Extract all interactive logic (swipe, flip, state management)
  - [x] Pass server-fetched data as props
  - [x] Maintain current functionality

#### Phase 3: Metadata Generation Logic

- [x] **3.1 Title Generation**
  - [x] Format: "shadefreude: You have a new postcard from {location}! Posted: {date}"
  - [x] Use `photo_location_country` or fallback to "an unknown location"
  - [x] Format `created_at` to "2024/12/15 17:31" format

- [x] **3.2 Description Generation**
  - [x] Primary: "Card ID {extended_id}: {truncated_note}" (30 char max for note)
  - [x] Fallback: "A unique AI-generated color postcard that turns everyday photos into shareable moments with custom color names and insights."

- [x] **3.3 Open Graph Image**
  - [x] Use `front_horizontal_image_url` as og:image
  - [x] Ensure proper aspect ratio and size

#### Phase 4: Database Schema (if needed)

- [ ] **4.1 Assess GPS Coordinate Storage**
  - [ ] Check if raw latitude/longitude needed
  - [ ] Create migration script if additional fields required
  - [ ] Update API to extract GPS coordinates from EXIF

- [ ] **4.2 Create Migration (if needed)**
  - [ ] New SQL script: `03_add_location_coordinates.sql`
  - [ ] Add `photo_latitude` and `photo_longitude` fields
  - [ ] Update card generation to store coordinates

#### Phase 5: Testing & Refinement

- [ ] **5.1 Test Open Graph Rendering**
  - [ ] Use Facebook/LinkedIn/Twitter debuggers
  - [ ] Verify image display and metadata
  - [ ] Test with various card configurations

- [ ] **5.2 Performance Testing**
  - [ ] Ensure server-side rendering performance
  - [ ] Test with missing/incomplete data
  - [ ] Verify client-side interactivity preserved

- [ ] **5.3 Fallback Testing**
  - [ ] Cards without EXIF data
  - [ ] Cards without personal notes
  - [ ] Cards with incomplete metadata

## Implementation Notes

### Date Formatting
```typescript
// Convert ISO timestamp to required format
const formatCardDate = (isoString: string): string => {
  const date = new Date(isoString);
  return date.toLocaleString('sv-SE', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit', 
    minute: '2-digit'
  }).replace(/(\d{4})-(\d{2})-(\d{2}) (\d{2}:\d{2})/, '$1/$2/$3 $4');
};
```

### Fallback Description Strategy
```typescript
const generateDescription = (extendedId: string, noteText?: string): string => {
  if (noteText) {
    const truncatedNote = noteText.length > 30 
      ? noteText.substring(0, 27) + "..."
      : noteText;
    return `Card ID ${extendedId}: ${truncatedNote}`;
  }
  return "A unique AI-generated color postcard that turns everyday photos into shareable moments with custom color names and insights.";
};
```

### File Structure After Changes
```
app/color/[id]/
├── page.tsx           (Server component with generateMetadata)
├── ClientCardPage.tsx (Client component with interactivity)
└── utils.ts          (Shared utilities for metadata generation)
```

## Success Criteria

1. ✅ Dynamic Open Graph previews show actual card images
2. ✅ Titles include personalized location and date information  
3. ✅ Descriptions feature card ID and notes with appropriate fallbacks
4. ✅ All existing page functionality preserved (swipe, flip, etc.)
5. ✅ Good performance for both server rendering and client interactivity
6. ✅ Graceful handling of missing/incomplete data

## Risk Mitigation

- **Data Migration Risk:** Thoroughly test with existing cards before deploying GPS coordinate storage
- **Performance Risk:** Implement efficient server-side caching and optimize API calls
- **SEO Risk:** Ensure metadata is properly server-rendered and not dependent on client-side JavaScript
- **Fallback Risk:** Comprehensive testing with cards that have incomplete metadata 