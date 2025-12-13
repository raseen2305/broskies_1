import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Loader2, 
  CheckCircle, 
  AlertCircle, 
  Github, 
  Database, 
  Brain, 
  Zap,
  User,
  GitBranch,
  Code,
  BarChart3
} from 'lucide-react';

interface StatusMessage {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: Date;
  details?: string;
}

interface RealTimeStatusDisplayProps {
  currentPhase: string;
  currentRepository?: string;
  repositoriesProcessed: number;
  totalRepositories: number;
  statusMessages: StatusMessage[];
  isConnected: boolean;
  className?: string;
}

const phaseIcons = {
  connecting: Github,
  profile: User,
  repositories: GitBranch,
  analysis: Code,
  insights: Brain,
  completed: CheckCircle
};

const phaseDescriptions = {
  connecting: 'Establishing secure connection to GitHub API',
  profile: 'Analyzing user profile and basic information',
  repositories: 'Discovering and cataloging repositories',
  analysis: 'Performing deep code analysis with AI and ACID scoring',
  insights: 'Generating personalized insights and recommendations',
  completed: 'Analysis complete - preparing results'
};

export const RealTimeStatusDisplay: React.FC<RealTimeStatusDisplayProps> = ({
  currentPhase,
  currentRepository,
  repositoriesProcessed,
  totalRepositories,
  statusMessages,
  isConnected,
  className = ''
}) => {
  const PhaseIcon = phaseIcons[currentPhase as keyof typeof phaseIcons] || Loader2;
  const phaseDescription = phaseDescriptions[currentPhase as keyof typeof phaseDescriptions] || 'Processing...';

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'success': return CheckCircle;
      case 'warning': return AlertCircle;
      case 'error': return AlertCircle;
      default: return Loader2;
    }
  };

  const getMessageColor = (type: string) => {
    switch (type) {
      case 'success': return 'text-green-600 bg-green-50 border-green-200';
      case 'warning': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Connection Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Real-time updates active' : 'Connection lost'}
          </span>
        </div>
        {!isConnected && (
          <motion.div
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="text-sm text-yellow-600"
          >
            Reconnecting...
          </motion.div>
        )}
      </div>

      {/* Current Phase Status */}
      <motion.div
        key={currentPhase}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl border border-gray-200 p-6"
      >
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
              <PhaseIcon className="h-6 w-6 text-primary-600" />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 capitalize mb-2">
              {currentPhase.replace('_', ' ')} Phase
            </h3>
            <p className="text-gray-600 mb-4">{phaseDescription}</p>
            
            {/* Repository Progress */}
            {totalRepositories > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Repository Progress</span>
                  <span className="font-medium text-gray-900">
                    {repositoriesProcessed} / {totalRepositories}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <motion.div
                    className="h-2 bg-primary-500 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${(repositoriesProcessed / totalRepositories) * 100}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
                {currentRepository && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-sm text-gray-500"
                  >
                    Currently analyzing: <span className="font-medium">{currentRepository}</span>
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Real-time Status Messages */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-gray-900">Live Updates</h4>
        <div className="max-h-64 overflow-y-auto space-y-2">
          <AnimatePresence>
            {statusMessages.slice(-5).reverse().map((message) => {
              const MessageIcon = getMessageIcon(message.type);
              const colorClasses = getMessageColor(message.type);
              
              return (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className={`flex items-start space-x-3 p-3 rounded-lg border ${colorClasses}`}
                >
                  <MessageIcon className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{message.message}</p>
                    {message.details && (
                      <p className="text-xs opacity-75 mt-1">{message.details}</p>
                    )}
                    <p className="text-xs opacity-60 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};