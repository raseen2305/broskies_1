/**
 * Specialized Error Boundary for API communication failures
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Wifi, WifiOff, Server, Clock } from 'lucide-react';
import { LoadingButton } from './LoadingStates';
import { RetryMechanism } from './RetryMechanism';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  onRetry?: () => Promise<void>;
  showRetryMechanism?: boolean;
  maxRetries?: number;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorType: 'network' | 'server' | 'client' | 'timeout' | 'unknown';
  isRetrying: boolean;
  retryCount: number;
  isOnline: boolean;
}

export class ApiErrorBoundary extends Component<Props, State> {
  private retryTimeoutId: number | null = null;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorType: 'unknown',
      isRetrying: false,
      retryCount: 0,
      isOnline: navigator.onLine
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorType: ApiErrorBoundary.categorizeError(error)
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('API Error Boundary caught an error:', error, errorInfo);
    
    this.setState({
      errorInfo
    });

    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  componentDidMount() {
    // Listen for online/offline events
    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);
  }

  componentWillUnmount() {
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
    
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }
  }

  private static categorizeError(error: Error): State['errorType'] {
    const message = error.message.toLowerCase();
    
    if (message.includes('network') || message.includes('fetch')) {
      return 'network';
    }
    if (message.includes('timeout')) {
      return 'timeout';
    }
    if (message.includes('server') || message.includes('500') || message.includes('502') || message.includes('503')) {
      return 'server';
    }
    if (message.includes('400') || message.includes('401') || message.includes('403') || message.includes('404')) {
      return 'client';
    }
    
    return 'unknown';
  }

  private handleOnline = () => {
    this.setState({ isOnline: true });
    
    // Auto-retry when coming back online if it was a network error
    if (this.state.hasError && this.state.errorType === 'network') {
      this.handleRetry();
    }
  };

  private handleOffline = () => {
    this.setState({ isOnline: false });
  };

  private handleRetry = async () => {
    const { maxRetries = 3 } = this.props;
    
    if (this.state.retryCount >= maxRetries) {
      return;
    }

    this.setState({ 
      isRetrying: true,
      retryCount: this.state.retryCount + 1
    });

    try {
      if (this.props.onRetry) {
        await this.props.onRetry();
      }
      
      // If retry succeeds, reset the error state
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        isRetrying: false
      });
    } catch (error) {
      console.error('Retry failed:', error);
      this.setState({ isRetrying: false });
      
      // Schedule another retry with exponential backoff
      const delay = Math.pow(2, this.state.retryCount) * 1000;
      this.retryTimeoutId = setTimeout(() => {
        if (this.state.retryCount < maxRetries) {
          this.handleRetry();
        }
      }, delay);
    }
  };

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      isRetrying: false,
      retryCount: 0
    });
    
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
      this.retryTimeoutId = null;
    }
  };

  private getErrorIcon() {
    switch (this.state.errorType) {
      case 'network':
        return this.state.isOnline ? <Wifi className="w-8 h-8" /> : <WifiOff className="w-8 h-8" />;
      case 'server':
        return <Server className="w-8 h-8" />;
      case 'timeout':
        return <Clock className="w-8 h-8" />;
      default:
        return <AlertTriangle className="w-8 h-8" />;
    }
  }

  private getErrorTitle() {
    switch (this.state.errorType) {
      case 'network':
        return this.state.isOnline ? 'Connection Error' : 'No Internet Connection';
      case 'server':
        return 'Server Error';
      case 'timeout':
        return 'Request Timeout';
      case 'client':
        return 'Request Error';
      default:
        return 'Something went wrong';
    }
  }

  private getErrorMessage() {
    switch (this.state.errorType) {
      case 'network':
        return this.state.isOnline 
          ? 'Unable to connect to the server. Please check your connection and try again.'
          : 'You appear to be offline. Please check your internet connection.';
      case 'server':
        return 'The server is experiencing issues. Our team has been notified and is working on a fix.';
      case 'timeout':
        return 'The request took too long to complete. This might be due to a slow connection or server load.';
      case 'client':
        return 'There was an issue with your request. Please try again or contact support if the problem persists.';
      default:
        return 'An unexpected error occurred. Please try again or contact support if the problem persists.';
    }
  }

  private getErrorColor() {
    switch (this.state.errorType) {
      case 'network':
        return this.state.isOnline ? 'text-orange-500' : 'text-red-500';
      case 'server':
        return 'text-red-500';
      case 'timeout':
        return 'text-yellow-500';
      case 'client':
        return 'text-blue-500';
      default:
        return 'text-gray-500';
    }
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { maxRetries = 3, showRetryMechanism = false } = this.props;
      const canRetry = this.state.retryCount < maxRetries;

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
          <div className="sm:mx-auto sm:w-full sm:max-w-md">
            <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
              <div className="text-center">
                <div className={`mx-auto mb-4 ${this.getErrorColor()}`}>
                  {this.getErrorIcon()}
                </div>
                
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  {this.getErrorTitle()}
                </h2>
                
                <p className="text-gray-600 mb-6">
                  {this.getErrorMessage()}
                </p>

                {/* Connection Status */}
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium mb-6 ${
                  this.state.isOnline 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {this.state.isOnline ? (
                    <>
                      <Wifi className="w-4 h-4 mr-2" />
                      Online
                    </>
                  ) : (
                    <>
                      <WifiOff className="w-4 h-4 mr-2" />
                      Offline
                    </>
                  )}
                </div>

                {/* Error Details */}
                {this.state.error && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
                    <div className="text-sm text-red-800">
                      <p className="font-medium">Error Details:</p>
                      <p className="mt-1">{this.state.error.message}</p>
                      {this.state.retryCount > 0 && (
                        <p className="mt-1">Retry attempts: {this.state.retryCount}/{maxRetries}</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="space-y-3">
                  {canRetry && this.props.onRetry && (
                    <LoadingButton
                      loading={this.state.isRetrying}
                      onClick={this.handleRetry}
                      className="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      {this.state.isRetrying ? 'Retrying...' : 'Try Again'}
                    </LoadingButton>
                  )}

                  <button
                    onClick={this.handleReset}
                    className="w-full flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Reset
                  </button>

                  <button
                    onClick={() => window.location.reload()}
                    className="w-full flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Reload Page
                  </button>
                </div>

                {/* Retry Mechanism Component */}
                {showRetryMechanism && this.props.onRetry && (
                  <div className="mt-6">
                    <RetryMechanism
                      onRetry={this.props.onRetry}
                      maxAttempts={maxRetries}
                      autoRetry={this.state.errorType === 'network' || this.state.errorType === 'timeout'}
                    />
                  </div>
                )}

                {/* Development Details */}
                {import.meta.env.DEV && this.state.error && (
                  <details className="mt-6 text-left">
                    <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                      Technical Details (Development)
                    </summary>
                    <div className="mt-2 p-3 bg-gray-100 rounded text-xs font-mono text-gray-800 overflow-auto max-h-40">
                      <div className="mb-2">
                        <strong>Error Type:</strong> {this.state.errorType}
                      </div>
                      <div className="mb-2">
                        <strong>Error:</strong> {this.state.error.message}
                      </div>
                      <div className="mb-2">
                        <strong>Stack:</strong>
                        <pre className="whitespace-pre-wrap">{this.state.error.stack}</pre>
                      </div>
                      {this.state.errorInfo && (
                        <div>
                          <strong>Component Stack:</strong>
                          <pre className="whitespace-pre-wrap">{this.state.errorInfo.componentStack}</pre>
                        </div>
                      )}
                    </div>
                  </details>
                )}
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for wrapping API components
export function withApiErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ApiErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ApiErrorBoundary>
  );

  WrappedComponent.displayName = `withApiErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}