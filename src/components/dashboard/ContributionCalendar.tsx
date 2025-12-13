import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Calendar, TrendingUp, Activity, Award, BarChart3, Clock } from 'lucide-react';

interface ContributionCalendarProps {
  scanResults?: any;
}

interface ContributionDay {
  date: string;
  count: number;
  weekday: number;
  level: number;
  color: string;
}

interface ContributionStats {
  calendar_data: ContributionDay[];
  contribution_streaks: {
    current_streak: number;
    longest_streak: number;
    streak_ranges: Array<{
      start: string;
      end: string;
      length: number;
    }>;
  };
  contribution_patterns: {
    weekday_averages: { [key: string]: number };
    most_active_day: {
      day: string;
      average_contributions: number;
    };
    monthly_trends: { [key: string]: number };
    total_active_days: number;
    total_days: number;
  };
  contribution_levels: { [key: string]: number };
  commit_repositories: Array<{
    name: string;
    owner: string;
    url: string;
    language: string;
    language_color: string;
    contributions: number;
  }>;
}

const ContributionCalendar: React.FC<ContributionCalendarProps> = ({ scanResults }) => {
  const [contributionStats, setContributionStats] = useState<ContributionStats | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<'week' | 'month' | 'year'>('year');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (scanResults?.contributionStats) {
      setContributionStats(scanResults.contributionStats);
      setIsLoading(false);
    }
  }, [scanResults]);

  const getWeekdayName = (index: number): string => {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    return days[index];
  };

  const getMonthName = (monthKey: string): string => {
    const [year, month] = monthKey.split('-');
    const date = new Date(parseInt(year), parseInt(month) - 1);
    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  };

  const renderContributionGrid = () => {
    if (!contributionStats?.calendar_data) return null;

    const weeks: ContributionDay[][] = [];
    let currentWeek: ContributionDay[] = [];

    contributionStats.calendar_data.forEach((day, index) => {
      currentWeek.push(day);
      if (day.weekday === 6 || index === contributionStats.calendar_data.length - 1) {
        weeks.push([...currentWeek]);
        currentWeek = [];
      }
    });

    return (
      <div className="overflow-x-auto">
        <div className="inline-flex flex-col space-y-1 min-w-max">
          {/* Weekday labels */}
          <div className="flex">
            <div className="w-8"></div>
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day, index) => (
              <div key={day} className="w-3 h-3 text-xs text-gray-500 flex items-center justify-center mr-1">
                {index % 2 === 1 ? day.charAt(0) : ''}
              </div>
            ))}
          </div>
          
          {/* Calendar grid */}
          <div className="flex space-x-1">
            {weeks.map((week, weekIndex) => (
              <div key={weekIndex} className="flex flex-col space-y-1">
                {Array.from({ length: 7 }, (_, dayIndex) => {
                  const day = week.find(d => d.weekday === dayIndex);
                  return (
                    <motion.div
                      key={`${weekIndex}-${dayIndex}`}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: weekIndex * 0.01 + dayIndex * 0.005 }}
                      className="w-3 h-3 rounded-sm border border-gray-200"
                      style={{ 
                        backgroundColor: day ? day.color : '#f3f4f6',
                        cursor: day ? 'pointer' : 'default'
                      }}
                      title={day ? `${day.date}: ${day.count} contributions` : ''}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <div className="h-8 bg-gray-200 rounded w-64 mb-2 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-96 animate-pulse"></div>
        </div>
        <div className="card p-6 animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-48 mb-6"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!contributionStats) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Contribution Calendar</h1>
          <p className="text-gray-600">GitHub activity and contribution patterns</p>
        </div>
        <div className="card p-8 text-center">
          <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Contribution Data</h3>
          <p className="text-gray-600">Contribution calendar data is not available.</p>
        </div>
      </div>
    );
  }

  const totalContributions = contributionStats.calendar_data?.reduce((sum, day) => sum + day.count, 0) || 0;
  const averageDaily = contributionStats.contribution_patterns?.total_days 
    ? totalContributions / contributionStats.contribution_patterns.total_days 
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Contribution Calendar</h1>
        <p className="text-gray-600">GitHub activity and contribution patterns over the last year</p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-green-100 rounded-lg p-3">
              <Activity className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Total Contributions</p>
              <p className="text-2xl font-bold text-gray-900">{totalContributions}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-blue-100 rounded-lg p-3">
              <Award className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Current Streak</p>
              <p className="text-2xl font-bold text-gray-900">
                {contributionStats.contribution_streaks.current_streak}
              </p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-purple-100 rounded-lg p-3">
              <TrendingUp className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Longest Streak</p>
              <p className="text-2xl font-bold text-gray-900">
                {contributionStats.contribution_streaks.longest_streak}
              </p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-orange-100 rounded-lg p-3">
              <Calendar className="h-6 w-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Active Days</p>
              <p className="text-2xl font-bold text-gray-900">
                {contributionStats.contribution_patterns.total_active_days}
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Contribution Heatmap */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-gray-900">Contribution Activity</h3>
          <div className="text-sm text-gray-500">
            {contributionStats.calendar_data.length} days
          </div>
        </div>

        {renderContributionGrid()}

        {/* Legend */}
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-gray-500">Less</div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 rounded-sm bg-gray-100 border border-gray-200"></div>
            <div className="w-3 h-3 rounded-sm bg-green-200"></div>
            <div className="w-3 h-3 rounded-sm bg-green-400"></div>
            <div className="w-3 h-3 rounded-sm bg-green-600"></div>
            <div className="w-3 h-3 rounded-sm bg-green-800"></div>
          </div>
          <div className="text-sm text-gray-500">More</div>
        </div>

        <div className="mt-4 text-center text-sm text-gray-600">
          <strong>{totalContributions}</strong> contributions in the last year •{' '}
          <strong>{averageDaily.toFixed(1)}</strong> average per day
        </div>
      </motion.div>

      {/* Activity Patterns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weekday Patterns */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Weekly Patterns</h3>
          <div className="space-y-3">
            {Object.entries(contributionStats.contribution_patterns.weekday_averages)
              .sort(([, a], [, b]) => b - a)
              .map(([day, average], index) => (
                <div key={day} className="flex items-center space-x-4">
                  <div className="w-20 text-sm font-medium text-gray-700">
                    {day}
                  </div>
                  <div className="flex-1 bg-gray-200 rounded-full h-3">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(average / Math.max(...Object.values(contributionStats.contribution_patterns.weekday_averages))) * 100}%` }}
                      transition={{ delay: 0.7 + index * 0.1, duration: 0.8 }}
                      className="h-3 rounded-full bg-gradient-to-r from-blue-500 to-green-500"
                    />
                  </div>
                  <div className="w-12 text-sm font-semibold text-gray-900 text-right">
                    {average.toFixed(1)}
                  </div>
                </div>
              ))}
          </div>
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <div className="text-sm font-medium text-blue-900">Most Active Day</div>
            <div className="text-sm text-blue-700">
              <strong>{contributionStats.contribution_patterns.most_active_day.day}</strong> with{' '}
              {contributionStats.contribution_patterns.most_active_day.average_contributions.toFixed(1)} average contributions
            </div>
          </div>
        </motion.div>

        {/* Monthly Trends */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Monthly Trends</h3>
          <div className="space-y-2">
            {Object.entries(contributionStats.contribution_patterns.monthly_trends)
              .sort(([a], [b]) => a.localeCompare(b))
              .slice(-12) // Last 12 months
              .map(([month, contributions], index) => (
                <div key={month} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                  <div className="text-sm font-medium text-gray-700">
                    {getMonthName(month)}
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(contributions / Math.max(...Object.values(contributionStats.contribution_patterns.monthly_trends))) * 100}%` }}
                        transition={{ delay: 0.8 + index * 0.05, duration: 0.6 }}
                        className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-pink-500"
                      />
                    </div>
                    <div className="text-sm font-semibold text-gray-900 w-8 text-right">
                      {contributions}
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </motion.div>
      </div>

      {/* Contribution Levels */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="card p-6"
      >
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Contribution Intensity</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Object.entries(contributionStats.contribution_levels)
            .sort(([a], [b]) => parseInt(a) - parseInt(b))
            .map(([level, count]) => (
              <div key={level} className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{count}</div>
                <div className="text-xs text-gray-600 mt-1">
                  {level === '0' ? 'No activity' : `${level} contribution${parseInt(level) > 1 ? 's' : ''}`}
                </div>
              </div>
            ))}
        </div>
      </motion.div>

      {/* Top Contributing Repositories */}
      {contributionStats.commit_repositories && contributionStats.commit_repositories.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Top Contributing Repositories</h3>
          <div className="space-y-3">
            {contributionStats.commit_repositories.slice(0, 10).map((repo, index) => (
              <motion.div
                key={repo.name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.0 + index * 0.1 }}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div 
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: repo.language_color }}
                  />
                  <div>
                    <div className="font-medium text-gray-900">{repo.name}</div>
                    <div className="text-sm text-gray-600">{repo.language}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-gray-900">{repo.contributions}</div>
                  <div className="text-xs text-gray-500">commits</div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Streak Information */}
      {contributionStats.contribution_streaks.streak_ranges && contributionStats.contribution_streaks.streak_ranges.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Contribution Streaks</h3>
          <div className="space-y-3">
            {contributionStats.contribution_streaks.streak_ranges
              .sort((a, b) => b.length - a.length)
              .slice(0, 10)
              .map((streak, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      streak.length >= 7 ? 'bg-green-500' :
                      streak.length >= 3 ? 'bg-yellow-500' : 'bg-gray-400'
                    }`} />
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {streak.start} to {streak.end}
                      </div>
                      <div className="text-xs text-gray-600">
                        {streak.length} day{streak.length > 1 ? 's' : ''}
                      </div>
                    </div>
                  </div>
                  <div className="text-sm font-semibold text-gray-900">
                    {streak.length} day{streak.length > 1 ? 's' : ''}
                  </div>
                </div>
              ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default ContributionCalendar;