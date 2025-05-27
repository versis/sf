/**
 * Simple in-memory cache for hero cards to avoid repeated API calls
 */

interface CachedCardData {
  id: string;
  v: string | null;
  h: string | null;
  bv: string | null;
  bh: string | null;
}

interface CacheEntry {
  data: CachedCardData[];
  timestamp: number;
  expiresAt: number;
}

class HeroCardCache {
  private cache: Map<string, CacheEntry> = new Map();
  private readonly CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

  private getCacheKey(extendedIds: string[]): string {
    return extendedIds.sort().join(',');
  }

  set(extendedIds: string[], data: CachedCardData[]): void {
    const key = this.getCacheKey(extendedIds);
    const now = Date.now();
    
    this.cache.set(key, {
      data: [...data], // Create a copy to avoid mutations
      timestamp: now,
      expiresAt: now + this.CACHE_DURATION,
    });

    console.log(`[Hero Cache] Cached ${data.length} cards for key: ${key.substring(0, 50)}...`);
  }

  get(extendedIds: string[]): CachedCardData[] | null {
    const key = this.getCacheKey(extendedIds);
    const entry = this.cache.get(key);

    if (!entry) {
      console.log(`[Hero Cache] Cache miss for key: ${key.substring(0, 50)}...`);
      return null;
    }

    const now = Date.now();
    if (now > entry.expiresAt) {
      console.log(`[Hero Cache] Cache expired for key: ${key.substring(0, 50)}...`);
      this.cache.delete(key);
      return null;
    }

    console.log(`[Hero Cache] Cache hit for key: ${key.substring(0, 50)}... (age: ${Math.round((now - entry.timestamp) / 1000)}s)`);
    return [...entry.data]; // Return a copy to avoid mutations
  }

  clear(): void {
    console.log(`[Hero Cache] Clearing cache (${this.cache.size} entries)`);
    this.cache.clear();
  }

  // Clean up expired entries
  cleanup(): void {
    const now = Date.now();
    let removedCount = 0;

    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.cache.delete(key);
        removedCount++;
      }
    }

    if (removedCount > 0) {
      console.log(`[Hero Cache] Cleaned up ${removedCount} expired entries`);
    }
  }

  getStats(): { size: number; entries: Array<{ key: string; age: number; expiresIn: number }> } {
    const now = Date.now();
    const entries = Array.from(this.cache.entries()).map(([key, entry]) => ({
      key: key.substring(0, 50) + (key.length > 50 ? '...' : ''),
      age: Math.round((now - entry.timestamp) / 1000),
      expiresIn: Math.round((entry.expiresAt - now) / 1000),
    }));

    return {
      size: this.cache.size,
      entries,
    };
  }
}

// Export a singleton instance
export const heroCardCache = new HeroCardCache();

// Optional: Set up periodic cleanup
if (typeof window !== 'undefined') {
  setInterval(() => {
    heroCardCache.cleanup();
  }, 60 * 60 * 1000); // Clean up every hour
} 