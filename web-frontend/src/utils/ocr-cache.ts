/**
 * OCR Cache Management
 * 
 * Implements localStorage-based caching for OCR results to:
 * - Reduce redundant API calls
 * - Improve user experience with instant results
 * - Decrease server load
 */

interface CachedResult {
    taskId: string;
    fileName: string;
    mode: string;
    result: any;
    timestamp: number;
}

export class OCRCache {
    private static readonly CACHE_PREFIX = 'ocr_';
    private static readonly MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours
    private static readonly MAX_CACHE_SIZE = 10; // Maximum number of cached items

    /**
     * Save OCR result to cache
     */
    static set(taskId: string, fileName: string, mode: string, result: any): void {
        try {
            const cached: CachedResult = {
                taskId,
                fileName,
                mode,
                result,
                timestamp: Date.now(),
            };

            const key = this.getCacheKey(taskId);
            localStorage.setItem(key, JSON.stringify(cached));

            // Cleanup old cache if needed
            this.cleanupOldCache();
        } catch (error) {
            console.warn('Failed to cache OCR result:', error);
            // If localStorage is full, clear old items
            if (error instanceof DOMException && error.name === 'QuotaExceededError') {
                this.clearOldestItem();
                // Try again
                this.set(taskId, fileName, mode, result);
            }
        }
    }

    /**
     * Get cached OCR result
     */
    static get(taskId: string): CachedResult | null {
        try {
            const key = this.getCacheKey(taskId);
            const cached = localStorage.getItem(key);

            if (!cached) return null;

            const data: CachedResult = JSON.parse(cached);
            const age = Date.now() - data.timestamp;

            // Check if cache is expired
            if (age > this.MAX_AGE_MS) {
                localStorage.removeItem(key);
                return null;
            }

            return data;
        } catch (error) {
            console.warn('Failed to get cached OCR result:', error);
            return null;
        }
    }

    /**
     * Check if result is cached
     */
    static has(taskId: string): boolean {
        return this.get(taskId) !== null;
    }

    /**
     * Remove specific cached result
     */
    static remove(taskId: string): void {
        const key = this.getCacheKey(taskId);
        localStorage.removeItem(key);
    }

    /**
     * Clear all OCR cache
     */
    static clear(): void {
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            if (key.startsWith(this.CACHE_PREFIX)) {
                localStorage.removeItem(key);
            }
        });
    }

    /**
     * Get all cached items sorted by timestamp
     */
    private static getAllCachedItems(): Array<{ key: string; data: CachedResult }> {
        const items: Array<{ key: string; data: CachedResult }> = [];

        Object.keys(localStorage).forEach(key => {
            if (key.startsWith(this.CACHE_PREFIX)) {
                try {
                    const data = JSON.parse(localStorage.getItem(key) || '');
                    items.push({ key, data });
                } catch {
                    // Invalid cache item, remove it
                    localStorage.removeItem(key);
                }
            }
        });

        return items.sort((a, b) => a.data.timestamp - b.data.timestamp);
    }

    /**
     * Cleanup old cache items
     */
    private static cleanupOldCache(): void {
        const items = this.getAllCachedItems();

        // Remove expired items
        const now = Date.now();
        items.forEach(({ key, data }) => {
            if (now - data.timestamp > this.MAX_AGE_MS) {
                localStorage.removeItem(key);
            }
        });

        // If still too many items, remove oldest
        const remainingItems = this.getAllCachedItems();
        if (remainingItems.length > this.MAX_CACHE_SIZE) {
            const toRemove = remainingItems.slice(0, remainingItems.length - this.MAX_CACHE_SIZE);
            toRemove.forEach(({ key }) => localStorage.removeItem(key));
        }
    }

    /**
     * Clear oldest cache item
     */
    private static clearOldestItem(): void {
        const items = this.getAllCachedItems();
        if (items.length > 0) {
            localStorage.removeItem(items[0].key);
        }
    }

    /**
     * Get cache key for task ID
     */
    private static getCacheKey(taskId: string): string {
        return `${this.CACHE_PREFIX}${taskId}`;
    }

    /**
     * Get cache statistics
     */
    static getStats(): {
        count: number;
        totalSize: number;
        oldestTimestamp: number | null;
        newestTimestamp: number | null;
    } {
        const items = this.getAllCachedItems();

        let totalSize = 0;
        items.forEach(({ key }) => {
            const item = localStorage.getItem(key);
            totalSize += item ? item.length : 0;
        });

        return {
            count: items.length,
            totalSize,
            oldestTimestamp: items.length > 0 ? items[0].data.timestamp : null,
            newestTimestamp: items.length > 0 ? items[items.length - 1].data.timestamp : null,
        };
    }
}

/**
 * Hook for using OCR cache in React components
 */
export function useOCRCache(taskId: string | null) {
    const getCached = () => {
        if (!taskId) return null;
        return OCRCache.get(taskId);
    };

    const setCached = (fileName: string, mode: string, result: any) => {
        if (!taskId) return;
        OCRCache.set(taskId, fileName, mode, result);
    };

    const clearCached = () => {
        if (!taskId) return;
        OCRCache.remove(taskId);
    };

    return {
        cached: getCached(),
        setCached,
        clearCached,
        hasCached: taskId ? OCRCache.has(taskId) : false,
    };
}
