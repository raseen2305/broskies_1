/**
 * Frontend error handling utilities for the GitHub Repository Evaluator
 */

export interface ApiError {
  error: {
    code: string;
    message: string;
    user_message: string;
    status_code: number;
    severity: 'low' | 'medium' | 'high' | 'critical';
    details?: Record<string, any>;
    recovery_suggestions?: string[];
    timestamp: string;
    request_id?: string;
  };
}

export interface ErrorDisplayInfo {
  title: string;
  message: string;
  type: 'error' | 'warning' | 'info';
  recoveryActions?: Array<{
    label: string;
    action: () => void;
  }>;
  details?: Record<string, any>;
}

export class ErrorHandler {
  private static instance: ErrorHandler;
  private errorCallbacks: Array<(error: ErrorDisplayInfo) => void> = [];

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  /**
   * Register a callback to handle error display
   */
  onError(callback: (error: ErrorDisplayInfo) => void): void {
    this.errorCallbacks.push(callback);
  }

  /**
   * Remove error callback
   */
  removeErrorCallback(callback: (error: ErrorDisplayInfo) => void): void {
    this.errorCallbacks = this.errorCallbacks.filter(cb => cb !== callback);
  }

  /**
   * Handle API errors from axios responses
   */
  handleApiError(error: any): ErrorDisplayInfo {
    let errorInfo: ErrorDisplayInfo;

    if (error.response?.data?.error) {
      // Structured API error
      const apiError: ApiError['error'] = error.response.data.error;
      errorInfo = this.processApiError(apiError);
    } else if (error.response) {
      // HTTP error without structured format
      errorInfo = this.processHttpError(error.response);
    } else if (error.request) {
      // Network error
      errorInfo = this.processNetworkError();
    } else {
      // Generic error
      errorInfo = this.processGenericError(error);
    }

    // Notify all callbacks
    this.errorCallbacks.forEach(callback => callback(errorInfo));

    return errorInfo;
  }

  private processApiError(apiError: ApiError['error']): ErrorDisplayInfo {
    const errorInfo: ErrorDisplayInfo = {
      title: this.getErrorTitle(apiError.code),
      message: apiError.user_message || apiError.message,
      type: this.getErrorType(apiError.severity),
      details: apiError.details
    };

    // Add recovery actions based on error code
    errorInfo.recoveryActions = this.getRecoveryActions(apiError);

    return errorInfo;
  }

  private processHttpError(response: any): ErrorDisplayInfo {
    const statusCode = response.status;
    const statusText = response.statusText;

    let title = 'Request Failed';
    let message = 'An error occurred while processing your request.';
    let type: 'error' | 'warning' | 'info' = 'error';

    switch (statusCode) {
      case 400:
        title = 'Invalid Request';
        message = 'The request contains invalid data. Please check your input and try again.';
        break;
      case 401:
        title = 'Authentication Required';
        message = 'You need to log in to access this resource.';
        type = 'warning';
        break;
      case 403:
        title = 'Access Denied';
        message = 'You don\'t have permission to access this resource.';
        break;
      case 404:
        title = 'Not Found';
        message = 'The requested resource could not be found.';
        break;
      case 429:
        title = 'Too Many Requests';
        message = 'You\'ve made too many requests. Please wait a moment and try again.';
        type = 'warning';
        break;
      case 500:
        title = 'Server Error';
        message = 'An internal server error occurred. Please try again later.';
        break;
      case 502:
      case 503:
        title = 'Service Unavailable';
        message = 'The service is temporarily unavailable. Please try again later.';
        break;
      default:
        title = `Error ${statusCode}`;
        message = statusText || 'An unexpected error occurred.';
    }

    return {
      title,
      message,
      type,
      recoveryActions: this.getHttpErrorRecoveryActions(statusCode)
    };
  }

  private processNetworkError(): ErrorDisplayInfo {
    return {
      title: 'Connection Error',
      message: 'Unable to connect to the server. Please check your internet connection and try again.',
      type: 'error',
      recoveryActions: [
        {
          label: 'Retry',
          action: () => window.location.reload()
        }
      ]
    };
  }

  private processGenericError(error: any): ErrorDisplayInfo {
    return {
      title: 'Unexpected Error',
      message: error.message || 'An unexpected error occurred. Please try again.',
      type: 'error',
      recoveryActions: [
        {
          label: 'Refresh Page',
          action: () => window.location.reload()
        }
      ]
    };
  }

  private getErrorTitle(errorCode: string): string {
    const titleMap: Record<string, string> = {
      'AUTH_001': 'Authentication Failed',
      'AUTH_002': 'Invalid Token',
      'AUTH_003': 'Session Expired',
      'AUTH_004': 'Access Denied',
      'AUTH_005': 'GitHub Login Failed',
      'AUTH_006': 'Google Login Failed',
      'VAL_001': 'Validation Error',
      'VAL_002': 'Invalid Input',
      'VAL_005': 'Invalid GitHub URL',
      'VAL_006': 'Invalid Email',
      'GH_001': 'GitHub Error',
      'GH_002': 'GitHub Rate Limit',
      'GH_003': 'Repository Not Found',
      'GH_004': 'User Not Found',
      'SCAN_001': 'Scan Error',
      'SCAN_002': 'Scan In Progress',
      'SCAN_003': 'Scan Failed',
      'SEC_001': 'Rate Limited',
      'SYS_001': 'System Error',
      'SYS_002': 'Service Unavailable'
    };

    return titleMap[errorCode] || 'Error';
  }

  private getErrorType(severity: string): 'error' | 'warning' | 'info' {
    switch (severity) {
      case 'critical':
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
      default:
        return 'info';
    }
  }

  private getRecoveryActions(apiError: ApiError['error']): Array<{ label: string; action: () => void }> {
    const actions: Array<{ label: string; action: () => void }> = [];

    // Add suggested recovery actions
    if (apiError.recovery_suggestions) {
      apiError.recovery_suggestions.forEach(suggestion => {
        if (suggestion.includes('log in') || suggestion.includes('login')) {
          actions.push({
            label: 'Log In',
            action: () => {
              // Redirect to login
              window.location.href = '/login';
            }
          });
        } else if (suggestion.includes('try again')) {
          actions.push({
            label: 'Try Again',
            action: () => window.location.reload()
          });
        } else if (suggestion.includes('wait')) {
          actions.push({
            label: 'Wait and Retry',
            action: () => {
              setTimeout(() => window.location.reload(), 5000);
            }
          });
        }
      });
    }

    // Add error-code specific actions
    switch (apiError.code) {
      case 'AUTH_002':
      case 'AUTH_003':
        actions.push({
          label: 'Log In Again',
          action: () => {
            localStorage.removeItem('token');
            window.location.href = '/login';
          }
        });
        break;
      case 'GH_002':
        if (apiError.details?.retry_after) {
          actions.push({
            label: `Wait ${apiError.details.retry_after}s`,
            action: () => {
              setTimeout(() => window.location.reload(), apiError.details!.retry_after * 1000);
            }
          });
        }
        break;
      case 'SEC_001':
        if (apiError.details?.retry_after) {
          actions.push({
            label: 'Wait and Retry',
            action: () => {
              setTimeout(() => window.location.reload(), apiError.details!.retry_after * 1000);
            }
          });
        }
        break;
    }

    return actions;
  }

  private getHttpErrorRecoveryActions(statusCode: number): Array<{ label: string; action: () => void }> {
    const actions: Array<{ label: string; action: () => void }> = [];

    switch (statusCode) {
      case 401:
        actions.push({
          label: 'Log In',
          action: () => {
            localStorage.removeItem('token');
            window.location.href = '/login';
          }
        });
        break;
      case 429:
        actions.push({
          label: 'Wait and Retry',
          action: () => {
            setTimeout(() => window.location.reload(), 60000); // Wait 1 minute
          }
        });
        break;
      case 500:
      case 502:
      case 503:
        actions.push({
          label: 'Try Again',
          action: () => window.location.reload()
        });
        break;
    }

    return actions;
  }

  /**
   * Handle validation errors from forms
   */
  handleValidationError(field: string, message: string): ErrorDisplayInfo {
    const errorInfo: ErrorDisplayInfo = {
      title: 'Validation Error',
      message: `${field}: ${message}`,
      type: 'warning',
      recoveryActions: [
        {
          label: 'Fix and Try Again',
          action: () => {
            // Focus on the field if possible
            const element = document.querySelector(`[name="${field}"]`) as HTMLElement;
            if (element) {
              element.focus();
            }
          }
        }
      ]
    };

    this.errorCallbacks.forEach(callback => callback(errorInfo));
    return errorInfo;
  }

  /**
   * Handle success messages
   */
  handleSuccess(message: string, title: string = 'Success'): void {
    const successInfo: ErrorDisplayInfo = {
      title,
      message,
      type: 'info'
    };

    this.errorCallbacks.forEach(callback => callback(successInfo));
  }
}

// Export singleton instance
export const errorHandler = ErrorHandler.getInstance();

// Axios interceptor setup
export const setupAxiosInterceptors = (axiosInstance: any) => {
  // Request interceptor to add request ID
  axiosInstance.interceptors.request.use(
    (config: any) => {
      // Add request timestamp for performance monitoring
      config.metadata = { startTime: new Date() };
      return config;
    },
    (error: any) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor for error handling
  axiosInstance.interceptors.response.use(
    (response: any) => {
      // Log successful requests for monitoring
      if (response.config.metadata) {
        const duration = new Date().getTime() - response.config.metadata.startTime.getTime();
        console.debug(`API Request: ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status} (${duration}ms)`);
      }
      return response;
    },
    (error: any) => {
      // Handle errors through error handler
      errorHandler.handleApiError(error);
      return Promise.reject(error);
    }
  );
};

// Utility functions
export const isApiError = (error: any): error is { response: { data: ApiError } } => {
  return error?.response?.data?.error !== undefined;
};

export const getErrorMessage = (error: any): string => {
  if (isApiError(error)) {
    return error.response.data.error.user_message || error.response.data.error.message;
  }
  return error.message || 'An unexpected error occurred';
};

export const getErrorCode = (error: any): string | null => {
  if (isApiError(error)) {
    return error.response.data.error.code;
  }
  return null;
};