import { useEffect, useRef, useCallback } from 'react';
import { rankingAPI } from '../services/profileAPI';

export interface ScoreSyncOptions {
  onSyncSuccess?: (data: any) => void;
  onSyncError?: (error: any) => void;
  debounceMs?: number;
  autoSync?: boolean;
}

export interface ScanCompletionEvent {
  type: 'scan_complete';
  userId: string;
  acidScore: number;
  timestamp: string;
}

/**
 * Custom hook for automatic score synchronization after repository scans
 * 
 * Features:
 * - Listens for scan completion events
 * - Debounces sync calls to prevent rapid successive syncs
 * - Automatic retry on failure
 * - Event cleanup on unmount
 */
export const useScoreSync = (options: ScoreSyncOptions = {}) => {
  const {
    onSyncSuccess,
    onSyncError,
    debounceMs = 2000,
    autoSync = true,
  } = options;

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastSyncTimeRef = useRef<number>(0);
  const retryCountRef = useRef<number>(0);
  const maxRetries = 3;

  /**
   * Sync user score with backend
   */
  const syncScore = useCallback(async () => {
    try {
      console.log('🔄 Syncing user score with rankings...');
      
      const response = await rankingAPI.syncScore();
      
      console.log('✅ Score sync successful:', response);
      
      // Reset retry count on success
      retryCountRef.current = 0;
      lastSyncTimeRef.current = Date.now();
      
      if (onSyncSuccess) {
        onSyncSuccess(response);
      }
      
      return response;
    } catch (error: any) {
      console.error('❌ Score sync failed:', error);
      
      // Retry logic
      if (retryCountRef.current < maxRetries) {
        retryCountRef.current++;
        const retryDelay = Math.pow(2, retryCountRef.current) * 1000; // Exponential backoff
        
        console.log(`🔄 Retrying score sync (attempt ${retryCountRef.current}/${maxRetries}) in ${retryDelay}ms...`);
        
        setTimeout(() => {
          syncScore();
        }, retryDelay);
      } else {
        console.error('❌ Max retry attempts reached for score sync');
        
        if (onSyncError) {
          onSyncError(error);
        }
      }
      
      throw error;
    }
  }, [onSyncSuccess, onSyncError]);

  /**
   * Debounced sync to prevent rapid successive calls
   */
  const debouncedSync = useCallback(() => {
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Check if we synced recently (within debounce window)
    const timeSinceLastSync = Date.now() - lastSyncTimeRef.current;
    if (timeSinceLastSync < debounceMs) {
      console.log(`⏳ Skipping sync - last sync was ${timeSinceLastSync}ms ago`);
      return;
    }

    // Set new timer
    debounceTimerRef.current = setTimeout(() => {
      syncScore();
    }, debounceMs);
  }, [syncScore, debounceMs]);

  /**
   * Handle scan completion event
   */
  const handleScanComplete = useCallback((event: CustomEvent<ScanCompletionEvent>) => {
    console.log('📊 Scan completion detected:', event.detail);
    
    if (autoSync) {
      debouncedSync();
    }
  }, [autoSync, debouncedSync]);

  /**
   * Manual sync trigger
   */
  const triggerSync = useCallback(() => {
    console.log('🔄 Manual score sync triggered');
    debouncedSync();
  }, [debouncedSync]);

  /**
   * Set up event listeners
   */
  useEffect(() => {
    if (!autoSync) {
      return;
    }

    // Listen for custom scan completion events
    const eventListener = (event: Event) => {
      handleScanComplete(event as CustomEvent<ScanCompletionEvent>);
    };

    window.addEventListener('scan_complete', eventListener);
    window.addEventListener('repository_scan_complete', eventListener);

    // Cleanup
    return () => {
      window.removeEventListener('scan_complete', eventListener);
      window.removeEventListener('repository_scan_complete', eventListener);
      
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [autoSync, handleScanComplete]);

  return {
    syncScore,
    triggerSync,
    isRecentlySync: () => {
      const timeSinceLastSync = Date.now() - lastSyncTimeRef.current;
      return timeSinceLastSync < debounceMs;
    },
  };
};

/**
 * Utility function to dispatch scan completion event
 * Call this after a repository scan completes
 */
export const dispatchScanCompleteEvent = (userId: string, acidScore: number) => {
  const event = new CustomEvent<ScanCompletionEvent>('scan_complete', {
    detail: {
      type: 'scan_complete',
      userId,
      acidScore,
      timestamp: new Date().toISOString(),
    },
  });
  
  window.dispatchEvent(event);
  console.log('📢 Scan completion event dispatched:', { userId, acidScore });
};
