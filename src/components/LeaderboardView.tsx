import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Trophy, 
  Medal, 
  Award, 
  Users, 
  MapPin, 
  GraduationCap,
  Crown,
  Star,
  TrendingUp,
  RefreshCw
} from 'lucide-react';
import { UserRankings } from '../types';
import { rankingAPI, withRetry } from '../services/profileAPI';

interface LeaderboardViewProps {
  rankings: UserRankings;
  userRegion: string;
  userUniversity: string;
}

interface LeaderboardEntry {
  rank: number;
  anonymous_id: string;
  score: number;
  percentile: number;
  is_current_user?: boolean;
}

interface LeaderboardData {
  regional: LeaderboardEntry[];
  university: LeaderboardEntry[];
}

const LeaderboardView: React.FC<LeaderboardViewProps> = ({ 
  rankings, 
  userRegion, 
  userUniversity 
}) => {
  const [leaderboardData, setLeaderboardData] = useState<LeaderboardData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'regional' | 'university'>('regional');

  useEffect(() => {
    loadLeaderboardData();
  }, [rankings]);

  const loadLeaderboardData = async () => {
    setIsLoading(true);
    try {
      // Simulate leaderboard data since we don't expose real user data
      const mockRegionalData: LeaderboardEntry[] = Array.from({ length: 10 }, (_, i) => ({
        rank: i + 1,
        anonymous_id: `user_${Math.random().toString(36).substr(2, 8)}`,
        score: 95 - (i * 2) + Math.random() * 2,
        percentile: 99 - (i * 1.5),
        is_current_user: i + 1 === (rankings.regional_ranking?.rank_in_region || 0)
      }));

      const mockUniversityData: LeaderboardEntry[] = Array.from({ length: 10 }, (_, i) => ({
        rank: i + 1,
        anonymous_id: `student_${Math.random().toString(36).substr(2, 8)}`,
        score: 92 - (i * 1.5) + Math.random() * 1.5,
        percentile: 98 - (i * 2),
        is_current_user: i + 1 === (rankings.university_ranking?.rank_in_university || 0)
      }));

      setLeaderboardData({
        regional: mockRegionalData,
        university: mockUniversityData
      });
    } catch (error) {
      console.error('Failed to load leaderboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Crown className="h-5 w-5 text-yellow-500" />;
      case 2:
        return <Medal className="h-5 w-5 text-gray-400" />;
      case 3:
        return <Award className="h-5 w-5 text-amber-600" />;
      default:
        return <span className="text-sm font-bold text-gray-600">#{rank}</span>;
    }
  };

  const getRankBadgeColor = (rank: number) => {
    switch (rank) {
      case 1:
        return 'bg-gradient-to-r from-yellow-400 to-yellow-500 text-white';
      case 2:
        return 'bg-gradient-to-r from-gray-300 to-gray-400 text-white';
      case 3:
        return 'bg-gradient-to-r from-amber-500 to-amber-600 text-white';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getScoreColor = (percentile: number) => {
    if (percentile >= 95) return 'text-green-600';
    if (percentile >= 85) return 'text-blue-600';
    if (percentile >= 70) return 'text-yellow-600';
    return 'text-gray-600';
  };

  const currentData = activeTab === 'regional' ? leaderboardData?.regional : leaderboardData?.university;
  const currentTotal = activeTab === 'regional' 
    ? (rankings.regional_ranking?.total_users_in_region || 0)
    : (rankings.university_ranking?.total_users_in_university || 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden"
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-500 to-secondary-500 text-white p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Trophy className="h-6 w-6" />
            <div>
              <h3 className="text-xl font-semibold">Leaderboards</h3>
              <p className="text-primary-100 text-sm">
                Top performers in your region and university
              </p>
            </div>
          </div>
          
          <button
            onClick={loadLeaderboardData}
            disabled={isLoading}
            className="p-2 rounded-lg bg-white/20 hover:bg-white/30 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex">
          <button
            onClick={() => setActiveTab('regional')}
            className={`flex-1 py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'regional'
                ? 'border-primary-500 text-primary-600 bg-primary-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-center space-x-2">
              <MapPin className="h-4 w-4" />
              <span>Regional ({userRegion})</span>
            </div>
          </button>
          
          <button
            onClick={() => setActiveTab('university')}
            className={`flex-1 py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'university'
                ? 'border-secondary-500 text-secondary-600 bg-secondary-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-center space-x-2">
              <GraduationCap className="h-4 w-4" />
              <span>University ({userUniversity})</span>
            </div>
          </button>
        </nav>
      </div>

      {/* Leaderboard Content */}
      <div className="p-6">
        {isLoading ? (
          <div className="text-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin text-primary-500 mx-auto mb-4" />
            <p className="text-gray-600">Loading leaderboard...</p>
          </div>
        ) : currentData ? (
          <div className="space-y-3">
            {/* Stats Header */}
            <motion.div 
              className="flex items-center justify-between mb-6 p-4 bg-gray-50 rounded-lg"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              <motion.div 
                className="text-center"
                whileHover={{ scale: 1.1, y: -2 }}
              >
                <motion.div 
                  className="text-lg font-semibold text-gray-900"
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5, delay: 0.1 }}
                >
                  {currentTotal.toLocaleString()}
                </motion.div>
                <div className="text-sm text-gray-500">Total Users</div>
              </motion.div>
              
              <motion.div 
                className="text-center"
                whileHover={{ scale: 1.1, y: -2 }}
              >
                <motion.div 
                  className="text-lg font-semibold text-gray-900"
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                >
                  Top 10
                </motion.div>
                <div className="text-sm text-gray-500">Shown Below</div>
              </motion.div>
              
              <motion.div 
                className="text-center"
                whileHover={{ scale: 1.15, y: -2 }}
              >
                <motion.div 
                  className="text-lg font-semibold text-primary-600"
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5, delay: 0.3 }}
                >
                  #{activeTab === 'regional' 
                    ? (rankings.regional_ranking?.rank_in_region || 0)
                    : (rankings.university_ranking?.rank_in_university || 0)}
                </motion.div>
                <div className="text-sm text-gray-500">Your Rank</div>
              </motion.div>
            </motion.div>

            {/* Leaderboard Entries */}
            {currentData.map((entry, index) => (
              <motion.div
                key={entry.anonymous_id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                whileHover={{ 
                  scale: 1.02, 
                  x: 5,
                  boxShadow: entry.is_current_user 
                    ? '0 10px 30px rgba(59, 130, 246, 0.2)' 
                    : '0 4px 12px rgba(0, 0, 0, 0.1)',
                  transition: { duration: 0.2 }
                }}
                className={`flex items-center justify-between p-4 rounded-lg border transition-all duration-200 relative overflow-hidden ${
                  entry.is_current_user
                    ? 'bg-primary-50 border-primary-200 ring-2 ring-primary-500 ring-opacity-20'
                    : 'bg-white border-gray-200 hover:bg-gray-50'
                }`}
              >
                {/* Shine Effect on Hover */}
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent"
                  initial={{ x: '-100%', skewX: -15 }}
                  whileHover={{ x: '100%' }}
                  transition={{ duration: 0.6 }}
                />

                <div className="flex items-center space-x-4 relative z-10">
                  {/* Rank Badge */}
                  <motion.div 
                    className={`w-10 h-10 rounded-full flex items-center justify-center ${getRankBadgeColor(entry.rank)}`}
                    whileHover={{ 
                      scale: 1.2, 
                      rotate: entry.rank <= 3 ? 360 : 0,
                      transition: { duration: 0.5 }
                    }}
                  >
                    {getRankIcon(entry.rank)}
                  </motion.div>
                  
                  {/* User Info */}
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className={`font-medium ${entry.is_current_user ? 'text-primary-700' : 'text-gray-900'}`}>
                        {entry.is_current_user ? 'You' : `User ${entry.anonymous_id.slice(-4)}`}
                      </span>
                      {entry.is_current_user && (
                        <Star className="h-4 w-4 text-primary-500 fill-current" />
                      )}
                    </div>
                    <div className="text-sm text-gray-500">
                      Rank #{entry.rank} • Top {entry.percentile.toFixed(1)}%
                    </div>
                  </div>
                </div>
                
                {/* Score */}
                <motion.div 
                  className="text-right relative z-10"
                  whileHover={{ scale: 1.1 }}
                >
                  <motion.div 
                    className={`text-lg font-semibold ${getScoreColor(entry.percentile)}`}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3, delay: index * 0.05 + 0.2 }}
                  >
                    {entry.score.toFixed(1)}
                  </motion.div>
                  <div className="text-sm text-gray-500">Score</div>
                </motion.div>
              </motion.div>
            ))}

            {/* Show More Indicator */}
            {currentTotal > 10 && (
              <div className="text-center py-4 border-t border-gray-200 mt-6">
                <p className="text-sm text-gray-500">
                  Showing top 10 of {currentTotal.toLocaleString()} users
                </p>
                <div className="flex items-center justify-center space-x-2 mt-2">
                  <TrendingUp className="h-4 w-4 text-gray-400" />
                  <span className="text-xs text-gray-400">
                    Rankings update automatically with new scans
                  </span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <Users className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">No Leaderboard Data</h4>
            <p className="text-gray-500">
              Leaderboard will be available once more users join your region and university.
            </p>
          </div>
        )}
      </div>

      {/* Privacy Notice */}
      <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
        <div className="flex items-start space-x-2">
          <div className="w-4 h-4 rounded-full bg-green-500 flex-shrink-0 mt-0.5">
            <div className="w-2 h-2 bg-white rounded-full mx-auto mt-1"></div>
          </div>
          <div className="text-xs text-gray-600">
            <strong>Privacy Protected:</strong> All user identities are anonymized. 
            Only aggregated performance data is shown to maintain user privacy while enabling meaningful comparisons.
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default LeaderboardView;