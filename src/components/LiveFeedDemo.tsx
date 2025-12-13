import React, { useState, useEffect } from 'react';
import LiveFeedPanel from './LiveFeedPanel';
import { LiveFeedItemData } from './LiveFeedItem';

/**
 * Demo component to test Live Feed functionality
 * This can be used for development and testing
 */
const LiveFeedDemo: React.FC = () => {
  const [items, setItems] = useState<LiveFeedItemData[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  // Simulate scan events
  useEffect(() => {
    if (!isRunning || isPaused) return;

    const simulateEvents = () => {
      const eventTypes = [
        {
          type: 'info' as const,
          title: 'Fetching repository',
          description: 'Fetching repository data from GitHub API',
          metadata: { repoName: 'user/awesome-project', count: 1 },
          status: 'in_progress' as const
        },
        {
          type: 'success' as const,
          title: 'Repository fetched',
          description: 'Successfully fetched repository metadata',
          metadata: { repoName: 'user/awesome-project', duration: 234 },
          status: 'completed' as const
        },
        {
          type: 'info' as const,
          title: 'Analyzing file',
          description: 'Analyzing source code for quality metrics',
          metadata: { fileName: 'src/main.ts', count: 15 },
          status: 'in_progress' as const
        },
        {
          type: 'success' as const,
          title: 'File analyzed',
          description: 'Completed code analysis with 95% quality score',
          metadata: { fileName: 'src/main.ts', duration: 156 },
          status: 'completed' as const
        },
        {
          type: 'info' as const,
          title: 'Fetching pull requests',
          description: 'Retrieving PR data for repository',
          metadata: { repoName: 'user/awesome-project', count: 23 },
          status: 'in_progress' as const
        },
        {
          type: 'success' as const,
          title: 'Pull requests fetched',
          description: 'Found 23 PRs (15 open, 8 merged)',
          metadata: { repoName: 'user/awesome-project', count: 23, duration: 189 },
          status: 'completed' as const
        },
        {
          type: 'warning' as const,
          title: 'Rate limit warning',
          description: 'Approaching GitHub API rate limit (100 calls remaining)',
          metadata: { count: 100 },
          status: 'completed' as const
        },
        {
          type: 'info' as const,
          title: 'Calculating scores',
          description: 'Computing ACID scores for repository',
          metadata: { repoName: 'user/awesome-project' },
          status: 'in_progress' as const
        },
        {
          type: 'success' as const,
          title: 'Scores calculated',
          description: 'Overall score: 87/100 (Excellent)',
          metadata: { repoName: 'user/awesome-project', duration: 45 },
          status: 'completed' as const
        },
        {
          type: 'error' as const,
          title: 'Failed to fetch issues',
          description: 'Repository not found or access denied',
          metadata: { repoName: 'user/private-repo' },
          status: 'failed' as const
        }
      ];

      const randomEvent = eventTypes[Math.floor(Math.random() * eventTypes.length)];
      
      const newItem: LiveFeedItemData = {
        id: `event-${Date.now()}-${Math.random()}`,
        timestamp: new Date(),
        ...randomEvent
      };

      setItems(prev => [...prev, newItem]);
    };

    const interval = setInterval(simulateEvents, 1500);
    return () => clearInterval(interval);
  }, [isRunning, isPaused]);

  const handleItemClick = (item: LiveFeedItemData) => {
    console.log('Clicked item:', item);
    alert(`Clicked: ${item.title}\n${item.description}`);
  };

  const handlePauseToggle = () => {
    setIsPaused(!isPaused);
  };

  const handleStart = () => {
    setIsRunning(true);
    setItems([]);
  };

  const handleStop = () => {
    setIsRunning(false);
  };

  const handleClear = () => {
    setItems([]);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Live Feed Component Demo
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Test the Live Feed component with simulated scan events
          </p>
          
          {/* Controls */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleStart}
              disabled={isRunning}
              className="px-4 py-2 bg-green-500 hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
            >
              Start Simulation
            </button>
            <button
              onClick={handleStop}
              disabled={!isRunning}
              className="px-4 py-2 bg-red-500 hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
            >
              Stop Simulation
            </button>
            <button
              onClick={handleClear}
              className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              Clear Events
            </button>
            <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Status:
              </span>
              <span className={`text-sm font-medium ${isRunning ? 'text-green-600 dark:text-green-400' : 'text-gray-600 dark:text-gray-400'}`}>
                {isRunning ? (isPaused ? 'Paused' : 'Running') : 'Stopped'}
              </span>
            </div>
          </div>
        </div>

        {/* Live Feed */}
        <LiveFeedPanel
          items={items}
          maxItems={50}
          autoScroll={true}
          onItemClick={handleItemClick}
          isPaused={isPaused}
          onPauseToggle={handlePauseToggle}
        />

        {/* Stats */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Statistics
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {items.length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Total Events
              </div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                {items.filter(i => i.type === 'success').length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Success
              </div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600 dark:text-red-400">
                {items.filter(i => i.type === 'error').length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Errors
              </div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600 dark:text-yellow-400">
                {items.filter(i => i.type === 'warning').length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Warnings
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveFeedDemo;
