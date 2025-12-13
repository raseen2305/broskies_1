import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

interface FloatingAction {
  icon: LucideIcon;
  label: string;
  onClick: () => void;
  color?: string;
}

interface FloatingActionButtonProps {
  mainIcon: LucideIcon;
  actions?: FloatingAction[];
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  size?: 'sm' | 'md' | 'lg';
  color?: string;
}

const FloatingActionButton: React.FC<FloatingActionButtonProps> = ({
  mainIcon: MainIcon,
  actions = [],
  position = 'bottom-right',
  size = 'md',
  color = 'bg-primary-500'
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const positionClasses = {
    'bottom-right': 'bottom-6 right-6',
    'bottom-left': 'bottom-6 left-6',
    'top-right': 'top-6 right-6',
    'top-left': 'top-6 left-6'
  };

  const sizeClasses = {
    sm: 'w-12 h-12',
    md: 'w-14 h-14',
    lg: 'w-16 h-16'
  };

  const iconSizes = {
    sm: 'h-5 w-5',
    md: 'h-6 w-6',
    lg: 'h-7 w-7'
  };

  return (
    <div className={`fixed ${positionClasses[position]} z-50`}>
      {/* Action Items */}
      <AnimatePresence>
        {isOpen && actions.length > 0 && (
          <motion.div
            className="absolute bottom-16 right-0 flex flex-col-reverse space-y-reverse space-y-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {actions.map((action, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20, scale: 0 }}
                animate={{ 
                  opacity: 1, 
                  y: 0, 
                  scale: 1,
                  transition: { delay: index * 0.05 }
                }}
                exit={{ 
                  opacity: 0, 
                  y: 20, 
                  scale: 0,
                  transition: { delay: (actions.length - index) * 0.05 }
                }}
                className="flex items-center space-x-3"
              >
                {/* Label */}
                <motion.div
                  className="bg-gray-900 text-white px-3 py-2 rounded-lg text-sm font-medium shadow-lg whitespace-nowrap"
                  whileHover={{ scale: 1.05, x: -2 }}
                >
                  {action.label}
                </motion.div>

                {/* Action Button */}
                <motion.button
                  onClick={() => {
                    action.onClick();
                    setIsOpen(false);
                  }}
                  className={`${sizeClasses[size]} ${action.color || 'bg-gray-700'} text-white rounded-full shadow-lg flex items-center justify-center`}
                  whileHover={{ 
                    scale: 1.1,
                    rotate: 360,
                    transition: { duration: 0.3 }
                  }}
                  whileTap={{ scale: 0.9 }}
                >
                  <action.icon className={iconSizes[size]} />
                </motion.button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main FAB */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className={`${sizeClasses[size]} ${color} text-white rounded-full shadow-2xl flex items-center justify-center relative overflow-hidden`}
        whileHover={{ 
          scale: 1.1,
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)',
          transition: { duration: 0.2 }
        }}
        whileTap={{ scale: 0.9 }}
        animate={{
          rotate: isOpen ? 45 : 0,
          transition: { duration: 0.3 }
        }}
      >
        {/* Ripple Effect */}
        <motion.div
          className="absolute inset-0 bg-white rounded-full"
          initial={{ scale: 0, opacity: 0.5 }}
          animate={{
            scale: isOpen ? [0, 2] : 0,
            opacity: isOpen ? [0.5, 0] : 0
          }}
          transition={{ duration: 0.6 }}
        />

        {/* Pulse Animation */}
        <motion.div
          className={`absolute inset-0 ${color} rounded-full`}
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.5, 0, 0.5]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            repeatType: 'loop'
          }}
        />

        {/* Icon */}
        <MainIcon className={`${iconSizes[size]} relative z-10`} />
      </motion.button>

      {/* Backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed inset-0 bg-black/20 backdrop-blur-sm -z-10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default FloatingActionButton;
