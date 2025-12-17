/**
 * Notification system for user feedback and error messages
 */

import React, { useState, useEffect, useCallback } from 'react';
import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';
import { errorHandler, ErrorDisplayInfo } from '../utils/errorHandler';

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  persistent?: boolean;
  actions?: Array<{
    label: string;
    action: () => void;
    primary?: boolean;
  }>;
}

interface NotificationItemProps {
  notification: Notification;
  onDismiss: (id: string) => void;
}

const NotificationItem: React.FC<NotificationItemProps> = ({ notification, onDismiss }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    // Animate in
    const timer = setTimeout(() => setIsVisible(true), 10);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!notification.persistent && notification.duration !== 0) {
      const duration = notification.duration || 5000;
      const timer = setTimeout(() => {
        handleDismiss();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [notification.duration, notification.persistent]);

  const handleDismiss = () => {
    setIsLeaving(true);
    setTimeout(() => {
      onDismiss(notification.id);
    }, 300);
  };

  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'info':
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getBackgroundColor = () => {
    switch (notification.type) {
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'info':
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  const getTextColor = () => {
    switch (notification.type) {
      case 'success':
        return 'text-green-800';
      case 'error':
        return 'text-red-800';
      case 'warning':
        return 'text-yellow-800';
      case 'info':
      default:
        return 'text-blue-800';
    }
  };

  return (
    <div
      className={`
        transform transition-all duration-300 ease-in-out
        ${isVisible && !isLeaving ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
        max-w-sm w-full ${getBackgroundColor()} border rounded-lg shadow-lg pointer-events-auto
      `}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            {getIcon()}
          </div>
          <div className="ml-3 w-0 flex-1">
            <p className={`text-sm font-medium ${getTextColor()}`}>
              {notification.title}
            </p>
            <p className={`mt-1 text-sm ${getTextColor()} opacity-90`}>
              {notification.message}
            </p>
            {notification.actions && notification.actions.length > 0 && (
              <div className="mt-3 flex space-x-2">
                {notification.actions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      action.action();
                      if (!notification.persistent) {
                        handleDismiss();
                      }
                    }}
                    className={`
                      text-xs font-medium rounded-md px-2 py-1 transition-colors
                      ${action.primary
                        ? `${notification.type === 'error' ? 'bg-red-600 hover:bg-red-700' : 
                            notification.type === 'warning' ? 'bg-yellow-600 hover:bg-yellow-700' :
                            notification.type === 'success' ? 'bg-green-600 hover:bg-green-700' :
                            'bg-blue-600 hover:bg-blue-700'} text-white`
                        : `${getTextColor()} hover:bg-white hover:bg-opacity-50`
                      }
                    `}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="ml-4 flex-shrink-0 flex">
            <button
              onClick={handleDismiss}
              className={`
                rounded-md inline-flex ${getTextColor()} hover:bg-white hover:bg-opacity-50
                focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
              `}
            >
              <span className="sr-only">Close</span>
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export const NotificationSystem: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const addNotification = useCallback((notification: Omit<Notification, 'id'>) => {
    const id = `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newNotification: Notification = {
      id,
      ...notification
    };

    setNotifications(prev => [...prev, newNotification]);
    return id;
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Handle errors from error handler
  useEffect(() => {
    const handleError = (errorInfo: ErrorDisplayInfo) => {
      addNotification({
        title: errorInfo.title,
        message: errorInfo.message,
        type: errorInfo.type,
        persistent: errorInfo.type === 'error',
        actions: errorInfo.recoveryActions?.map(action => ({
          label: action.label,
          action: action.action,
          primary: true
        }))
      });
    };

    errorHandler.onError(handleError);

    return () => {
      errorHandler.removeErrorCallback(handleError);
    };
  }, [addNotification]);

  // Expose notification functions globally
  useEffect(() => {
    (window as any).showNotification = addNotification;
    (window as any).clearNotifications = clearAllNotifications;
  }, [addNotification, clearAllNotifications]);

  return (
    <div
      aria-live="assertive"
      className="fixed inset-0 flex items-end justify-center px-4 py-6 pointer-events-none sm:p-6 sm:items-start sm:justify-end z-50"
    >
      <div className="w-full flex flex-col items-center space-y-4 sm:items-end">
        {notifications.map(notification => (
          <NotificationItem
            key={notification.id}
            notification={notification}
            onDismiss={removeNotification}
          />
        ))}
      </div>
    </div>
  );
};

// Hook for using notifications
export const useNotifications = () => {
  const showNotification = useCallback((notification: Omit<Notification, 'id'>) => {
    if ((window as any).showNotification) {
      return (window as any).showNotification(notification);
    }
  }, []);

  const showSuccess = useCallback((title: string, message: string, actions?: Notification['actions']) => {
    return showNotification({
      title,
      message,
      type: 'success',
      actions
    });
  }, [showNotification]);

  const showError = useCallback((title: string, message: string, actions?: Notification['actions']) => {
    return showNotification({
      title,
      message,
      type: 'error',
      persistent: true,
      actions
    });
  }, [showNotification]);

  const showWarning = useCallback((title: string, message: string, actions?: Notification['actions']) => {
    return showNotification({
      title,
      message,
      type: 'warning',
      actions
    });
  }, [showNotification]);

  const showInfo = useCallback((title: string, message: string, actions?: Notification['actions']) => {
    return showNotification({
      title,
      message,
      type: 'info',
      actions
    });
  }, [showNotification]);

  const clearAll = useCallback(() => {
    if ((window as any).clearNotifications) {
      (window as any).clearNotifications();
    }
  }, []);

  return {
    showNotification,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    clearAll
  };
};

// Utility functions for common notification patterns
export const notificationUtils = {
  showApiError: (error: any) => {
    // This will be handled automatically by the error handler
    errorHandler.handleApiError(error);
  },

  showValidationError: (field: string, message: string) => {
    errorHandler.handleValidationError(field, message);
  },

  showSuccess: (message: string, title: string = 'Success') => {
    errorHandler.handleSuccess(message, title);
  },

  showScanProgress: (progress: number, currentRepo: string) => {
    if ((window as any).showNotification) {
      (window as any).showNotification({
        title: 'Scanning Repository',
        message: `${progress}% complete - ${currentRepo}`,
        type: 'info',
        duration: 2000
      });
    }
  },

  showScanComplete: (repositoryCount: number) => {
    if ((window as any).showNotification) {
      (window as any).showNotification({
        title: 'Scan Complete',
        message: `Successfully analyzed ${repositoryCount} repositories`,
        type: 'success',
        actions: [
          {
            label: 'View Results',
            action: () => window.location.href = '/dashboard',
            primary: true
          }
        ]
      });
    }
  }
};