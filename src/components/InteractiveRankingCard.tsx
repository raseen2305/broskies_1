import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Trophy, 
  Info, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Share2,
  Download
} from 'lucide-react';
import '../styles/rankings.css';

interface RankingData {
  percentileText: string;
  rank: number;
  totalUsers: number;
  percentile: number;
  location: string;
  type: 'regional' | 'university';
}

interface InteractiveRankingCardProps {
  data: RankingData;
  changeIndicator?: 'up' | 'down' | 'same' | null;
  onShare?: () => void;
  onExport?: () => void;
  className?: string;
}

const InteractiveRankingCard: React.FC<InteractiveRankingCardProps> = ({
  data,
  changeIndicator,
  onShare,
  onExport,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  const getPercentileColor = (percentile: number) => {
    if (percentile >= 90) return 'from-green-500 to-emerald-500';
    if (percentile >= 75) return 'from-blue-500 to-cyan-500';
    if (percentile >= 50) return 'from-yellow-500 to-orange-500';
    return 'from-red-500 to-pink-500';
  };

  const getChangeIcon = () => {
    switch (changeIndicator) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      case 'same':
        return <Minus className="h-4 w-4 text-gray-600" />;
      default:
        return null;
    }
  };

  const getChangeText = () => {
    switch (changeIndicator) {
      case 'up':
        return 'Improved since last update';
      case 'down':
        return 'Decreased since last update';
      case 'same':
        return 'No change since last update';
      default:
        return 'First time ranking';
    }
  };

  const handleCardClick = () => {
    setIsExpanded(!isExpanded);
  };

  const handleShare = async () => {
    if (onShare) {
      onShare();
      return;
    }

    // Default share functionality
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'My Coding Ranking',
          text: `I'm in the ${data.percentileText} for coding performance!`,
          url: window.location.href
        });
      } catch (error) {
        console.log('Share cancelled or failed');
      }
    } else {
      // Fallback: copy to clipboard
      const text = `I'm in the ${data.percentileText} for coding performance! Check out your ranking at ${window.location.href}`;
      await navigator.clipboard.writeText(text);
      
      // Show temporary success message
      setShowTooltip(true);
      setTimeout(() => setShowTooltip(false), 2000);
    }
  };

  const handleExport = () => {
    if (onExport) {
      onExport();
      return;
    }

    // Default export functionality
    const exportData = {
      ranking: data.percentileText,
      rank: data.rank,
      totalUsers: data.totalUsers,
      percentile: data.percentile,
      location: data.location,
      type: data.type,
      timestamp: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ranking-${data.type}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <motion.div
      ref={cardRef}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ 
        y: -8, 
        scale: 1.02,
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        transition: { duration: 0.3 } 
      }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      className={`comparison-card cursor-pointer relative overflow-hidden ${className}`}
      onClick={handleCardClick}
      style={{ transformStyle: 'preserve-3d' }}
    >
      {/* Animated Border Glow */}
      <motion.div
        className="absolute -inset-1 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-xl blur opacity-0"
        animate={{ opacity: isHovered ? 0.3 : 0 }}
        transition={{ duration: 0.3 }}
        style={{ zIndex: -1 }}
      />

      {/* Hover Glow Effect */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-primary-500/5 to-secondary-500/5 rounded-xl"
        initial={{ opacity: 0 }}
        animate={{ opacity: isHovered ? 1 : 0 }}
        transition={{ duration: 0.3 }}
      />

      {/* Shine Effect on Hover */}
      {isHovered && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
          initial={{ x: '-100%', skewX: -15 }}
          animate={{ x: '100%' }}
          transition={{ duration: 0.8, ease: 'easeInOut' }}
        />
      )}

      {/* Card Header */}
      <div className="comparison-card-header relative z-10">
        <div className={`comparison-card-icon bg-gradient-to-br ${getPercentileColor(data.percentile)}`}>
          <Trophy className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
        </div>
        
        <div className="comparison-card-title">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 flex items-center space-x-2">
            <span>{data.type === 'regional' ? 'Regional' : 'University'} Ranking</span>
            {changeIndicator && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="flex items-center space-x-1"
              >
                {getChangeIcon()}
              </motion.div>
            )}
            <motion.div
              animate={{ rotate: isExpanded ? 180 : 0 }}
              transition={{ duration: 0.3 }}
            >
              <ChevronDown className="h-4 w-4 text-gray-400" />
            </motion.div>
          </h3>
          <p className="text-xs sm:text-sm text-gray-500">
            Compared to peers in {data.location}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={(e) => {
              e.stopPropagation();
              handleShare();
            }}
            className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors relative"
          >
            <Share2 className="h-4 w-4 text-gray-600" />
            {showTooltip && (
              <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded">
                Copied!
              </div>
            )}
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={(e) => {
              e.stopPropagation();
              handleExport();
            }}
            className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors"
          >
            <Download className="h-4 w-4 text-gray-600" />
          </motion.button>
        </div>
      </div>

      {/* Main Ranking Badge */}
      <motion.div
        className={`ranking-badge bg-gradient-to-r ${getPercentileColor(data.percentile)} relative z-10 overflow-hidden`}
        whileHover={{ scale: 1.05, rotate: [0, -1, 1, 0] }}
        transition={{ duration: 0.4 }}
      >
        <div className="ranking-badge-text">
          {data.percentileText}
        </div>
        <div className="ranking-badge-subtitle">
          {data.type === 'regional' ? 'Regional' : 'University'} Performance
        </div>

        {/* Animated Background Pattern */}
        <motion.div
          className="absolute inset-0 opacity-10"
          animate={{
            backgroundPosition: isHovered ? ['0% 0%', '100% 100%'] : '0% 0%'
          }}
          transition={{ duration: 2, repeat: Infinity, repeatType: 'reverse' }}
          style={{
            backgroundImage: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
            backgroundSize: '200% 200%'
          }}
        />

        {/* Sparkle Effect */}
        {isHovered && (
          <>
            <motion.div
              className="absolute top-2 right-2 w-2 h-2 bg-white rounded-full"
              animate={{
                scale: [0, 1, 0],
                opacity: [0, 1, 0]
              }}
              transition={{ duration: 1, repeat: Infinity, delay: 0 }}
            />
            <motion.div
              className="absolute bottom-4 left-4 w-1.5 h-1.5 bg-white rounded-full"
              animate={{
                scale: [0, 1, 0],
                opacity: [0, 1, 0]
              }}
              transition={{ duration: 1, repeat: Infinity, delay: 0.3 }}
            />
            <motion.div
              className="absolute top-1/2 right-8 w-1 h-1 bg-white rounded-full"
              animate={{
                scale: [0, 1, 0],
                opacity: [0, 1, 0]
              }}
              transition={{ duration: 1, repeat: Infinity, delay: 0.6 }}
            />
          </>
        )}
      </motion.div>

      {/* Quick Stats */}
      <div className="stats-grid relative z-10">
        <motion.div 
          className="stat-item relative overflow-hidden"
          whileHover={{ 
            scale: 1.08,
            backgroundColor: 'rgba(59, 130, 246, 0.05)',
            transition: { duration: 0.2 }
          }}
        >
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-transparent"
            initial={{ x: '-100%' }}
            whileHover={{ x: '100%' }}
            transition={{ duration: 0.6 }}
          />
          <div className="stat-value relative z-10">#{data.rank.toLocaleString()}</div>
          <div className="stat-label relative z-10">Your Rank</div>
        </motion.div>
        
        <motion.div 
          className="stat-item relative overflow-hidden"
          whileHover={{ 
            scale: 1.08,
            backgroundColor: 'rgba(59, 130, 246, 0.05)',
            transition: { duration: 0.2 }
          }}
        >
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-secondary-500/10 to-transparent"
            initial={{ x: '-100%' }}
            whileHover={{ x: '100%' }}
            transition={{ duration: 0.6 }}
          />
          <div className="stat-value relative z-10">{data.totalUsers.toLocaleString()}</div>
          <div className="stat-label relative z-10">Total Users</div>
        </motion.div>
      </div>

      {/* Expandable Details */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="border-t border-gray-200 mt-4 pt-4 relative z-10"
          >
            <div className="space-y-3">
              {/* Detailed Stats */}
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Performance Details</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-gray-500">Percentile:</span>
                    <span className="ml-2 font-medium">{data.percentile.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Users Below:</span>
                    <span className="ml-2 font-medium">
                      {(data.totalUsers - data.rank).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Change Information */}
              {changeIndicator && (
                <div className="flex items-center space-x-2 text-sm">
                  {getChangeIcon()}
                  <span className="text-gray-600">{getChangeText()}</span>
                </div>
              )}

              {/* Progress Visualization */}
              <div className="progress-container">
                <div className="progress-header">
                  <span>Performance Level</span>
                  <span>{data.percentile.toFixed(1)}%</span>
                </div>
                <div className="progress-bar">
                  <motion.div
                    className={`progress-fill bg-gradient-to-r ${getPercentileColor(data.percentile)}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${data.percentile}%` }}
                    transition={{ duration: 1, delay: 0.2 }}
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-2 pt-2">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleShare();
                  }}
                  className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition-colors text-sm"
                >
                  <Share2 className="h-4 w-4" />
                  <span>Share</span>
                </motion.button>
                
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleExport();
                  }}
                  className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors text-sm"
                >
                  <Download className="h-4 w-4" />
                  <span>Export</span>
                </motion.button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Click Indicator */}
      <motion.div
        className="absolute bottom-2 right-2 text-xs text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity"
        animate={{ opacity: isHovered ? 1 : 0 }}
      >
        Click to {isExpanded ? 'collapse' : 'expand'}
      </motion.div>
    </motion.div>
  );
};

export default InteractiveRankingCard;