import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, XCircle, AlertTriangle, Info, X, RefreshCw } from 'lucide-react';

export type ErrorType = 'error' | 'warning' | 'info' | 'not-approved' | 'network' | 'token-expired';

interface ErrorMessageProps {
  type?: ErrorType;
  title?: string;
  message: string;
  details?: string;
  onClose?: () => void;
  onRetry?: () => void;
  showRetry?: boolean;
  className?: string;
}

/**
 * ErrorMessage Component
 * 
 * A reusable error display component with different styles for various error types.
 * 
 * Features:
 * - Multiple error types (error, warning, info, not-approved, network, token-expired)
 * - Custom titles and messages
 * - Optional details section
 * - Close button
 * - Retry button for network errors
 * - Smooth animations
 * - Accessible
 * 
 * @example
 * ```tsx
 * <ErrorMessage 
 *   type="not-approved"
 *   message="Your account is not approved yet"
 *   details="Please complete the registration form first"
 *   onClose={() => setError(null)}
 * />
 * ```
 */
const ErrorMessage: React.FC<ErrorMessageProps> = ({
  type = 'error',
  title,
  message,
  details,
  onClose,
  onRetry,
  showRetry = false,
  className = '',
}) => {
  /**
   * Get icon based on error type
   */
  const getIcon = () => {
    switch (type) {
      case 'warning':
      case 'not-approved':
        return <AlertTriangle className="h-5 w-5" />;
      case 'info':
        return <Info className="h-5 w-5" />;
      case 'network':
      case 'token-expired':
        return <AlertCircle className="h-5 w-5" />;
      case 'error':
      default:
        return <XCircle className="h-5 w-5" />;
    }
  };

  /**
   * Get colors based on error type
   */
  const getColors = () => {
    switch (type) {
      case 'warning':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          icon: 'text-yellow-600',
          title: 'text-yellow-900',
          text: 'text-yellow-800',
          button: 'text-yellow-600 hover:text-yellow-800',
        };
      case 'info':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          icon: 'text-blue-600',
          title: 'text-blue-900',
          text: 'text-blue-800',
          button: 'text-blue-600 hover:text-blue-800',
        };
      case 'not-approved':
        return {
          bg: 'bg-orange-50',
          border: 'border-orange-200',
          icon: 'text-orange-600',
          title: 'text-orange-900',
          text: 'text-orange-800',
          button: 'text-orange-600 hover:text-orange-800',
        };
      case 'network':
      case 'token-expired':
        return {
          bg: 'bg-purple-50',
          border: 'border-purple-200',
          icon: 'text-purple-600',
          title: 'text-purple-900',
          text: 'text-purple-800',
          button: 'text-purple-600 hover:text-purple-800',
        };
      case 'error':
      default:
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          icon: 'text-red-600',
          title: 'text-red-900',
          text: 'text-red-800',
          button: 'text-red-600 hover:text-red-800',
        };
    }
  };

  /**
   * Get default title based on error type
   */
  const getDefaultTitle = () => {
    switch (type) {
      case 'warning':
        return 'Warning';
      case 'info':
        return 'Information';
      case 'not-approved':
        return 'Account Not Approved';
      case 'network':
        return 'Network Error';
      case 'token-expired':
        return 'Session Expired';
      case 'error':
      default:
        return 'Error';
    }
  };

  const colors = getColors();
  const displayTitle = title || getDefaultTitle();

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.2 }}
        className={`${colors.bg} ${colors.border} border rounded-lg p-4 ${className}`}
        role="alert"
      >
        <div className="flex items-start space-x-3">
          {/* Icon */}
          <div className={`flex-shrink-0 ${colors.icon} mt-0.5`}>
            {getIcon()}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Title */}
            <h3 className={`text-sm font-semibold ${colors.title} mb-1`}>
              {displayTitle}
            </h3>

            {/* Message */}
            <p className={`text-sm ${colors.text}`}>
              {message}
            </p>

            {/* Details */}
            {details && (
              <p className={`text-xs ${colors.text} mt-2 opacity-90`}>
                {details}
              </p>
            )}

            {/* Retry Button */}
            {(showRetry || onRetry) && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onRetry}
                className={`mt-3 flex items-center space-x-2 text-sm font-medium ${colors.button} transition-colors`}
              >
                <RefreshCw className="h-4 w-4" />
                <span>Try Again</span>
              </motion.button>
            )}
          </div>

          {/* Close Button */}
          {onClose && (
            <button
              onClick={onClose}
              className={`flex-shrink-0 ${colors.button} transition-colors`}
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default ErrorMessage;
