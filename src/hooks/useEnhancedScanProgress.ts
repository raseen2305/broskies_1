import { useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { LiveFeedItemData } from '../components/LiveFeedItem';

// Enhanced progress event structure (Requirements: 1.1, 1.2, 1.3, 1.4, 1.5)
interface DetailedProgressEvent {
  // Core identification
  scanId: string;
  timestamp: string;
  
  // Progress tracking
  phase: 'connecting' | 'fetching_profile' | 'fetching_repos' | 
         'fetching_prs' | 'fetching_issues' | 'analyzing_code' | 
         'calculating_scores' | 'generating_insights' | 'completed';
  progressPercentage: number;
  
  // Current operation details
  currentOperation: {
    type: 'fetch_repo' | 'fetch_pr' | 'fetch_issue' | 'analyze_file' | 'calculate_score' | 'fetch_account';
    target: string;
    details: string;
    startTime: string;
  };
  
  // Account information (Requirements: 5.1, 5.2, 5.3, 5.4, 5.5)
  accountInfo?: {
    username: string;
    accountType: 'User' | 'Organization';
    avatarUrl: string;
    followers: number;
    following: number;
    publicRepos: number;
    totalStars: number;
    contributionStreak: number;
  };
  
  // Repository progress (Requirements: 1.2, 1.3)
  repositoryProgress?: {
    current: number;
    total: number;
    currentRepo?: {
      name: string;
      fullName: string;
      description: string;
      language: string;
      stars: number;
      forks: number;
      size: number;
      lastUpdated: string;
    };
  };
  
  // PR/Issue progress (Requirements: 1.4, 1.5)
  prProgress?: {
    fetched: number;
    total: number;
    openCount: number;
    closedCount: number;
    mergedCount: number;
  };
  
  issueProgress?: {
    fetched: number;
    total: number;
    openCount: number;
    closedCount: number;
  };
  
  // Analysis metrics (Requirements: 4.3, 4.4)
  analysisMetrics?: {
    filesAnalyzed: number;
    totalFiles: number;
    linesOfCode: number;
    apiCallsMade: number;
    apiCallsRemaining: number;
  };
  
  // Time estimates (Requirements: 4.5)
  timeEstimates: {
    elapsedSeconds: number;
    estimatedRemainingSeconds: number;
    estimatedCompletionTime: string;
  };
  
  // Status and errors
  status: 'in_progress' | 'completed' | 'error' | 'paused';
  errors: Array<{
    code: string;
    message: string;
    timestamp: string;
    recoverySuggestion?: string;
  }>;
}

// Legacy interface for backward compatibility
interface EnhancedScanProgress {
  scanId: string;
  status: string;
  phase: string;
  progressPercentage: number;
  message: string;
  currentRepository?: string;
  repositoriesProcessed: number;
  totalRepositories: number;
  errors: string[];
  startTime?: string;
  estimatedCompletion?: string;
  detailedProgress: {
    username?: string;
    scanType?: string;
    phasesCompleted: Array<{
      phase: string;
      completedAt: string;
      durationSeconds: number;
    }>;
    currentPhaseProgress: number;
  };
}

interface StatusMessage {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: Date;
  details?: string;
}

interface UseEnhancedScanProgressOptions {
  scanId?: string;
  onComplete?: (progress: EnhancedScanProgress) => void;
  onError?: (error: string) => void;
  onPhaseChange?: (phase: string, progress: EnhancedScanProgress) => void;
}

export const useEnhancedScanProgress = (options: UseEnhancedScanProgressOptions = {}) => {
  const { scanId, onComplete, onError, onPhaseChange } = options;
  
  const [progress, setProgress] = useState<EnhancedScanProgress | null>(null);
  const [detailedProgress, setDetailedProgress] = useState<DetailedProgressEvent | null>(null);
  const [statusMessages, setStatusMessages] = useState<StatusMessage[]>([]);
  const [liveFeedItems, setLiveFeedItems] = useState<LiveFeedItemData[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [scanStartTime, setScanStartTime] = useState<Date | null>(null);
  
  // Account info state (Requirements: 5.1, 5.2, 5.3, 5.4, 5.5)
  const [accountInfo, setAccountInfo] = useState<DetailedProgressEvent['accountInfo'] | null>(null);
  
  // Repository progress state (Requirements: 1.2, 1.3)
  const [repositoryProgress, setRepositoryProgress] = useState<DetailedProgressEvent['repositoryProgress'] | null>(null);
  
  // PR/Issue progress state (Requirements: 1.4, 1.5)
  const [prProgress, setPrProgress] = useState<DetailedProgressEvent['prProgress'] | null>(null);
  const [issueProgress, setIssueProgress] = useState<DetailedProgressEvent['issueProgress'] | null>(null);
  
  // Analysis metrics state (Requirements: 4.3, 4.4)
  const [analysisMetrics, setAnalysisMetrics] = useState<DetailedProgressEvent['analysisMetrics'] | null>(null);
  
  const previousPhaseRef = useRef<string>('');
  const messageIdCounterRef = useRef(0);
  const liveFeedIdCounterRef = useRef(0);
  const maxProgressRef = useRef<number>(0); // Track maximum progress to prevent backwards movement

  const addStatusMessage = useCallback((type: StatusMessage['type'], message: string, details?: string) => {
    const newMessage: StatusMessage = {
      id: `msg-${messageIdCounterRef.current++}`,
      type,
      message,
      details,
      timestamp: new Date()
    };
    
    setStatusMessages(prev => [...prev.slice(-20), newMessage]); // Keep last 20 messages
  }, []);

  // Generate live feed item from progress event (Requirements: 3.1, 3.2, 3.3)
  const createLiveFeedItem = useCallback((event: DetailedProgressEvent): LiveFeedItemData => {
    const { currentOperation, repositoryProgress, analysisMetrics, status } = event;
    
    // Determine item type based on status and errors
    let itemType: LiveFeedItemData['type'] = 'info';
    if (status === 'completed') itemType = 'success';
    else if (status === 'error' || event.errors.length > 0) itemType = 'error';
    
    // Determine item status
    let itemStatus: LiveFeedItemData['status'] = 'in_progress';
    if (status === 'completed') itemStatus = 'completed';
    else if (status === 'error') itemStatus = 'failed';
    else if (status === 'paused') itemStatus = 'pending';
    
    // Build metadata
    const metadata: LiveFeedItemData['metadata'] = {};
    if (repositoryProgress?.currentRepo) {
      metadata.repoName = repositoryProgress.currentRepo.name;
    }
    if (currentOperation.type === 'analyze_file') {
      metadata.fileName = currentOperation.target;
    }
    if (analysisMetrics) {
      metadata.count = analysisMetrics.filesAnalyzed;
    }
    
    return {
      id: `feed-${liveFeedIdCounterRef.current++}`,
      timestamp: new Date(event.timestamp),
      type: itemType,
      title: formatOperationType(currentOperation.type),
      description: currentOperation.details,
      metadata,
      status: itemStatus
    };
  }, []);

  // Format operation type for display
  const formatOperationType = (type: string): string => {
    const typeMap: Record<string, string> = {
      'fetch_repo': 'Fetching Repository',
      'fetch_pr': 'Fetching Pull Requests',
      'fetch_issue': 'Fetching Issues',
      'analyze_file': 'Analyzing File',
      'calculate_score': 'Calculating Score',
      'fetch_account': 'Fetching Account Info'
    };
    return typeMap[type] || type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const handleWebSocketMessage = useCallback((message: any) => {
    // Handle new detailed progress events (Requirements: 1.1, 1.2, 1.3, 1.4, 1.5)
    if (message.type === 'scan_progress' && message.progress) {
      const progressEvent = message.progress as DetailedProgressEvent;
      
      // Only process messages for our scan ID
      if (scanId && progressEvent.scanId !== scanId) {
        return;
      }
      
      // Ensure progress never decreases - only update if new progress is higher
      if (progressEvent.progressPercentage < maxProgressRef.current) {
        progressEvent.progressPercentage = maxProgressRef.current;
      } else {
        maxProgressRef.current = progressEvent.progressPercentage;
      }
      
      // Update detailed progress
      setDetailedProgress(progressEvent);
      
      // Update account info (Requirements: 5.1, 5.2, 5.3, 5.4, 5.5)
      if (progressEvent.accountInfo) {
        setAccountInfo(progressEvent.accountInfo);
      }
      
      // Update repository progress (Requirements: 1.2, 1.3)
      if (progressEvent.repositoryProgress) {
        setRepositoryProgress(progressEvent.repositoryProgress);
      }
      
      // Update PR progress (Requirements: 1.4)
      if (progressEvent.prProgress) {
        setPrProgress(progressEvent.prProgress);
      }
      
      // Update issue progress (Requirements: 1.5)
      if (progressEvent.issueProgress) {
        setIssueProgress(progressEvent.issueProgress);
      }
      
      // Update analysis metrics (Requirements: 4.3, 4.4)
      if (progressEvent.analysisMetrics) {
        setAnalysisMetrics(progressEvent.analysisMetrics);
      }
      
      // Generate live feed item
      if (!isPaused) {
        const feedItem = createLiveFeedItem(progressEvent);
        setLiveFeedItems(prev => [...prev, feedItem]);
      }
      
      // Track phase changes
      if (previousPhaseRef.current !== progressEvent.phase) {
        previousPhaseRef.current = progressEvent.phase;
        onPhaseChange?.(progressEvent.phase, progress!);
        
        // Add status message for phase change
        addStatusMessage('info', `Started ${progressEvent.phase.replace(/_/g, ' ')} phase`);
      }
      
      // Handle completion
      if (progressEvent.status === 'completed') {
        setIsScanning(false);
        addStatusMessage('success', 'Scan completed successfully!');
        onComplete?.(progress!);
      }
      
      // Handle errors
      if (progressEvent.errors && progressEvent.errors.length > 0) {
        const latestError = progressEvent.errors[progressEvent.errors.length - 1];
        addStatusMessage('error', 'Scan error occurred', latestError.message);
        onError?.(latestError.message);
      }
      
      // Convert to legacy format for backward compatibility
      const legacyProgress: EnhancedScanProgress = {
        scanId: progressEvent.scanId,
        status: progressEvent.status,
        phase: progressEvent.phase,
        progressPercentage: progressEvent.progressPercentage,
        message: progressEvent.currentOperation.details,
        currentRepository: progressEvent.repositoryProgress?.currentRepo?.name,
        repositoriesProcessed: progressEvent.repositoryProgress?.current || 0,
        totalRepositories: progressEvent.repositoryProgress?.total || 0,
        errors: progressEvent.errors.map(e => e.message),
        startTime: progressEvent.currentOperation.startTime,
        estimatedCompletion: progressEvent.timeEstimates.estimatedCompletionTime,
        detailedProgress: {
          username: progressEvent.accountInfo?.username,
          scanType: 'comprehensive',
          phasesCompleted: [],
          currentPhaseProgress: progressEvent.progressPercentage
        }
      };
      setProgress(legacyProgress);
    }
    // Handle legacy progress updates for backward compatibility
    else if (message.type === 'progress_update' && message.data) {
      const progressData = message.data as EnhancedScanProgress;
      
      // Only process messages for our scan ID
      if (scanId && progressData.scanId !== scanId) {
        return;
      }
      
      setProgress(progressData);
      
      // Track phase changes
      if (previousPhaseRef.current !== progressData.phase) {
        previousPhaseRef.current = progressData.phase;
        onPhaseChange?.(progressData.phase, progressData);
        
        // Add status message for phase change
        addStatusMessage('info', `Started ${progressData.phase.replace('_', ' ')} phase`, progressData.message);
      }
      
      // Handle completion
      if (progressData.status === 'completed') {
        setIsScanning(false);
        addStatusMessage('success', 'Scan completed successfully!');
        onComplete?.(progressData);
      }
      
      // Handle errors
      if (progressData.errors && progressData.errors.length > 0) {
        const latestError = progressData.errors[progressData.errors.length - 1];
        addStatusMessage('error', 'Scan error occurred', latestError);
        onError?.(latestError);
      }
      
      // Add progress updates
      if (progressData.currentRepository) {
        addStatusMessage('info', `Analyzing repository: ${progressData.currentRepository}`);
      }
    } else if (message.type === 'error_notification') {
      addStatusMessage('error', 'Scan error', message.error?.message || 'Unknown error occurred');
      onError?.(message.error?.message || 'Unknown error occurred');
    } else if (message.type === 'scan_completed') {
      setIsScanning(false);
      addStatusMessage('success', 'Scan completed!', 'Results are ready for review');
    }
  }, [scanId, onComplete, onError, onPhaseChange, addStatusMessage, createLiveFeedItem, isPaused, progress]);

  const { isConnected, sendMessage, subscribeToTask } = useWebSocket({
    onMessage: handleWebSocketMessage,
    onConnect: () => {
      addStatusMessage('success', 'Connected to real-time updates');
      // Subscribe to scan updates if we have a scan ID
      if (scanId) {
        subscribeToTask(scanId);
      }
    },
    onDisconnect: () => {
      addStatusMessage('warning', 'Lost connection to real-time updates');
    },
    onError: () => {
      addStatusMessage('error', 'Connection error occurred');
    }
  });

  // Start scanning
  const startScan = useCallback((newScanId: string) => {
    setIsScanning(true);
    setScanStartTime(new Date());
    setProgress(null);
    setStatusMessages([]);
    previousPhaseRef.current = '';
    maxProgressRef.current = 0; // Reset max progress for new scan
    
    addStatusMessage('info', 'Starting scan...', `Scan ID: ${newScanId}`);
    
    // Subscribe to the new scan
    if (isConnected) {
      subscribeToTask(newScanId);
    }
  }, [isConnected, subscribeToTask, addStatusMessage]);

  // Stop scanning
  const stopScan = useCallback(() => {
    setIsScanning(false);
    addStatusMessage('info', 'Scan stopped by user');
  }, [addStatusMessage]);

  // Toggle pause state (Requirements: 7.4)
  const togglePause = useCallback(() => {
    setIsPaused(prev => {
      const newState = !prev;
      addStatusMessage('info', newState ? 'Live feed paused' : 'Live feed resumed');
      return newState;
    });
  }, [addStatusMessage]);

  // Clear live feed
  const clearLiveFeed = useCallback(() => {
    setLiveFeedItems([]);
    addStatusMessage('info', 'Live feed cleared');
  }, [addStatusMessage]);

  // Subscribe to scan updates when scan ID changes
  useEffect(() => {
    if (scanId && isConnected) {
      subscribeToTask(scanId);
      addStatusMessage('info', `Subscribed to scan updates: ${scanId}`);
    }
  }, [scanId, isConnected, subscribeToTask, addStatusMessage]);

  // Calculate derived values (Requirements: 4.5)
  const estimatedTimeRemaining = detailedProgress?.timeEstimates.estimatedRemainingSeconds 
    || (progress?.estimatedCompletion 
      ? Math.max(0, (new Date(progress.estimatedCompletion).getTime() - new Date().getTime()) / 1000)
      : undefined);

  const scanDuration = detailedProgress?.timeEstimates.elapsedSeconds
    || (scanStartTime 
      ? (new Date().getTime() - scanStartTime.getTime()) / 1000
      : 0);

  return {
    // Core progress data
    progress,
    detailedProgress,
    isScanning,
    isConnected,
    isPaused,
    
    // Time tracking (Requirements: 4.5)
    scanStartTime,
    scanDuration,
    estimatedTimeRemaining,
    estimatedCompletionTime: detailedProgress?.timeEstimates.estimatedCompletionTime,
    
    // Status and messages
    statusMessages,
    liveFeedItems,
    
    // Account info (Requirements: 5.1, 5.2, 5.3, 5.4, 5.5)
    accountInfo,
    
    // Repository progress (Requirements: 1.2, 1.3, 4.1, 4.2)
    repositoryProgress,
    currentRepository: repositoryProgress?.currentRepo,
    repositoriesProcessed: repositoryProgress?.current || progress?.repositoriesProcessed || 0,
    totalRepositories: repositoryProgress?.total || progress?.totalRepositories || 0,
    
    // PR/Issue progress (Requirements: 1.4, 1.5)
    prProgress,
    issueProgress,
    
    // Analysis metrics (Requirements: 4.3, 4.4)
    analysisMetrics,
    filesAnalyzed: analysisMetrics?.filesAnalyzed || 0,
    totalFiles: analysisMetrics?.totalFiles || 0,
    linesOfCode: analysisMetrics?.linesOfCode || 0,
    apiCallsMade: analysisMetrics?.apiCallsMade || 0,
    apiCallsRemaining: analysisMetrics?.apiCallsRemaining || 0,
    
    // Actions
    startScan,
    stopScan,
    togglePause,
    clearLiveFeed,
    addStatusMessage,
    
    // Derived values
    currentPhase: detailedProgress?.phase || progress?.phase || 'connecting',
    currentOperation: detailedProgress?.currentOperation,
    progressPercentage: detailedProgress?.progressPercentage || progress?.progressPercentage || 0,
    hasErrors: (detailedProgress?.errors?.length || progress?.errors?.length || 0) > 0,
    errors: detailedProgress?.errors || [],
    
    // WebSocket controls
    sendMessage
  };
};