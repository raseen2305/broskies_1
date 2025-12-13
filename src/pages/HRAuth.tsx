/**
 * HR Authentication Page
 * Handles HR user registration and Google OAuth sign-in
 */

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Users, AlertCircle, Loader2, Key } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useHRAuth } from '../contexts/HRAuthContext';
import { isDevLoginEnabled, performDevLogin, getDevCredentials } from '../utils/devAuth';

// Google Form URL from environment or default
const GOOGLE_FORM_URL = import.meta.env.VITE_GOOGLE_FORM_URL || 
  'https://docs.google.com/forms/d/e/1FAIpQLSfpKFvNqca-W4fvPn7sa1zm6NpJpzvZYY948fk4_YbPdDRilA/viewform';

/**
 * Development Login Section Component
 * Only visible when VITE_ENABLE_DEV_LOGIN=true in .env
 */
const DevLoginSection: React.FC = () => {
  const navigate = useNavigate();
  const [devEmail, setDevEmail] = useState('');
  const [devPassword, setDevPassword] = useState('');
  const [devError, setDevError] = useState('');
  const [devLoading, setDevLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const devCreds = getDevCredentials();

  const handleDevLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setDevError('');
    setDevLoading(true);

    try {
      const result = await performDevLogin(devEmail, devPassword);
      
      if (result.success) {
        // Give context a moment to update, then navigate
        setTimeout(() => {
          navigate('/hr/dashboard');
        }, 100);
      } else {
        setDevError(result.error || 'Login failed');
      }
    } catch (error) {
      setDevError('Login failed. Please try again.');
    } finally {
      setDevLoading(false);
    }
  };

  const fillDevCredentials = () => {
    if (devCreds) {
      setDevEmail(devCreds.email);
      setDevPassword(devCreds.password);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      className="mt-6 p-4 bg-yellow-50 border-2 border-yellow-300 rounded-lg"
    >
      <div className="flex items-center space-x-2 mb-3">
        <Key className="h-5 w-5 text-yellow-700" />
        <h3 className="text-sm font-semibold text-yellow-900">
          Development Login (Testing Only)
        </h3>
      </div>
      
      <form onSubmit={handleDevLogin} className="space-y-3">
        <div>
          <input
            type="email"
            placeholder="Email"
            value={devEmail}
            onChange={(e) => setDevEmail(e.target.value)}
            className="w-full px-3 py-2 border border-yellow-300 rounded-lg text-sm focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
            required
          />
        </div>
        <div className="relative">
          <input
            type={showPassword ? 'text' : 'password'}
            placeholder="Password"
            value={devPassword}
            onChange={(e) => setDevPassword(e.target.value)}
            className="w-full px-3 py-2 border border-yellow-300 rounded-lg text-sm focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
            required
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-yellow-700 hover:text-yellow-900"
          >
            {showPassword ? 'Hide' : 'Show'}
          </button>
        </div>
        
        {devError && (
          <p className="text-xs text-red-600">{devError}</p>
        )}
        
        <div className="flex space-x-2">
          <button
            type="submit"
            className="flex-1 bg-yellow-600 hover:bg-yellow-700 text-white font-medium py-2 px-3 rounded-lg text-sm transition-colors"
          >
            Dev Login
          </button>
          <button
            type="button"
            onClick={fillDevCredentials}
            className="px-3 py-2 bg-yellow-100 hover:bg-yellow-200 text-yellow-800 text-xs rounded-lg transition-colors"
          >
            Fill
          </button>
        </div>
      </form>
      
      <p className="text-xs text-yellow-700 mt-2">
        ⚠️ This login bypasses OAuth for testing. Disable in production!
      </p>
    </motion.div>
  );
};

const HRAuth: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { signInWithGoogle, isLoading, error, clearError, isAuthenticated } = useHRAuth();
  
  const [localError, setLocalError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Handle OAuth callback
  useEffect(() => {
    const code = searchParams.get('code');
    const errorParam = searchParams.get('error');

    // Debug: Show OAuth attempt info from sessionStorage
    const oauthAttempt = sessionStorage.getItem('oauth_callback_attempt');
    const oauthCode = sessionStorage.getItem('oauth_code');
    const oauthError = sessionStorage.getItem('oauth_error');
    const oauthSuccess = sessionStorage.getItem('oauth_success');

    if (oauthAttempt) {
      console.log('📊 OAuth Debug Info:');
      console.log('   Last attempt:', oauthAttempt);
      console.log('   Code used:', oauthCode);
      console.log('   Success:', oauthSuccess);
      console.log('   Error:', oauthError);
    }

    // Check for error in URL params
    if (errorParam) {
      if (errorParam === 'auth_failed') {
        const detailedError = oauthError ? `Authentication failed: ${oauthError}` : 'Authentication failed. Please try again.';
        setLocalError(detailedError);
      } else if (errorParam === 'not_approved') {
        setLocalError('Your account is not approved yet. Please complete the registration form first.');
      } else if (errorParam === 'server_unavailable') {
        setLocalError('Cannot connect to server. Please ensure the backend is running on http://localhost:8000 and try again.');
      } else {
        setLocalError('An error occurred during authentication.');
      }
      // Clear error from URL
      window.history.replaceState({}, '', '/hr/auth');
      
      // Clear OAuth debug info after showing error
      sessionStorage.removeItem('oauth_callback_attempt');
      sessionStorage.removeItem('oauth_code');
      sessionStorage.removeItem('oauth_error');
      sessionStorage.removeItem('oauth_success');
    }

    // If we have a code, the HRAuthContext will handle it automatically
    if (code) {
      setIsProcessing(true);
    }
  }, [searchParams]);

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (isAuthenticated && !isProcessing) {
      navigate('/hr/dashboard');
    }
  }, [isAuthenticated, isProcessing, navigate]);

  // Handle error from context
  useEffect(() => {
    if (error) {
      setLocalError(error);
      setIsProcessing(false);
    }
  }, [error]);

  /**
   * Handle "Fill Registration Form" button click
   * Opens Google Form in new tab
   */
  const handleFillForm = () => {
    window.open(GOOGLE_FORM_URL, '_blank');
  };

  /**
   * Handle "Continue with Google" button click
   * Initiates OAuth flow
   */
  const handleGoogleSignIn = async () => {
    try {
      setLocalError(null);
      clearError();
      await signInWithGoogle();
    } catch (err) {
      console.error('Google sign-in error:', err);
      setLocalError(err instanceof Error ? err.message : 'Failed to initiate Google sign-in');
    }
  };

  /**
   * Clear error message
   */
  const handleClearError = () => {
    setLocalError(null);
    clearError();
  };

  // Show loading state during OAuth callback processing
  if (isProcessing || (isLoading && searchParams.get('code'))) {
    return (
      <div className="min-h-screen gradient-bg flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md"
        >
          <div className="text-center">
            <Loader2 className="h-12 w-12 text-primary-500 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Authenticating...
            </h2>
            <p className="text-gray-600">
              Please wait while we verify your credentials
            </p>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen gradient-bg flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Users className="h-12 w-12 text-primary-500" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            HR Recruitment Dashboard
          </h1>
          <p className="text-gray-600">
            Access developer talent insights
          </p>
        </div>

        {/* Error Message */}
        {(localError || error) && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3"
          >
            <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-red-800">
                {localError || error}
              </p>
              {(localError?.includes('not approved') || error?.includes('not approved')) && (
                <p className="text-xs text-red-600 mt-2">
                  Please fill out the registration form and wait for approval before signing in.
                </p>
              )}
            </div>
            <button
              onClick={handleClearError}
              className="text-red-500 hover:text-red-700 text-sm font-medium"
            >
              ×
            </button>
          </motion.div>
        )}

        {/* Authentication Options */}
        <div className="space-y-4">
          {/* Continue with Google Button */}
          <button
            onClick={handleGoogleSignIn}
            disabled={isLoading}
            className="w-full bg-white hover:bg-gray-50 text-gray-700 font-medium py-3 px-4 rounded-lg border-2 border-gray-300 flex items-center justify-center space-x-3 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <svg className="h-5 w-5" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
            )}
            <span>Continue with Google</span>
          </button>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">OR</span>
            </div>
          </div>

          {/* Fill Registration Form Button */}
          <button
            onClick={handleFillForm}
            className="w-full bg-primary-500 hover:bg-primary-600 text-white font-medium py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors duration-200 shadow-sm hover:shadow-md"
          >
            <span>Fill Registration Form</span>
          </button>
        </div>

        {/* Development Login (Only visible in dev mode) */}
        {isDevLoginEnabled() && <DevLoginSection />}

        {/* Info Text */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            New to the platform? Fill out the registration form to request access.
          </p>
          <p className="text-xs text-gray-400 mt-2">
            <strong>First time?</strong> Complete the form above, then sign in with Google.<br/>
            <strong>Returning user?</strong> Just click "Continue with Google" to sign in.
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default HRAuth;
