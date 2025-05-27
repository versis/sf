# Hero Card Cache Workflow

## Quick Start

### When you need to update hero cards:

1. **Start local API server**:
   ```bash
   npm run fastapi-dev
   ```

2. **Generate cache** (in another terminal):
   ```bash
   npm run generate-hero-cache
   ```

3. **Commit and deploy**:
   ```bash
   git add public/hero-cache
   git commit -m "Update hero card cache"
   git push
   ```

That's it! Vercel will automatically deploy with the new cached files.

## How It Works

### ✅ What Happens Locally
- Script fetches hero card data from your local API
- Downloads all images (front/back, vertical/horizontal) 
- Creates `public/hero-cache/manifest.json` with image paths
- Total cache size: ~17MB for 8 cards (32 images)

### ✅ What Happens on Vercel
- Build process: Just `next build` (no API calls needed)
- Cache files served as static assets from `public/hero-cache/`
- Hero cards load instantly from cached files
- Zero build dependencies or timeouts

### ✅ What Happens for Users
- **Instant loading**: Hero cards appear immediately
- **Reliable**: No API calls needed for hero section
- **Fallback**: If cache missing, automatically uses API

## When to Regenerate

- Hero card IDs change in `lib/heroCardConfig.ts`
- Card images updated in database
- Adding new hero cards

## Troubleshooting

### Script fails with "API server not running"
```bash
# Start the API server first
npm run fastapi-dev
```

### Script fails with "No data for card"
- Check that hero cards exist in your database
- Verify hero card IDs in `lib/heroCardConfig.ts`

### Cache not loading on frontend
- Verify files exist in `public/hero-cache/`
- Check that manifest.json is valid JSON
- Frontend will automatically fallback to API if cache unavailable

## File Structure

```
public/hero-cache/
├── manifest.json                           # Maps card IDs to image paths
├── 000000228_FE_F_front_vertical.png      # Card images
├── 000000228_FE_F_front_horizontal.png
├── 000000228_FE_F_back_vertical.png
├── 000000228_FE_F_back_horizontal.png
└── ... (28 more images)
```

## Benefits

- **Zero build time**: No API dependencies during Vercel build
- **Instant loading**: Hero cards appear immediately 
- **Version controlled**: Cache changes tracked in git
- **Reliable deployment**: Static files always available
- **Simple workflow**: Generate locally, commit, deploy 