import React from 'react';
import { motion } from 'framer-motion';
import '../styles/rankings.css';

interface ResponsiveRankingWrapperProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Responsive wrapper component for ranking interfaces
 * Provides consistent spacing, animations, and responsive behavior
 */
const ResponsiveRankingWrapper: React.FC<ResponsiveRankingWrapperProps> = ({ 
  children, 
  className = '' 
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={`rankings-container ${className}`}
    >
      <div className="space-y-6 sm:space-y-8">
        {children}
      </div>
    </motion.div>
  );
};

/**
 * Responsive grid component for ranking cards
 */
export const RankingGrid: React.FC<{ children: React.ReactNode; className?: string }> = ({ 
  children, 
  className = '' 
}) => {
  return (
    <div className={`rankings-grid ${className}`}>
      {children}
    </div>
  );
};

/**
 * Responsive card component with consistent styling
 */
export const RankingCard: React.FC<{ 
  children: React.ReactNode; 
  className?: string;
  delay?: number;
}> = ({ children, className = '', delay = 0 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className={`comparison-card ${className}`}
    >
      {children}
    </motion.div>
  );
};

/**
 * Responsive section header component
 */
export const SectionHeader: React.FC<{
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}> = ({ title, subtitle, icon, action }) => {
  return (
    <div className="statistics-header">
      <div>
        <h2 className="statistics-title">
          {icon}
          <span>{title}</span>
        </h2>
        {subtitle && (
          <p className="text-sm sm:text-base text-gray-600 mt-2">{subtitle}</p>
        )}
      </div>
      {action && (
        <div className="flex-shrink-0">
          {action}
        </div>
      )}
    </div>
  );
};

/**
 * Responsive stats grid component
 */
export const StatsGrid: React.FC<{ 
  children: React.ReactNode; 
  columns?: 2 | 3 | 4;
  className?: string;
}> = ({ children, columns = 4, className = '' }) => {
  const gridClass = columns === 2 ? 'grid-cols-2' : 
                   columns === 3 ? 'grid-cols-1 sm:grid-cols-3' :
                   'grid-cols-2 lg:grid-cols-4';
  
  return (
    <div className={`grid ${gridClass} gap-3 sm:gap-4 ${className}`}>
      {children}
    </div>
  );
};

/**
 * Responsive stat card component
 */
export const StatCard: React.FC<{
  value: string | number;
  label: string;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  icon?: React.ReactNode;
}> = ({ value, label, color = 'primary', icon }) => {
  const colorClasses = {
    primary: 'text-primary-600',
    secondary: 'text-secondary-600', 
    success: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600'
  };

  return (
    <div className="quick-stat-card">
      {icon && (
        <div className={`${colorClasses[color]} mb-2 flex justify-center`}>
          {icon}
        </div>
      )}
      <div className={`quick-stat-value ${colorClasses[color]}`}>
        {value}
      </div>
      <div className="quick-stat-label">{label}</div>
    </div>
  );
};

/**
 * Responsive loading skeleton component
 */
export const LoadingSkeleton: React.FC<{ 
  type?: 'card' | 'list' | 'stats';
  count?: number;
}> = ({ type = 'card', count = 2 }) => {
  if (type === 'stats') {
    return (
      <StatsGrid>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="quick-stat-card">
            <div className="skeleton-text h-6 w-16 mx-auto mb-2" />
            <div className="skeleton-text h-4 w-12 mx-auto" />
          </div>
        ))}
      </StatsGrid>
    );
  }

  if (type === 'list') {
    return (
      <div className="space-y-3">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="flex items-center space-x-4 p-4 border border-gray-200 rounded-lg">
            <div className="skeleton-circle w-10 h-10" />
            <div className="flex-1 space-y-2">
              <div className="skeleton-text w-3/4" />
              <div className="skeleton-text w-1/2" />
            </div>
            <div className="skeleton-text w-16 h-6" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <RankingGrid>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="comparison-card">
          <div className="comparison-card-header">
            <div className="skeleton-circle w-12 h-12" />
            <div className="flex-1 space-y-2">
              <div className="skeleton-text w-3/4" />
              <div className="skeleton-text w-1/2" />
            </div>
          </div>
          <div className="space-y-3">
            <div className="skeleton-text h-8 w-full" />
            <div className="skeleton-text w-2/3" />
          </div>
        </div>
      ))}
    </RankingGrid>
  );
};

/**
 * Responsive error component
 */
export const ErrorDisplay: React.FC<{
  title: string;
  message: string;
  onRetry?: () => void;
  icon?: React.ReactNode;
}> = ({ title, message, onRetry, icon }) => {
  return (
    <div className="error-container">
      <div className="error-icon">
        {icon}
      </div>
      <h3 className="error-title">{title}</h3>
      <p className="error-message mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors text-sm sm:text-base"
        >
          Try Again
        </button>
      )}
    </div>
  );
};

/**
 * Responsive success component
 */
export const SuccessDisplay: React.FC<{
  title: string;
  message: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}> = ({ title, message, action, icon }) => {
  return (
    <div className="success-container">
      <div className="success-icon">
        {icon}
      </div>
      <h3 className="success-title">{title}</h3>
      <p className="success-message mb-4">{message}</p>
      {action && action}
    </div>
  );
};

export default ResponsiveRankingWrapper;