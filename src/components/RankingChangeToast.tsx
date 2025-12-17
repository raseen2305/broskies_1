import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingUp, TrendingDown, X } from 'lucide-react';

export interface RankingChangeToastProps {
  isVisible: boolean;
  type: 'regional' | 'university';
  change: number;
  onClose: () => void;
  autoCloseMs?: number;
}

const RankingChangeToast: React.FC<RankingChangeToastProps> = ({
  isVisible,
  type,
  change,
  onClose,
  autoCloseMs = 5000,
}) => {
  const isImprovement = change > 0;
  const isSignificant = Math.abs(change) > 5;

  useEffect(() => {
    if (isVisible && autoCloseMs > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, autoCloseMs);

      return () => clearTimeout(timer);
    }
  }, [isVisible, autoCloseMs, onClose]);

  if (!isSignificant) {
    return null;
  }

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -50, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -50, scale: 0.9 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="fixed top-4 right-4 left-4 sm:left-auto z-50 max-w-md mx-auto sm:mx-0"
        >
          <div className={`rounded-lg shadow-2xl p-4 ${
            isImprovement 
              ? 'bg-gradient-to-r from-green-500 to-green-600' 
              : 'bg-gradient-to-r from-orange-500 to-orange-600'
          } text-white`}>
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                {isImprovement ? (
                  <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                    <TrendingUp className="h-6 w-6" />
                  </div>
                ) : (
                  <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                    <TrendingDown className="h-6 w-6" />
                  </div>
                )}
              </div>
              
              <div className="flex-1">
                <h3 className="font-bold text-lg mb-1">
                  {isImprovement ? '🎉 Ranking Improved!' : '📊 Ranking Changed'}
                </h3>
                <p className="text-sm opacity-90">
                  Your {type === 'regional' ? 'regional' : 'university'} ranking {isImprovement ? 'increased' : 'decreased'} by{' '}
                  <span className="font-bold">{Math.abs(change).toFixed(1)}%</span>
                </p>
                {isImprovement && (
                  <p className="text-xs opacity-75 mt-1">
                    Great work! Keep coding to maintain your position.
                  </p>
                )}
              </div>

              <button
                onClick={onClose}
                className="flex-shrink-0 p-1 hover:bg-white/20 rounded transition-colors"
                aria-label="Close notification"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Progress bar for auto-close */}
            {autoCloseMs > 0 && (
              <motion.div
                initial={{ width: '100%' }}
                animate={{ width: '0%' }}
                transition={{ duration: autoCloseMs / 1000, ease: 'linear' }}
                className="h-1 bg-white/30 rounded-full mt-3"
              />
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default RankingChangeToast;
