import React, { useState } from 'react';
import { RefreshCw } from 'lucide-react';

interface ForceFreshScanButtonProps {
  username: string;
  onScanComplete?: () => void;
}

const ForceFreshScanButton: React.FC<ForceFreshScanButtonProps> = ({ 
  username, 
  onScanComplete 
}) => {
  const [isClearing, setIsClearing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleForceFreshScan = async () => {
    setIsClearing(true);
    setMessage(null);

    try {
      // Step 1: Clear cache
      const token = localStorage.getItem('auth_token');
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      
      const response = await fetch(`${apiUrl}/api/scan/cache/invalidate/${username}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to clear cache');
      }

      setMessage('Cache cleared! Redirecting to rescan...');
      
      // Step 2: Redirect to scan page after a short delay
      setTimeout(() => {
        if (onScanComplete) {
          onScanComplete();
        } else {
          window.location.href = '/developer/auth';
        }
      }, 1500);

    } catch (error) {
      console.error('Error clearing cache:', error);
      setMessage('Failed to clear cache. Please try again.');
      setIsClearing(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        onClick={handleForceFreshScan}
        disabled={isClearing}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
      >
        <RefreshCw className={`w-4 h-4 ${isClearing ? 'animate-spin' : ''}`} />
        {isClearing ? 'Clearing Cache...' : 'Force Fresh Scan'}
      </button>
      
      {message && (
        <p className={`text-sm ${message.includes('Failed') ? 'text-red-600' : 'text-green-600'}`}>
          {message}
        </p>
      )}
      
      <p className="text-xs text-gray-500 text-center max-w-xs">
        This will clear cached data and fetch fresh PR/issue information
      </p>
    </div>
  );
};

export default ForceFreshScanButton;
