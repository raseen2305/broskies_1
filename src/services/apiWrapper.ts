/**
 * Enhanced API wrapper with loading states, error handling, and retry logic
 */

import { useState, useCallback } from 'react';
import { errorHandler } from '../utils/errorHandler';

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

export interface ApiOptions {
  retries?: number;
  retryDelay?: number;
  timeout?: number;
  showErrorNotification?: boolean;
  cacheKey?: string;
  cacheDuration?: number; // in milliseconds
}

// Simple in-memory cache
const apiCache = new Map<string, { data: any; timestamp: number; duration: number }>();

export class ApiWrapper {
  private static instance: ApiWrapper;
  
  static getInstance(): ApiWrapper {
    if (!ApiWrapper.instance) {
      ApiWrapper.instance = new ApiWrapper();
    }
    return ApiWrapper.instance;
  }

  /**
   * Execute API call with enhanced error handling and retry logic
   */
  async executeWithRetry<T>(
    apiCall: () => Promise<T>,
    options: ApiOptions = {}
  ): Promise<T> {
    const {
      retries = 3,
      retryDelay = 1000,
      timeout = 30000,
      showErrorNotification = true,
      cacheKey,
      cacheDuration = 300000 // 5 minutes default
    } = options;

    // Check cache first
    if (cacheKey) {
      const cached = apiCache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < cached.duration) {
        return cached.data;
      }
    }

    let lastError: any;
    
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        // Add timeout to the API call
        const result = await Promise.race([
          apiCall(),
          new Promise<never>((_, reject) => 
            setTimeout(() => reject(new Error('Request timeout')), timeout)
          )
        ]);

        // Cache successful result
        if (cacheKey) {
          apiCache.set(cacheKey, {
            data: result,
            timestamp: Date.now(),
            duration: cacheDuration
          });
        }

        return result;
      } catch (error) {
        lastError = error;
        
        // Don't retry on client errors (4xx) except 429 (rate limit)
        if ((error as any).response?.status >= 400 && (error as any).response?.status < 500 && (error as any).response?.status !== 429) {
          break;
        }
        
        // Don't retry on the last attempt
        if (attempt === retries) {
          break;
        }
        
        // Wait before retrying with exponential backoff
        const delay = retryDelay * Math.pow(2, attempt - 1);
        console.log(`API call failed (attempt ${attempt}/${retries}). Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    // Handle the final error
    if (showErrorNotification) {
      errorHandler.handleApiError(lastError);
    }
    
    throw lastError;
  }

  /**
   * Clear cache for a specific key or all cache
   */
  clearCache(key?: string): void {
    if (key) {
      apiCache.delete(key);
    } else {
      apiCache.clear();
    }
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: apiCache.size,
      keys: Array.from(apiCache.keys())
    };
  }
}

/**
 * React hook for API calls with loading states and error handling
 */
export function useApiCall<T>(
  apiCall: () => Promise<T>,
  options: ApiOptions & { immediate?: boolean } = {}
) {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: null,
    lastUpdated: null
  });

  const apiWrapper = ApiWrapper.getInstance();
  const { immediate = false, ...apiOptions } = options;

  const execute = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const result = await apiWrapper.executeWithRetry(apiCall, apiOptions);
      setState({
        data: result,
        loading: false,
        error: null,
        lastUpdated: new Date()
      });
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage
      }));
      throw error;
    }
  }, [apiCall, apiOptions]);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
      lastUpdated: null
    });
  }, []);

  const refresh = useCallback(() => {
    if (options.cacheKey) {
      apiWrapper.clearCache(options.cacheKey);
    }
    return execute();
  }, [execute, options.cacheKey]);

  // Execute immediately if requested
  React.useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate, execute]);

  return {
    ...state,
    execute,
    reset,
    refresh,
    isStale: state.lastUpdated ? Date.now() - state.lastUpdated.getTime() > (options.cacheDuration || 300000) : false
  };
}

/**
 * Hook for paginated API calls
 */
export function usePaginatedApiCall<T>(
  apiCall: (page: number, limit: number) => Promise<{ data: T[]; total: number; page: number; limit: number }>,
  options: ApiOptions & { initialPage?: number; initialLimit?: number } = {}
) {
  const { initialPage = 1, initialLimit = 10, ...apiOptions } = options;
  
  const [page, setPage] = useState(initialPage);
  const [limit, setLimit] = useState(initialLimit);
  const [allData, setAllData] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  
  const paginatedCall = useCallback(() => {
    return apiCall(page, limit);
  }, [apiCall, page, limit]);

  const {
    data: pageData,
    loading,
    error,
    execute,
    lastUpdated
  } = useApiCall(paginatedCall, {
    ...apiOptions,
    cacheKey: options.cacheKey ? `${options.cacheKey}_page_${page}_limit_${limit}` : undefined
  });

  // Update aggregated data when page data changes
  React.useEffect(() => {
    if (pageData) {
      if (page === 1) {
        setAllData(pageData.data);
      } else {
        setAllData(prev => [...prev, ...pageData.data]);
      }
      setTotal(pageData.total);
    }
  }, [pageData, page]);

  const loadMore = useCallback(() => {
    if (!loading && allData.length < total) {
      setPage(prev => prev + 1);
    }
  }, [loading, allData.length, total]);

  const reset = useCallback(() => {
    setPage(initialPage);
    setAllData([]);
    setTotal(0);
  }, [initialPage]);

  const hasMore = allData.length < total;
  const progress = total > 0 ? (allData.length / total) * 100 : 0;

  return {
    data: allData,
    loading,
    error,
    lastUpdated,
    page,
    limit,
    total,
    hasMore,
    progress,
    loadMore,
    reset,
    refresh: execute,
    setLimit: (newLimit: number) => {
      setLimit(newLimit);
      reset();
    }
  };
}

/**
 * Hook for real-time data with polling
 */
export function usePollingApiCall<T>(
  apiCall: () => Promise<T>,
  options: ApiOptions & { 
    interval?: number; 
    enabled?: boolean;
    stopOnError?: boolean;
  } = {}
) {
  const { interval = 5000, enabled = true, stopOnError = false, ...apiOptions } = options;
  const [isPolling, setIsPolling] = useState(false);
  
  const apiState = useApiCall(apiCall, apiOptions);
  
  React.useEffect(() => {
    if (!enabled || !apiState.data) return;
    
    setIsPolling(true);
    const intervalId = setInterval(async () => {
      try {
        await apiState.execute();
      } catch (error) {
        if (stopOnError) {
          setIsPolling(false);
          clearInterval(intervalId);
        }
      }
    }, interval);

    return () => {
      clearInterval(intervalId);
      setIsPolling(false);
    };
  }, [enabled, interval, stopOnError, apiState.execute, apiState.data]);

  return {
    ...apiState,
    isPolling,
    startPolling: () => setIsPolling(true),
    stopPolling: () => setIsPolling(false)
  };
}

// Re-export React for hooks
import React from 'react';

export default ApiWrapper.getInstance();