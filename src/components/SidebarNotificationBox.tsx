import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Award, X } from 'lucide-react';
import api from '../services/api';

export interface SidebarNotificationBoxProps {
  onSetupClick: () => void;
  visible: boolean;
}

export interface NotificationState {
  hasProfile: boolean;
  dismissed: boolean;
}

const SidebarNotificationBox: React.FC<SidebarNotificationBoxProps> = ({ 
  onSetupClick, 
  visible 
}) => {
  const [notificationState, setNotificationState] = useState<NotificationState>({
    hasProfile: false,
    dismissed: false,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkProfileStatus();
  }, []);

  const checkProfileStatus = async () => {
    try {
      setIsLoading(true);
      
      // Check localStorage for dismissal state
      const dismissed = localStorage.getItem('ranking_notification_dismissed') === 'true';
      
      // Check if user has completed profile via API
      const response = await api.get('/profile/status');
      const hasProfile = response.data.has_profile;
      
      setNotificationState({
        hasProfile,
        dismissed,
      });
    } catch (error) {
      console.error('Failed to check profile status:', error);
      // If API fails, check localStorage only
      const dismissed = localStorage.getItem('ranking_notification_dismissed') === 'true';
      setNotificationState({
        hasProfile: false,
        dismissed,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDismiss = (e: React.MouseEvent) => {
    e.stopPropagation();
    localStorage.setItem('ranking_notification_dismissed', 'true');
    setNotificationState(prev => ({ ...prev, dismissed: true }));
  };

  const handleClick = () => {
    onSetupClick();
  };

  // Don't show if loading, has profile, dismissed, or parent says not visible
  if (isLoading || notificationState.hasProfile || notificationState.dismissed || !visible) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 20 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="relative"
      >
        <div
          onClick={handleClick}
          className="mx-6 mb-6 p-4 bg-gradient-to-br from-primary-50 to-secondary-50 border-2 border-primary-200 rounded-lg cursor-pointer hover:shadow-lg hover:border-primary-300 transition-all duration-300 group"
        >
          {/* Dismiss Button */}
          <button
            onClick={handleDismiss}
            className="absolute top-2 right-2 p-1 rounded-full hover:bg-white/50 transition-colors"
            aria-label="Dismiss notification"
          >
            <X className="h-4 w-4 text-gray-500 hover:text-gray-700" />
          </button>

          {/* Icon */}
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <Award className="h-5 w-5 text-white" />
            </div>

            {/* Content */}
            <div className="flex-1">
              <h4 className="font-semibold text-gray-900 mb-1">
                See How You Rank!
              </h4>
              <p className="text-sm text-gray-600 leading-relaxed">
                Complete your profile to see how you rank!
              </p>
              <div className="mt-2 text-xs font-medium text-primary-600 group-hover:text-primary-700">
                Click to get started →
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default SidebarNotificationBox;
