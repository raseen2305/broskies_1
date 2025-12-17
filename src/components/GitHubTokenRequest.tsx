import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Github, Key, AlertCircle, CheckCircle, ExternalLink, Eye, EyeOff } from 'lucide-react';

interface GitHubTokenRequestProps {
  onTokenProvided: (token: string) => void;
  onSkip?: () => void;
  isOptional?: boolean;
}

const GitHubTokenRequest: React.FC<GitHubTokenRequestProps> = ({ 
  onTokenProvided, 
  onSkip, 
  isOptional = false 
}) => {
  const [token, setToken] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState('');

  const validateToken = async (tokenValue: string) => {
    if (!tokenValue.trim()) {
      setError('Please enter a GitHub token');
      return false;
    }

    if (!tokenValue.startsWith('ghp_') && !tokenValue.startsWith('github_pat_')) {
      setError('Invalid GitHub token format');
      return false;
    }

    setIsValidating(true);
    setError('');

    try {
      // Test the token by making a simple API call
      const response = await fetch('https://api.github.com/user', {
        headers: {
          'Authorization': `token ${tokenValue}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      });

      if (response.ok) {
        const userData = await response.json();
        console.log('Token validated for user:', userData.login);
        return true;
      } else {
        setError('Invalid or expired GitHub token');
        return false;
      }
    } catch (error) {
      setError('Failed to validate token. Please check your connection.');
      return false;
    } finally {
      setIsValidating(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const isValid = await validateToken(token);
    if (isValid) {
      onTokenProvided(token);
    }
  };

  const handleSkip = () => {
    if (onSkip) {
      onSkip();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-2xl shadow-lg p-8 max-w-2xl mx-auto"
    >
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
          <Key className="h-8 w-8 text-blue-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          {isOptional ? 'Enhanced Analysis Available' : 'GitHub Token Required'}
        </h2>
        <p className="text-gray-600">
          {isOptional 
            ? 'Provide your GitHub token for detailed repository analysis and higher API limits'
            : 'A GitHub personal access token is required for comprehensive repository analysis'
          }
        </p>
      </div>

      {/* Benefits */}
      <div className="bg-blue-50 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-blue-900 mb-3">With your GitHub token, you get:</h3>
        <ul className="space-y-2 text-sm text-blue-800">
          <li className="flex items-center">
            <CheckCircle className="h-4 w-4 mr-2 text-blue-600" />
            Detailed code analysis and ACID scoring for each repository
          </li>
          <li className="flex items-center">
            <CheckCircle className="h-4 w-4 mr-2 text-blue-600" />
            Comprehensive language and technology stack detection
          </li>
          <li className="flex items-center">
            <CheckCircle className="h-4 w-4 mr-2 text-blue-600" />
            Repository quality metrics and security analysis
          </li>
          <li className="flex items-center">
            <CheckCircle className="h-4 w-4 mr-2 text-blue-600" />
            Commit history and collaboration insights
          </li>
          <li className="flex items-center">
            <CheckCircle className="h-4 w-4 mr-2 text-blue-600" />
            Higher API rate limits for faster scanning
          </li>
        </ul>
      </div>

      {/* Token Input Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="github-token" className="block text-sm font-medium text-gray-700 mb-2">
            GitHub Personal Access Token
          </label>
          <div className="relative">
            <input
              id="github-token"
              type={showToken ? 'text' : 'password'}
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
              className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={() => setShowToken(!showToken)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showToken ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>
          {error && (
            <div className="mt-2 flex items-center text-red-600 text-sm">
              <AlertCircle className="h-4 w-4 mr-1" />
              {error}
            </div>
          )}
        </div>

        <div className="flex space-x-3">
          <button
            type="submit"
            disabled={isValidating || !token.trim()}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors"
          >
            {isValidating ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Validating...
              </div>
            ) : (
              'Use This Token'
            )}
          </button>
          
          {isOptional && (
            <button
              type="button"
              onClick={handleSkip}
              className="px-6 py-3 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Skip
            </button>
          )}
        </div>
      </form>

      {/* Instructions */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-2">How to create a GitHub token:</h4>
        <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
          <li>Go to GitHub Settings → Developer settings → Personal access tokens</li>
          <li>Click "Generate new token (classic)"</li>
          <li>Select scopes: <code className="bg-gray-200 px-1 rounded">public_repo</code> and <code className="bg-gray-200 px-1 rounded">read:user</code></li>
          <li>Copy the generated token and paste it above</li>
        </ol>
        <a
          href="https://github.com/settings/tokens"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center mt-3 text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          <ExternalLink className="h-4 w-4 mr-1" />
          Create GitHub Token
        </a>
      </div>

      {/* Security Note */}
      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-start">
          <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5 mr-2" />
          <div className="text-sm text-yellow-800">
            <strong>Security:</strong> Your token is only used for this analysis session and is not stored permanently. 
            It's transmitted securely and used only to access public repository information.
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default GitHubTokenRequest;