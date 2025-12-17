import React from 'react';
import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

interface AnimatedButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  icon?: LucideIcon;
  iconPosition?: 'left' | 'right';
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
  fullWidth?: boolean;
  animationType?: 'lift' | 'scale' | 'glow' | 'shine' | 'ripple';
}

const AnimatedButton: React.FC<AnimatedButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  icon: Icon,
  iconPosition = 'left',
  disabled = false,
  loading = false,
  className = '',
  type = 'button',
  fullWidth = false,
  animationType = 'lift'
}) => {
  const baseClasses = 'font-medium rounded-lg transition-all duration-200 relative overflow-hidden inline-flex items-center justify-center';
  
  const variantClasses = {
    primary: 'bg-primary-500 hover:bg-primary-600 active:bg-primary-700 text-white shadow-sm hover:shadow-md',
    secondary: 'bg-secondary-500 hover:bg-secondary-600 active:bg-secondary-700 text-white shadow-sm hover:shadow-md',
    outline: 'border-2 border-primary-500 text-primary-500 hover:bg-primary-500 hover:text-white',
    ghost: 'text-gray-600 hover:text-primary-500 hover:bg-primary-50',
    danger: 'bg-red-500 hover:bg-red-600 active:bg-red-700 text-white shadow-sm hover:shadow-md',
    success: 'bg-green-500 hover:bg-green-600 active:bg-green-700 text-white shadow-sm hover:shadow-md'
  };

  const sizeClasses = {
    sm: 'py-1.5 px-3 text-sm',
    md: 'py-2.5 px-5 text-base',
    lg: 'py-3 px-6 text-lg'
  };

  const disabledClasses = 'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none';

  const getAnimationProps = () => {
    switch (animationType) {
      case 'lift':
        return {
          whileHover: { y: -2, transition: { duration: 0.2 } },
          whileTap: { y: 0, scale: 0.98 }
        };
      case 'scale':
        return {
          whileHover: { scale: 1.05, transition: { duration: 0.2 } },
          whileTap: { scale: 0.95 }
        };
      case 'glow':
        return {
          whileHover: { 
            boxShadow: '0 0 20px rgba(59, 130, 246, 0.5)',
            transition: { duration: 0.3 }
          },
          whileTap: { scale: 0.98 }
        };
      default:
        return {
          whileHover: { y: -2 },
          whileTap: { scale: 0.98 }
        };
    }
  };

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        ${baseClasses}
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${disabledClasses}
        ${fullWidth ? 'w-full' : ''}
        ${className}
      `}
      {...(disabled || loading ? {} : getAnimationProps())}
    >
      {/* Shine Effect */}
      {animationType === 'shine' && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
          initial={{ x: '-100%', skewX: -15 }}
          whileHover={{ x: '100%', transition: { duration: 0.6 } }}
        />
      )}

      {/* Ripple Effect */}
      {animationType === 'ripple' && (
        <motion.div
          className="absolute inset-0 bg-white/20 rounded-full"
          initial={{ scale: 0, opacity: 0 }}
          whileTap={{ scale: 2, opacity: 1, transition: { duration: 0.4 } }}
        />
      )}

      {/* Loading Spinner */}
      {loading && (
        <motion.div
          className="mr-2"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24">
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
      )}

      {/* Icon Left */}
      {Icon && iconPosition === 'left' && !loading && (
        <motion.div
          className="mr-2"
          whileHover={{ x: -2, transition: { duration: 0.2 } }}
        >
          <Icon className={size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-6 w-6' : 'h-5 w-5'} />
        </motion.div>
      )}

      {/* Button Text */}
      <span className="relative z-10">{children}</span>

      {/* Icon Right */}
      {Icon && iconPosition === 'right' && !loading && (
        <motion.div
          className="ml-2"
          whileHover={{ x: 2, transition: { duration: 0.2 } }}
        >
          <Icon className={size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-6 w-6' : 'h-5 w-5'} />
        </motion.div>
      )}
    </motion.button>
  );
};

export default AnimatedButton;
