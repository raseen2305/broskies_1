import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import DeveloperAuth from './pages/DeveloperAuth'
import DeveloperDashboard from './pages/DeveloperDashboard'
import HRAuth from './pages/HRAuth'
import HRDashboard from './pages/HRDashboard'
import HRProtectedRoute from './components/HRProtectedRoute'
import RepositoryScanner from './pages/RepositoryScanner'
import ScanningProgress from './pages/ScanningProgress'
import AnimationShowcase from './pages/AnimationShowcase'
import { AuthProvider } from './contexts/AuthContext'
import { HRAuthProvider } from './contexts/HRAuthContext'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ApiErrorBoundary } from './components/ApiErrorBoundary'
import { NotificationSystem } from './components/NotificationSystem'
import { setupAxiosInterceptors } from './utils/errorHandler'
import { logEnvironmentConfig } from './utils/config'
import axios from 'axios'
import { useEffect, lazy, Suspense } from 'react'

// Lazy load CandidateProfile component for better performance
const CandidateProfile = lazy(() => import('./pages/hr/CandidateProfile'))

// Setup axios interceptors for error handling
setupAxiosInterceptors(axios)

function App() {
  useEffect(() => {
    // Log environment configuration for debugging
    if (import.meta.env.DEV) {
      logEnvironmentConfig();
    }

    // Setup global error handlers
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      console.error('Unhandled promise rejection:', event.reason)
      // You can also send this to your error reporting service
    }

    const handleError = (event: ErrorEvent) => {
      console.error('Global error:', event.error)
      // You can also send this to your error reporting service
    }

    window.addEventListener('unhandledrejection', handleUnhandledRejection)
    window.addEventListener('error', handleError)

    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection)
      window.removeEventListener('error', handleError)
    }
  }, [])

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Log error to monitoring service
        console.error('React Error Boundary caught error:', error, errorInfo)
        // You can send this to your error reporting service here
      }}
    >
      <ApiErrorBoundary
        onError={(error, errorInfo) => {
          console.error('API Error Boundary caught error:', error, errorInfo)
        }}
        showRetryMechanism={true}
        maxRetries={3}
      >
        <AuthProvider>
          <HRAuthProvider>
            <Router>
              <div className="min-h-screen bg-gray-50">
                <Routes>
                  <Route path="/" element={<LandingPage />} />
                  <Route path="/developer/auth" element={<DeveloperAuth />} />
                  <Route path="/developer/dashboard/*" element={<DeveloperDashboard />} />
                  <Route path="/developer/scan" element={<RepositoryScanner />} />
                  <Route path="/scanning-progress" element={<ScanningProgress />} />
                  
                  {/* HR Authentication Routes */}
                  <Route path="/hr/auth" element={<HRAuth />} />
                  <Route path="/hr/auth/callback" element={<HRAuth />} />
                  
                  {/* HR Protected Routes */}
                  <Route 
                    path="/hr/dashboard/*" 
                    element={
                      <HRProtectedRoute>
                        <HRDashboard />
                      </HRProtectedRoute>
                    } 
                  />
                  <Route 
                    path="/hr/candidates/:username" 
                    element={
                      <HRProtectedRoute>
                        <Suspense fallback={
                          <div className="min-h-screen flex items-center justify-center bg-gray-50">
                            <div className="text-center">
                              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                              <p className="text-gray-600">Loading candidate profile...</p>
                            </div>
                          </div>
                        }>
                          <CandidateProfile />
                        </Suspense>
                      </HRProtectedRoute>
                    } 
                  />
                  
                  <Route path="/animations" element={<AnimationShowcase />} />
                </Routes>
                <NotificationSystem />
              </div>
            </Router>
          </HRAuthProvider>
        </AuthProvider>
      </ApiErrorBoundary>
    </ErrorBoundary>
  )
}

export default App