#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

console.log('🎯 Hero Card Cache Generator');
console.log('📝 This script generates hero card cache for faster loading');
console.log('⚠️  Requirements: Local FastAPI server must be running on localhost:8000');
console.log('');

// Import hero card configuration from centralized source
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
const API_BASE_URL = 'http://localhost:8000';

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

// Check if local API server is running
async function checkApiServer() {
  console.log('🔍 Checking if local API server is running...');
  
  try {
    const response = await fetch(`${API_BASE_URL}/docs`);
    if (response.ok) {
      console.log('✅ Local FastAPI server is running');
      return true;
    } else {
      throw new Error(`Server responded with status: ${response.status}`);
    }
  } catch (error) {
    console.error('❌ Local FastAPI server is not running or not accessible');
    console.error('🚀 Please start the server first:');
    console.error('   npm run fastapi-dev');
    console.error('');
    console.error('📍 Then run this script again:');
    console.error('   npm run generate-hero-cache');
    process.exit(1);
  }
}

// Fetch hero card data from API
async function fetchHeroCards() {
  console.log('🔍 Fetching hero card data from local API...');
  
  const response = await fetch(`${API_BASE_URL}/api/batch-retrieve-cards`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ extended_ids: HERO_CARD_IDS }),
  });
  
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }
  
  const data = await response.json();
  console.log(`📊 Fetched data for ${Object.keys(data.cards).length} cards`);
  
  return data.cards;
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

// Main cache generation function
async function generateHeroCache() {
  try {
    console.log('🚀 Starting hero card cache generation...');
    
    // Step 1: Check if API server is running
    await checkApiServer();
    
    // Step 2: Prepare cache directory
    ensureCacheDir();
    
    // Step 3: Fetch card data
    const cards = await fetchHeroCards();
    
    // Step 4: Download images
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
    
    // Step 5: Save manifest
    const manifestPath = path.join(CACHE_DIR, 'manifest.json');
    fs.writeFileSync(manifestPath, JSON.stringify(cardManifest, null, 2));
    console.log('📋 Saved card manifest:', manifestPath);
    
    console.log('');
    console.log('🎉 Hero card cache generation completed successfully!');
    console.log(`📁 Cache location: ${CACHE_DIR}`);
    console.log(`🃏 Cached ${Object.keys(cardManifest).length} cards`);
    console.log(`🖼️  Downloaded ${downloadPromises.length} images`);
    console.log(`💾 Total cache size: ${getCacheSize()} MB`);
    console.log('');
    console.log('📝 Next steps:');
    console.log('   1. Review the generated cache files');
    console.log('   2. Commit the cache to git:');
    console.log('      git add public/hero-cache');
    console.log('      git commit -m "Update hero card cache"');
    console.log('   3. Deploy to production');
    
  } catch (error) {
    console.error('❌ Error generating hero card cache:', error.message);
    console.error('');
    console.error('🔧 Troubleshooting:');
    console.error('   1. Ensure FastAPI server is running: npm run fastapi-dev');
    console.error('   2. Check that hero cards exist in the database');
    console.error('   3. Verify network connectivity');
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  generateHeroCache();
}

module.exports = { generateHeroCache }; 