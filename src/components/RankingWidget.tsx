<<<<<<< HEAD
import React, { useState, useEffect, useCallback, useRef } from "react";
import { motion } from "framer-motion";
import {
  Award,
  TrendingUp,
  Users,
  Building2,
  ChevronDown,
  ChevronUp,
  Share2,
  BarChart3,
  Trophy,
} from "lucide-react";
import { rankingAPI } from "../services/profileAPI";
import { UserRankings } from "../types";
import StatisticsPanel from "./StatisticsPanel";
import Tooltip from "./Tooltip";
import RankingChangeToast from "./RankingChangeToast";
=======
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { Award, TrendingUp, Users, Building2, ChevronDown, ChevronUp, Share2, BarChart3, Trophy } from 'lucide-react';
import { rankingAPI } from '../services/profileAPI';
import { UserRankings } from '../types';
import StatisticsPanel from './StatisticsPanel';
import Tooltip from './Tooltip';
import RankingChangeToast from './RankingChangeToast';
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085

export interface RankingWidgetProps {
  onSetupProfile?: () => void;
}

export interface RankingData {
  regional: RankingInfo | null;
  university: RankingInfo | null;
}

export interface RankingInfo {
  percentile_text: string;
  rank_position: number;
  total_users: number;
  percentile_score: number;
}

const RankingWidget: React.FC<RankingWidgetProps> = ({ onSetupProfile }) => {
  const [rankings, setRankings] = useState<UserRankings | null>(null);
<<<<<<< HEAD
  const [previousRankings, setPreviousRankings] = useState<UserRankings | null>(
    null
  );
=======
  const [previousRankings, setPreviousRankings] = useState<UserRankings | null>(null);
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
  const [isLoading, setIsLoading] = useState(true);
  const [isCalculating, setIsCalculating] = useState(false);
  const [pollCount, setPollCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [hasProfile, setHasProfile] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [rankingChange, setRankingChange] = useState<{
    regional: number;
    university: number;
  } | null>(null);
  const [showToast, setShowToast] = useState<{
<<<<<<< HEAD
    type: "regional" | "university";
    change: number;
  } | null>(null);

  // Use ref to access latest rankings without causing re-renders
  const rankingsRef = useRef<UserRankings | null>(null);
  const MAX_POLLS = 10; // Poll for up to 5 minutes (30s intervals)

=======
    type: 'regional' | 'university';
    change: number;
  } | null>(null);
  
  // Use ref to access latest rankings without causing re-renders
  const rankingsRef = useRef<UserRankings | null>(null);
  const MAX_POLLS = 10; // Poll for up to 5 minutes (30s intervals)
  
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
  // Update ref when rankings change
  useEffect(() => {
    rankingsRef.current = rankings;
  }, [rankings]);

<<<<<<< HEAD
  const loadRankings = useCallback(
    async (showLoading = true) => {
      console.log("🔄 loadRankings called, showLoading:", showLoading);
      try {
        if (showLoading) {
          console.log("⏳ Setting isLoading to true");
          setIsLoading(true);
        }
        setError(null);

        console.log("📡 Calling rankingAPI.getRankings()...");
        const data = await rankingAPI.getRankings();
        console.log("✅ Rankings data received:", data);

        // Handle different response statuses from backend
        if (data.status === "pending_profile") {
          console.log("🚫 Profile setup required");
          setHasProfile(false);
          setError("NO_PROFILE");
          setIsCalculating(false);
          return;
        } else if (data.status === "pending_scan") {
          console.log("⏳ Scan required");
          setHasProfile(true);
          setError("NO_SCAN_RESULTS");
          setIsCalculating(false);
          return;
        } else if (data.status === "calculating") {
          console.log("⏳ Rankings being calculated");
          setHasProfile(true);
          setIsCalculating(true);
          setError(null);
          return;
        }

        // Handle successful rankings data
        if (
          data.status === "available" &&
          (data.regional_ranking || data.university_ranking)
        ) {
          // Calculate ranking changes using ref to avoid dependency
          if (
            rankingsRef.current &&
            rankingsRef.current.regional_ranking &&
            rankingsRef.current.university_ranking &&
            data.regional_ranking &&
            data.university_ranking
          ) {
            const regionalChange =
              data.regional_ranking.percentile_region -
              rankingsRef.current.regional_ranking.percentile_region;
            const universityChange =
              data.university_ranking.percentile_university -
              rankingsRef.current.university_ranking.percentile_university;

            setRankingChange({
              regional: regionalChange,
              university: universityChange,
            });

            // Show toast for significant changes (>5%)
            if (Math.abs(regionalChange) > 5) {
              setShowToast({ type: "regional", change: regionalChange });
            } else if (Math.abs(universityChange) > 5) {
              setShowToast({ type: "university", change: universityChange });
            }

            // Store previous rankings in localStorage
            localStorage.setItem(
              "previous_rankings",
              JSON.stringify(rankingsRef.current)
            );
            setPreviousRankings(rankingsRef.current);
          } else {
            // Try to load previous rankings from localStorage
            const stored = localStorage.getItem("previous_rankings");
            if (stored) {
              setPreviousRankings(JSON.parse(stored));
            }
          }

          setRankings(data);
          setHasProfile(true);
          setIsCalculating(false); // Rankings loaded successfully
          setPollCount(0); // Reset poll count
          setLastRefresh(new Date());
        } else {
          // Fallback for unexpected response format
          console.log("⚠️ Unexpected response format:", data);
          setError("GENERIC_ERROR");
          setIsCalculating(false);
        }
      } catch (err: any) {
        console.error("Failed to load rankings:", err);

        // Detailed error handling based on error type
        if (
          err.status_code === 404 ||
          err.message?.includes("Profile not found") ||
          err.error?.code === "UX_001"
        ) {
          // NO_PROFILE error
          console.log("🚫 No profile found, setting hasProfile to false");
          setHasProfile(false);
          setError("NO_PROFILE");
          setIsCalculating(false);
        } else if (
          err.message?.includes("not available") ||
          err.message?.includes("scan first") ||
          err.message?.includes("Please scan")
        ) {
          // NO_SCAN_RESULTS error - Rankings not ready yet
          console.log("⏳ Rankings not ready, starting/continuing polling");
          if (pollCount < MAX_POLLS) {
            setIsCalculating(true);
            setHasProfile(true);
            setError(null);
          } else {
            console.log("⏱️ Max polls reached, stopping");
            setError("TIMEOUT");
            setIsCalculating(false);
          }
        } else if (
          err.status_code === 500 ||
          err.message?.includes("server") ||
          err.message?.includes("database")
        ) {
          // Database/server error
          console.log("❌ Server error:", err);
          setError("SERVER_ERROR");
          setIsCalculating(false);
        } else if (
          err.message?.includes("Invalid") ||
          err.message?.includes("invalid")
        ) {
          // Invalid score error
          console.log("❌ Invalid score error:", err);
          setError("INVALID_SCORE");
          setIsCalculating(false);
        } else {
          // Generic error
          console.log("❌ Generic rankings error:", err);
          setError("GENERIC_ERROR");
          setIsCalculating(false);
        }
      } finally {
        // Always set loading to false, regardless of showLoading parameter
        console.log("⏹️ Setting isLoading to false");
        setIsLoading(false);
      }
    },
    [pollCount, MAX_POLLS]
  ); // Add dependencies
=======
  const loadRankings = useCallback(async (showLoading = true) => {
    console.log('🔄 loadRankings called, showLoading:', showLoading);
    try {
      if (showLoading) {
        console.log('⏳ Setting isLoading to true');
        setIsLoading(true);
      }
      setError(null);
      
      console.log('📡 Calling rankingAPI.getRankings()...');
      const data = await rankingAPI.getRankings();
      console.log('✅ Rankings data received:', data);
      
      // Calculate ranking changes using ref to avoid dependency
      if (rankingsRef.current && 
          rankingsRef.current.regional_ranking && 
          rankingsRef.current.university_ranking &&
          data.regional_ranking && 
          data.university_ranking) {
        const regionalChange = data.regional_ranking.percentile_region - rankingsRef.current.regional_ranking.percentile_region;
        const universityChange = data.university_ranking.percentile_university - rankingsRef.current.university_ranking.percentile_university;
        
        setRankingChange({
          regional: regionalChange,
          university: universityChange,
        });
        
        // Show toast for significant changes (>5%)
        if (Math.abs(regionalChange) > 5) {
          setShowToast({ type: 'regional', change: regionalChange });
        } else if (Math.abs(universityChange) > 5) {
          setShowToast({ type: 'university', change: universityChange });
        }
        
        // Store previous rankings in localStorage
        localStorage.setItem('previous_rankings', JSON.stringify(rankingsRef.current));
        setPreviousRankings(rankingsRef.current);
      } else {
        // Try to load previous rankings from localStorage
        const stored = localStorage.getItem('previous_rankings');
        if (stored) {
          setPreviousRankings(JSON.parse(stored));
        }
      }
      
      setRankings(data);
      setHasProfile(true);
      setIsCalculating(false); // Rankings loaded successfully
      setPollCount(0); // Reset poll count
      setLastRefresh(new Date());
    } catch (err: any) {
      console.error('Failed to load rankings:', err);
      
      // Detailed error handling based on error type
      if (err.status_code === 404 || err.message?.includes('Profile not found') || err.error?.code === 'UX_001') {
        // NO_PROFILE error
        console.log('🚫 No profile found, setting hasProfile to false');
        setHasProfile(false);
        setError('NO_PROFILE');
        setIsCalculating(false);
      } else if (err.message?.includes('not available') || err.message?.includes('scan first') || err.message?.includes('Please scan')) {
        // NO_SCAN_RESULTS error - Rankings not ready yet
        console.log('⏳ Rankings not ready, starting/continuing polling');
        if (pollCount < MAX_POLLS) {
          setIsCalculating(true);
          setHasProfile(true);
          setError(null);
        } else {
          console.log('⏱️ Max polls reached, stopping');
          setError('TIMEOUT');
          setIsCalculating(false);
        }
      } else if (err.status_code === 500 || err.message?.includes('server') || err.message?.includes('database')) {
        // Database/server error
        console.log('❌ Server error:', err);
        setError('SERVER_ERROR');
        setIsCalculating(false);
      } else if (err.message?.includes('Invalid') || err.message?.includes('invalid')) {
        // Invalid score error
        console.log('❌ Invalid score error:', err);
        setError('INVALID_SCORE');
        setIsCalculating(false);
      } else {
        // Generic error
        console.log('❌ Generic rankings error:', err);
        setError('GENERIC_ERROR');
        setIsCalculating(false);
      }
    } finally {
      // Always set loading to false, regardless of showLoading parameter
      console.log('⏹️ Setting isLoading to false');
      setIsLoading(false);
    }
  }, [pollCount, MAX_POLLS]); // Add dependencies
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085

  // Load rankings on mount
  useEffect(() => {
    loadRankings();
  }, [loadRankings]);

  // Poll for rankings when in calculating state
  useEffect(() => {
    if (!isCalculating || pollCount >= MAX_POLLS) {
      return;
    }

<<<<<<< HEAD
    console.log(
      `⏳ Polling for rankings (attempt ${pollCount + 1}/${MAX_POLLS})`
    );
    const pollTimeout = setTimeout(() => {
      setPollCount((prev) => prev + 1);
=======
    console.log(`⏳ Polling for rankings (attempt ${pollCount + 1}/${MAX_POLLS})`);
    const pollTimeout = setTimeout(() => {
      setPollCount(prev => prev + 1);
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
      loadRankings(false); // Don't show loading spinner during polls
    }, 30000); // Poll every 30 seconds

    return () => clearTimeout(pollTimeout);
  }, [isCalculating, pollCount, MAX_POLLS, loadRankings]);

  // Refresh rankings when tab gains focus
  useEffect(() => {
    const handleFocus = () => {
      loadRankings();
    };

<<<<<<< HEAD
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
=======
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
  }, [loadRankings]);

  // Poll for updates every 5 minutes (when not calculating)
  useEffect(() => {
    if (isCalculating) {
      return; // Don't run regular polling when calculating
    }

    const pollInterval = setInterval(() => {
      loadRankings(false);
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(pollInterval);
  }, [loadRankings, isCalculating]);

  const handleRefresh = () => {
    loadRankings(true);
  };

<<<<<<< HEAD
  const handleShareRanking = (type: "regional" | "university") => {
    if (!rankings) return;

    let text: string;

    if (type === "regional") {
      const ranking = rankings.regional_ranking;
      if (!ranking) return;
      text = `I'm ranked #${ranking.rank_in_region} out of ${
        ranking.total_users_in_region
      } developers in my region (Top ${
        ranking.percentile_region?.toFixed(1) || 0
      }%)!`;
    } else {
      const ranking = rankings.university_ranking;
      if (!ranking) return;
      text = `I'm ranked #${ranking.rank_in_university} out of ${
        ranking.total_users_in_university
      } students at my university (Top ${
        ranking.percentile_university?.toFixed(1) || 0
      }%)!`;
    }

    if (navigator.share) {
      navigator
        .share({
          title: "My Developer Ranking",
          text: text,
        })
        .catch(() => {
          // Fallback to clipboard
          navigator.clipboard.writeText(text);
          alert("Ranking copied to clipboard!");
        });
    } else {
      navigator.clipboard.writeText(text);
      alert("Ranking copied to clipboard!");
    }
  };

  const handleViewLeaderboard = (type: "regional" | "university") => {
    // Navigate to leaderboard page (to be implemented)
    console.log(`View ${type} leaderboard`);
    alert(
      `${
        type === "regional" ? "Regional" : "University"
      } leaderboard feature coming soon!`
    );
  };

  const handleViewStats = (type: "regional" | "university") => {
    // Navigate to detailed stats page (to be implemented)
    console.log(`View ${type} stats`);
    alert(
      `Detailed ${
        type === "regional" ? "regional" : "university"
      } statistics coming soon!`
    );
  };

  // Debug: Log current state
  console.log("🎨 RankingWidget render state:", {
    isLoading,
    hasProfile,
    error,
    rankings: !!rankings,
  });

  // Debug: Log rankings data to see what we're getting
  if (rankings) {
    console.log("🔍 Rankings data:", {
      regional_overall_score: rankings.regional_ranking?.overall_score,
      university_overall_score: rankings.university_ranking?.overall_score,
      regional_avg_score: rankings.regional_ranking?.avg_score,
      university_avg_score: rankings.university_ranking?.avg_score,
    });
  }
=======
  const handleShareRanking = (type: 'regional' | 'university') => {
    if (!rankings) return;
    
    const ranking = type === 'regional' ? rankings.regional_ranking : rankings.university_ranking;
    if (!ranking) return; // Don't share if ranking data is not available
    
    const text = type === 'regional' 
      ? `I'm ranked #${ranking.rank_in_region} out of ${ranking.total_users_in_region} developers in my region (Top ${ranking.percentile_region?.toFixed(1) || 0}%)!`
      : `I'm ranked #${ranking.rank_in_university} out of ${ranking.total_users_in_university} students at my university (Top ${ranking.percentile_university?.toFixed(1) || 0}%)!`;
    
    if (navigator.share) {
      navigator.share({
        title: 'My Developer Ranking',
        text: text,
      }).catch(() => {
        // Fallback to clipboard
        navigator.clipboard.writeText(text);
        alert('Ranking copied to clipboard!');
      });
    } else {
      navigator.clipboard.writeText(text);
      alert('Ranking copied to clipboard!');
    }
  };

  const handleViewLeaderboard = (type: 'regional' | 'university') => {
    // Navigate to leaderboard page (to be implemented)
    console.log(`View ${type} leaderboard`);
    alert(`${type === 'regional' ? 'Regional' : 'University'} leaderboard feature coming soon!`);
  };

  const handleViewStats = (type: 'regional' | 'university') => {
    // Navigate to detailed stats page (to be implemented)
    console.log(`View ${type} stats`);
    alert(`Detailed ${type === 'regional' ? 'regional' : 'university'} statistics coming soon!`);
  };

  // Debug: Log current state
  console.log('🎨 RankingWidget render state:', { isLoading, hasProfile, error, rankings: !!rankings });
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[1, 2].map((i) => (
          <div key={i} className="card p-6 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-48 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-24"></div>
          </div>
        ))}
      </div>
    );
  }

  // Calculating state - rankings are being calculated
  if (isCalculating) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card p-6 bg-blue-50 border border-blue-200"
      >
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">
              Your rankings are being calculated...
            </h3>
            <p className="text-sm text-blue-800 mb-3">
<<<<<<< HEAD
              This may take a few moments. Your rankings will appear
              automatically when ready.
=======
              This may take a few moments. Your rankings will appear automatically when ready.
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            </p>
            <div className="flex items-center space-x-2 text-xs text-blue-700">
              <span>Checking for updates</span>
              <span className="animate-pulse">•</span>
<<<<<<< HEAD
              <span>
                Attempt {pollCount + 1} of {MAX_POLLS}
              </span>
=======
              <span>Attempt {pollCount + 1} of {MAX_POLLS}</span>
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  // Show message if no profile
  if (!hasProfile) {
    return (
      <div className="card p-6 text-center">
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mb-4">
            <Award className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
<<<<<<< HEAD
            Profile Setup Required
          </h3>
          <p className="text-sm text-gray-600 max-w-md mb-4">
            Complete your profile setup to see how you rank against other
            developers in your region and university.
          </p>
          {onSetupProfile && (
            <button onClick={onSetupProfile} className="btn-primary">
=======
            No Ranking Available
          </h3>
          <p className="text-sm text-gray-600 max-w-md mb-4">
            Complete your profile to see how you rank against other developers in your region and university.
          </p>
          {onSetupProfile && (
            <button
              onClick={onSetupProfile}
              className="btn-primary"
            >
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
              Setup Profile
            </button>
          )}
        </div>
      </div>
    );
  }

  // Show error state with specific messages
  if (error && hasProfile) {
<<<<<<< HEAD
    const errorMessages: Record<
      string,
      { title: string; message: string; showRetry: boolean }
    > = {
      NO_PROFILE: {
        title: "Profile Setup Required",
        message: "Please complete your profile setup to see rankings.",
        showRetry: false,
      },
      NO_SCAN_RESULTS: {
        title: "Repository Scan Required",
        message: "Please scan your repositories to calculate rankings.",
        showRetry: false,
      },
      INVALID_SCORE: {
        title: "Invalid Score",
        message: "Unable to calculate rankings. Please try scanning again.",
        showRetry: true,
      },
      SERVER_ERROR: {
        title: "Temporarily Unavailable",
        message: "Rankings temporarily unavailable. Please try again later.",
        showRetry: true,
      },
      TIMEOUT: {
        title: "Taking Longer Than Expected",
        message:
          "Rankings are taking longer than expected. Please try refreshing later.",
        showRetry: true,
      },
      GENERIC_ERROR: {
        title: "Failed to Load Rankings",
        message: "An error occurred while loading rankings. Please try again.",
        showRetry: true,
      },
    };

    const errorInfo = errorMessages[error] || errorMessages["GENERIC_ERROR"];
=======
    const errorMessages: Record<string, { title: string; message: string; showRetry: boolean }> = {
      'NO_PROFILE': {
        title: 'Profile Required',
        message: 'Please complete your profile to see rankings.',
        showRetry: false
      },
      'NO_SCAN_RESULTS': {
        title: 'No Scan Results',
        message: 'Please scan your repositories to calculate rankings.',
        showRetry: false
      },
      'INVALID_SCORE': {
        title: 'Invalid Score',
        message: 'Unable to calculate rankings. Please try scanning again.',
        showRetry: true
      },
      'SERVER_ERROR': {
        title: 'Temporarily Unavailable',
        message: 'Rankings temporarily unavailable. Please try again later.',
        showRetry: true
      },
      'TIMEOUT': {
        title: 'Taking Longer Than Expected',
        message: 'Rankings are taking longer than expected. Please try refreshing later.',
        showRetry: true
      },
      'GENERIC_ERROR': {
        title: 'Failed to Load Rankings',
        message: 'An error occurred while loading rankings. Please try again.',
        showRetry: true
      }
    };

    const errorInfo = errorMessages[error] || errorMessages['GENERIC_ERROR'];
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card p-6 bg-red-50 border border-red-200"
      >
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
<<<<<<< HEAD
            <svg
              className="h-6 w-6 text-red-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
=======
            <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-red-900 mb-2">
              {errorInfo.title}
            </h3>
<<<<<<< HEAD
            <p className="text-sm text-red-800 mb-4">{errorInfo.message}</p>
=======
            <p className="text-sm text-red-800 mb-4">
              {errorInfo.message}
            </p>
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            {errorInfo.showRetry && (
              <button
                onClick={() => {
                  setError(null);
                  setPollCount(0);
                  loadRankings(true);
                }}
                className="btn-ghost text-red-700 hover:bg-red-100"
              >
                Try Again
              </button>
            )}
          </div>
        </div>
      </motion.div>
    );
  }

  // Show rankings
  return (
    <div>
      {/* Header with refresh button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-2">
        <div>
<<<<<<< HEAD
          <h2 className="text-lg sm:text-xl font-semibold text-gray-900">
            Your Rankings
          </h2>
=======
          <h2 className="text-lg sm:text-xl font-semibold text-gray-900">Your Rankings</h2>
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
          {lastRefresh && (
            <p className="text-xs text-gray-500 mt-1">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </p>
          )}
        </div>
        <button
          onClick={handleRefresh}
          disabled={isLoading}
          className="btn-ghost text-sm whitespace-nowrap"
        >
<<<<<<< HEAD
          {isLoading ? "Refreshing..." : "Refresh"}
=======
          {isLoading ? 'Refreshing...' : 'Refresh'}
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
<<<<<<< HEAD
        {/* Regional Ranking Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
          whileTap={{ scale: 0.98 }}
          transition={{ duration: 0.4 }}
          className="card p-6 hover:shadow-xl transition-all duration-300 cursor-pointer"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Tooltip content="Regional comparison with developers in your area">
                <div className="p-3 rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 hover:from-blue-100 hover:to-blue-200 transition-colors duration-200">
                  <Users className="h-6 w-6 text-blue-600" />
                </div>
              </Tooltip>
              <div>
                <h3 className="text-sm font-medium text-gray-600">
                  Regional Ranking
                </h3>
                <p className="text-xs text-gray-500">Your region</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Tooltip content="Your ranking is active">
                <TrendingUp className="h-5 w-5 text-green-500" />
              </Tooltip>
              {isExpanded ? (
                <ChevronUp className="h-5 w-5 text-gray-400" />
              ) : (
                <ChevronDown className="h-5 w-5 text-gray-400" />
              )}
            </div>
          </div>

          <div className="mb-4">
            <Tooltip
              content={`Your ACID score: ${
                typeof rankings?.regional_ranking?.overall_score === "number"
                  ? rankings.regional_ranking.overall_score.toFixed(1)
                  : typeof rankings?.regional_ranking?.avg_score === "number"
                  ? rankings.regional_ranking.avg_score.toFixed(1)
                  : "N/A"
              }`}
            >
              <div className="flex flex-wrap items-center gap-2">
                <div className="text-2xl sm:text-3xl font-bold text-gray-900 hover:text-blue-600 transition-colors duration-200">
                  {rankings?.regional_percentile_text || "N/A"}
                </div>
                {rankingChange && Math.abs(rankingChange.regional) > 0.1 && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className={`flex items-center space-x-1 text-sm font-medium ${
                      rankingChange.regional > 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {rankingChange.regional > 0 ? (
                      <TrendingUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                    <span>{Math.abs(rankingChange.regional).toFixed(1)}%</span>
                  </motion.div>
                )}
              </div>
            </Tooltip>
            <Tooltip
              content={`${
                rankings?.regional_ranking?.total_users_in_region || 0
              } developers registered in your region`}
            >
              <div className="text-sm text-gray-600 hover:text-gray-900 transition-colors duration-200">
                Rank #{rankings?.regional_ranking?.rank_in_region || 0} of{" "}
                {rankings?.regional_ranking?.total_users_in_region || 0}{" "}
                developers
              </div>
              {(rankings?.regional_ranking?.overall_score ||
                rankings?.regional_ranking?.avg_score) && (
                <div className="text-xs text-blue-600 font-medium mt-1">
                  ACID Score:{" "}
                  {typeof (
                    rankings.regional_ranking.overall_score ||
                    rankings.regional_ranking.avg_score
                  ) === "number"
                    ? (
                        rankings.regional_ranking.overall_score ||
                        rankings.regional_ranking.avg_score
                      ).toFixed(1)
                    : "N/A"}
                </div>
              )}
            </Tooltip>
          </div>

          <div className="relative pt-1">
            <div className="flex mb-2 items-center justify-between">
              <div>
                <span className="text-xs font-semibold inline-block text-blue-600">
                  Percentile
                </span>
              </div>
              <div className="text-right">
                <span className="text-xs font-semibold inline-block text-blue-600">
                  {rankings?.regional_ranking?.percentile_region?.toFixed(1) ||
                    0}
                  %
                </span>
              </div>
            </div>
            <div className="overflow-hidden h-2 text-xs flex rounded-full bg-blue-100">
              <motion.div
                initial={{ width: 0 }}
                animate={{
                  width: `${
                    rankings?.regional_ranking?.percentile_region || 0
                  }%`,
                }}
                transition={{ duration: 1, ease: "easeOut" }}
                className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-blue-500 to-blue-600"
              />
            </div>
          </div>

          {/* Expandable Statistics Panel */}
          {rankings?.regional_ranking && (
            <StatisticsPanel
              isExpanded={isExpanded}
              type="regional"
              rankPosition={rankings.regional_ranking.rank_in_region}
              totalUsers={rankings.regional_ranking.total_users_in_region}
              percentileScore={rankings.regional_ranking.percentile_region}
              contextName={
                rankings.regional_percentile_text?.split(" in ")[1] ||
                "your region"
              }
            />
          )}

          {/* Action Buttons - Always visible */}
          {rankings?.regional_ranking && (
            <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-2">
              <Tooltip content="Share your regional ranking">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleShareRanking("regional");
                  }}
                  className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                >
                  <Share2 className="h-3.5 w-3.5" />
                  <span>Share</span>
                </button>
              </Tooltip>

              <Tooltip content="View regional leaderboard">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleViewLeaderboard("regional");
                  }}
                  className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                >
                  <Trophy className="h-3.5 w-3.5" />
                  <span>Leaderboard</span>
                </button>
              </Tooltip>

              <Tooltip content="View detailed regional statistics">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleViewStats("regional");
                  }}
                  className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                >
                  <BarChart3 className="h-3.5 w-3.5" />
                  <span>Stats</span>
                </button>
              </Tooltip>
            </div>
          )}
        </motion.div>

        {/* University Ranking Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
          whileTap={{ scale: 0.98 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="card p-6 hover:shadow-xl transition-all duration-300 cursor-pointer"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Tooltip content="University comparison with students at your institution">
                <div className="p-3 rounded-lg bg-gradient-to-br from-purple-50 to-purple-100 hover:from-purple-100 hover:to-purple-200 transition-colors duration-200">
                  <Building2 className="h-6 w-6 text-purple-600" />
                </div>
              </Tooltip>
              <div>
                <h3 className="text-sm font-medium text-gray-600">
                  University Ranking
                </h3>
                <p className="text-xs text-gray-500">Your university</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Tooltip content="Your ranking is active">
                <TrendingUp className="h-5 w-5 text-green-500" />
              </Tooltip>
              {isExpanded ? (
                <ChevronUp className="h-5 w-5 text-gray-400" />
              ) : (
                <ChevronDown className="h-5 w-5 text-gray-400" />
              )}
            </div>
          </div>

          <div className="mb-4">
            <Tooltip
              content={`Your ACID score: ${
                typeof rankings?.university_ranking?.overall_score === "number"
                  ? rankings.university_ranking.overall_score.toFixed(1)
                  : typeof rankings?.university_ranking?.avg_score === "number"
                  ? rankings.university_ranking.avg_score.toFixed(1)
                  : "N/A"
              }`}
            >
              <div className="flex flex-wrap items-center gap-2">
                <div className="text-2xl sm:text-3xl font-bold text-gray-900 hover:text-purple-600 transition-colors duration-200">
                  {rankings?.university_percentile_text || "N/A"}
                </div>
                {rankingChange && Math.abs(rankingChange.university) > 0.1 && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className={`flex items-center space-x-1 text-sm font-medium ${
                      rankingChange.university > 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {rankingChange.university > 0 ? (
                      <TrendingUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                    <span>
                      {Math.abs(rankingChange.university).toFixed(1)}%
                    </span>
                  </motion.div>
                )}
              </div>
            </Tooltip>
            <Tooltip
              content={`${
                rankings?.university_ranking?.total_users_in_university || 0
              } students registered at your university`}
            >
              <div className="text-sm text-gray-600 hover:text-gray-900 transition-colors duration-200">
                Rank #{rankings?.university_ranking?.rank_in_university || 0} of{" "}
                {rankings?.university_ranking?.total_users_in_university || 0}{" "}
                students
              </div>
              {(rankings?.university_ranking?.overall_score ||
                rankings?.university_ranking?.avg_score) && (
                <div className="text-xs text-purple-600 font-medium mt-1">
                  ACID Score:{" "}
                  {typeof (
                    rankings.university_ranking.overall_score ||
                    rankings.university_ranking.avg_score
                  ) === "number"
                    ? (
                        rankings.university_ranking.overall_score ||
                        rankings.university_ranking.avg_score
                      ).toFixed(1)
                    : "N/A"}
                </div>
              )}
            </Tooltip>
          </div>

          <div className="relative pt-1">
            <div className="flex mb-2 items-center justify-between">
              <div>
                <span className="text-xs font-semibold inline-block text-purple-600">
                  Percentile
                </span>
              </div>
              <div className="text-right">
                <span className="text-xs font-semibold inline-block text-purple-600">
                  {rankings?.university_ranking?.percentile_university?.toFixed(
                    1
                  ) || 0}
                  %
                </span>
              </div>
            </div>
            <div className="overflow-hidden h-2 text-xs flex rounded-full bg-purple-100">
              <motion.div
                initial={{ width: 0 }}
                animate={{
                  width: `${
                    rankings?.university_ranking?.percentile_university || 0
                  }%`,
                }}
                transition={{ duration: 1, ease: "easeOut", delay: 0.1 }}
                className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-purple-500 to-purple-600"
              />
            </div>
          </div>

          {/* Expandable Statistics Panel */}
          {rankings?.university_ranking && (
            <StatisticsPanel
              isExpanded={isExpanded}
              type="university"
              rankPosition={rankings.university_ranking.rank_in_university}
              totalUsers={rankings.university_ranking.total_users_in_university}
              percentileScore={
                rankings.university_ranking.percentile_university
              }
              contextName={
                rankings.university_percentile_text?.split(" in ")[1] ||
                "your university"
              }
            />
          )}

          {/* Action Buttons - Always visible */}
          {rankings?.university_ranking && (
            <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-2">
              <Tooltip content="Share your university ranking">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleShareRanking("university");
                  }}
                  className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-purple-600 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors"
                >
                  <Share2 className="h-3.5 w-3.5" />
                  <span>Share</span>
                </button>
              </Tooltip>

              <Tooltip content="View university leaderboard">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleViewLeaderboard("university");
                  }}
                  className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-purple-600 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors"
                >
                  <Trophy className="h-3.5 w-3.5" />
                  <span>Leaderboard</span>
                </button>
              </Tooltip>

              <Tooltip content="View detailed university statistics">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleViewStats("university");
                  }}
                  className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-purple-600 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors"
                >
                  <BarChart3 className="h-3.5 w-3.5" />
                  <span>Stats</span>
                </button>
              </Tooltip>
            </div>
          )}
        </motion.div>
=======
      {/* Regional Ranking Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
        whileTap={{ scale: 0.98 }}
        transition={{ duration: 0.4 }}
        className="card p-6 hover:shadow-xl transition-all duration-300 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Tooltip content="Regional comparison with developers in your area">
              <div className="p-3 rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 hover:from-blue-100 hover:to-blue-200 transition-colors duration-200">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
            </Tooltip>
            <div>
              <h3 className="text-sm font-medium text-gray-600">Regional Ranking</h3>
              <p className="text-xs text-gray-500">Your region</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Tooltip content="Your ranking is active">
              <TrendingUp className="h-5 w-5 text-green-500" />
            </Tooltip>
            {isExpanded ? (
              <ChevronUp className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronDown className="h-5 w-5 text-gray-400" />
            )}
          </div>
        </div>

        <div className="mb-4">
          <Tooltip content={`Your ACID score: ${rankings?.regional_ranking?.percentile_region?.toFixed(1) || 0}%`}>
            <div className="flex flex-wrap items-center gap-2">
              <div className="text-2xl sm:text-3xl font-bold text-gray-900 hover:text-blue-600 transition-colors duration-200">
                {rankings?.regional_percentile_text || 'N/A'}
              </div>
              {rankingChange && Math.abs(rankingChange.regional) > 0.1 && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className={`flex items-center space-x-1 text-sm font-medium ${
                    rankingChange.regional > 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {rankingChange.regional > 0 ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                  <span>{Math.abs(rankingChange.regional).toFixed(1)}%</span>
                </motion.div>
              )}
            </div>
          </Tooltip>
          <Tooltip content={`${rankings?.regional_ranking?.total_users_in_region || 0} developers registered in your region`}>
            <div className="text-sm text-gray-600 hover:text-gray-900 transition-colors duration-200">
              Rank #{rankings?.regional_ranking?.rank_in_region || 0} of{' '}
              {rankings?.regional_ranking?.total_users_in_region || 0} developers
            </div>
          </Tooltip>
        </div>

        <div className="relative pt-1">
          <div className="flex mb-2 items-center justify-between">
            <div>
              <span className="text-xs font-semibold inline-block text-blue-600">
                Percentile
              </span>
            </div>
            <div className="text-right">
              <span className="text-xs font-semibold inline-block text-blue-600">
                {rankings?.regional_ranking?.percentile_region?.toFixed(1) || 0}%
              </span>
            </div>
          </div>
          <div className="overflow-hidden h-2 text-xs flex rounded-full bg-blue-100">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${rankings?.regional_ranking?.percentile_region || 0}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
              className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-blue-500 to-blue-600"
            />
          </div>
        </div>

        {/* Expandable Statistics Panel */}
        {rankings?.regional_ranking && (
          <StatisticsPanel
            isExpanded={isExpanded}
            type="regional"
            rankPosition={rankings.regional_ranking.rank_in_region}
            totalUsers={rankings.regional_ranking.total_users_in_region}
            percentileScore={rankings.regional_ranking.percentile_region}
            contextName={rankings.regional_percentile_text.split(' in ')[1] || 'your region'}
          />
        )}

        {/* Action Buttons - Always visible */}
        {rankings?.regional_ranking && (
          <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-2">
          <Tooltip content="Share your regional ranking">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleShareRanking('regional');
              }}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
            >
              <Share2 className="h-3.5 w-3.5" />
              <span>Share</span>
            </button>
          </Tooltip>
          
          <Tooltip content="View regional leaderboard">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleViewLeaderboard('regional');
              }}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
            >
              <Trophy className="h-3.5 w-3.5" />
              <span>Leaderboard</span>
            </button>
          </Tooltip>
          
          <Tooltip content="View detailed regional statistics">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleViewStats('regional');
              }}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
            >
              <BarChart3 className="h-3.5 w-3.5" />
              <span>Stats</span>
            </button>
          </Tooltip>
          </div>
        )}
      </motion.div>

      {/* University Ranking Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
        whileTap={{ scale: 0.98 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="card p-6 hover:shadow-xl transition-all duration-300 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Tooltip content="University comparison with students at your institution">
              <div className="p-3 rounded-lg bg-gradient-to-br from-purple-50 to-purple-100 hover:from-purple-100 hover:to-purple-200 transition-colors duration-200">
                <Building2 className="h-6 w-6 text-purple-600" />
              </div>
            </Tooltip>
            <div>
              <h3 className="text-sm font-medium text-gray-600">University Ranking</h3>
              <p className="text-xs text-gray-500">Your university</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Tooltip content="Your ranking is active">
              <TrendingUp className="h-5 w-5 text-green-500" />
            </Tooltip>
            {isExpanded ? (
              <ChevronUp className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronDown className="h-5 w-5 text-gray-400" />
            )}
          </div>
        </div>

        <div className="mb-4">
          <Tooltip content={`Your ACID score: ${rankings?.university_ranking?.percentile_university?.toFixed(1) || 0}%`}>
            <div className="flex flex-wrap items-center gap-2">
              <div className="text-2xl sm:text-3xl font-bold text-gray-900 hover:text-purple-600 transition-colors duration-200">
                {rankings?.university_percentile_text || 'N/A'}
              </div>
              {rankingChange && Math.abs(rankingChange.university) > 0.1 && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className={`flex items-center space-x-1 text-sm font-medium ${
                    rankingChange.university > 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {rankingChange.university > 0 ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                  <span>{Math.abs(rankingChange.university).toFixed(1)}%</span>
                </motion.div>
              )}
            </div>
          </Tooltip>
          <Tooltip content={`${rankings?.university_ranking?.total_users_in_university || 0} students registered at your university`}>
            <div className="text-sm text-gray-600 hover:text-gray-900 transition-colors duration-200">
              Rank #{rankings?.university_ranking?.rank_in_university || 0} of{' '}
              {rankings?.university_ranking?.total_users_in_university || 0} students
            </div>
          </Tooltip>
        </div>

        <div className="relative pt-1">
          <div className="flex mb-2 items-center justify-between">
            <div>
              <span className="text-xs font-semibold inline-block text-purple-600">
                Percentile
              </span>
            </div>
            <div className="text-right">
              <span className="text-xs font-semibold inline-block text-purple-600">
                {rankings?.university_ranking?.percentile_university?.toFixed(1) || 0}%
              </span>
            </div>
          </div>
          <div className="overflow-hidden h-2 text-xs flex rounded-full bg-purple-100">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${rankings?.university_ranking?.percentile_university || 0}%` }}
              transition={{ duration: 1, ease: 'easeOut', delay: 0.1 }}
              className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-purple-500 to-purple-600"
            />
          </div>
        </div>

        {/* Expandable Statistics Panel */}
        {rankings?.university_ranking && (
          <StatisticsPanel
            isExpanded={isExpanded}
            type="university"
            rankPosition={rankings.university_ranking.rank_in_university}
            totalUsers={rankings.university_ranking.total_users_in_university}
            percentileScore={rankings.university_ranking.percentile_university}
            contextName={rankings.university_percentile_text.split(' in ')[1] || 'your university'}
          />
        )}

        {/* Action Buttons - Always visible */}
        {rankings?.university_ranking && (
          <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-2">
          <Tooltip content="Share your university ranking">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleShareRanking('university');
              }}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-purple-600 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors"
            >
              <Share2 className="h-3.5 w-3.5" />
              <span>Share</span>
            </button>
          </Tooltip>
          
          <Tooltip content="View university leaderboard">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleViewLeaderboard('university');
              }}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-purple-600 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors"
            >
              <Trophy className="h-3.5 w-3.5" />
              <span>Leaderboard</span>
            </button>
          </Tooltip>
          
          <Tooltip content="View detailed university statistics">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleViewStats('university');
              }}
              className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-purple-600 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors"
            >
              <BarChart3 className="h-3.5 w-3.5" />
              <span>Stats</span>
            </button>
          </Tooltip>
          </div>
        )}
      </motion.div>
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
      </div>

      {/* Ranking Change Toast */}
      {showToast && (
        <RankingChangeToast
          isVisible={true}
          type={showToast.type}
          change={showToast.change}
          onClose={() => setShowToast(null)}
        />
      )}
    </div>
  );
};

export default RankingWidget;
