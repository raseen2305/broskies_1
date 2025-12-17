import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Loader2, CheckCircle, RefreshCw, AlertCircle } from 'lucide-react';
import { scanAPI } from '../services/api';

interface AnalysisProgress {
  total_repos: number;
  scored: number;
  categorized: number;
  evaluated: number;
  to_evaluate: number;
  percentage: number;
  current_message?: string;
}

interface AnalysisStatus {
  analysis_id: string;
  status: 'started' | 'scoring' | 'categorizing' | 'evaluating' | 'calculating' | 'complete' | 'failed';
  current_phase: string;
  progress: AnalysisProgress;
  message?: string;
  error?: string;
}

interface AnalyzeButtonProps {
  username: string;
  analyzed: boolean;
  analyzedAt?: string;
  onAnalysisComplete?: () => void;
  className?: string;
}

const AnalyzeButton: React.FC<AnalyzeButtonProps> = ({
  username,
  analyzed,
  analyzedAt,
  onAnalysisComplete,
  className = ''
}) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showReanalyzeConfirm, setShowReanalyzeConfirm] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [isRateLimited, setIsRateLimited] = useState(false);

  // Poll for analysis status
  useEffect(() => {
    if (!isAnalyzing || !analysisStatus?.analysis_id) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await scanAPI.getAnalysisStatus(username, analysisStatus.analysis_id);
        setAnalysisStatus(status as AnalysisStatus);

        // Check if analysis is complete or failed
        if (status.status === 'complete') {
          setIsAnalyzing(false);
          clearInterval(pollInterval);
          
          // Check for partial success
          if (status.progress && status.progress.evaluated < status.progress.to_evaluate) {
            const failedCount = status.progress.to_evaluate - status.progress.evaluated;
            console.warn(`Partial success: ${failedCount} repositories failed evaluation`);
          }
          
          // Fetch the updated analysis results
          try {
            console.log('✅ Analysis complete, fetching updated results...');
            const results = await scanAPI.getAnalysisResults(username, analysisStatus.analysis_id);
            console.log('📊 Updated analysis results:', results);
            console.log('📊 Repositories with categories:', results.repositories?.filter((r: any) => r.category).length);
            
            // Update localStorage with new results
            const storedResults = localStorage.getItem('dashboard_scan_results');
            if (storedResults) {
              const parsedResults = JSON.parse(storedResults);
              
              // Recalculate languages from updated repositories
              const languageMap: Record<string, number> = {};
              results.repositories?.forEach((repo: any) => {
                if (repo.language) {
                  languageMap[repo.language] = (languageMap[repo.language] || 0) + (repo.size || 0);
                }
              });
              
              const totalBytes = Object.values(languageMap).reduce((sum: number, bytes: number) => sum + bytes, 0);
              const languagesArray = Object.entries(languageMap)
                .map(([language, bytes]) => ({
                  language,
                  percentage: totalBytes > 0 ? (bytes / totalBytes) * 100 : 0,
                  repositories: results.repositories?.filter((r: any) => r.language === language).length || 0,
                  stars: results.repositories?.filter((r: any) => r.language === language)
                    .reduce((sum: number, r: any) => sum + (r.stargazers_count || 0), 0) || 0
                }))
                .sort((a, b) => b.percentage - a.percentage);
              
              // Update the repositories with analysis data
              parsedResults.repositories = results.repositories;
              parsedResults.analyzed = true;
              parsedResults.analyzedAt = results.analyzedAt || new Date().toISOString();
              parsedResults.overallScore = results.overallScore;
              parsedResults.categoryDistribution = results.categoryDistribution;
              parsedResults.evaluatedCount = results.evaluatedCount;
              parsedResults.flagshipCount = results.flagshipCount;
              parsedResults.significantCount = results.significantCount;
              parsedResults.supportingCount = results.supportingCount;
              parsedResults.languages = languagesArray;  // Update languages
              parsedResults.primaryLanguage = languagesArray[0]?.language || 'Unknown';
              
              localStorage.setItem('dashboard_scan_results', JSON.stringify(parsedResults));
              localStorage.setItem('dashboard_scan_timestamp', Date.now().toString());
              console.log('💾 Updated scan results saved to localStorage');
              console.log('💾 Saved repos with categories:', parsedResults.repositories?.filter((r: any) => r.category).length);
              console.log('💾 Updated languages:', languagesArray.map(l => l.language).join(', '));
              
              // Force a small delay to ensure localStorage write completes
              await new Promise(resolve => setTimeout(resolve, 100));
            }
          } catch (err) {
            console.error('Failed to fetch updated results:', err);
          }
          
          if (onAnalysisComplete) {
            onAnalysisComplete();
          }
        } else if (status.status === 'failed') {
          setIsAnalyzing(false);
          
          // Enhanced error message for failures
          let errorMsg = status.error || 'Analysis failed';
          if (status.error?.includes('rate limit')) {
            setIsRateLimited(true);
            errorMsg = 'GitHub API rate limit exceeded. Please try again later.';
          }
          
          setError(errorMsg);
          clearInterval(pollInterval);
        }
      } catch (err: any) {
        console.error('Error polling analysis status:', err);
        
        // Handle polling errors gracefully
        let errorMsg = 'Failed to check analysis status';
        if (err.response?.status === 429) {
          setIsRateLimited(true);
          errorMsg = 'Rate limit exceeded while checking status. Analysis may still be running.';
        } else if (err.message) {
          errorMsg = err.message;
        }
        
        setError(errorMsg);
        setIsAnalyzing(false);
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [isAnalyzing, analysisStatus?.analysis_id, username, onAnalysisComplete]);

  const initiateAnalysis = async () => {
    setIsAnalyzing(true);
    setError(null);
    setAnalysisStatus(null);
    setIsRateLimited(false);

    try {
      const data = await scanAPI.initiateAnalysis(username, 15);
      setRetryCount(0); // Reset retry count on success
      
      setAnalysisStatus({
        analysis_id: data.analysis_id,
        status: 'started',
        current_phase: 'started',
        progress: {
          total_repos: data.repositories_count || 0,
          scored: 0,
          categorized: 0,
          evaluated: 0,
          to_evaluate: data.max_evaluate || 15,
          percentage: 0,
          current_message: data.message
        },
        message: data.message
      });
    } catch (err: any) {
      console.error('Error initiating analysis:', err);
      
      // Enhanced error handling
      let errorMessage = 'Failed to start analysis';
      let rateLimited = false;
      
      if (err.response?.status === 429) {
        rateLimited = true;
        const retryAfter = err.response?.headers?.['retry-after'] || 60;
        errorMessage = `GitHub API rate limit exceeded. Please try again in ${retryAfter} seconds.`;
      } else if (err.response?.status === 404) {
        errorMessage = `User '${username}' not found. Please check the username and try again.`;
      } else if (err.response?.status === 403) {
        errorMessage = 'Access denied. This profile may be private or restricted.';
      } else if (err.response?.status >= 500) {
        errorMessage = 'Server error occurred. Please try again in a few moments.';
      } else if (err.message?.includes('Network')) {
        errorMessage = 'Network error. Please check your connection and try again.';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      setIsRateLimited(rateLimited);
      setIsAnalyzing(false);
      setRetryCount(prev => prev + 1);
    }
  };

  const handleAnalyzeClick = () => {
    if (analyzed && !showReanalyzeConfirm) {
      setShowReanalyzeConfirm(true);
    } else {
      initiateAnalysis();
      setShowReanalyzeConfirm(false);
    }
  };

  const handleCancelReanalyze = () => {
    setShowReanalyzeConfirm(false);
  };

  const getPhaseMessage = () => {
    if (!analysisStatus) return '';
    
    const { status, progress } = analysisStatus;
    
    switch (status) {
      case 'started':
        return 'Starting analysis...';
      case 'scoring':
        return 'Calculating importance scores...';
      case 'categorizing':
        return 'Categorizing repositories...';
      case 'evaluating':
        return `Evaluating ${progress.evaluated} of ${progress.to_evaluate} repositories...`;
      case 'calculating':
        return 'Calculating overall score...';
      case 'complete':
        return 'Analysis complete!';
      case 'failed':
        return 'Analysis failed';
      default:
        return progress.current_message || 'Processing...';
    }
  };

  const formatAnalyzedTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else if (diffHours > 0) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else {
      return 'just now';
    }
  };

  // Ready state (not analyzed)
  if (!analyzed && !isAnalyzing) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`card p-6 bg-gradient-to-r from-primary-50 to-blue-50 border-2 border-primary-200 ${className}`}
      >
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <Search className="h-6 w-6 text-primary-600" />
              <h3 className="text-xl font-semibold text-gray-900">
                Analyze Repositories
              </h3>
            </div>
            <p className="text-gray-600 text-sm">
              Categorize and evaluate your projects to get detailed insights and an overall developer score
            </p>
          </div>
          <button
            onClick={handleAnalyzeClick}
            className="ml-6 px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors shadow-md hover:shadow-lg flex items-center space-x-2"
          >
            <Search className="h-5 w-5" />
            <span>Start Analysis</span>
          </button>
        </div>
      </motion.div>
    );
  }

  // Loading state (analyzing)
  if (isAnalyzing) {
    // Show loading even if analysisStatus is not yet available
    if (!analysisStatus) {
      return (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className={`card p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 ${className}`}
        >
          <div className="flex items-center space-x-3">
            <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
            <h3 className="text-xl font-semibold text-gray-900">
              Initiating Analysis...
            </h3>
          </div>
        </motion.div>
      );
    }
    
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className={`card p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 ${className}`}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
              <h3 className="text-xl font-semibold text-gray-900">
                Analyzing Repositories...
              </h3>
            </div>
            <div className="text-2xl font-bold text-blue-600">
              {analysisStatus.progress.percentage}%
            </div>
          </div>

          {/* Progress Bar */}
          <div className="relative">
            <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${analysisStatus.progress.percentage}%` }}
                transition={{ duration: 0.5 }}
                className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full"
              />
            </div>
          </div>

          {/* Status Message */}
          <div className="flex items-center justify-between text-sm">
            <p className="text-gray-700 font-medium">{getPhaseMessage()}</p>
            {analysisStatus.status === 'evaluating' && (
              <p className="text-gray-500">
                {analysisStatus.progress.evaluated} / {analysisStatus.progress.to_evaluate} evaluated
              </p>
            )}
          </div>

          {/* Phase Indicators */}
          <div className="flex items-center space-x-2 text-xs">
            <div className={`px-2 py-1 rounded ${
              ['scoring', 'categorizing', 'evaluating', 'calculating', 'complete'].includes(analysisStatus.status)
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-500'
            }`}>
              ✓ Scoring
            </div>
            <div className={`px-2 py-1 rounded ${
              ['categorizing', 'evaluating', 'calculating', 'complete'].includes(analysisStatus.status)
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-500'
            }`}>
              ✓ Categorizing
            </div>
            <div className={`px-2 py-1 rounded ${
              ['evaluating', 'calculating', 'complete'].includes(analysisStatus.status)
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-500'
            }`}>
              {analysisStatus.status === 'evaluating' ? '⏳' : '✓'} Evaluating
            </div>
            <div className={`px-2 py-1 rounded ${
              ['calculating', 'complete'].includes(analysisStatus.status)
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-500'
            }`}>
              {analysisStatus.status === 'complete' ? '✓' : '○'} Complete
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  // Complete state (analyzed)
  if (analyzed && !isAnalyzing) {
    return (
      <AnimatePresence mode="wait">
        {showReanalyzeConfirm ? (
          <motion.div
            key="confirm"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className={`card p-6 bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-200 ${className}`}
          >
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <AlertCircle className="h-6 w-6 text-yellow-600" />
                <h3 className="text-xl font-semibold text-gray-900">
                  Re-analyze Repositories?
                </h3>
              </div>
              <p className="text-gray-600 text-sm">
                This will replace your previous analysis results with new data. The process may take 45-60 seconds.
              </p>
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleAnalyzeClick}
                  className="px-4 py-2 bg-yellow-600 text-white font-medium rounded-lg hover:bg-yellow-700 transition-colors"
                >
                  Confirm Re-analyze
                </button>
                <button
                  onClick={handleCancelReanalyze}
                  className="px-4 py-2 bg-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="complete"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`card p-6 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 ${className}`}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-6 w-6 text-green-600" />
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">
                      Analysis Complete
                    </h3>
                    {analyzedAt && (
                      <p className="text-sm text-gray-600">
                        Analyzed {formatAnalyzedTime(analyzedAt)}
                      </p>
                    )}
                  </div>
                </div>
                <button
                  onClick={handleAnalyzeClick}
                  className="px-4 py-2 bg-white text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors border border-gray-300 flex items-center space-x-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span>Re-analyze</span>
                </button>
              </div>
              
              {/* Partial success warning */}
              {analysisStatus?.progress && 
               analysisStatus.progress.evaluated < analysisStatus.progress.to_evaluate && (
                <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <div className="flex items-start space-x-2">
                    <AlertCircle className="h-4 w-4 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-yellow-800">
                      <strong>Partial Success:</strong> {analysisStatus.progress.evaluated} of {analysisStatus.progress.to_evaluate} repositories 
                      were evaluated successfully. {analysisStatus.progress.to_evaluate - analysisStatus.progress.evaluated} failed due to 
                      access restrictions or API limits.
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    );
  }

  // Error state
  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className={`card p-6 bg-gradient-to-r ${
          isRateLimited 
            ? 'from-yellow-50 to-orange-50 border-2 border-yellow-200'
            : 'from-red-50 to-pink-50 border-2 border-red-200'
        } ${className}`}
      >
        <div className="space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3 flex-1">
              <AlertCircle className={`h-6 w-6 flex-shrink-0 ${isRateLimited ? 'text-yellow-600' : 'text-red-600'}`} />
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 mb-1">
                  {isRateLimited ? 'Rate Limit Exceeded' : 'Analysis Failed'}
                </h3>
                <p className={`text-sm ${isRateLimited ? 'text-yellow-700' : 'text-red-600'} mb-2`}>
                  {error}
                </p>
                
                {/* Retry count indicator */}
                {retryCount > 0 && (
                  <p className="text-xs text-gray-500">
                    Retry attempt: {retryCount}
                  </p>
                )}
                
                {/* Rate limit specific guidance */}
                {isRateLimited && (
                  <div className="mt-3 p-3 bg-yellow-100 rounded-lg border border-yellow-300">
                    <p className="text-sm text-yellow-800">
                      <strong>What happened?</strong> GitHub has rate limits to prevent abuse. 
                      This usually resets within an hour.
                    </p>
                    <p className="text-sm text-yellow-800 mt-2">
                      <strong>What to do:</strong> Wait a few minutes and try again, or try analyzing a different profile.
                    </p>
                  </div>
                )}
                
                {/* General error guidance */}
                {!isRateLimited && retryCount >= 2 && (
                  <div className="mt-3 p-3 bg-red-100 rounded-lg border border-red-300">
                    <p className="text-sm text-red-800">
                      <strong>Multiple failures detected.</strong> This might be a temporary issue. 
                      Try again later or contact support if the problem persists.
                    </p>
                  </div>
                )}
              </div>
            </div>
            
            <button
              onClick={() => {
                setError(null);
                initiateAnalysis();
              }}
              disabled={isRateLimited && retryCount >= 3}
              className={`px-4 py-2 font-medium rounded-lg transition-colors flex items-center space-x-2 flex-shrink-0 ml-4 ${
                isRateLimited && retryCount >= 3
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : isRateLimited
                  ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                  : 'bg-red-600 text-white hover:bg-red-700'
              }`}
            >
              <RefreshCw className="h-4 w-4" />
              <span>{isRateLimited && retryCount >= 3 ? 'Wait...' : 'Retry'}</span>
            </button>
          </div>
        </div>
      </motion.div>
    );
  }

  return null;
};

export default AnalyzeButton;
