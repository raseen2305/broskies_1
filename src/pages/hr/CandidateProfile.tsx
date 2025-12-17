/**
 * Candidate Profile Page
 * 
 * HR view of a candidate's complete developer profile.
 * Loads data instantly from database and displays using the DeveloperDashboard component.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, RefreshCw, AlertCircle, Loader2, Clock, ChevronRight, Share2, Check } from 'lucide-react';
import { getCandidateProfile, refreshCandidateProfile } from '../../services/hrAPI';
import type { CandidateProfile as CandidateProfileType } from '../../services/hrAPI';
import DeveloperDashboard from '../DeveloperDashboard';

const CandidateProfile: React.FC = () => {
  const { username: encodedUsername } = useParams<{ username: string }>();
  // Decode the username from URL (handles special characters)
  const username = encodedUsername ? decodeURIComponent(encodedUsername) : undefined;
  const navigate = useNavigate();
  
  const [profile, setProfile] = useState<CandidateProfileType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshStatus, setRefreshStatus] = useState<string>('');
  const [showCopiedToast, setShowCopiedToast] = useState(false);

  useEffect(() => {
    if (username) {
      loadProfile();
    }
  }, [username]);

  const loadProfile = async () => {
    if (!username) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      console.log(`📡 Loading candidate profile for: ${username}`);
      const data = await getCandidateProfile(username);
      
      console.log('✅ Profile loaded:', data);
      setProfile(data);
      
    } catch (err: any) {
      console.error('❌ Failed to load profile:', err);
      setError(err.message || 'Failed to load candidate profile');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!username) return;
    
    try {
      setIsRefreshing(true);
      setRefreshStatus('Initiating scan...');
      
      console.log(`🔄 Initiating profile refresh for: ${username}`);
      
      // Trigger the refresh/scan
      const refreshResult = await refreshCandidateProfile(username);
      
      if (refreshResult.success) {
        setRefreshStatus('Scan in progress...');
        console.log('✅ Scan initiated successfully');
        
        // Wait a bit for the scan to complete (external scans are typically fast)
        // Poll for updated data every 2 seconds for up to 30 seconds
        let attempts = 0;
        const maxAttempts = 15; // 30 seconds total
        
        const pollForUpdates = async () => {
          attempts++;
          setRefreshStatus(`Updating profile... (${attempts}/${maxAttempts})`);
          
          try {
            // Try to fetch the updated profile
            const updatedProfile = await getCandidateProfile(username);
            
            // Check if the data is fresher than before
            const oldDate = profile?.last_scan_date ? new Date(profile.last_scan_date).getTime() : 0;
            const newDate = new Date(updatedProfile.last_scan_date).getTime();
            
            if (newDate > oldDate || attempts >= maxAttempts) {
              // Profile has been updated or we've reached max attempts
              console.log('✅ Profile updated successfully');
              setProfile(updatedProfile);
              setRefreshStatus('Profile refreshed successfully!');
              
              // Clear success message after 3 seconds
              setTimeout(() => {
                setRefreshStatus('');
              }, 3000);
              
              setIsRefreshing(false);
              return;
            }
            
            // Continue polling if not updated yet
            if (attempts < maxAttempts) {
              setTimeout(pollForUpdates, 2000);
            } else {
              // Max attempts reached, reload anyway
              setProfile(updatedProfile);
              setRefreshStatus('Profile loaded (scan may still be in progress)');
              setTimeout(() => {
                setRefreshStatus('');
              }, 3000);
              setIsRefreshing(false);
            }
          } catch (err) {
            console.error('Error polling for updates:', err);
            if (attempts < maxAttempts) {
              setTimeout(pollForUpdates, 2000);
            } else {
              setRefreshStatus('Scan initiated, please refresh page to see updates');
              setTimeout(() => {
                setRefreshStatus('');
              }, 5000);
              setIsRefreshing(false);
            }
          }
        };
        
        // Start polling after a short delay
        setTimeout(pollForUpdates, 3000);
      }
      
    } catch (err: any) {
      console.error('❌ Failed to refresh profile:', err);
      setRefreshStatus('');
      setError(err.message || 'Failed to refresh profile');
      setIsRefreshing(false);
    }
  };

  const handleBack = () => {
    navigate('/hr/dashboard');
  };

  const handleShareProfile = async () => {
    if (!username) return;
    
    try {
      // Encode username for URL (handles special characters)
      const encodedUsername = encodeURIComponent(username);
      const profileUrl = `${window.location.origin}/hr/candidates/${encodedUsername}`;
      
      // Copy to clipboard
      await navigator.clipboard.writeText(profileUrl);
      
      // Show success toast
      setShowCopiedToast(true);
      setTimeout(() => {
        setShowCopiedToast(false);
      }, 3000);
      
      console.log('✅ Profile URL copied to clipboard:', profileUrl);
    } catch (err) {
      console.error('❌ Failed to copy URL:', err);
      // Fallback: show alert with URL
      const encodedUsername = encodeURIComponent(username);
      const profileUrl = `${window.location.origin}/hr/candidates/${encodedUsername}`;
      alert(`Profile URL: ${profileUrl}`);
    }
  };

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header Skeleton */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center space-x-2 mb-4">
              <div className="h-4 w-4 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 w-4 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
            </div>
            <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>

        {/* Content Skeleton */}
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="space-y-6">
            <div className="h-64 bg-white rounded-lg animate-pulse" />
            <div className="h-96 bg-white rounded-lg animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="max-w-7xl mx-auto">
            <button
              onClick={handleBack}
              className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </button>
          </div>
        </div>

        {/* Error Content */}
        <div className="max-w-7xl mx-auto px-6 py-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-lg shadow-sm p-8 text-center"
          >
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                <AlertCircle className="w-8 h-8 text-red-600" />
              </div>
            </div>
            
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              {error.includes('not found') ? 'Profile Not Found' : 'Unable to Load Profile'}
            </h2>
            
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
              {error}
            </p>

            <div className="flex justify-center space-x-4">
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="btn-primary flex items-center"
              >
                {isRefreshing ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4 mr-2" />
                )}
                Try Again
              </button>
              
              <button
                onClick={handleBack}
                className="btn-ghost"
              >
                Back to Dashboard
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  // Profile loaded successfully
  if (!profile) return null;

  // Check if data is outdated (older than 7 days)
  const isDataOutdated = profile.data_age_days !== null && profile.data_age_days > 7;

  // Convert profile data to format expected by DeveloperDashboard
  const scanResults = {
    userId: `external_${profile.github_username}`,
    username: profile.github_username,
    targetUsername: profile.github_username,
    overallScore: profile.scores.overall_score,
    analyzed: profile.analyzed,
    analyzedAt: profile.last_scan_date,
    categoryDistribution: profile.category_distribution,
    analysis_available: true,
    analysis_type: profile.analysis_type,
    repositoryCount: profile.repository_count,
    lastScanDate: profile.last_scan_date,
    languages: profile.languages,
    techStack: profile.tech_stack,
    repositories: profile.repositories,
    repositoryDetails: profile.repositories,
    githubProfile: {
      username: profile.profile.name || profile.github_username,
      name: profile.profile.name,
      bio: profile.profile.bio,
      location: profile.profile.location,
      company: profile.profile.company,
      blog: profile.profile.blog,
      public_repos: profile.profile.public_repos,
      followers: profile.profile.followers,
      following: profile.profile.following,
      avatar_url: profile.profile.avatar_url,
    },
    userInfo: {
      login: profile.github_username,
      name: profile.profile.name,
      bio: profile.profile.bio,
      avatar_url: profile.profile.avatar_url,
      location: profile.profile.location,
      company: profile.profile.company,
      email: profile.profile.email,
      blog: profile.profile.blog,
      public_repos: profile.profile.public_repos,
      followers: profile.profile.followers,
      following: profile.profile.following,
    },
    comprehensiveData: profile.comprehensive_data,
    scanType: 'other',
    isExternalScan: true,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* HR Navigation Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto">
          {/* Breadcrumbs */}
          <div className="flex items-center space-x-2 text-sm text-gray-600 mb-3">
            <Link to="/hr/dashboard" className="hover:text-gray-900">
              HR Dashboard
            </Link>
            <ChevronRight className="w-4 h-4" />
            <span className="text-gray-900 font-medium">{profile.github_username}</span>
          </div>

          {/* Header Actions */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={handleBack}
                className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Dashboard
              </button>
              
              {/* Data Freshness Indicator */}
              <div className="flex items-center space-x-2 text-sm">
                <Clock className="w-4 h-4 text-gray-400" />
                <span className="text-gray-600">
                  Last updated: {profile.data_age_days === 0 ? 'Today' : `${profile.data_age_days} days ago`}
                </span>
                {isDataOutdated && (
                  <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                    Data may be outdated
                  </span>
                )}
              </div>
            </div>

            {/* Refresh Button, Share Button and Status */}
            <div className="flex items-center space-x-3">
              {refreshStatus && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center space-x-2 text-sm"
                >
                  {isRefreshing ? (
                    <>
                      <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                      <span className="text-blue-600 font-medium">{refreshStatus}</span>
                    </>
                  ) : (
                    <span className="text-green-600 font-medium">{refreshStatus}</span>
                  )}
                </motion.div>
              )}
              
              <button
                onClick={handleShareProfile}
                className="btn-ghost flex items-center"
                title="Copy profile URL to clipboard"
              >
                {showCopiedToast ? (
                  <>
                    <Check className="w-4 h-4 mr-2 text-green-600" />
                    <span className="text-green-600">Copied!</span>
                  </>
                ) : (
                  <>
                    <Share2 className="w-4 h-4 mr-2" />
                    Share Profile
                  </>
                )}
              </button>
              
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className={`btn-ghost flex items-center ${isRefreshing ? 'opacity-50 cursor-not-allowed' : ''}`}
                title="Trigger a new scan to update profile data"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                {isRefreshing ? 'Refreshing...' : 'Refresh Profile'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Developer Dashboard Content */}
      <div className="max-w-7xl mx-auto px-6 py-6 relative">
        {/* Refresh Overlay */}
        {isRefreshing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 bg-white/80 backdrop-blur-sm z-20 flex items-center justify-center rounded-lg"
          >
            <div className="bg-white rounded-lg shadow-lg p-8 text-center max-w-md">
              <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Refreshing Profile
              </h3>
              <p className="text-gray-600 mb-4">
                {refreshStatus || 'Scanning GitHub profile and repositories...'}
              </p>
              <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                <motion.div
                  className="h-full bg-blue-600"
                  initial={{ width: '0%' }}
                  animate={{ width: '100%' }}
                  transition={{ duration: 30, ease: 'linear' }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                This may take up to 30 seconds
              </p>
            </div>
          </motion.div>
        )}
        
        <DeveloperDashboard scanResults={scanResults} />
      </div>
    </div>
  );
};

export default CandidateProfile;
