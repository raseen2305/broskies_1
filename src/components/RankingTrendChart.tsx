import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface TrendDataPoint {
  date: string;
  percentile: number;
  rank: number;
}

export interface RankingTrendChartProps {
  data: TrendDataPoint[];
  type: 'regional' | 'university';
}

const RankingTrendChart: React.FC<RankingTrendChartProps> = ({ data, type }) => {
  if (!data || data.length === 0) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg text-center">
        <p className="text-sm text-gray-600">No trend data available yet</p>
        <p className="text-xs text-gray-500 mt-1">Check back after a few days to see your progress</p>
      </div>
    );
  }

  // Calculate trend
  const firstPercentile = data[0].percentile;
  const lastPercentile = data[data.length - 1].percentile;
  const percentileChange = lastPercentile - firstPercentile;
  const isImproving = percentileChange > 0;
  const isStable = Math.abs(percentileChange) < 1;

  // Normalize data for visualization
  const maxPercentile = Math.max(...data.map(d => d.percentile));
  const minPercentile = Math.min(...data.map(d => d.percentile));
  const range = maxPercentile - minPercentile || 1;

  const normalizeY = (percentile: number) => {
    return ((percentile - minPercentile) / range) * 100;
  };

  // Create SVG path
  const width = 100;
  const height = 60;
  const points = data.map((point, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - (normalizeY(point.percentile) / 100) * height;
    return { x, y, ...point };
  });

  const pathD = points.reduce((path, point, index) => {
    if (index === 0) {
      return `M ${point.x} ${point.y}`;
    }
    return `${path} L ${point.x} ${point.y}`;
  }, '');

  const areaPathD = `${pathD} L ${width} ${height} L 0 ${height} Z`;

  return (
    <div className="mt-4 p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-gray-900">30-Day Trend</h4>
        <div className={`flex items-center space-x-1 text-sm font-medium ${
          isStable ? 'text-gray-600' : isImproving ? 'text-green-600' : 'text-red-600'
        }`}>
          {isStable ? (
            <Minus className="h-4 w-4" />
          ) : isImproving ? (
            <TrendingUp className="h-4 w-4" />
          ) : (
            <TrendingDown className="h-4 w-4" />
          )}
          <span>
            {isStable ? 'Stable' : `${Math.abs(percentileChange).toFixed(1)}%`}
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="relative h-24 bg-white rounded-lg p-2">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-full"
          preserveAspectRatio="none"
        >
          {/* Grid lines */}
          <line x1="0" y1={height / 2} x2={width} y2={height / 2} stroke="#e5e7eb" strokeWidth="0.5" />
          
          {/* Area fill */}
          <motion.path
            d={areaPathD}
            fill={type === 'regional' ? 'url(#blueGradient)' : 'url(#purpleGradient)'}
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.3 }}
            transition={{ duration: 0.5 }}
          />
          
          {/* Line */}
          <motion.path
            d={pathD}
            fill="none"
            stroke={type === 'regional' ? '#3b82f6' : '#9333ea'}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1, ease: 'easeInOut' }}
          />
          
          {/* Data points */}
          {points.map((point, index) => (
            <motion.circle
              key={index}
              cx={point.x}
              cy={point.y}
              r="2"
              fill={type === 'regional' ? '#3b82f6' : '#9333ea'}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.5 + index * 0.1, duration: 0.2 }}
            />
          ))}
          
          {/* Gradients */}
          <defs>
            <linearGradient id="blueGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="purpleGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#9333ea" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#9333ea" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 mt-3">
        <div className="text-center p-2 bg-white rounded">
          <p className="text-xs text-gray-500">Start</p>
          <p className="text-sm font-semibold text-gray-900">{firstPercentile.toFixed(1)}%</p>
        </div>
        <div className="text-center p-2 bg-white rounded">
          <p className="text-xs text-gray-500">Current</p>
          <p className="text-sm font-semibold text-gray-900">{lastPercentile.toFixed(1)}%</p>
        </div>
        <div className="text-center p-2 bg-white rounded">
          <p className="text-xs text-gray-500">Change</p>
          <p className={`text-sm font-semibold ${
            isStable ? 'text-gray-600' : isImproving ? 'text-green-600' : 'text-red-600'
          }`}>
            {percentileChange > 0 ? '+' : ''}{percentileChange.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Significant changes indicator */}
      {Math.abs(percentileChange) > 5 && (
        <div className={`mt-3 p-2 rounded-lg text-xs ${
          isImproving ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
        }`}>
          <span className="font-medium">
            {isImproving ? '🎉 Great progress!' : '⚠️ Ranking dropped'}
          </span>
          {' '}
          Your percentile {isImproving ? 'increased' : 'decreased'} by {Math.abs(percentileChange).toFixed(1)}% over the last 30 days.
        </div>
      )}
    </div>
  );
};

export default RankingTrendChart;
