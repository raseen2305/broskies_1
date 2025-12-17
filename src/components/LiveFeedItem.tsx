import React from 'react';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertCircle,
  GitBranch,
  GitPullRequest,
  FileCode,
  Calculator,
  User,
  Folder
} from 'lucide-react';

export interface LiveFeedItemData {
  id: string;
  timestamp: Date;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  description: string;
  metadata?: {
    repoName?: string;
    fileName?: string;
    count?: number;
    duration?: number;
  };
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
}

interface LiveFeedItemProps {
  item: LiveFeedItemData;
  onClick?: (item: LiveFeedItemData) => void;
  isNew?: boolean;
}

const LiveFeedItem: React.FC<LiveFeedItemProps> = ({ item, onClick, isNew = false }) => {
  // Get icon based on item type and status
  const getIcon = () => {
    if (item.status === 'completed') {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    }
    if (item.status === 'failed') {
      return <XCircle className="w-5 h-5 text-red-500" />;
    }
    if (item.status === 'in_progress') {
      return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
    }
    
    // Default icons based on description content
    if (item.description.includes('repository') || item.description.includes('repo')) {
      return <Folder className="w-5 h-5 text-purple-500" />;
    }
    if (item.description.includes('pull request') || item.description.includes('PR')) {
      return <GitPullRequest className="w-5 h-5 text-indigo-500" />;
    }
    if (item.description.includes('file') || item.description.includes('analyzing')) {
      return <FileCode className="w-5 h-5 text-cyan-500" />;
    }
    if (item.description.includes('score') || item.description.includes('calculating')) {
      return <Calculator className="w-5 h-5 text-orange-500" />;
    }
    if (item.description.includes('account') || item.description.includes('profile')) {
      return <User className="w-5 h-5 text-pink-500" />;
    }
    
    return <AlertCircle className="w-5 h-5 text-gray-500" />;
  };

  // Get background color based on type
  const getBackgroundColor = () => {
    switch (item.type) {
      case 'success':
        return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
      case 'error':
        return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
      default:
        return 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700';
    }
  };

  // Format timestamp
  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return date.toLocaleTimeString();
  };

  return (
    <div
      className={`
        relative p-3 rounded-lg border transition-all duration-300 cursor-pointer
        ${getBackgroundColor()}
        ${isNew ? 'animate-slideIn' : ''}
        hover:shadow-md hover:scale-[1.02]
      `}
      onClick={() => onClick?.(item)}
    >
      {/* New indicator */}
      {isNew && (
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
      )}
      
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 mt-0.5">
          {getIcon()}
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title and timestamp */}
          <div className="flex items-start justify-between gap-2 mb-1">
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
              {item.title}
            </h4>
            <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
              {formatTime(item.timestamp)}
            </span>
          </div>
          
          {/* Description */}
          <p className="text-xs text-gray-600 dark:text-gray-300 line-clamp-2">
            {item.description}
          </p>
          
          {/* Metadata */}
          {item.metadata && (
            <div className="flex flex-wrap gap-2 mt-2">
              {item.metadata.repoName && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs text-gray-700 dark:text-gray-300">
                  <GitBranch className="w-3 h-3" />
                  {item.metadata.repoName}
                </span>
              )}
              {item.metadata.fileName && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs text-gray-700 dark:text-gray-300">
                  <FileCode className="w-3 h-3" />
                  {item.metadata.fileName}
                </span>
              )}
              {item.metadata.count !== undefined && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 rounded text-xs text-blue-700 dark:text-blue-300">
                  {item.metadata.count} items
                </span>
              )}
              {item.metadata.duration !== undefined && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 rounded text-xs text-purple-700 dark:text-purple-300">
                  {item.metadata.duration}ms
                </span>
              )}
            </div>
          )}
        </div>
      </div>
      
      {/* Status indicator bar */}
      {item.status === 'in_progress' && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gray-200 dark:bg-gray-700 overflow-hidden rounded-b-lg">
          <div className="h-full bg-blue-500 animate-progress" />
        </div>
      )}
    </div>
  );
};

export default LiveFeedItem;
