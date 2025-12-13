import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import { scanAPI } from '../services/api';
import { ScanProgress, UseScanProgressOptions } from '../types';



export const useScanProgress = (options: UseScanProgressOptions = {}) => {
  const [scanProgresses, setScanProgresses] = useState<Record<string, ScanProgress>>({});
  const [activeScanIds, setActiveScanIds] = useState<Set<string>>(new Set());
  
  const { onComplete, onError, onProgress } = options;

  const handleWebSocketMessage = useCallback((message: any) => {
    if (message.type === 'scan_progress' && message.task_id && message.progress) {
      const scanId = message.task_id;
      const progress: ScanProgress = {
        scanId,
        status: message.progress.status || 'pending',
        progress: message.progress.progress || 0,
        currentRepo: message.progress.current_repo,
        totalRepos: message.progress.total_repos || 0,
        message: message.progress.message,
        errors: message.progress.errors || [],
        timestamp: message.timestamp
      };

      setScanProgresses(prev => ({
        ...prev,
        [scanId]: progress
      }));

      // Call progress callback
      onProgress?.(scanId, progress);

      // Handle completion or error
      if (progress.status === 'completed') {
        onComplete?.(scanId, progress);
        setActiveScanIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(scanId);
          return newSet;
        });
      } else if (progress.status === 'error') {
        onError?.(scanId, progress.message || 'Scan failed');
        setActiveScanIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(scanId);
          return newSet;
        });
      }
    }
  }, [onComplete, onError, onProgress]);

  const {
    isConnected,
    connectionState,
    subscribeToTask,
    unsubscribeFromTask
  } = useWebSocket({
    onMessage: handleWebSocketMessage
  });

  const startTracking = useCallback(async (scanId: string) => {
    // Add to active scans
    setActiveScanIds(prev => new Set(prev).add(scanId));
    
    // Subscribe to WebSocket updates
    if (isConnected) {
      subscribeToTask(scanId);
    }
    
    // Get initial progress from API
    try {
      const initialProgress = await scanAPI.getScanProgress(scanId);
      setScanProgresses(prev => ({
        ...prev,
        [scanId]: {
          scanId,
          status: initialProgress.status || 'pending',
          progress: initialProgress.progress || 0,
          currentRepo: initialProgress.currentRepo,
          totalRepos: initialProgress.totalRepos || 0,
          message: initialProgress.message,
          errors: [],
          timestamp: new Date().toISOString()
        }
      }));
    } catch (error) {
      console.error('Failed to get initial scan progress:', error);
    }
  }, [isConnected, subscribeToTask]);

  const stopTracking = useCallback((scanId: string) => {
    setActiveScanIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(scanId);
      return newSet;
    });
    
    unsubscribeFromTask(scanId);
    
    // Optionally remove from progress state
    setScanProgresses(prev => {
      const newState = { ...prev };
      delete newState[scanId];
      return newState;
    });
  }, [unsubscribeFromTask]);

  const getProgress = useCallback((scanId: string): ScanProgress | undefined => {
    return scanProgresses[scanId];
  }, [scanProgresses]);

  const isTracking = useCallback((scanId: string): boolean => {
    return activeScanIds.has(scanId);
  }, [activeScanIds]);

  const clearProgress = useCallback((scanId: string) => {
    setScanProgresses(prev => {
      const newState = { ...prev };
      delete newState[scanId];
      return newState;
    });
  }, []);

  const clearAllProgress = useCallback(() => {
    setScanProgresses({});
    setActiveScanIds(new Set());
  }, []);

  // Auto-subscribe to active scans when WebSocket connects
  useEffect(() => {
    if (isConnected && activeScanIds.size > 0) {
      activeScanIds.forEach(scanId => {
        subscribeToTask(scanId);
      });
    }
  }, [isConnected, activeScanIds, subscribeToTask]);

  return {
    // State
    scanProgresses,
    activeScanIds: Array.from(activeScanIds),
    isConnected,
    connectionState,
    
    // Actions
    startTracking,
    stopTracking,
    getProgress,
    isTracking,
    clearProgress,
    clearAllProgress
  };
};