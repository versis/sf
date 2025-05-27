# Local Hero Card Cache Generation

**Date:** December 30, 2024  
**Status:** 🔄 In Progress

## Problem Statement

The build-time caching approach is complex and fragile. We want a simpler solution where:
1. Cache is generated locally by the developer
2. Cache files are committed to the repository
3. Vercel build just serves the pre-existing cache files
4. No API dependencies during build

## Solution: Local Cache Generation

### Approach
1. **Local Script**: Run locally when hero cards change
2. **Commit Cache**: Add cache files to git repository
3. **Static Serving**: Vercel serves cached files directly
4. **Remove Prebuild**: No build-time caching needed

### Benefits
- ✅ **Zero build dependencies**: No API calls during Vercel build
- ✅ **Predictable performance**: Cache always available
- ✅ **Version controlled**: Cache changes tracked in git
- ✅ **Simple deployment**: Just static file serving
- ✅ **Developer control**: Cache updated when needed

## Implementation Plan

### Step 1: Create Local Cache Script ✅
- [ ] Create `scripts/generate-hero-cache.js` (separate from build process)
- [ ] Remove prebuild hook from `package.json`
- [ ] Add cache directory to git (with `.gitkeep` or actual files)

### Step 2: Update Cache Script ✅
- [ ] Remove build environment detection
- [ ] Always use localhost API (developer must have server running)
- [ ] Fail fast if API not available (clear error message)
- [ ] Add instructions for running the script

### Step 3: Update Frontend ✅
- [ ] Keep existing cache-first loading logic
- [ ] Remove any build-time dependencies
- [ ] Ensure graceful fallback still works

### Step 4: Documentation ✅
- [ ] Add README instructions for cache generation
- [ ] Document when to regenerate cache
- [ ] Add git workflow for cache updates

## Technical Implementation

### New Script: `scripts/generate-hero-cache.js`
```javascript
// Local cache generation - run when hero cards change
// Requires local FastAPI server to be running
```

### Updated `package.json`
```json
{
  "scripts": {
    "generate-hero-cache": "node scripts/generate-hero-cache.js",
    "build": "next build"  // Remove prebuild hook
  }
}
```

### Git Integration
```
public/hero-cache/
├── manifest.json        # Committed to repo
├── *.png               # All cached images committed
└── .gitkeep            # Ensure directory exists
```

## Workflow

### For Developers
1. **When hero cards change**:
   ```bash
   npm run fastapi-dev        # Start local API
   npm run generate-hero-cache # Generate cache
   git add public/hero-cache  # Commit cache files
   git commit -m "Update hero card cache"
   ```

2. **Regular development**: No cache regeneration needed

### For Deployment
1. **Vercel build**: Just builds Next.js (no prebuild)
2. **Cache serving**: Static files served from `public/hero-cache/`
3. **Performance**: Instant loading from committed cache

## Migration Steps

1. Remove prebuild hook
2. Create new local generation script
3. Generate initial cache locally
4. Commit cache files to repo
5. Deploy and verify 