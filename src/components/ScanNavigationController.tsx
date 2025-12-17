import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Home, BarChart3, Settings, RefreshCw } from 'lucide-react';

interface ScanNavigationControllerProps {
  scanResults: any;
  onReturnToScanner?: () => void;
  onGoToSettings?: () => void;
  cacheResults?: boolean;
  className?: string;
}

interface CachedScanResult {
  id: string;
  results: any;
  timestamp: Date;
  expiresAt: Date;
}

export const ScanNavigationController: React.FC<ScanNavigationControllerProps> = ({
  scanResults,
  onReturnToScanner,
  onGoToSettings,
  cacheResults = true,
  className = ''
}) => {
  const navigate = useNavigate();
  const [isCaching, setIsCaching] = useState(false);
  const [cachedScans, setCachedScans] = useState<CachedScanResult[]>([]);

  // Cache management
  useEffect(() => {
    if (cacheResults && scanResults) {
      cacheScanResults(scanResults);
    }
    loadCachedScans();
  }, [scanResults, cacheResults]);

  const cacheScanResults = async (results: any) => {
    setIsCaching(true);
    try {
      const cacheKey = `scan_results_${results.userId}_${Date.now()}`;
      const cacheData: CachedScanResult = {
        id: cacheKey,
        results,
        timestamp: new Date(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000) // 24 hours
      };

      // Store in localStorage
      const existingCache = JSON.parse(localStorage.getItem('cached_scan_results') || '[]');
      const updatedCache = [...existingCache, cacheData].slice(-10); // Keep last 10 scans
      localStorage.setItem('cached_scan_results', JSON.stringify(updatedCache));
      
      setCachedScans(updatedCache);
      
      // Also store the latest result for immediate dashboard access
      localStorage.setItem('latest_scan_result', JSON.stringify(results));
      
    } catch (error) {
      console.error('Failed to cache scan results:', error);
    } finally {
      setIsCaching(false);
    }
  };

  const loadCachedScans = () => {
    try {
      const cached = JSON.parse(localStorage.getItem('cached_scan_results') || '[]');
      const validCache = cached.filter((item: CachedScanResult) => 
        new Date(item.expiresAt) > new Date()
      );
      setCachedScans(validCache);
      
      // Clean up expired cache
      if (validCache.length !== cached.length) {
        localStorage.setItem('cached_scan_results', JSON.stringify(validCache));
      }
    } catch (error) {
      console.error('Failed to load cached scans:', error);
    }
  };

  const clearCache = () => {
    localStorage.removeItem('cached_scan_results');
    localStorage.removeItem('latest_scan_result');
    setCachedScans([]);
  };

  const navigateToDashboard = () => {
    navigate('/developer/dashboard', {
      state: { scanResults },
      replace: true
    });
  };

  const navigateToHome = () => {
    navigate('/developer/auth', { replace: true });
  };

  const navigateToComparison = () => {
    navigate('/developer/comparison', {
      state: { 
        currentResults: scanResults,
        cachedResults: cachedScans 
      }
    });
  };

  const loadPreviousScan = (cachedScan: CachedScanResult) => {
    navigate('/developer/dashboard', {
      state: { scanResults: cachedScan.results },
      replace: true
    });
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Primary Navigation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl shadow-lg p-6"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">What's Next?</h3>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* View Dashboard */}
          <motion.button
            onClick={navigateToDashboard}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex items-center space-x-3 p-4 bg-gradient-to-r from-primary-50 to-secondary-50 border border-primary-200 rounded-lg hover:from-primary-100 hover:to-secondary-100 transition-all duration-200"
          >
            <div className="w-10 h-10 bg-primary-500 rounded-full flex items-center justify-center">
              <BarChart3 className="h-5 w-5 text-white" />
            </div>
            <div className="text-left">
              <div className="font-medium text-gray-900">View Dashboard</div>
              <div className="text-sm text-gray-600">Explore detailed analysis</div>
            </div>
          </motion.button>

          {/* New Scan */}
          {onReturnToScanner && (
            <motion.button
              onClick={onReturnToScanner}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex items-center space-x-3 p-4 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-all duration-200"
            >
              <div className="w-10 h-10 bg-gray-500 rounded-full flex items-center justify-center">
                <RefreshCw className="h-5 w-5 text-white" />
              </div>
              <div className="text-left">
                <div className="font-medium text-gray-900">New Scan</div>
                <div className="text-sm text-gray-600">Scan another profile</div>
              </div>
            </motion.button>
          )}

          {/* Home */}
          <motion.button
            onClick={navigateToHome}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex items-center space-x-3 p-4 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-all duration-200"
          >
            <div className="w-10 h-10 bg-gray-500 rounded-full flex items-center justify-center">
              <Home className="h-5 w-5 text-white" />
            </div>
            <div className="text-left">
              <div className="font-medium text-gray-900">Home</div>
              <div className="text-sm text-gray-600">Return to main page</div>
            </div>
          </motion.button>
        </div>
      </motion.div>

      {/* Cache Status */}
      {cacheResults && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-md font-semibold text-gray-900">Scan Cache</h4>
            <div className="flex items-center space-x-2">
              {isCaching && (
                <div className="flex items-center space-x-2 text-sm text-blue-600">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                  <span>Caching results...</span>
                </div>
              )}
              {cachedScans.length > 0 && (
                <button
                  onClick={clearCache}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Clear Cache
                </button>
              )}
            </div>
          </div>

          {cachedScans.length > 0 ? (
            <div className="space-y-2">
              <p className="text-sm text-gray-600 mb-3">
                {cachedScans.length} recent scan{cachedScans.length !== 1 ? 's' : ''} cached for quick access
              </p>
              
              {/* Recent Scans */}
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {cachedScans.slice(-3).reverse().map((cached, index) => (
                  <motion.div
                    key={cached.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">
                        {cached.results.githubProfile?.name || cached.results.username}
                      </div>
                      <div className="text-xs text-gray-500">
                        {cached.timestamp.toLocaleString()} • Score: {Math.round(cached.results.overallScore)}
                      </div>
                    </div>
                    <button
                      onClick={() => loadPreviousScan(cached)}
                      className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                    >
                      Load
                    </button>
                  </motion.div>
                ))}
              </div>

              {/* Compare Option */}
              {cachedScans.length > 1 && (
                <button
                  onClick={navigateToComparison}
                  className="w-full mt-3 py-2 text-sm font-medium text-primary-600 border border-primary-200 rounded-lg hover:bg-primary-50 transition-colors"
                >
                  Compare with Previous Scans
                </button>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              Results will be cached for quick dashboard access
            </p>
          )}
        </motion.div>
      )}

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="flex flex-wrap gap-3"
      >
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Go Back
        </button>
        
        {onGoToSettings && (
          <button
            onClick={onGoToSettings}
            className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors"
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </button>
        )}
      </motion.div>
    </div>
  );
};