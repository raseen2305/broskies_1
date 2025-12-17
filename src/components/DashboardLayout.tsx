import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart3, 
  Code, 
  Layers, 
  Map, 
  GitBranch, 
  User, 
  LogOut,
  Scan,
  Menu,
  X,
  GitPullRequest,
  AlertCircle,
  Calendar,
  Award,
  Bell,
  Settings,
  ArrowLeft,
  Home,
  ChevronDown,
  ChevronUp,
  Info
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { scanAPI } from '../services/api';
import SidebarNotificationBox from './SidebarNotificationBox';
import ProfileSetupModal from './ProfileSetupModal';

interface DashboardLayoutProps {
  children: React.ReactNode;
  scanResults?: any;
}

interface UserStats {
  overallScore: number;
  repositoryCount: number;
  lastScanDate: string | null;
  languages: Array<{
    language: string;
    percentage: number;
    repositories?: number;
    stars?: number;
  }>;
  githubProfile?: {
    username: string;
    name: string | null;
    bio: string | null;
    location: string | null;
    company: string | null;
    public_repos: number;
    followers: number;
    following: number;
    avatar_url: string | null;
  };
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children, scanResults }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleProfileSetupClick = () => {
    setIsProfileModalOpen(true);
  };

  const handleProfileSetupSuccess = (profile: any) => {
    console.log('Profile created successfully:', profile);
    // Optionally refresh user stats or show notification
  };

  const [isAdditionalInfoExpanded, setIsAdditionalInfoExpanded] = useState(false);

  const navItems = [
    { path: '/developer/dashboard/overview', icon: BarChart3, label: 'Overview', description: 'Your coding overview' },
    { path: '/developer/dashboard/rankings', icon: Award, label: 'Rankings', description: 'Your regional & university rankings' },
    { path: '/developer/dashboard/languages', icon: Code, label: 'Languages', description: 'Programming languages' },
    { path: '/developer/dashboard/tech-stack', icon: Layers, label: 'Tech Stack', description: 'Technologies used' },
    { path: '/developer/dashboard/repositories', icon: GitBranch, label: 'Repositories', description: 'Your repositories' },
  ];

  const additionalInfoItems = [
    { path: '/developer/dashboard/pull-requests', icon: GitPullRequest, label: 'Pull Requests', description: 'PR analysis & collaboration' },
    { path: '/developer/dashboard/issues', icon: AlertCircle, label: 'Issues', description: 'Issue tracking & resolution' },
  ];

  // Use scan results if available
  useEffect(() => {
    if (scanResults) {
      // Transform scan results to match UserStats interface
      const transformedStats: UserStats = {
        overallScore: scanResults.overallScore || scanResults.hybrid_score || 0,
        repositoryCount: scanResults.repositoryCount || 0,
        lastScanDate: new Date().toISOString(),
        languages: scanResults.languages || [],
        githubProfile: scanResults.userInfo ? {
          username: scanResults.userInfo.login || scanResults.targetUsername,
          name: scanResults.userInfo.name,
          bio: scanResults.userInfo.bio,
          location: scanResults.userInfo.location,
          company: scanResults.userInfo.company,
          public_repos: scanResults.userInfo.public_repos || scanResults.repositoryCount,
          followers: scanResults.userInfo.followers || 0,
          following: scanResults.userInfo.following || 0,
          avatar_url: scanResults.userInfo.avatar_url
        } : undefined
      };
      
      setUserStats(transformedStats);
      setIsLoading(false);
    } else {
      // No scan results available, show basic user info
      setUserStats(null);
      setIsLoading(false);
    }
  }, [scanResults]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Header */}
      <div className="lg:hidden bg-white shadow-sm border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {userStats?.githubProfile?.avatar_url ? (
              <img 
                src={userStats.githubProfile.avatar_url} 
                alt="GitHub Avatar"
                className="w-8 h-8 rounded-full"
              />
            ) : (
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full flex items-center justify-center">
                <User className="h-4 w-4 text-white" />
              </div>
            )}
            <div>
              <h3 className="font-semibold text-gray-900 text-sm">
                {userStats?.githubProfile?.name || user?.githubUsername || 'Developer'}
              </h3>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/')}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              title="Home"
            >
              <Home className="h-4 w-4 text-gray-600" />
            </button>
            <button
              onClick={handleLogout}
              className="p-2 rounded-lg hover:bg-red-50 transition-colors"
              title="Logout"
            >
              <LogOut className="h-4 w-4 text-red-600" />
            </button>
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Desktop Sidebar */}
        <div className="hidden lg:flex lg:flex-col lg:w-80 bg-white shadow-lg">
          {/* User Profile Header */}
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center space-x-4 mb-4">
              {userStats?.githubProfile?.avatar_url ? (
                <img 
                  src={userStats.githubProfile.avatar_url} 
                  alt="GitHub Avatar"
                  className="w-12 h-12 rounded-full"
                />
              ) : (
                <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full flex items-center justify-center">
                  <User className="h-6 w-6 text-white" />
                </div>
              )}
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">
                  {userStats?.githubProfile?.name || user?.githubUsername || 'Developer'}
                </h3>
                <p className="text-sm text-gray-500">
                  {userStats?.githubProfile?.bio || 'Developer Profile'}
                </p>
              </div>
            </div>

            {/* Key Metrics */}
            {userStats && (
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gradient-to-br from-primary-50 to-primary-100 rounded-lg p-3">
                  <div className="flex items-center space-x-2">
                    <Award className="h-4 w-4 text-primary-600" />
                    <span className="text-xs font-medium text-primary-700">Overall Score</span>
                  </div>
                  <div className="text-lg font-bold text-primary-900 mt-1">
                    {userStats.overallScore.toFixed(1)}
                  </div>
                </div>
                <div className="bg-gradient-to-br from-secondary-50 to-secondary-100 rounded-lg p-3">
                  <div className="flex items-center space-x-2">
                    <GitBranch className="h-4 w-4 text-secondary-600" />
                    <span className="text-xs font-medium text-secondary-700">Repositories</span>
                  </div>
                  <div className="text-lg font-bold text-secondary-900 mt-1">
                    {userStats.repositoryCount}
                  </div>
                </div>
                <div className="bg-gradient-to-br from-accent-50 to-accent-100 rounded-lg p-3">
                  <div className="flex items-center space-x-2">
                    <Code className="h-4 w-4 text-accent-600" />
                    <span className="text-xs font-medium text-accent-700">Top Language</span>
                  </div>
                  <div className="text-sm font-bold text-accent-900 mt-1">
                    {userStats.languages[0]?.language || 'N/A'}
                  </div>
                </div>
                <div className="bg-gradient-to-br from-success-50 to-success-100 rounded-lg p-3">
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4 text-success-600" />
                    <span className="text-xs font-medium text-success-700">Last Scan</span>
                  </div>
                  <div className="text-xs font-bold text-success-900 mt-1">
                    {userStats.lastScanDate 
                      ? new Date(userStats.lastScanDate).toLocaleDateString()
                      : 'Just now'
                    }
                  </div>
                </div>
              </div>
            )}

            {!userStats && (
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <div className="text-sm text-gray-600 mb-2">No profile data available</div>
                <div className="text-xs text-gray-500">Scan a GitHub profile to see metrics</div>
              </div>
            )}
          </div>

          {/* Navigation */}
          <nav className="flex-1 py-6">
            {navItems.map((item, index) => (
              <motion.div
                key={item.path}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center space-x-3 px-6 py-4 text-gray-700 hover:bg-gray-50 hover:text-primary-500 transition-all duration-200 group ${
                      isActive ? 'bg-primary-50 text-primary-500 border-r-4 border-primary-500' : ''
                    }`
                  }
                >
                  <div className="flex items-center justify-center w-8 h-8 rounded-lg group-hover:bg-primary-100 transition-colors">
                    <item.icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{item.label}</div>
                    <div className="text-xs text-gray-500 group-hover:text-primary-400">
                      {item.description}
                    </div>
                  </div>
                </NavLink>
              </motion.div>
            ))}

            {/* Additional Info Dropdown */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: navItems.length * 0.1 }}
            >
              <button
                onClick={() => setIsAdditionalInfoExpanded(!isAdditionalInfoExpanded)}
                className="w-full flex items-center space-x-3 px-6 py-4 text-gray-700 hover:bg-gray-50 hover:text-primary-500 transition-all duration-200 group"
              >
                <div className="flex items-center justify-center w-8 h-8 rounded-lg group-hover:bg-primary-100 transition-colors">
                  <Info className="h-5 w-5" />
                </div>
                <div className="flex-1 text-left">
                  <div className="font-medium">Additional Info</div>
                  <div className="text-xs text-gray-500 group-hover:text-primary-400">
                    PRs & Issues
                  </div>
                </div>
                {isAdditionalInfoExpanded ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </button>

              {/* Collapsible Additional Info Items */}
              <AnimatePresence>
                {isAdditionalInfoExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden bg-gray-50"
                  >
                    {additionalInfoItems.map((item) => (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                          `flex items-center space-x-3 px-6 py-3 pl-14 text-sm text-gray-600 hover:bg-gray-100 hover:text-primary-500 transition-all duration-200 group ${
                            isActive ? 'bg-primary-50 text-primary-500 border-r-4 border-primary-500' : ''
                          }`
                        }
                      >
                        <item.icon className="h-4 w-4" />
                        <div className="flex-1">
                          <div className="font-medium">{item.label}</div>
                        </div>
                      </NavLink>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </nav>

          {/* Action Buttons */}
          <div className="px-6 py-4 space-y-2 border-t border-gray-200">
            <button
              onClick={() => navigate('/')}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 text-sm font-medium text-gray-700 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <Home className="h-4 w-4" />
              <span>Back to Home</span>
            </button>
            {userStats?.githubProfile?.username ? (
              <button
                onClick={() => {
                  navigate('/scanning-progress', {
                    state: {
                      scanType: 'self',
                      username: userStats.githubProfile.username
                    }
                  });
                }}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
              >
                <Scan className="h-4 w-4" />
                <span>Rescan Profile</span>
              </button>
            ) : (
              <button
                onClick={() => navigate('/developer/auth')}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
              >
                <Scan className="h-4 w-4" />
                <span>Scan Repositories</span>
              </button>
            )}
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 text-sm font-medium text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
            >
              <LogOut className="h-4 w-4" />
              <span>Logout</span>
            </button>
          </div>

          {/* Ranking Notification - Removed: Form should appear after scan, not before */}
          {/* <SidebarNotificationBox 
            onSetupClick={handleProfileSetupClick}
            visible={true}
          /> */}
        </div>

        {/* Mobile Sidebar */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="lg:hidden fixed inset-0 z-50 bg-black bg-opacity-50"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              <motion.div
                initial={{ x: -300 }}
                animate={{ x: 0 }}
                exit={{ x: -300 }}
                className="w-80 bg-white h-full shadow-xl"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      {userStats?.githubProfile?.avatar_url ? (
                        <img 
                          src={userStats.githubProfile.avatar_url} 
                          alt="GitHub Avatar"
                          className="w-10 h-10 rounded-full"
                        />
                      ) : (
                        <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-full flex items-center justify-center">
                          <User className="h-5 w-5 text-white" />
                        </div>
                      )}
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {userStats?.githubProfile?.name || user?.githubUsername || 'Developer'}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {userStats?.githubProfile?.bio || 'Developer Profile'}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => setIsMobileMenuOpen(false)}
                      className="p-2 rounded-lg hover:bg-gray-100"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  {/* Mobile Key Metrics */}
                  {userStats && (
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-primary-50 rounded-lg p-2">
                        <div className="text-xs text-primary-700">Score</div>
                        <div className="text-lg font-bold text-primary-900">
                          {userStats.overallScore.toFixed(1)}
                        </div>
                      </div>
                      <div className="bg-secondary-50 rounded-lg p-2">
                        <div className="text-xs text-secondary-700">Repos</div>
                        <div className="text-lg font-bold text-secondary-900">
                          {userStats.repositoryCount}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {!userStats && (
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <div className="text-xs text-gray-600">No profile data</div>
                    </div>
                  )}
                </div>

                <nav className="py-4">
                  {navItems.map((item) => (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={() => setIsMobileMenuOpen(false)}
                      className={({ isActive }) =>
                        `flex items-center space-x-3 px-6 py-3 text-gray-700 hover:bg-gray-50 hover:text-primary-500 transition-colors duration-200 ${
                          isActive ? 'bg-primary-50 text-primary-500 border-r-4 border-primary-500' : ''
                        }`
                      }
                    >
                      <item.icon className="h-5 w-5" />
                      <div>
                        <div className="font-medium">{item.label}</div>
                        <div className="text-xs text-gray-500">{item.description}</div>
                      </div>
                    </NavLink>
                  ))}
                </nav>

                {/* Ranking Notification - Mobile - Removed: Form should appear after scan */}
                {/* <div className="mt-auto">
                  <SidebarNotificationBox 
                    onSetupClick={() => {
                      handleProfileSetupClick();
                      setIsMobileMenuOpen(false);
                    }}
                    visible={true}
                  />
                </div> */}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <div className="flex-1 overflow-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="p-4 lg:p-8"
          >
            {children}
          </motion.div>
        </div>
      </div>

      {/* Profile Setup Modal */}
      <ProfileSetupModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        onSuccess={handleProfileSetupSuccess}
      />
    </div>
  );
};

export default DashboardLayout;