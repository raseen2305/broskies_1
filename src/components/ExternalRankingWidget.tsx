import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Users, Award, MapPin, GraduationCap, AlertCircle } from 'lucide-react';
import { rankingAPI } from '../services/profileAPI';

interface ExternalRankingWidgetProps {
  githubUsername: string;
}

const ExternalRankingWidget: React.FC<ExternalRankingWidgetProps> = ({ githubUsername }) => {
  const [rankingData, setRankingData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRankings = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        console.log(`📡 Fetching rankings for external user: ${githubUsername}`);
        const data = await rankingAPI.checkExternalRanking(githubUsername);
        
        console.log('✅ External ranking data:', data);
        setRankingData(data);
        
      } catch (err: any) {
        console.error('❌ Failed to fetch external rankings:', err);
        setError(err.message || 'Failed to load rankings');
      } finally {
        setIsLoading(false);
      }
    };

    if (githubUsername) {
      fetchRankings();
    }
  }, [githubUsername]);

  // Loading state
  if (isLoading) {
    return (
      <div className="card p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  // No ranking data available - External scan specific message
  if (!rankingData?.has_ranking_data) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card p-6 bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200"
      >
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
          <div>
            <h3 className="text-lg font-semibold text-amber-900 mb-2">
              User Doesn't Have a Profile
            </h3>
            <p className="text-sm text-amber-700">
              This user hasn't set up their profile yet. Rankings are only available for users who have completed their profile setup and repository scan.
            </p>
          </div>
        </div>
      </motion.div>
    );
  }

  const { regional_ranking, university_ranking, profile } = rankingData;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Award className="w-5 h-5 text-primary-500" />
          <h3 className="text-lg font-semibold text-gray-900">Rankings</h3>
        </div>
        {profile && (
          <p className="text-xs text-gray-500">
            {profile.full_name} • {profile.university_short}
          </p>
        )}
      </div>

      {/* Side-by-side Rankings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Regional Ranking */}
        {regional_ranking && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-100"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <MapPin className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-gray-700">Regional</span>
              </div>
              <span className="text-xs text-gray-500">{regional_ranking.region}</span>
            </div>
            
            <div className="flex items-baseline space-x-2 mb-3">
              <span className="text-3xl font-bold text-blue-600">
                #{regional_ranking.rank_in_region}
              </span>
              <span className="text-sm text-gray-600">
                of {regional_ranking.total_users_in_region}
              </span>
            </div>
            
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-blue-700">Percentile</span>
                <span className="font-semibold text-blue-600">
                  Top {regional_ranking.percentile_region.toFixed(1)}%
                </span>
              </div>
              <div className="bg-blue-200 rounded-full h-2">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${100 - regional_ranking.percentile_region}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                  className="bg-blue-600 h-2 rounded-full"
                />
              </div>
            </div>
          </motion.div>
        )}

        {/* University Ranking */}
        {university_ranking && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-100"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <GraduationCap className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium text-gray-700">University</span>
              </div>
              <span className="text-xs text-gray-500">{university_ranking.university_short}</span>
            </div>
            
            <div className="flex items-baseline space-x-2 mb-3">
              <span className="text-3xl font-bold text-purple-600">
                #{university_ranking.rank_in_university}
              </span>
              <span className="text-sm text-gray-600">
                of {university_ranking.total_users_in_university}
              </span>
            </div>
            
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-purple-700">Percentile</span>
                <span className="font-semibold text-purple-600">
                  Top {university_ranking.percentile_university.toFixed(1)}%
                </span>
              </div>
              <div className="bg-purple-200 rounded-full h-2">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${100 - university_ranking.percentile_university}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                  className="bg-purple-600 h-2 rounded-full"
                />
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Overall Score Display */}
      {(regional_ranking?.overall_score || university_ranking?.overall_score) && (
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Overall Score</span>
            <span className="text-lg font-bold text-primary-600">
              {(regional_ranking?.overall_score || university_ranking?.overall_score).toFixed(1)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExternalRankingWidget;
