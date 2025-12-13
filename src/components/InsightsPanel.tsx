import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Users, Star, TrendingUp, Code, Award } from 'lucide-react';
import { AggregateInsights } from '../services/hrCandidatesApi';
import { CandidateCardData } from './CandidateCard';

interface InsightsPanelProps {
  insights: AggregateInsights | null;
  isLoading?: boolean;
  className?: string;
}

/**
 * InsightsPanel Component
 * 
 * Displays recruitment insights and analytics for the HR dashboard.
 * 
 * Features:
 * - Total candidates count
 * - Average score
 * - Top 5 languages with usage bars
 * - Skill distribution visualization
 * - Top 5 performers (score ≥8.0) as mini cards
 * - Auto-updates when data changes
 * - Loading states
 * 
 * @example
 * ```tsx
 * <InsightsPanel 
 *   insights={aggregateInsights}
 *   isLoading={false}
 * />
 * ```
 */
const InsightsPanel: React.FC<InsightsPanelProps> = ({
  insights,
  isLoading = false,
  className = '',
}) => {
  const [animatedScore, setAnimatedScore] = useState(0);

  // Animate average score
  useEffect(() => {
    if (insights?.average_score) {
      let start = 0;
      const end = insights.average_score;
      const duration = 1000;
      const increment = end / (duration / 16);

      const timer = setInterval(() => {
        start += increment;
        if (start >= end) {
          setAnimatedScore(end);
          clearInterval(timer);
        } else {
          setAnimatedScore(start);
        }
      }, 16);

      return () => clearInterval(timer);
    }
  }, [insights?.average_score]);

  /**
   * Get color for skill level
   */
  const getSkillColor = (level: string): string => {
    if (level.includes('Expert') || level.includes('9-10')) return 'bg-green-500';
    if (level.includes('Advanced') || level.includes('7-8')) return 'bg-blue-500';
    if (level.includes('Intermediate') || level.includes('5-6')) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  /**
   * Get initials from username
   */
  const getInitials = (username: string): string => {
    return username
      .split('-')
      .map(part => part.charAt(0).toUpperCase())
      .slice(0, 2)
      .join('');
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <div className="space-y-6 animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/2"></div>
          <div className="space-y-3">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <p className="text-gray-500 text-center">No insights available</p>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
          <TrendingUp className="h-5 w-5 text-primary-600" />
          <span>Recruitment Insights</span>
        </h3>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4">
          {/* Total Candidates */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200"
          >
            <Users className="h-6 w-6 text-blue-600 mb-2" />
            <p className="text-2xl font-bold text-blue-900">
              {insights.total_candidates}
            </p>
            <p className="text-xs text-blue-700">Total Candidates</p>
          </motion.div>

          {/* Average Score */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200"
          >
            <Star className="h-6 w-6 text-green-600 mb-2" />
            <p className="text-2xl font-bold text-green-900">
              {animatedScore.toFixed(1)}
            </p>
            <p className="text-xs text-green-700">Average Score</p>
          </motion.div>
        </div>

        {/* Top Languages */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center space-x-2">
            <Code className="h-4 w-4" />
            <span>Top Languages</span>
          </h4>
          <div className="space-y-2">
            {insights.top_languages.slice(0, 5).map(([language, count], index) => {
              const maxCount = insights.top_languages[0][1];
              const percentage = (count / maxCount) * 100;

              return (
                <motion.div
                  key={language}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="space-y-1"
                >
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-gray-700">{language}</span>
                    <span className="text-gray-500">{count}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full"
                    />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Skill Distribution */}
        {Object.keys(insights.skill_distribution).length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">
              Skill Distribution
            </h4>
            <div className="space-y-2">
              {Object.entries(insights.skill_distribution).map(([level, count], index) => {
                const total = Object.values(insights.skill_distribution).reduce(
                  (sum, val) => sum + val,
                  0
                );
                const percentage = (count / total) * 100;

                return (
                  <motion.div
                    key={level}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center space-x-2 flex-1">
                      <div className={`w-3 h-3 rounded-full ${getSkillColor(level)}`}></div>
                      <span className="text-sm text-gray-700">{level}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${percentage}%` }}
                          transition={{ duration: 0.5, delay: index * 0.1 }}
                          className={`h-2 rounded-full ${getSkillColor(level)}`}
                        />
                      </div>
                      <span className="text-xs text-gray-500 w-8 text-right">
                        {count}
                      </span>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        )}

        {/* Top Performers */}
        {insights.top_performers.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center space-x-2">
              <Award className="h-4 w-4 text-yellow-600" />
              <span>Top Performers (8.0+)</span>
            </h4>
            <div className="space-y-2">
              {insights.top_performers.slice(0, 5).map((candidate, index) => (
                <motion.div
                  key={candidate.username}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center space-x-3 p-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                  onClick={() => window.location.href = `/hr/candidates/${candidate.username}`}
                >
                  {/* Avatar */}
                  {candidate.profile_picture ? (
                    <img
                      src={candidate.profile_picture}
                      alt={candidate.username}
                      className="w-10 h-10 rounded-full object-cover border-2 border-gray-200"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold text-sm">
                      {getInitials(candidate.username)}
                    </div>
                  )}

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {candidate.full_name || `@${candidate.username}`}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {candidate.role_category}
                    </p>
                  </div>

                  {/* Score Badge */}
                  <div className="flex items-center space-x-1 px-2 py-1 bg-green-100 text-green-700 rounded-full border border-green-200">
                    <Star className="h-3 w-3 fill-current" />
                    <span className="text-xs font-bold">
                      {candidate.overall_score.toFixed(1)}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InsightsPanel;
