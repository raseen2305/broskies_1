import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingUp, Users, Award } from 'lucide-react';
import RankingTrendChart, { TrendDataPoint } from './RankingTrendChart';

export interface StatisticsPanelProps {
  isExpanded: boolean;
  type: 'regional' | 'university';
  rankPosition: number;
  totalUsers: number;
  percentileScore: number;
  contextName: string;
  trendData?: TrendDataPoint[];
}

const StatisticsPanel: React.FC<StatisticsPanelProps> = ({
  isExpanded,
  type,
  rankPosition,
  totalUsers,
  percentileScore,
  contextName,
  trendData,
}) => {
  const progressPercentage = ((totalUsers - rankPosition + 1) / totalUsers) * 100;
  const isTopPerformer = percentileScore >= 90;
  const isGoodPerformer = percentileScore >= 70 && percentileScore < 90;

  return (
    <AnimatePresence>
      {isExpanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          className="overflow-hidden"
        >
          <div className="pt-4 mt-4 border-t border-gray-200">
            {/* Detailed Statistics */}
            <div className="space-y-4">
              {/* Rank Position */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-white rounded-lg">
                    <Award className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">Your Rank</p>
                    <p className="text-xs text-gray-500">Position in {contextName}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900">#{rankPosition}</p>
                  <p className="text-xs text-gray-500">out of {totalUsers}</p>
                </div>
              </div>

              {/* Percentile Score */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-white rounded-lg">
                    <TrendingUp className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">Percentile Score</p>
                    <p className="text-xs text-gray-500">Your performance level</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900">{percentileScore.toFixed(1)}%</p>
                  <p className={`text-xs font-medium ${
                    isTopPerformer ? 'text-green-600' : isGoodPerformer ? 'text-blue-600' : 'text-gray-600'
                  }`}>
                    {isTopPerformer ? 'Top Performer' : isGoodPerformer ? 'Good Standing' : 'Keep Growing'}
                  </p>
                </div>
              </div>

              {/* Total Users */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-white rounded-lg">
                    <Users className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">Total {type === 'regional' ? 'Developers' : 'Students'}</p>
                    <p className="text-xs text-gray-500">In {contextName}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900">{totalUsers}</p>
                  <p className="text-xs text-gray-500">registered users</p>
                </div>
              </div>

              {/* Visual Progress Bar */}
              <div className="p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-gray-900">Your Position</p>
                  <p className="text-xs text-gray-600">
                    {totalUsers - rankPosition} users below you
                  </p>
                </div>
                
                {/* Position Indicator */}
                <div className="relative h-8 bg-white rounded-full overflow-hidden border border-gray-200">
                  {/* Background gradient */}
                  <div className="absolute inset-0 bg-gradient-to-r from-red-100 via-yellow-100 via-green-100 to-green-200" />
                  
                  {/* Position marker */}
                  <motion.div
                    initial={{ left: 0 }}
                    animate={{ left: `${progressPercentage}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                    className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2"
                    style={{ left: `${progressPercentage}%` }}
                  >
                    <div className="relative">
                      <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full border-2 border-white shadow-lg" />
                      <div className="absolute -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap">
                        <div className="bg-gray-900 text-white text-xs px-2 py-1 rounded shadow-lg">
                          You
                        </div>
                      </div>
                    </div>
                  </motion.div>
                </div>
                
                {/* Scale labels */}
                <div className="flex justify-between mt-2 text-xs text-gray-500">
                  <span>Bottom</span>
                  <span>Middle</span>
                  <span>Top</span>
                </div>
              </div>

              {/* Performance Insight */}
              <div className={`p-3 rounded-lg border-2 ${
                isTopPerformer 
                  ? 'bg-green-50 border-green-200' 
                  : isGoodPerformer 
                    ? 'bg-blue-50 border-blue-200' 
                    : 'bg-gray-50 border-gray-200'
              }`}>
                <p className="text-sm font-medium text-gray-900 mb-1">
                  {isTopPerformer 
                    ? '🎉 Outstanding Performance!' 
                    : isGoodPerformer 
                      ? '👍 Great Work!' 
                      : '💪 Keep Improving!'}
                </p>
                <p className="text-xs text-gray-600">
                  {isTopPerformer 
                    ? percentileScore === 100
                      ? `You're the top performer among ${type === 'regional' ? 'developers in your region' : 'students at your university'}. Excellent work!`
                      : `You're in the top ${(100 - percentileScore).toFixed(0)}% of ${type === 'regional' ? 'developers in your region' : 'students at your university'}. Excellent work!`
                    : isGoodPerformer 
                      ? `You're performing well! Keep coding to reach the top tier.`
                      : `You're ranked #${rankPosition} out of ${totalUsers}. Keep building projects to improve your ranking!`}
                </p>
              </div>

              {/* Ranking Trend Chart */}
              {trendData && trendData.length > 0 && (
                <RankingTrendChart data={trendData} type={type} />
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default StatisticsPanel;
