import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useHRAuth } from '../contexts/HRAuthContext';
import { motion } from 'framer-motion';

interface HRProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * HRProtectedRoute Component
 * 
 * A route wrapper that ensures only authenticated HR users can access protected pages.
 * 
 * Features:
 * - Checks authentication status from HRAuthContext
 * - Shows loading spinner while verifying authentication
 * - Redirects to /hr/auth if not authenticated
 * - Preserves the intended destination URL for post-login redirect
 * - Renders children if authenticated
 * 
 * @example
 * ```tsx
 * <Route 
 *   path="/hr/dashboard" 
 *   element={
 *     <HRProtectedRoute>
 *       <HRDashboard />
 *     </HRProtectedRoute>
 *   } 
 * />
 * ```
 */
const HRProtectedRoute: React.FC<HRProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading, hrUser } = useHRAuth();
  const location = useLocation();

  useEffect(() => {
    // Log authentication check for debugging
    if (import.meta.env.DEV) {
      console.log('HRProtectedRoute check:', {
        isAuthenticated,
        isLoading,
        hasUser: !!hrUser,
        path: location.pathname,
      });
    }
  }, [isAuthenticated, isLoading, hrUser, location.pathname]);

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <motion.div
            className="inline-block"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          >
            <svg
              className="w-12 h-12 text-primary-600"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </motion.div>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="mt-4 text-gray-600 font-medium"
          >
            Verifying authentication...
          </motion.p>
        </motion.div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    // Save the intended destination for redirect after login
    const redirectPath = location.pathname + location.search;
    
    return (
      <Navigate 
        to="/hr/auth" 
        state={{ from: redirectPath }} 
        replace 
      />
    );
  }

  // Render protected content if authenticated
  return <>{children}</>;
};

export default HRProtectedRoute;
