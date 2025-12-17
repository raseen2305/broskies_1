import { useState, useEffect, useCallback } from 'react';
import { UserRankings } from '../types';

interface RankingChange {
  type: 'improvement' | 'decline' | 'achievement';
  message: string;
  previousRank?: number;
  newRank?: number;
  percentileChange?: number;
  timestamp: Date;
}

interface UseRankingNotificationsOptions {
  onNotification?: (notification: RankingChange) => void;
  significantChangeThreshold?: number; // Percentile change threshold
  enableToasts?: boolean;
}

/**
 * Custom hook for tracking ranking changes and showing notifications
 */
export const useRankingNotifications = (options: UseRankingNotificationsOptions = {}) => {
  const {
    onNotification,
    significantChangeThreshold = 5, // 5% percentile change
    enableToasts = true
  } = options;

  const [notifications, setNotifications] = useState<RankingChange[]>([]);
  const [previousRankings, setPreviousRankings] = useState<UserRankings | null>(null);

  /**
   * Show toast notification
   */
  const showToast = useCallback((notification: RankingChange) => {
    if (!enableToasts) return;

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `
      fixed top-4 right-4 z-50 max-w-sm bg-white border border-gray-200 rounded-lg shadow-lg p-4
      transform transition-all duration-300 ease-in-out translate-x-full opacity-0
    `;

    // Toast content
    const icon = notification.type === 'improvement' ? '🎉' : 
                 notification.type === 'achievement' ? '🏆' : '📊';
    
    const bgColor = notification.type === 'improvement' ? 'bg-green-50 border-green-200' :
                    notification.type === 'achievement' ? 'bg-yellow-50 border-yellow-200' :
                    'bg-blue-50 border-blue-200';

    toast.innerHTML = `
      <div class="flex items-start space-x-3">
        <div class="text-2xl">${icon}</div>
        <div class="flex-1">
          <div class="font-medium text-gray-900">Ranking Update</div>
          <div class="text-sm text-gray-600 mt-1">${notification.message}</div>
        </div>
        <button class="text-gray-400 hover:text-gray-600 ml-2" onclick="this.parentElement.parentElement.remove()">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
          </svg>
        </button>
      </div>
    `;

    toast.className = toast.className.replace('translate-x-full opacity-0', bgColor);

    // Add to DOM
    document.body.appendChild(toast);

    // Animate in
    setTimeout(() => {
      toast.className = toast.className.replace('translate-x-full opacity-0', 'translate-x-0 opacity-100');
    }, 100);

    // Auto remove after 5 seconds
    setTimeout(() => {
      toast.className = toast.className.replace('translate-x-0 opacity-100', 'translate-x-full opacity-0');
      setTimeout(() => {
        if (toast.parentElement) {
          toast.remove();
        }
      }, 300);
    }, 5000);
  }, [enableToasts]);

  /**
   * Compare rankings and detect changes
   */
  const detectRankingChanges = useCallback((newRankings: UserRankings) => {
    if (!previousRankings) {
      setPreviousRankings(newRankings);
      return;
    }

    const changes: RankingChange[] = [];

    // Parse percentiles
    const parsePercentile = (text: string) => {
      const match = text.match(/Top (\d+(?:\.\d+)?)% in/);
      return match ? parseFloat(match[1]) : 0;
    };

    const prevRegionalPercentile = parsePercentile(previousRankings.regional_percentile_text);
    const newRegionalPercentile = parsePercentile(newRankings.regional_percentile_text);
    const prevUniversityPercentile = parsePercentile(previousRankings.university_percentile_text);
    const newUniversityPercentile = parsePercentile(newRankings.university_percentile_text);

    // Check regional ranking changes
    const regionalPercentileChange = newRegionalPercentile - prevRegionalPercentile;
    if (Math.abs(regionalPercentileChange) >= significantChangeThreshold && 
        previousRankings.regional_ranking && newRankings.regional_ranking) {
      const isImprovement = regionalPercentileChange > 0;
      const change: RankingChange = {
        type: isImprovement ? 'improvement' : 'decline',
        message: isImprovement 
          ? `Your regional ranking improved to ${newRankings.regional_percentile_text}!`
          : `Your regional ranking changed to ${newRankings.regional_percentile_text}`,
        previousRank: previousRankings.regional_ranking.rank_in_region,
        newRank: newRankings.regional_ranking.rank_in_region,
        percentileChange: regionalPercentileChange,
        timestamp: new Date()
      };
      changes.push(change);
    }

    // Check university ranking changes
    const universityPercentileChange = newUniversityPercentile - prevUniversityPercentile;
    if (Math.abs(universityPercentileChange) >= significantChangeThreshold && 
        previousRankings.university_ranking && newRankings.university_ranking) {
      const isImprovement = universityPercentileChange > 0;
      const change: RankingChange = {
        type: isImprovement ? 'improvement' : 'decline',
        message: isImprovement 
          ? `Your university ranking improved to ${newRankings.university_percentile_text}!`
          : `Your university ranking changed to ${newRankings.university_percentile_text}`,
        previousRank: previousRankings.university_ranking.rank_in_university,
        newRank: newRankings.university_ranking.rank_in_university,
        percentileChange: universityPercentileChange,
        timestamp: new Date()
      };
      changes.push(change);
    }

    // Check for achievements
    if (newRegionalPercentile >= 95 && prevRegionalPercentile < 95) {
      changes.push({
        type: 'achievement',
        message: 'Achievement unlocked: Top 5% in your region! 🏆',
        timestamp: new Date()
      });
    }

    if (newUniversityPercentile >= 90 && prevUniversityPercentile < 90) {
      changes.push({
        type: 'achievement',
        message: 'Achievement unlocked: Top 10% at your university! 🎓',
        timestamp: new Date()
      });
    }

    // Process changes
    if (changes.length > 0) {
      setNotifications(prev => [...prev, ...changes]);
      changes.forEach(change => {
        onNotification?.(change);
        showToast(change);
      });
    }

    setPreviousRankings(newRankings);
  }, [previousRankings, significantChangeThreshold, onNotification, showToast]);

  /**
   * Store ranking history in localStorage
   */
  const storeRankingHistory = useCallback((rankings: UserRankings) => {
    try {
      const history = JSON.parse(localStorage.getItem('ranking_history') || '[]');
      const entry = {
        timestamp: new Date().toISOString(),
        regional_percentile: parseFloat(rankings.regional_percentile_text?.match(/(\d+(?:\.\d+)?)%/)?.[1] || '0'),
        university_percentile: parseFloat(rankings.university_percentile_text?.match(/(\d+(?:\.\d+)?)%/)?.[1] || '0'),
        regional_rank: rankings.regional_ranking?.rank_in_region || 0,
        university_rank: rankings.university_ranking?.rank_in_university || 0
      };

      history.push(entry);

      // Keep only last 50 entries
      if (history.length > 50) {
        history.splice(0, history.length - 50);
      }

      localStorage.setItem('ranking_history', JSON.stringify(history));
    } catch (error) {
      console.error('Failed to store ranking history:', error);
    }
  }, []);

  /**
   * Get ranking history from localStorage
   */
  const getRankingHistory = useCallback(() => {
    try {
      return JSON.parse(localStorage.getItem('ranking_history') || '[]');
    } catch (error) {
      console.error('Failed to get ranking history:', error);
      return [];
    }
  }, []);

  /**
   * Clear notifications
   */
  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  /**
   * Update rankings and detect changes
   */
  const updateRankings = useCallback((newRankings: UserRankings) => {
    detectRankingChanges(newRankings);
    storeRankingHistory(newRankings);
  }, [detectRankingChanges, storeRankingHistory]);

  return {
    notifications,
    updateRankings,
    clearNotifications,
    getRankingHistory,
    hasUnreadNotifications: notifications.length > 0
  };
};

/**
 * Hook for displaying ranking change indicators in UI
 */
export const useRankingChangeIndicators = (currentRankings: UserRankings | null) => {
  const [indicators, setIndicators] = useState<{
    regional: 'up' | 'down' | 'same' | null;
    university: 'up' | 'down' | 'same' | null;
  }>({ regional: null, university: null });

  useEffect(() => {
    if (!currentRankings) return;

    try {
      const history = JSON.parse(localStorage.getItem('ranking_history') || '[]');
      if (history.length < 2) return;

      const current = history[history.length - 1];
      const previous = history[history.length - 2];

      const regionalChange = current.regional_percentile - previous.regional_percentile;
      const universityChange = current.university_percentile - previous.university_percentile;

      setIndicators({
        regional: regionalChange > 1 ? 'up' : regionalChange < -1 ? 'down' : 'same',
        university: universityChange > 1 ? 'up' : universityChange < -1 ? 'down' : 'same'
      });
    } catch (error) {
      console.error('Failed to calculate ranking indicators:', error);
    }
  }, [currentRankings]);

  return indicators;
};