import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart3, 
  Users, 
  Trophy, 
  TrendingUp, 
  MapPin, 
  GraduationCap,
  RefreshCw,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { UserRankings } from '../types';
import { rankingAPI, withRetry } from '../services/profileAPI';

interface StatisticsViewProps {
  rankings: UserRankings;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

interface RegionalStats {
  region: string;
  total_users: number;
  average_score: number;
  top_performers: Array<{
    rank: number;
    score: number;
    anonymous_id: string;
  }>;
}

interface UniversityStats {
  university: string;
  university_short: string;
  total_users: number;
  average_score: number;
  top_performers: Array<{
    rank: number;
    score: number;
    anonymous_id: string;
  }>;
}

const StatisticsView: React.FC<StatisticsViewProps> = ({ 
  rankings, 
  onRefresh,
  isRefreshing = false 
}) => {
  const [regionalStats, setRegionalStats] = useState<RegionalStats | null>(null);
  const [universityStats, setUniversityStats] = useState<UniversityStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [expandedSection, setExpandedSection] = useState<'regional' | 'university' | null>(null);

  useEffect(() => {
    loadDetailedStats();
  }, [rankings]);

  const loadDetailedStats = async () => {
    setIsLoadingStats(true);
    try {
      const [regionalData, universityData] = await Promise.all([
        withRetry(() => rankingAPI.getRegionalStats()),
        withRetry(() => rankingAPI.getUniversityStats())
      ]);
      
      setRegionalStats(regionalData);
      setUniversityStats(universityData);
    } catch (error) {
      console.error('Failed to load detailed stats:', error);
    } finally {
      setIsLoadingStats(false);
    }
  };

  const getPercentileColor = (percentile: number) => {
    if (percentile >= 90) return 'text-green-600 bg-green-50';
    if (percentile >= 75) return 'text-blue-600 bg-blue-50';
    if (percentile >= 50) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const formatRankText = (text: string) => {
    const match = text.match(/Top (\d+(?:\.\d+)?)% in (.+)/);
    if (match) {
      return {
        percentage: parseFloat(match[1]),
        location: match[2]
      };
    }
    return { percentage: 0, location: text };
  };

  const regionalData = formatRankText(rankings.regional_percentile_text);
  const universityData = formatRankText(rankings.university_percentile_text);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
          <BarChart3 className="h-6 w-6 text-primary-500" />
          <span>Detailed Statistics</span>
        </h3>
        
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing || isLoadingStats}
            className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 text-gray-700 rounded-lg transition-colors disabled:cursor-not-allowed"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        )}
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
          <div className="text-2xl font-bold text-primary-600">
            #{rankings.regional_ranking?.rank_in_region || 0}
          </div>
          <div className="text-sm text-gray-500">Regional Rank</div>
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
          <div className="text-2xl font-bold text-secondary-600">
            #{rankings.university_ranking?.rank_in_university || 0}
          </div>
          <div className="text-sm text-gray-500">University Rank</div>
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
          <div className="text-2xl font-bold text-green-600">
            {regionalData.percentage.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500">Regional Percentile</div>
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">
            {universityData.percentage.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500">University Percentile</div>
        </div>
      </div>

      {/* Regional Statistics */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <button
          onClick={() => setExpandedSection(expandedSection === 'regional' ? null : 'regional')}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <MapPin className="h-5 w-5 text-primary-500" />
            <div className="text-left">
              <h4 className="font-semibold text-gray-900">Regional Statistics</h4>
              <p className="text-sm text-gray-500">
                Performance in {regionalData.location} • {(rankings.regional_ranking?.total_users_in_region || 0).toLocaleString()} users
              </p>
            </div>
          </div>
          {expandedSection === 'regional' ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>
        
        {expandedSection === 'regional' && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="border-t border-gray-200 px-6 py-4"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-lg font-semibold text-gray-900">
                  {(rankings.regional_ranking?.total_users_in_region || 0).toLocaleString()}
                </div>
                <div className="text-sm text-gray-500">Total Users</div>
              </div>
              
              <div className="text-center">
                <div className="text-lg font-semibold text-gray-900">
                  #{(rankings.regional_ranking?.rank_in_region || 0).toLocaleString()}
                </div>
                <div className="text-sm text-gray-500">Your Position</div>
              </div>
              
              <div className="text-center">
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getPercentileColor(regionalData.percentage)}`}>
                  <Trophy className="h-4 w-4 mr-1" />
                  Top {regionalData.percentage}%
                </div>
                <div className="text-sm text-gray-500 mt-1">Performance Level</div>
              </div>
            </div>
            
            {regionalStats && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <h5 className="font-medium text-gray-900 mb-3">Regional Insights</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Average Score:</span>
                    <span className="ml-2 font-medium">{regionalStats.average_score.toFixed(1)}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Users Better Than You:</span>
                    <span className="ml-2 font-medium">
                      {((rankings.regional_ranking?.rank_in_region || 1) - 1).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* University Statistics */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <button
          onClick={() => setExpandedSection(expandedSection === 'university' ? null : 'university')}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <GraduationCap className="h-5 w-5 text-secondary-500" />
            <div className="text-left">
              <h4 className="font-semibold text-gray-900">University Statistics</h4>
              <p className="text-sm text-gray-500">
                Performance at {universityData.location} • {(rankings.university_ranking?.total_users_in_university || 0).toLocaleString()} users
              </p>
            </div>
          </div>
          {expandedSection === 'university' ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>
        
        {expandedSection === 'university' && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="border-t border-gray-200 px-6 py-4"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-lg font-semibold text-gray-900">
                  {(rankings.university_ranking?.total_users_in_university || 0).toLocaleString()}
                </div>
                <div className="text-sm text-gray-500">Total Users</div>
              </div>
              
              <div className="text-center">
                <div className="text-lg font-semibold text-gray-900">
                  #{(rankings.university_ranking?.rank_in_university || 0).toLocaleString()}
                </div>
                <div className="text-sm text-gray-500">Your Position</div>
              </div>
              
              <div className="text-center">
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getPercentileColor(universityData.percentage)}`}>
                  <Trophy className="h-4 w-4 mr-1" />
                  Top {universityData.percentage}%
                </div>
                <div className="text-sm text-gray-500 mt-1">Performance Level</div>
              </div>
            </div>
            
            {universityStats && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <h5 className="font-medium text-gray-900 mb-3">University Insights</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Average Score:</span>
                    <span className="ml-2 font-medium">{universityStats.average_score.toFixed(1)}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Users Better Than You:</span>
                    <span className="ml-2 font-medium">
                      {((rankings.university_ranking?.rank_in_university || 1) - 1).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* Performance Comparison */}
      <div className="bg-gradient-to-r from-primary-50 to-secondary-50 rounded-xl border border-primary-200 p-6">
        <h4 className="font-semibold text-gray-900 mb-4 flex items-center space-x-2">
          <TrendingUp className="h-5 w-5 text-primary-500" />
          <span>Performance Comparison</span>
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h5 className="font-medium text-gray-700 mb-2">Regional Performance</h5>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Better than</span>
                <span className="font-medium">
                  {((rankings.regional_ranking?.total_users_in_region || 0) - (rankings.regional_ranking?.rank_in_region || 0)).toLocaleString()} users
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${rankings.regional_ranking?.percentile_region || 0}%` }}
                />
              </div>
            </div>
          </div>
          
          <div>
            <h5 className="font-medium text-gray-700 mb-2">University Performance</h5>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Better than</span>
                <span className="font-medium">
                  {((rankings.university_ranking?.total_users_in_university || 0) - (rankings.university_ranking?.rank_in_university || 0)).toLocaleString()} users
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-secondary-500 to-secondary-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${rankings.university_ranking?.percentile_university || 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoadingStats && (
        <div className="text-center py-4">
          <div className="inline-flex items-center space-x-2 text-gray-500">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Loading detailed statistics...</span>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default StatisticsView;