import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { GitBranch, Github, User, ExternalLink, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const DeveloperAuth: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, user } = useAuth();
  const callbackProcessed = useRef(false);
  
  // State for "Scan Others" functionality
  const [githubUrl, setGithubUrl] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [urlValidation, setUrlValidation] = useState<{
    isValid: boolean;
    username?: string;
    repository?: string;
    errorMessage?: string;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isProcessingOAuth, setIsProcessingOAuth] = useState(false);

  useEffect(() => {
    // Handle OAuth callback
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const sessionId = searchParams.get('session');
    
    if (code && !callbackProcessed.current) {
      callbackProcessed.current = true;
      setIsProcessingOAuth(true);
      handleOAuthCallback(code, state);
    } else if (sessionId && !callbackProcessed.current) {
      callbackProcessed.current = true;
      setIsProcessingOAuth(true);
      handleSessionCallback(sessionId);
    }
  }, [searchParams]);

  const handleOAuthCallback = async (code: string, state: string | null) => {
    try {
      setError('');
      
      const response = await authAPI.githubCallback({ code, state });
      login(response.user, response.access_token);
      
      // Auto-initiate scanning after successful OAuth
      console.log('✅ GitHub OAuth successful, auto-starting scan for:', response.user.githubUsername);
      
      // Navigate directly to scanning progress with self-scan parameters
      navigate('/scanning-progress', {
        state: {
          scanType: 'self',
          username: response.user.githubUsername
        }
      });
      
    } catch (error: any) {
      console.error('OAuth callback failed:', error);
      setError(error.response?.data?.detail || 'GitHub authentication failed. Please try again.');
      setIsProcessingOAuth(false);
    }
  };

  const handleSessionCallback = async (sessionId: string) => {
    try {
      setError('');
      
      const response = await authAPI.getSession(sessionId);
      login(response.user, response.access_token, response.refresh_token);
      
      // Auto-initiate scanning after successful session callback
      console.log('✅ GitHub session restored, auto-starting scan for:', response.user.githubUsername);
      
      // Navigate directly to scanning progress with self-scan parameters
      navigate('/scanning-progress', {
        state: {
          scanType: 'self',
          username: response.user.githubUsername
        }
      });
      
    } catch (error: any) {
      console.error('Session callback failed:', error);
      setError(error.response?.data?.detail || 'Failed to restore GitHub session. Please try connecting again.');
      setIsProcessingOAuth(false);
    }
  };

  const handleGitHubLogin = async () => {
    try {
      const response = await authAPI.getGitHubAuthUrl();
      window.location.href = response.authorization_url;
    } catch (error) {
      console.error('GitHub login failed:', error);
      // Handle error - show message to user
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

  // Extract username from GitHub URL or plain username
  const extractUsernameFromUrl = (url: string): string | null => {
    // If it's already just a username (no URL), return it
    if (/^[a-zA-Z0-9_-]+$/.test(url.trim())) {
      return url.trim();
    }
    // Otherwise extract from full GitHub URL
    const match = url.match(/github\.com\/([a-zA-Z0-9_-]+)/);
    return match ? match[1] : null;
  };

  // Validate GitHub URL or username
  const validateGitHubUrl = (url: string) => {
    if (!url.trim()) {
      setUrlValidation(null);
      return;
    }

    setIsValidating(true);
    
    // Simulate validation delay for better UX
    setTimeout(() => {
      const username = extractUsernameFromUrl(url);
      
      // Accept either full URL or just username
      if (username) {
        setUrlValidation({
          isValid: true,
          username: username,
          errorMessage: undefined
        });
      } else {
        setUrlValidation({
          isValid: false,
          errorMessage: 'Please enter a GitHub username or profile URL'
        });
      }
      
      setIsValidating(false);
    }, 500);
  };

  // Handle "Scan Myself" functionality
  const handleScanMyself = async () => {
    if (!user?.githubUsername) {
      setError('GitHub username not found. Please reconnect your GitHub account.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Navigate to scanning progress page
      navigate('/scanning-progress', {
        state: {
          scanType: 'self',
          username: user.githubUsername
        }
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start scan');
      setIsLoading(false);
    }
  };

  // Handle "Scan Others" functionality
  const handleScanOther = async () => {
    if (!githubUrl.trim()) {
      setError('Please enter a GitHub username or URL');
      return;
    }

    if (!urlValidation?.isValid) {
      setError('Please enter a valid GitHub username or profile URL');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const username = extractUsernameFromUrl(githubUrl);
      if (!username) {
        setError('Could not extract username');
        setIsLoading(false);
        return;
      }
      
      // Construct full GitHub URL if user only provided username
      const fullUrl = githubUrl.includes('github.com') 
        ? githubUrl 
        : `https://github.com/${username}`;
      
      // Navigate to scanning progress page
      navigate('/scanning-progress', {
        state: {
          scanType: 'other',
          githubUrl: fullUrl,
          username: username
        }
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start scan');
      setIsLoading(false);
    }
  };

  // Show OAuth processing screen
  if (isProcessingOAuth) {
    return (
      <div className="min-h-screen gradient-bg flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md mx-4 text-center"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full mb-6">
            <Github className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Connecting GitHub Account</h2>
          <p className="text-gray-600 mb-6">
            Processing your GitHub authorization and preparing to scan your repositories...
          </p>
          <div className="flex items-center justify-center space-x-2 text-primary-600">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="font-medium">Setting up your profile...</span>
          </div>
          {error && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-red-500" />
                <p className="text-red-700 text-sm">{error}</p>
              </div>
              <button
                onClick={() => {
                  setIsProcessingOAuth(false);
                  setError('');
                  // Clear URL parameters
                  navigate('/developer/auth', { replace: true });
                }}
                className="mt-3 w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
              >
                Try Again
              </button>
            </div>
          )}
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen gradient-bg">
      {/* Top Navigation with GitHub Login */}
      <div className="flex justify-between items-center p-6">
        <div className="flex items-center space-x-2">
          <GitBranch className="h-8 w-8 text-white" />
          <span className="text-xl font-bold text-white">BroskiesHub</span>
        </div>
        <button
          onClick={handleGitHubLogin}
          className="bg-gray-900 hover:bg-gray-800 text-white font-medium py-2 px-4 rounded-lg flex items-center space-x-2 transition-colors duration-200"
        >
          <Github className="h-4 w-4" />
          <span>Continue with GitHub</span>
        </button>
      </div>

      {/* Center Content - Scanning Options */}
      <div className="flex items-center justify-center min-h-[calc(100vh-120px)]">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-4xl mx-4"
        >
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Repository Scanner
            </h1>
            <p className="text-gray-600 text-lg">
              Analyze GitHub repositories with our advanced ACID scoring system
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg"
            >
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-red-500" />
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            </motion.div>
          )}

          {/* Scanning Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Scan Repositories */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="border-2 border-primary-200 rounded-xl p-6 hover:border-primary-400 transition-colors"
            >
              <div className="flex items-center mb-4">
                <div className="bg-primary-100 rounded-lg p-3 mr-4">
                  <User className="h-6 w-6 text-primary-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900">Scan Repositories</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Analyze your own GitHub repositories to get comprehensive insights into your coding skills and repository quality.
              </p>
              <div className="bg-gray-50 rounded-lg p-3 mb-4">
                <p className="text-sm text-gray-700">
                  <strong>What you'll get:</strong> Personal coding analytics, skill assessment, and improvement recommendations
                </p>
              </div>
              
              {user?.githubUsername ? (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <Github className="h-4 w-4" />
                    <span>Connected as: <strong>{user.githubUsername}</strong></span>
                  </div>
                  <button
                    onClick={handleScanMyself}
                    disabled={isLoading}
                    className="w-full bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>Starting Scan...</span>
                      </>
                    ) : (
                      <>
                        <GitBranch className="h-4 w-4" />
                        <span>Scan My Profile</span>
                      </>
                    )}
                  </button>
                </div>
              ) : (
                <div className="text-center">
                  <p className="text-sm text-gray-500 mb-3">Connect your GitHub account to scan your repositories</p>
                  <button
                    onClick={handleGitHubLogin}
                    className="w-full bg-gray-900 hover:bg-gray-800 text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors"
                  >
                    <Github className="h-4 w-4" />
                    <span>Connect GitHub</span>
                  </button>
                </div>
              )}
            </motion.div>

            {/* Scan Other Repositories */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="border-2 border-secondary-200 rounded-xl p-6 hover:border-secondary-400 transition-colors"
            >
              <div className="flex items-center mb-4">
                <div className="bg-secondary-100 rounded-lg p-3 mr-4">
                  <ExternalLink className="h-6 w-6 text-secondary-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900">Scan Other Repositories</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Evaluate any GitHub user or repository to assess code quality, security, and development practices.
              </p>
              <div className="bg-gray-50 rounded-lg p-3 mb-4">
                <p className="text-sm text-gray-700">
                  <strong>What you'll get:</strong> ACID scoring, security analysis, and detailed code quality metrics
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label htmlFor="github-url" className="block text-sm font-medium text-gray-700 mb-2">
                    GitHub Profile URL
                  </label>
                  <div className="relative">
                    <input
                      id="github-url"
                      type="url"
                      value={githubUrl}
                      onChange={(e) => {
                        setGithubUrl(e.target.value);
                        validateGitHubUrl(e.target.value);
                        setError('');
                      }}
                      placeholder="Enter GitHub username or URL (e.g., octocat)"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary-500 focus:border-transparent"
                    />
                    {isValidating && (
                      <div className="absolute right-3 top-2.5">
                        <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />
                      </div>
                    )}
                  </div>
                  
                  {/* URL Validation Status */}
                  {urlValidation && (
                    <div className={`mt-2 p-2 rounded-lg text-sm ${
                      urlValidation.isValid 
                        ? 'bg-green-50 border border-green-200 text-green-700' 
                        : 'bg-red-50 border border-red-200 text-red-700'
                    }`}>
                      <div className="flex items-center space-x-2">
                        {urlValidation.isValid ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-red-600" />
                        )}
                        <span>
                          {urlValidation.isValid 
                            ? `Valid GitHub URL - User: ${urlValidation.username}` 
                            : urlValidation.errorMessage
                          }
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                <button
                  onClick={handleScanOther}
                  disabled={isLoading || !urlValidation?.isValid}
                  className="w-full bg-secondary-600 hover:bg-secondary-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Starting Scan...</span>
                    </>
                  ) : (
                    <>
                      <Github className="h-4 w-4" />
                      <span>Scan Profile</span>
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          </div>

          {/* Features Preview */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="bg-accent-100 rounded-full p-4 w-16 h-16 mx-auto mb-3">
                <span className="text-2xl">📊</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">ACID Scoring</h4>
              <p className="text-sm text-gray-600">Comprehensive code quality analysis based on Atomicity, Consistency, Isolation, and Durability principles.</p>
            </div>
            <div className="text-center">
              <div className="bg-success-100 rounded-full p-4 w-16 h-16 mx-auto mb-3">
                <span className="text-2xl">🔒</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Security Analysis</h4>
              <p className="text-sm text-gray-600">Automated vulnerability detection and security best practices evaluation.</p>
            </div>
            <div className="text-center">
              <div className="bg-warning-100 rounded-full p-4 w-16 h-16 mx-auto mb-3">
                <span className="text-2xl">💡</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Skill Insights</h4>
              <p className="text-sm text-gray-600">Detailed breakdown of programming languages, frameworks, and technical skills.</p>
            </div>
          </div>

          <div className="mt-8 text-center">
            <p className="text-xs text-gray-500">
              By using our service, you agree to our{' '}
              <a href="#" className="text-primary-500 hover:underline">Terms of Service</a>
              {' '}and{' '}
              <a href="#" className="text-primary-500 hover:underline">Privacy Policy</a>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default DeveloperAuth;