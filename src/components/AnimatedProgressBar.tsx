import React from 'react';
import { motion } from 'framer-motion';

interface AnimatedProgressBarProps {
  progress: number;
  phase: string;
  showPhaseIndicators?: boolean;
  estimatedTimeRemaining?: number;
  className?: string;
}

const phases = [
  { id: 'connecting', label: 'Connecting', percentage: 10 },
  { id: 'profile', label: 'Profile Analysis', percentage: 25 },
  { id: 'repositories', label: 'Repository Scan', percentage: 60 },
  { id: 'analysis', label: 'Code Analysis', percentage: 85 },
  { id: 'insights', label: 'Generating Insights', percentage: 100 }
];

export const AnimatedProgressBar: React.FC<AnimatedProgressBarProps> = ({
  progress,
  phase,
  showPhaseIndicators = true,
  estimatedTimeRemaining,
  className = ''
}) => {
  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Progress Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-2xl font-bold text-primary-600">
            {Math.round(progress)}%
          </span>
          <span className="text-sm text-gray-600 capitalize">
            {phase.replace('_', ' ')}
          </span>
        </div>
        {estimatedTimeRemaining && estimatedTimeRemaining > 0 && (
          <div className="text-sm text-gray-500">
            ~{formatTime(estimatedTimeRemaining)} remaining
          </div>
        )}
      </div>

      {/* Main Progress Bar */}
      <div className="relative">
        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-primary-500 via-secondary-500 to-primary-600 rounded-full relative"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            {/* Animated shimmer effect */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
              animate={{ x: ['-100%', '100%'] }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            />
          </motion.div>
        </div>

        {/* Phase Indicators */}
        {showPhaseIndicators && (
          <div className="absolute -top-2 left-0 right-0 flex justify-between">
            {phases.map((phaseItem, index) => {
              const isActive = progress >= phaseItem.percentage;
              const isCurrent = phase === phaseItem.id;
              
              return (
                <motion.div
                  key={phaseItem.id}
                  className="relative"
                  style={{ left: `${phaseItem.percentage}%` }}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <div
                    className={`w-6 h-6 rounded-full border-2 transition-all duration-300 ${
                      isActive
                        ? 'bg-primary-500 border-primary-500'
                        : 'bg-white border-gray-300'
                    } ${isCurrent ? 'ring-4 ring-primary-200' : ''}`}
                  >
                    {isActive && (
                      <motion.div
                        className="w-2 h-2 bg-white rounded-full absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.2 }}
                      />
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};