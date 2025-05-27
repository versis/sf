#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

// Import hero card configuration from centralized source
// Since this is a Node.js script, we need to read the TypeScript file and extract the array
function loadHeroCardIds() {
  try {
    const configPath = path.join(process.cwd(), 'lib', 'heroCardConfig.ts');
    const configContent = fs.readFileSync(configPath, 'utf8');
    
    // Extract the array from the TypeScript file using regex
    const arrayMatch = configContent.match(/export const HERO_CARD_IDS = \[([\s\S]*?)\];/);
    if (!arrayMatch) {
      throw new Error('Could not find HERO_CARD_IDS array in heroCardConfig.ts');
    }
    
    // Parse the array content
    const arrayContent = arrayMatch[1];
    const ids = arrayContent
      .split(',')
      .map(line => line.trim())
      .filter(line => line.startsWith('"'))
      .map(line => line.replace(/"/g, ''));
    
    console.log(`📋 Loaded ${ids.length} hero card IDs from centralized config`);
    return ids;
  } catch (error) {
    console.error('❌ Failed to load hero card IDs from config:', error.message);
    console.error('💥 Cannot proceed without centralized configuration');
    console.error('🔧 Please ensure lib/heroCardConfig.ts exists and is properly formatted');
    process.exit(1);
  }
}

const HERO_CARD_IDS = loadHeroCardIds();

const CACHE_DIR = path.join(process.cwd(), 'public', 'hero-cache');
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

// Ensure cache directory exists
function ensureCacheDir() {
  if (fs.existsSync(CACHE_DIR)) {
    // Clean existing cache
    console.log('🧹 Cleaning existing hero cache...');
    fs.rmSync(CACHE_DIR, { recursive: true, force: true });
  }
  
  fs.mkdirSync(CACHE_DIR, { recursive: true });
  console.log('📁 Created hero cache directory:', CACHE_DIR);
}

// Download image from URL to local file
function downloadImage(url, filename) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https:') ? https : http;
    const filePath = path.join(CACHE_DIR, filename);
    
    console.log(`⬇️  Downloading: ${filename}`);
    
    protocol.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download ${url}: ${response.statusCode}`));
        return;
      }
      
      const fileStream = fs.createWriteStream(filePath);
      response.pipe(fileStream);
      
      fileStream.on('finish', () => {
        fileStream.close();
        console.log(`✅ Downloaded: ${filename}`);
        resolve(filePath);
      });
      
      fileStream.on('error', reject);
    }).on('error', reject);
  });
}

// Fetch hero card data from API
async function fetchHeroCards() {
  console.log('🔍 Fetching hero card data...');
  
  const response = await fetch(`${API_BASE_URL}/api/batch-retrieve-cards`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ extended_ids: HERO_CARD_IDS }),
  });
  
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  
  const data = await response.json();
  console.log(`📊 Fetched data for ${Object.keys(data.cards).length} cards`);
  
  return data.cards;
}

// Generate safe filename from URL
function getFilenameFromUrl(url, prefix = '') {
  const urlObj = new URL(url);
  const pathname = urlObj.pathname;
  const filename = path.basename(pathname);
  return prefix ? `${prefix}_${filename}` : filename;
}

// Calculate total cache size in MB
function getCacheSize() {
  try {
    let totalSize = 0;
    const files = fs.readdirSync(CACHE_DIR);
    
    for (const file of files) {
      const filePath = path.join(CACHE_DIR, file);
      const stats = fs.statSync(filePath);
      totalSize += stats.size;
    }
    
    return (totalSize / (1024 * 1024)).toFixed(2);
  } catch (error) {
    console.warn('⚠️  Could not calculate cache size:', error.message);
    return 'unknown';
  }
}

// Main caching function
async function cacheHeroCards() {
  try {
    console.log('🚀 Starting hero card caching...');
    
    // Step 1: Prepare cache directory
    ensureCacheDir();
    
    // Step 2: Fetch card data
    const cards = await fetchHeroCards();
    
    // Step 3: Download images
    const downloadPromises = [];
    const cardManifest = {};
    
    console.log(`🔄 Processing ${Object.keys(cards).length} cards for image downloads...`);
    
    for (const [extendedId, cardData] of Object.entries(cards)) {
      if (!cardData) {
        console.log(`⚠️  No data for card: ${extendedId}`);
        continue;
      }
      
      const cardId = extendedId.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
      cardManifest[extendedId] = {
        id: extendedId,
        v: null,
        h: null,
        bv: null,
        bh: null,
      };
      
      // Download front images
      if (cardData.front_vertical_image_url) {
        const filename = `${cardId}_front_vertical.png`;
        downloadPromises.push(
          downloadImage(cardData.front_vertical_image_url, filename)
            .then(() => {
              cardManifest[extendedId].v = `/hero-cache/${filename}`;
            })
        );
      }
      
      if (cardData.front_horizontal_image_url) {
        const filename = `${cardId}_front_horizontal.png`;
        downloadPromises.push(
          downloadImage(cardData.front_horizontal_image_url, filename)
            .then(() => {
              cardManifest[extendedId].h = `/hero-cache/${filename}`;
            })
        );
      }
      
      // Download back images
      if (cardData.back_vertical_image_url) {
        const filename = `${cardId}_back_vertical.png`;
        downloadPromises.push(
          downloadImage(cardData.back_vertical_image_url, filename)
            .then(() => {
              cardManifest[extendedId].bv = `/hero-cache/${filename}`;
            })
        );
      }
      
      if (cardData.back_horizontal_image_url) {
        const filename = `${cardId}_back_horizontal.png`;
        downloadPromises.push(
          downloadImage(cardData.back_horizontal_image_url, filename)
            .then(() => {
              cardManifest[extendedId].bh = `/hero-cache/${filename}`;
            })
        );
      }
    }
    
    // Wait for all downloads to complete
    await Promise.all(downloadPromises);
    
    // Step 4: Save manifest
    const manifestPath = path.join(CACHE_DIR, 'manifest.json');
    fs.writeFileSync(manifestPath, JSON.stringify(cardManifest, null, 2));
    console.log('📋 Saved card manifest:', manifestPath);
    
    console.log('🎉 Hero card caching completed successfully!');
    console.log(`📁 Cache location: ${CACHE_DIR}`);
    console.log(`🃏 Cached ${Object.keys(cardManifest).length} cards`);
    console.log(`🖼️  Downloaded ${downloadPromises.length} images`);
    console.log(`💾 Total cache size: ${getCacheSize()} MB`);
    
  } catch (error) {
    console.error('❌ Error caching hero cards:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  cacheHeroCards();
}

module.exports = { cacheHeroCards }; 