import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Pause, Play, ChevronDown, ChevronUp, X } from 'lucide-react';
import LiveFeedItem, { LiveFeedItemData } from './LiveFeedItem';

interface LiveFeedPanelProps {
  items: LiveFeedItemData[];
  maxItems?: number;
  autoScroll?: boolean;
  onItemClick?: (item: LiveFeedItemData) => void;
  isPaused?: boolean;
  onPauseToggle?: () => void;
  className?: string;
}

const LiveFeedPanel: React.FC<LiveFeedPanelProps> = ({
  items,
  maxItems = 50,
  autoScroll = true,
  onItemClick,
  isPaused = false,
  onPauseToggle,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = useState(autoScroll);
  const [newItemIds, setNewItemIds] = useState<Set<string>>(new Set());
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const previousItemsLengthRef = useRef(items.length);

  // Limit items to maxItems
  const displayedItems = items.slice(-maxItems);

  // Track new items for animation
  useEffect(() => {
    if (items.length > previousItemsLengthRef.current) {
      const newItems = items.slice(previousItemsLengthRef.current);
      const newIds = new Set(newItems.map(item => item.id));
      setNewItemIds(newIds);
      
      // Remove new indicator after animation
      setTimeout(() => {
        setNewItemIds(new Set());
      }, 2000);
    }
    previousItemsLengthRef.current = items.length;
  }, [items]);

  // Auto-scroll to bottom when new items arrive
  useEffect(() => {
    if (isAutoScrollEnabled && !isPaused && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [items, isAutoScrollEnabled, isPaused]);

  // Handle manual scroll - disable auto-scroll if user scrolls up
  const handleScroll = useCallback(() => {
    if (!scrollContainerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    
    if (!isAtBottom && isAutoScrollEnabled) {
      setIsAutoScrollEnabled(false);
    } else if (isAtBottom && !isAutoScrollEnabled) {
      setIsAutoScrollEnabled(true);
    }
  }, [isAutoScrollEnabled]);

  // Scroll to bottom manually
  const scrollToBottom = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
      setIsAutoScrollEnabled(true);
    }
  };

  return (
    <div className={`flex flex-col bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Live Feed
          </h3>
          <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-medium rounded-full">
            {items.length} events
          </span>
          {!isAutoScrollEnabled && (
            <button
              onClick={scrollToBottom}
              className="px-2 py-1 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-xs font-medium rounded transition-colors"
              title="Scroll to bottom"
            >
              <ChevronDown className="w-4 h-4" />
            </button>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* Pause/Resume button */}
          {onPauseToggle && (
            <button
              onClick={onPauseToggle}
              className={`
                p-2 rounded-lg transition-all duration-200
                ${isPaused 
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-900/50' 
                  : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50'
                }
              `}
              title={isPaused ? 'Resume updates' : 'Pause updates'}
            >
              {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
            </button>
          )}
          
          {/* Expand/Collapse button */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 transition-colors"
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>
      
      {/* Feed content */}
      {isExpanded && (
        <>
          {/* Status indicators */}
          <div className="flex items-center gap-4 px-4 py-2 bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isPaused ? 'bg-yellow-500' : 'bg-green-500 animate-pulse'}`} />
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {isPaused ? 'Paused' : 'Live'}
              </span>
            </div>
            {!isAutoScrollEnabled && (
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-orange-500" />
                <span className="text-xs text-gray-600 dark:text-gray-400">
                  Auto-scroll disabled
                </span>
              </div>
            )}
          </div>
          
          {/* Scrollable feed */}
          <div
            ref={scrollContainerRef}
            onScroll={handleScroll}
            className="flex-1 overflow-y-auto p-4 space-y-2 max-h-[500px] min-h-[200px]"
            style={{
              scrollBehavior: isAutoScrollEnabled ? 'smooth' : 'auto'
            }}
          >
            {displayedItems.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mb-4">
                  <Play className="w-8 h-8 text-gray-400 dark:text-gray-500" />
                </div>
                <p className="text-gray-500 dark:text-gray-400 text-sm">
                  Waiting for scan events...
                </p>
                <p className="text-gray-400 dark:text-gray-500 text-xs mt-1">
                  Events will appear here as the scan progresses
                </p>
              </div>
            ) : (
              displayedItems.map((item) => (
                <LiveFeedItem
                  key={item.id}
                  item={item}
                  onClick={onItemClick}
                  isNew={newItemIds.has(item.id)}
                />
              ))
            )}
          </div>
          
          {/* Footer with stats */}
          <div className="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-600 dark:text-gray-400">
            <span>
              Showing {displayedItems.length} of {items.length} events
            </span>
            {items.length > maxItems && (
              <span className="text-orange-600 dark:text-orange-400">
                Oldest events hidden
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default LiveFeedPanel;
