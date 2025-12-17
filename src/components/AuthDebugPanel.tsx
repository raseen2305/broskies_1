/**
 * Authentication Debug Panel
 * 
 * Shows current authentication status and provides tools to fix auth issues
 * For development/testing only
 */

import React, { useState, useEffect } from 'react';
import { getAuthStatus, createTestAuthToken, clearTestAuth } from '../utils/testAuth';

interface AuthDebugPanelProps {
  onAuthChange?: () => void;
}

const AuthDebugPanel: React.FC<AuthDebugPanelProps> = ({ onAuthChange }) => {
  const [authStatus, setAuthStatus] = useState(getAuthStatus());
  const [isVisible, setIsVisible] = useState(false);
  const [userId, setUserId] = useState('thoshifraseen4');  // Correct user_id from database
  const [username, setUsername] = useState('raseen2305');
  const [debugData, setDebugData] = useState<any>(null);
  const [isDebugging, setIsDebugging] = useState(false);

  useEffect(() => {
    // Update auth status periodically
    const interval = setInterval(() => {
      setAuthStatus(getAuthStatus());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const handleCreateTestAuth = () => {
    createTestAuthToken(userId, username);
    setAuthStatus(getAuthStatus());
    onAuthChange?.();
    
    // Refresh the page to apply authentication
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  };

  const handleClearAuth = () => {
    clearTestAuth();
    setAuthStatus(getAuthStatus());
    onAuthChange?.();
  };

  const handleDebugUserData = async () => {
    if (!authStatus.hasToken) {
      alert('Please create an auth token first');
      return;
    }

    setIsDebugging(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('http://localhost:8000/debug/rankings/user-data', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDebugData(data);
      } else {
        const error = await response.json();
        alert(`Debug failed: ${error.detail}`);
      }
    } catch (error) {
      alert(`Debug error: ${error}`);
    } finally {
      setIsDebugging(false);
    }
  };

  const handleFixDataLinking = async () => {
    if (!authStatus.hasToken) {
      alert('Please create an auth token first');
      return;
    }

    setIsDebugging(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('http://localhost:8000/debug/rankings/fix-data-linking', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Fix applied! Fixes: ${result.fixes_applied.join(', ')}`);
        // Refresh the page to see changes
        setTimeout(() => window.location.reload(), 1000);
      } else {
        const error = await response.json();
        alert(`Fix failed: ${error.detail}`);
      }
    } catch (error) {
      alert(`Fix error: ${error}`);
    } finally {
      setIsDebugging(false);
    }
  };

  // Only show in development
  if (import.meta.env.PROD) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Toggle Button */}
      <button
        onClick={() => setIsVisible(!isVisible)}
        className={`mb-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
          authStatus.hasToken 
            ? 'bg-green-100 text-green-800 border border-green-300' 
            : 'bg-red-100 text-red-800 border border-red-300'
        }`}
      >
        🔐 Auth: {authStatus.hasToken ? '✅' : '❌'}
      </button>

      {/* Debug Panel */}
      {isVisible && (
        <div className="bg-white border border-gray-300 rounded-lg shadow-lg p-4 w-80 max-h-96 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900">Auth Debug</h3>
            <button
              onClick={() => setIsVisible(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          {/* Current Status */}
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Current Status</h4>
            <div className="space-y-1 text-sm">
              <div>Has Token: <span className={authStatus.hasToken ? 'text-green-600' : 'text-red-600'}>
                {authStatus.hasToken ? 'Yes' : 'No'}
              </span></div>
              <div>Token Type: <span className="text-gray-600">{authStatus.tokenType || 'None'}</span></div>
              <div>User ID: <span className="text-gray-600">{authStatus.userId || 'None'}</span></div>
            </div>
          </div>

          {/* Actions */}
          {!authStatus.hasToken ? (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  User ID
                </label>
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="Enter user ID"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="Enter username"
                />
              </div>

              <button
                onClick={handleCreateTestAuth}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                Create Test Auth Token
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">
                  ✅ Authentication token is present. You should be able to access protected endpoints.
                </p>
              </div>
              
              <div className="space-y-2">
                <button
                  onClick={handleDebugUserData}
                  disabled={isDebugging}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {isDebugging ? 'Debugging...' : 'Debug User Data'}
                </button>
                
                <button
                  onClick={handleFixDataLinking}
                  disabled={isDebugging}
                  className="w-full bg-green-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  {isDebugging ? 'Fixing...' : 'Fix Data Linking'}
                </button>
                
                <button
                  onClick={handleClearAuth}
                  className="w-full bg-red-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-red-700 transition-colors"
                >
                  Clear Auth Token
                </button>
              </div>
            </div>
          )}

          {/* Debug Data Display */}
          {debugData && (
            <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg max-h-40 overflow-y-auto">
              <h4 className="font-medium text-gray-900 mb-2">Debug Results</h4>
              <div className="text-xs text-gray-600 space-y-1">
                <div>Scan Records: {debugData.internal_users?.count || 0}</div>
                <div>Profile Records: {debugData.profile_users?.count || 0}</div>
                <div>Joined Records: {debugData.joined_data?.count || 0}</div>
                <div>ID Match: {debugData.id_matching?.has_match ? '✅' : '❌'}</div>
                {debugData.diagnosis?.map((d: string, i: number) => (
                  <div key={i} className="text-xs">{d}</div>
                ))}
              </div>
            </div>
          )}

          {/* Instructions */}
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-xs text-yellow-800">
              <strong>Note:</strong> This is a development tool. Use "Debug User Data" to see why rankings show N/A, 
              then "Fix Data Linking" to resolve issues.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuthDebugPanel;