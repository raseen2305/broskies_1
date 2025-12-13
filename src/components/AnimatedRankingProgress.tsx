import React, { useEffect, useState } from 'react';
import { motion, useAnimation } from 'framer-motion';
import { Trophy, TrendingUp, Users, Target } from 'lucide-react';

interface AnimatedRankingProgressProps {
  currentPercentile: number;
  previousPercentile?: number;
  rank: number;
  totalUsers: number;
  label: string;
  color?: 'primary' | 'secondary' | 'success' | 'warning';
  showAnimation?: boolean;
  onAnimationComplete?: () => void;
}

const AnimatedRankingProgress: React.FC<AnimatedRankingProgressProps> = ({
  currentPercentile,
  previousPercentile,
  rank,
  totalUsers,
  label,
  color = 'primary',
  showAnimation = true,
  onAnimationComplete
}) => {
  const [displayPercentile, setDisplayPercentile] = useState(previousPercentile || 0);
  const [isAnimating, setIsAnimating] = useState(false);
  const controls = useAnimation();

  const colorClasses = {
    primary: {
      bg: 'from-primary-500 to-primary-600',
      text: 'text-primary-600',
      light: 'bg-primary-50'
    },
    secondary: {
      bg: 'from-secondary-500 to-secondary-600',
      text: 'text-secondary-600',
      light: 'bg-secondary-50'
    },
    success: {
      bg: 'from-green-500 to-green-600',
      text: 'text-green-600',
      light: 'bg-green-50'
    },
    warning: {
      bg: 'from-yellow-500 to-yellow-600',
      text: 'text-yellow-600',
      light: 'bg-yellow-50'
    }
  };

  const getPercentileIcon = (percentile: number) => {
    if (percentile >= 90) return Trophy;
    if (percentile >= 75) return TrendingUp;
    if (percentile >= 50) return Target;
    return Users;
  };

  const formatPercentile = (value: number) => {
    return Math.round(value * 10) / 10;
  };

  const animateProgress = async () => {
    if (!showAnimation) {
      setDisplayPercentile(currentPercentile);
      return;
    }

    setIsAnimating(true);
    
    // Animate the progress bar
    await controls.start({
      width: `${currentPercentile}%`,
      transition: { duration: 1.5, ease: 'easeOut' }
    });

    // Animate the number counter
    const startValue = previousPercentile || 0;
    const endValue = currentPercentile;
    const duration = 1000; // 1 second
    const steps = 60; // 60 FPS
    const increment = (endValue - startValue) / steps;
    
    for (let i = 0; i <= steps; i++) {
      setTimeout(() => {
        const value = startValue + (increment * i);
        setDisplayPercentile(value);
        
        if (i === steps) {
          setIsAnimating(false);
          onAnimationComplete?.();
        }
      }, (duration / steps) * i);
    }
  };

  useEffect(() => {
    animateProgress();
  }, [currentPercentile, previousPercentile]);

  const PercentileIcon = getPercentileIcon(currentPercentile);
  const hasImproved = previousPercentile !== undefined && currentPercentile > previousPercentile;
  const hasDeclined = previousPercentile !== undefined && currentPercentile < previousPercentile;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${colorClasses[color].bg} flex items-center justify-center`}>
            <PercentileIcon className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{label}</h3>
            <p className="text-sm text-gray-500">
              Rank #{rank.toLocaleString()} of {totalUsers.toLocaleString()}
            </p>
          </div>
        </div>

        {/* Change Indicator */}
        {(hasImproved || hasDeclined) && (
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 1.5, duration: 0.5, type: 'spring' }}
            className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${
              hasImproved 
                ? 'bg-green-100 text-green-700' 
                : 'bg-red-100 text-red-700'
            }`}
          >
            <TrendingUp className={`h-3 w-3 ${hasDeclined ? 'rotate-180' : ''}`} />
            <span>
              {hasImproved ? '+' : ''}{formatPercentile(currentPercentile - (previousPercentile || 0))}%
            </span>
          </motion.div>
        )}
      </div>

      {/* Main Percentile Display */}
      <div className="text-center space-y-2">
        <motion.div
          className={`text-4xl font-bold ${colorClasses[color].text}`}
          animate={isAnimating ? { scale: [1, 1.1, 1] } : {}}
          transition={{ duration: 0.3, repeat: isAnimating ? Infinity : 0, repeatDelay: 0.5 }}
        >
          Top {formatPercentile(displayPercentile)}%
        </motion.div>
        <p className="text-sm text-gray-600">Performance Percentile</p>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-gray-600">
          <span>Progress</span>
          <span>{formatPercentile(displayPercentile)}%</span>
        </div>
        
        <div className="relative">
          {/* Background */}
          <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
            {/* Animated Progress */}
            <motion.div
              className={`h-full bg-gradient-to-r ${colorClasses[color].bg} relative`}
              initial={{ width: previousPercentile ? `${previousPercentile}%` : '0%' }}
              animate={controls}
            >
              {/* Shimmer Effect */}
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                animate={{
                  x: ['-100%', '100%']
                }}
                transition={{
                  duration: 1.5,
                  repeat: isAnimating ? Infinity : 0,
                  repeatDelay: 0.5
                }}
                style={{ width: '50%' }}
              />
            </motion.div>
          </div>

          {/* Milestone Markers */}
          <div className="absolute -top-1 w-full h-5 flex justify-between items-center">
            {[25, 50, 75, 90].map((milestone) => (
              <motion.div
                key={milestone}
                className={`w-1 h-5 rounded-full ${
                  currentPercentile >= milestone 
                    ? `bg-gradient-to-b ${colorClasses[color].bg}` 
                    : 'bg-gray-300'
                }`}
                initial={{ scale: 0 }}
                animate={{ scale: currentPercentile >= milestone ? 1 : 0.5 }}
                transition={{ delay: 0.5 + (milestone / 100), duration: 0.3 }}
                style={{ left: `${milestone}%`, transform: 'translateX(-50%)' }}
              />
            ))}
          </div>
        </div>

        {/* Milestone Labels */}
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>0%</span>
          <span>25%</span>
          <span>50%</span>
          <span>75%</span>
          <span>90%</span>
          <span>100%</span>
        </div>
      </div>

      {/* Achievement Badges */}
      <div className="flex flex-wrap gap-2">
        {currentPercentile >= 90 && (
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 2, type: 'spring' }}
            className="flex items-center space-x-1 px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium"
          >
            <Trophy className="h-3 w-3" />
            <span>Top Performer</span>
          </motion.div>
        )}
        
        {currentPercentile >= 75 && (
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 2.2, type: 'spring' }}
            className="flex items-center space-x-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium"
          >
            <TrendingUp className="h-3 w-3" />
            <span>High Achiever</span>
          </motion.div>
        )}

        {hasImproved && (
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 2.4, type: 'spring' }}
            className="flex items-center space-x-1 px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium"
          >
            <TrendingUp className="h-3 w-3" />
            <span>Improved</span>
          </motion.div>
        )}
      </div>

      {/* Statistics */}
      <div className={`${colorClasses[color].light} rounded-lg p-3 grid grid-cols-3 gap-3 text-center`}>
        <div>
          <div className="text-lg font-semibold text-gray-900">
            {(totalUsers - rank).toLocaleString()}
          </div>
          <div className="text-xs text-gray-600">Users Below</div>
        </div>
        <div>
          <div className="text-lg font-semibold text-gray-900">
            #{rank.toLocaleString()}
          </div>
          <div className="text-xs text-gray-600">Your Rank</div>
        </div>
        <div>
          <div className="text-lg font-semibold text-gray-900">
            {Math.round((rank / totalUsers) * 100)}%
          </div>
          <div className="text-xs text-gray-600">Rank Ratio</div>
        </div>
      </div>
    </div>
  );
};

export default AnimatedRankingProgress;