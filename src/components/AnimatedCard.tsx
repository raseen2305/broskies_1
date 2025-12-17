import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface AnimatedCardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
  animationType?: 'lift' | 'tilt' | 'glow' | 'scale' | 'border';
  delay?: number;
}

const AnimatedCard: React.FC<AnimatedCardProps> = ({
  children,
  className = '',
  onClick,
  hoverable = true,
  animationType = 'lift',
  delay = 0
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const getAnimationProps = () => {
    if (!hoverable) return {};

    switch (animationType) {
      case 'lift':
        return {
          whileHover: { 
            y: -8, 
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
            transition: { duration: 0.3 }
          },
          whileTap: onClick ? { scale: 0.98 } : {}
        };
      
      case 'tilt':
        return {
          whileHover: {
            rotateX: 5,
            rotateY: 5,
            scale: 1.02,
            transition: { duration: 0.3 }
          },
          whileTap: onClick ? { scale: 0.98 } : {}
        };
      
      case 'glow':
        return {
          whileHover: {
            boxShadow: '0 0 30px rgba(59, 130, 246, 0.3)',
            borderColor: 'rgba(59, 130, 246, 0.5)',
            transition: { duration: 0.3 }
          },
          whileTap: onClick ? { scale: 0.98 } : {}
        };
      
      case 'scale':
        return {
          whileHover: { 
            scale: 1.03,
            transition: { duration: 0.3 }
          },
          whileTap: onClick ? { scale: 0.97 } : {}
        };
      
      case 'border':
        return {
          whileHover: {
            borderWidth: '2px',
            borderColor: 'rgba(59, 130, 246, 0.5)',
            transition: { duration: 0.3 }
          },
          whileTap: onClick ? { scale: 0.98 } : {}
        };
      
      default:
        return {};
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={onClick}
      className={`
        bg-white rounded-xl shadow-lg border border-gray-100 
        transition-all duration-300 relative overflow-hidden
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
      style={{ transformStyle: 'preserve-3d' }}
      {...getAnimationProps()}
    >
      {/* Gradient Overlay on Hover */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-br from-primary-500/5 via-transparent to-secondary-500/5 pointer-events-none"
        initial={{ opacity: 0 }}
        animate={{ opacity: isHovered ? 1 : 0 }}
        transition={{ duration: 0.3 }}
      />

      {/* Animated Border Glow */}
      {animationType === 'glow' && (
        <motion.div
          className="absolute -inset-1 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-xl blur opacity-0"
          animate={{ opacity: isHovered ? 0.3 : 0 }}
          transition={{ duration: 0.3 }}
          style={{ zIndex: -1 }}
        />
      )}

      {/* Shine Effect */}
      {isHovered && animationType === 'lift' && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
          initial={{ x: '-100%', skewX: -15 }}
          animate={{ x: '100%' }}
          transition={{ duration: 0.8, ease: 'easeInOut' }}
        />
      )}

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </motion.div>
  );
};

export default AnimatedCard;
