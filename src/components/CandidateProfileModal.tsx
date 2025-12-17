/**
 * Candidate Profile Modal Component
 * 
 * Displays candidate's full dashboard data in a modal overlay
 * Loads data from user_rankings and state_analysis collections
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, RefreshCw, Loader2, Clock, Share2, Check, AlertCircle } from 'lucide-react';
import { getCandidateProfile, refreshCandidateProfile } from '../services/hrAPI';
import type { CandidateProfile as CandidateProfileType } from '../services/hrAPI';
import ModalDeveloperDashboard from './ModalDeveloperDashboard';

interface CandidateProfileModalProps {
  username: string;
  isOpen: boolean;
  onClose: () => void;
}

const CandidateProfileModal: React.FC<CandidateProfileModalProps> = ({
  username,
  isOpen,
  onClose,
}) => {
  const [profile, setProfile] = useState<CandidateProfileType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshStatus, setRefreshStatus] = useState<string>('');
  const [showCopiedToast, setShowCopiedToast] = useState(false);

  useEffect(() => {
    if (isOpen && username) {
      // Reset state when opening modal or username changes
      setProfile(null);
      setError(null);
      setIsRefreshing(false);
      setRefreshStatus('');
      loadProfile();
    }
  }, [isOpen, username]);

  const loadProfile = async () => {
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
    try {
      setIsRefreshing(true);
      setRefreshStatus('Initiating scan...');
      
      console.log(`🔄 Initiating profile refresh for: ${username}`);
      
      const refreshResult = await refreshCandidateProfile(username);
      
      if (refreshResult.success) {
        setRefreshStatus('Scan in progress...');
        console.log('✅ Scan initiated successfully');
        
        // Poll for updated data
        let attempts = 0;
        const maxAttempts = 15;
        
        const pollForUpdates = async () => {
          attempts++;
          setRefreshStatus(`Updating profile... (${attempts}/${maxAttempts})`);
          
          try {
            const updatedProfile = await getCandidateProfile(username);
            
            const oldDate = profile?.last_scan_date ? new Date(profile.last_scan_date).getTime() : 0;
            const newDate = new Date(updatedProfile.last_scan_date).getTime();
            
            if (newDate > oldDate || attempts >= maxAttempts) {
              console.log('✅ Profile updated successfully');
              setProfile(updatedProfile);
              setRefreshStatus('Profile refreshed successfully!');
              
              setTimeout(() => {
                setRefreshStatus('');
              }, 3000);
              
              setIsRefreshing(false);
              return;
            }
            
            if (attempts < maxAttempts) {
              setTimeout(pollForUpdates, 2000);
            } else {
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
              setRefreshStatus('Scan initiated, please refresh to see updates');
              setTimeout(() => {
                setRefreshStatus('');
              }, 5000);
              setIsRefreshing(false);
            }
          }
        };
        
        setTimeout(pollForUpdates, 3000);
      }
      
    } catch (err: any) {
      console.error('❌ Failed to refresh profile:', err);
      setRefreshStatus('');
      setError(err.message || 'Failed to refresh profile');
      setIsRefreshing(false);
    }
  };

  const handleShareProfile = async () => {
    try {
      const encodedUsername = encodeURIComponent(username);
      const profileUrl = `${window.location.origin}/hr/candidates/${encodedUsername}`;
      
      await navigator.clipboard.writeText(profileUrl);
      
      setShowCopiedToast(true);
      setTimeout(() => {
        setShowCopiedToast(false);
      }, 3000);
      
      console.log('✅ Profile URL copied to clipboard:', profileUrl);
    } catch (err) {
      console.error('❌ Failed to copy URL:', err);
      const encodedUsername = encodeURIComponent(username);
      const profileUrl = `${window.location.origin}/hr/candidates/${encodedUsername}`;
      alert(`Profile URL: ${profileUrl}`);
    }
  };

  // Convert profile data to format expected by DeveloperDashboard
  const getScanResults = () => {
    if (!profile) return null;

    return {
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
  };

  const isDataOutdated = profile?.data_age_days !== null && profile?.data_age_days && profile.data_age_days > 7;
  const scanResults = getScanResults();

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', duration: 0.5 }}
            className="fixed inset-4 md:inset-8 bg-white rounded-2xl shadow-2xl z-50 flex flex-col overflow-hidden"
          >
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-4 flex items-center justify-between border-b border-indigo-700">
              <div className="flex items-center space-x-4 flex-1">
                <h2 className="text-xl font-bold text-white">
                  {profile?.github_username || username}
                </h2>
                
                {profile && (
                  <div className="flex items-center space-x-2 text-sm text-indigo-100">
                    <Clock className="w-4 h-4" />
                    <span>
                      Last updated: {profile.data_age_days === 0 ? 'Today' : `${profile.data_age_days} days ago`}
                    </span>
                    {isDataOutdated && (
                      <span className="px-2 py-1 bg-yellow-500 text-white text-xs rounded-full font-semibold">
                        Outdated
                      </span>
                    )}
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-2">
                {refreshStatus && (
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center space-x-2 text-sm mr-3"
                  >
                    {isRefreshing ? (
                      <>
                        <Loader2 className="w-4 h-4 text-white animate-spin" />
                        <span className="text-white font-medium">{refreshStatus}</span>
                      </>
                    ) : (
                      <span className="text-green-200 font-medium">{refreshStatus}</span>
                    )}
                  </motion.div>
                )}

                <button
                  onClick={handleShareProfile}
                  className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors"
                  title="Copy profile URL"
                >
                  {showCopiedToast ? (
                    <Check className="w-5 h-5 text-green-200" />
                  ) : (
                    <Share2 className="w-5 h-5" />
                  )}
                </button>

                <button
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                  className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors disabled:opacity-50"
                  title="Refresh profile"
                >
                  <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
                </button>

                <button
                  onClick={onClose}
                  className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors"
                  title="Close"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto bg-gray-50">
              {isLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mx-auto mb-4" />
                    <p className="text-gray-600 font-medium">Loading profile...</p>
                  </div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center h-full p-8">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white rounded-lg shadow-lg p-8 text-center max-w-md"
                  >
                    <div className="flex justify-center mb-4">
                      <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                        <AlertCircle className="w-8 h-8 text-red-600" />
                      </div>
                    </div>
                    
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                      {error.includes('not found') ? 'Profile Not Found' : 'Unable to Load Profile'}
                    </h3>
                    
                    <p className="text-gray-600 mb-6">
                      {error}
                    </p>

                    <button
                      onClick={handleRefresh}
                      disabled={isRefreshing}
                      className="btn-primary flex items-center mx-auto"
                    >
                      {isRefreshing ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4 mr-2" />
                      )}
                      Try Again
                    </button>
                  </motion.div>
                </div>
              ) : scanResults ? (
                <div className="p-6 relative">
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
                  
                  <ModalDeveloperDashboard scanResults={scanResults} />
                </div>
              ) : null}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default CandidateProfileModal;
