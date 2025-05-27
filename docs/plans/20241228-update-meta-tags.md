# Update Meta Tags Plan - 2024-12-28

## Objective
Update the HTML head section with new meta tags for SEO and social media sharing, including title, description, Open Graph, and Twitter Card tags.

## Current State
- Meta tags are handled via Next.js 13+ Metadata API in `app/layout.tsx`
- Current title and description exist but need updating
- No Open Graph or Twitter Card tags currently

## Tasks
- [x] Update title and description in metadata object
- [x] Add Open Graph meta tags (without image since og-preview.jpg doesn't exist)
- [x] Add Twitter Card meta tags (without image)
- [x] Add canonical URL
- [x] Test the changes

## Implementation Steps
1. Update the metadata object in `app/layout.tsx`
2. Add openGraph configuration
3. Add twitter configuration
4. Add canonical URL via alternates
5. Verify the changes work correctly

## Notes
- Removing image-related meta tags since `og-preview.jpg` doesn't exist
- Using Next.js 13+ metadata API instead of manual meta tags for consistency 