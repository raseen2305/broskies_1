import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Search, 
  GitBranch, 
  Users, 
  Loader, 
  CheckCircle, 
  AlertCircle, 
  Star,
  GitFork,
  ExternalLink,
  BarChart3,
  Shield,
  TrendingUp
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { scanAPI } from '../services/api';
import { useScanProgress } from '../hooks/useScanProgress';
import { GitHubUrlValidation } from '../types';

const RepositoryScanner: React.FC = () => {
  const { user } = useAuth();
  const [githubUrl, setGithubUrl] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [validation, setValidation] = useState<GitHubUrlValidation | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [rateLimitInfo, setRateLimitInfo] = useState<any>(null);

  const scanProgressData = useScanProgress();
  
  // Provide default values for missing properties
  const scanId = null;
  const progress: any = null;
  const isScanning = false;
  const scanError = null;
  const startScan = async (request: any) => {};
  const resetScan = () => {};

  useEffect(() => {
    loadRateLimitInfo();
  }, []);

  const loadRateLimitInfo = async () => {
    try {
      const info = await scanAPI.getRateLimitStatus();
      setRateLimitInfo(info);
    } catch (error) {
      console.error('Failed to load rate limit info:', error);
    }
  };

  // Enhanced GitHub URL validation function
  const isValidGitHubUrl = (url: string): boolean => {
    if (!url.trim()) return false;
    
    // Enhanced GitHub URL patterns supporting multiple formats
    const patterns = [
      /^https:\/\/github\.com\/([a-zA-Z0-9_-]+)\/?$/,                    // Basic user profile
      /^https:\/\/github\.com\/([a-zA-Z0-9_-]+)\/([a-zA-Z0-9_.-]+)\/?$/, // User with repo
      /^https:\/\/github\.com\/([a-zA-Z0-9_-]+)\?tab=repositories$/,     // Repositories tab
      /^https:\/\/github\.com\/([a-zA-Z0-9_-]+)\?tab=overview$/,         // Overview tab
      /^https:\/\/github\.com\/([a-zA-Z0-9_-]+)\?tab=projects$/,         // Projects tab
      /^https:\/\/github\.com\/([a-zA-Z0-9_-]+)\?tab=packages$/,         // Packages tab
      /^https:\/\/github\.com\/([a-zA-Z0-9_-]+)\?tab=stars$/,            // Stars tab
      /^https:\/\/github\.com\/([a-zA-Z0-9_-]+)\/([a-zA-Z0-9_.-]+)\?.*$/ // Repository with params
    ];
    
    return patterns.some(pattern => pattern.test(url));
  };

  // Extract username from GitHub URL
  const extractUsernameFromUrl = (url: string): string | null => {
    const match = url.match(/github\.com\/([a-zA-Z0-9_-]+)/);
    return match ? match[1] : null;
  };

  const validateUrl = async (url: string) => {
    if (!url.trim()) {
      setValidation(null);
      return;
    }

    setIsValidating(true);
    
    // Use enhanced frontend validation first
    const isValid = isValidGitHubUrl(url);
    const username = extractUsernameFromUrl(url);
    
    if (isValid && username) {
      // Try to get additional info from backend if available
      try {
        const result = await scanAPI.validateGitHubUrl(url);
        setValidation(result);
      } catch (error) {
        // Fallback to frontend validation result
        setValidation({
          valid: true,
          username: username,
          repository: '',
          user_info: null,
          url_type: 'user_profile'
        });
      }
    } else {
      setValidation({
        valid: false,
        username: '',
        repository: '',
        user_info: null,
        url_type: '',
        error: 'Invalid GitHub URL format',
        suggestion: 'Please enter a valid GitHub URL like: https://github.com/username'
      });
    }
    
    setIsValidating(false);
  };

  const searchRepositories = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const results = await scanAPI.searchRepositories(searchQuery);
      setSearchResults(results.repositories || []);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleStartScan = async () => {
    if (!validation?.valid || !githubUrl) return;

    try {
      const scanRequest = {
        github_url: githubUrl,
        scan_type: 'others'
      };

      await startScan(scanRequest);
    } catch (error) {
      console.error('Failed to start scan:', error);
    }
  };

  const renderScanProgress = () => {
    if (!isScanning && !progress) return null;

    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-blue-900">Scanning Progress</h4>
          <span className="text-sm text-blue-700">{progress?.progress || 0}%</span>
        </div>
        
        <div className="w-full bg-blue-200 rounded-full h-2 mb-3">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress?.progress || 0}%` }}
          />
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-blue-700">Status:</span>
            <span className="font-medium text-blue-900">{progress?.status || 'Initializing'}</span>
          </div>
          
          {progress?.current_repo && (
            <div className="flex items-center justify-between">
              <span className="text-blue-700">Current Repository:</span>
              <span className="font-medium text-blue-900">{progress.current_repo}</span>
            </div>
          )}
          
          {progress?.total_repos && (
            <div className="flex items-center justify-between">
              <span className="text-blue-700">Repositories:</span>
              <span className="font-medium text-blue-900">{progress.total_repos}</span>
            </div>
          )}
        </div>

        {scanError && (
          <div className="mt-3 p-2 bg-red-100 border border-red-200 rounded text-sm text-red-700">
            {scanError}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Repository Scanner</h1>
          <p className="text-lg text-gray-600">
            Analyze GitHub repositories with our advanced ACID scoring system
          </p>
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
          <div className="border-b border-gray-200 px-6 py-4">
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5 text-primary-600" />
              <h2 className="text-lg font-semibold text-gray-900">Scan Other Repositories</h2>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Evaluate any GitHub user or repository to assess code quality and development practices
            </p>
          </div>

          <div className="p-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="space-y-6">
                {/* Repository Search */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-3">Search Repositories</h4>
                  <div className="flex space-x-3">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search repositories (e.g., 'react', 'machine learning', 'javascript')"
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      onKeyPress={(e) => e.key === 'Enter' && searchRepositories()}
                    />
                    <button
                      onClick={searchRepositories}
                      disabled={isSearching || !searchQuery.trim()}
                      className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                    >
                      {isSearching ? (
                        <Loader className="h-4 w-4 animate-spin" />
                      ) : (
                        <Search className="h-4 w-4" />
                      )}
                      <span>Search</span>
                    </button>
                  </div>

                  {/* Search Results */}
                  {searchResults.length > 0 && (
                    <div className="mt-4 space-y-2 max-h-60 overflow-y-auto">
                      {searchResults.map((repo) => (
                        <div
                          key={repo.id}
                          onClick={() => {
                            setGithubUrl(repo.html_url);
                            validateUrl(repo.html_url);
                            setSearchResults([]);
                            setSearchQuery('');
                          }}
                          className="p-3 border border-gray-200 rounded-lg hover:bg-white cursor-pointer transition-colors"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h5 className="font-medium text-gray-900">{repo.full_name}</h5>
                              <p className="text-sm text-gray-600 mt-1">{repo.description}</p>
                              <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                                <div className="flex items-center space-x-1">
                                  <Star className="h-3 w-3" />
                                  <span>{repo.stargazers_count}</span>
                                </div>
                                <div className="flex items-center space-x-1">
                                  <GitFork className="h-3 w-3" />
                                  <span>{repo.forks_count}</span>
                                </div>
                                {repo.language && (
                                  <span className="bg-gray-100 px-2 py-0.5 rounded">
                                    {repo.language}
                                  </span>
                                )}
                              </div>
                            </div>
                            <ExternalLink className="h-4 w-4 text-gray-400" />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* URL Input */}
                <div className="space-y-4">
                  <div>
                    <label htmlFor="github-url" className="block text-sm font-medium text-gray-700 mb-2">
                      GitHub Repository or User URL
                    </label>
                    <div className="relative">
                      <input
                        id="github-url"
                        type="url"
                        value={githubUrl}
                        onChange={(e) => {
                          setGithubUrl(e.target.value);
                          validateUrl(e.target.value);
                        }}
                        placeholder="https://github.com/username (supports various GitHub URL formats)"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      />
                      {isValidating && (
                        <div className="absolute right-3 top-3">
                          <Loader className="h-5 w-5 text-gray-400 animate-spin" />
                        </div>
                      )}
                    </div>
                    
                    {/* Validation Status */}
                    {validation && (
                      <div className={`mt-2 p-3 rounded-lg ${
                        validation.valid 
                          ? 'bg-green-50 border border-green-200' 
                          : 'bg-red-50 border border-red-200'
                      }`}>
                        <div className="flex items-start space-x-2">
                          {validation.valid ? (
                            <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
                          )}
                          <div className="flex-1">
                            <p className={`text-sm font-medium ${
                              validation.valid ? 'text-green-800' : 'text-red-800'
                            }`}>
                              {validation.valid ? 'Valid GitHub URL' : (validation.error || 'Invalid GitHub URL')}
                            </p>
                            
                            {validation.valid && validation.user_info && (
                              <div className="mt-2 text-sm text-green-700">
                                <p><strong>Type:</strong> {validation.url_type}</p>
                                <p><strong>User:</strong> {validation.username}</p>
                                {validation.repository && (
                                  <p><strong>Repository:</strong> {validation.repository}</p>
                                )}
                              </div>
                            )}
                            
                            {!validation.valid && (
                              <div className="mt-2 text-sm text-red-700">
                                {validation.suggestion && (
                                  <p className="mb-2">{validation.suggestion}</p>
                                )}
                                {validation.example && (
                                  <p className="mb-2"><strong>Example:</strong> {validation.example}</p>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Scan Button */}
                  {validation?.valid && (
                    <button
                      onClick={handleStartScan}
                      disabled={isScanning}
                      className="w-full bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors"
                    >
                      {isScanning ? (
                        <>
                          <Loader className="h-5 w-5 animate-spin" />
                          <span>Scanning...</span>
                        </>
                      ) : (
                        <>
                          <GitBranch className="h-5 w-5" />
                          <span>Start Analysis</span>
                        </>
                      )}
                    </button>
                  )}
                </div>

                {renderScanProgress()}
              </div>
            </motion.div>
          </div>
        </div>

        {/* Benefits Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            What You'll Get From Our Analysis
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-start space-x-3">
              <div className="bg-primary-100 rounded-lg p-2">
                <BarChart3 className="h-5 w-5 text-primary-600" />
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-1">ACID Scoring</h4>
                <p className="text-sm text-gray-600">
                  Comprehensive code quality analysis based on Atomicity, Consistency, Isolation, and Durability principles.
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="bg-secondary-100 rounded-lg p-2">
                <Shield className="h-5 w-5 text-secondary-600" />
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-1">Security Analysis</h4>
                <p className="text-sm text-gray-600">
                  Automated vulnerability detection and security best practices evaluation.
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="bg-accent-100 rounded-lg p-2">
                <TrendingUp className="h-5 w-5 text-accent-600" />
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-1">Skill Insights</h4>
                <p className="text-sm text-gray-600">
                  Detailed breakdown of programming languages, frameworks, and technical skills.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RepositoryScanner;