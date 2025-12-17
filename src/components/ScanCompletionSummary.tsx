import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircle, 
  TrendingUp, 
  GitBranch, 
  Star, 
  Code, 
  Users, 
  Calendar,
  Award,
  ArrowRight,
  Download,
  Share2,
  Eye,
  BarChart3
} from 'lucide-react';

interface ScanResults {
  userId: string;
  username: string;
  overallScore: number;
  repositoryCount: number;
  lastScanDate: string;
  languages: Array<{
    language: string;
    percentage: number;
    repositories: number;
    stars: number;
  }>;
  techStack: Array<{
    name: string;
    category: string;
    confidence: number;
    repositories: number;
    experienceLevel: string;
  }>;
  roadmap: Array<{
    title: string;
    description: string;
    priority: string;
    category: string;
    estimatedTime: string;
    skills: string[];
    resources: string[];
  }>;
  githubProfile: {
    username: string;
    name: string;
    bio: string;
    location: string;
    company: string;
    public_repos: number;
    followers: number;
    following: number;
    avatar_url: string;
  };
  scanMetadata: {
    scanDate: string;
    scanDuration: string;
    dataSource: string;
    analysisDepth: string;
    repositoriesAnalyzed: number;
    totalRepositories: number;
  };
}

interface ScanCompletionSummaryProps {
  results: ScanResults;
  onViewDashboard: () => void;
  onDownloadReport?: () => void;
  onShareResults?: () => void;
  autoNavigateDelay?: number; // seconds
  className?: string;
}

export const ScanCompletionSummary: React.FC<ScanCompletionSummaryProps> = ({
  results,
  onViewDashboard,
  onDownloadReport,
  onShareResults,
  autoNavigateDelay = 10,
  className = ''
}) => {
  const [countdown, setCountdown] = useState(autoNavigateDelay);
  const [autoNavigateEnabled, setAutoNavigateEnabled] = useState(true);

  // Auto-navigation countdown
  useEffect(() => {
    if (!autoNavigateEnabled || countdown <= 0) return;

    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          onViewDashboard();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown, autoNavigateEnabled, onViewDashboard]);

  const cancelAutoNavigate = () => {
    setAutoNavigateEnabled(false);
    setCountdown(0);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreGradient = (score: number) => {
    if (score >= 80) return 'from-green-500 to-green-600';
    if (score >= 60) return 'from-yellow-500 to-yellow-600';
    return 'from-red-500 to-red-600';
  };

  const formatDuration = (duration: string) => {
    // Assuming duration is in seconds or a formatted string
    if (typeof duration === 'string' && duration.includes('real_time')) {
      return 'Real-time';
    }
    return duration;
  };

  return (
    <div className={`max-w-4xl mx-auto space-y-6 ${className}`}>
      {/* Success Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-6"
        >
          <CheckCircle className="h-10 w-10 text-green-500" />
        </motion.div>
        
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Scan Complete!
        </h1>
        <p className="text-xl text-gray-600 mb-2">
          Successfully analyzed {results.repositoryCount} repositories for {results.githubProfile.name || results.username}
        </p>
        <p className="text-sm text-gray-500">
          Scan completed on {new Date(results.lastScanDate).toLocaleDateString()} using {results.scanMetadata.analysisDepth} analysis
        </p>
      </motion.div>

      {/* Key Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white rounded-2xl shadow-lg p-8"
      >
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Key Metrics</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Overall Score */}
          <div className="text-center">
            <div className={`text-4xl font-bold mb-2 ${getScoreColor(results.overallScore)}`}>
              {Math.round(results.overallScore)}
            </div>
            <div className="text-sm text-gray-600 mb-3">Overall Score</div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <motion.div
                className={`h-2 rounded-full bg-gradient-to-r ${getScoreGradient(results.overallScore)}`}
                initial={{ width: 0 }}
                animate={{ width: `${results.overallScore}%` }}
                transition={{ delay: 0.5, duration: 1 }}
              />
            </div>
          </div>

          {/* Repositories */}
          <div className="text-center">
            <div className="text-4xl font-bold text-blue-600 mb-2">
              {results.repositoryCount}
            </div>
            <div className="text-sm text-gray-600 mb-3">Repositories</div>
            <div className="flex items-center justify-center text-xs text-gray-500">
              <GitBranch className="h-3 w-3 mr-1" />
              {results.scanMetadata.repositoriesAnalyzed} analyzed
            </div>
          </div>

          {/* Languages */}
          <div className="text-center">
            <div className="text-4xl font-bold text-purple-600 mb-2">
              {results.languages.length}
            </div>
            <div className="text-sm text-gray-600 mb-3">Languages</div>
            <div className="flex items-center justify-center text-xs text-gray-500">
              <Code className="h-3 w-3 mr-1" />
              {results.languages[0]?.language || 'N/A'} primary
            </div>
          </div>

          {/* Tech Stack */}
          <div className="text-center">
            <div className="text-4xl font-bold text-orange-600 mb-2">
              {results.techStack.length}
            </div>
            <div className="text-sm text-gray-600 mb-3">Technologies</div>
            <div className="flex items-center justify-center text-xs text-gray-500">
              <Award className="h-3 w-3 mr-1" />
              Stack identified
            </div>
          </div>
        </div>
      </motion.div>

      {/* Top Languages */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white rounded-2xl shadow-lg p-8"
      >
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Top Programming Languages</h3>
        <div className="space-y-4">
          {results.languages.slice(0, 5).map((lang, index) => (
            <motion.div
              key={lang.language}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 + index * 0.1 }}
              className="flex items-center justify-between"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
                  {index + 1}
                </div>
                <div>
                  <div className="font-medium text-gray-900">{lang.language}</div>
                  <div className="text-sm text-gray-500">{lang.repositories} repositories</div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <div className="font-semibold text-gray-900">{lang.percentage.toFixed(1)}%</div>
                  <div className="text-sm text-gray-500 flex items-center">
                    <Star className="h-3 w-3 mr-1" />
                    {lang.stars}
                  </div>
                </div>
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <motion.div
                    className="h-2 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${lang.percentage}%` }}
                    transition={{ delay: 0.7 + index * 0.1, duration: 0.8 }}
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Scan Metadata */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="bg-gray-50 rounded-2xl p-6"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Scan Details</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-gray-600">Duration</div>
            <div className="font-medium text-gray-900">{formatDuration(results.scanMetadata.scanDuration)}</div>
          </div>
          <div>
            <div className="text-gray-600">Data Source</div>
            <div className="font-medium text-gray-900 capitalize">{results.scanMetadata.dataSource.replace('_', ' ')}</div>
          </div>
          <div>
            <div className="text-gray-600">Analysis Type</div>
            <div className="font-medium text-gray-900 capitalize">{results.scanMetadata.analysisDepth}</div>
          </div>
          <div>
            <div className="text-gray-600">Completion</div>
            <div className="font-medium text-gray-900">{new Date(results.scanMetadata.scanDate).toLocaleTimeString()}</div>
          </div>
        </div>
      </motion.div>

      {/* Action Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-white rounded-2xl shadow-lg p-8"
      >
        <div className="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0 sm:space-x-4">
          {/* Auto-navigation notice */}
          {autoNavigateEnabled && countdown > 0 && (
            <div className="flex items-center space-x-3 text-sm text-gray-600">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                <span>Auto-redirecting to dashboard in {countdown}s</span>
              </div>
              <button
                onClick={cancelAutoNavigate}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Cancel
              </button>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex space-x-3">
            {onDownloadReport && (
              <button
                onClick={onDownloadReport}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <Download className="h-4 w-4 mr-2" />
                Download Report
              </button>
            )}
            
            {onShareResults && (
              <button
                onClick={onShareResults}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <Share2 className="h-4 w-4 mr-2" />
                Share Results
              </button>
            )}
            
            <button
              onClick={onViewDashboard}
              className="inline-flex items-center px-6 py-2 text-sm font-medium text-white bg-gradient-to-r from-primary-600 to-secondary-600 rounded-lg hover:from-primary-700 hover:to-secondary-700 transition-all duration-200 shadow-lg"
            >
              <Eye className="h-4 w-4 mr-2" />
              View Dashboard
              <ArrowRight className="h-4 w-4 ml-2" />
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};