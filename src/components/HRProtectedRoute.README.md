# HRProtectedRoute Component

A route protection component that ensures only authenticated HR users can access protected pages in the HR dashboard.

## Features

- ✅ Authentication verification using HRAuthContext
- ✅ Loading state with animated spinner
- ✅ Automatic redirect to login page if not authenticated
- ✅ Preserves intended destination URL for post-login redirect
- ✅ Debug logging in development mode
- ✅ Smooth animations using Framer Motion

## Usage

### Basic Usage

Wrap any HR dashboard route with `HRProtectedRoute` to make it accessible only to authenticated HR users:

```tsx
import HRProtectedRoute from '../components/HRProtectedRoute';
import HRDashboard from '../pages/HRDashboard';

<Route 
  path="/hr/dashboard" 
  element={
    <HRProtectedRoute>
      <HRDashboard />
    </HRProtectedRoute>
  } 
/>
```

### Multiple Protected Routes

```tsx
<Routes>
  {/* Public HR routes */}
  <Route path="/hr/auth" element={<HRAuth />} />
  <Route path="/hr/auth/callback" element={<HRAuth />} />
  
  {/* Protected HR routes */}
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
        <CandidateDetail />
      </HRProtectedRoute>
    } 
  />
</Routes>
```

## How It Works

### Authentication Flow

1. **Loading State**: While checking authentication, displays a loading spinner
2. **Authentication Check**: Verifies user is authenticated via `useHRAuth()` hook
3. **Redirect**: If not authenticated, redirects to `/hr/auth` with the intended destination saved
4. **Render**: If authenticated, renders the protected children components

### State Management

The component uses the `HRAuthContext` to access:
- `isAuthenticated`: Boolean indicating if user is logged in
- `isLoading`: Boolean indicating if auth check is in progress
- `hrUser`: The authenticated HR user object (or null)

### Redirect Behavior

When redirecting unauthenticated users:
```typescript
// Saves the intended destination
const redirectPath = location.pathname + location.search;

<Navigate 
  to="/hr/auth" 
  state={{ from: redirectPath }} 
  replace 
/>
```

After successful login, the auth page can redirect back to the saved location:
```typescript
const location = useLocation();
const from = location.state?.from || '/hr/dashboard';
navigate(from);
```

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `children` | `React.ReactNode` | Yes | The protected content to render when authenticated |

## Loading State

The loading spinner appears while authentication is being verified:

```tsx
<div className="min-h-screen flex items-center justify-center">
  <motion.div animate={{ rotate: 360 }}>
    {/* Animated spinner */}
  </motion.div>
  <p>Verifying authentication...</p>
</div>
```

## Debug Logging

In development mode, the component logs authentication checks:

```typescript
console.log('HRProtectedRoute check:', {
  isAuthenticated,
  isLoading,
  hasUser: !!hrUser,
  path: location.pathname,
});
```

## Security Considerations

1. **Client-Side Only**: This is a UI protection layer. Always verify authentication on the backend
2. **Token Validation**: The HRAuthContext automatically validates tokens with the backend
3. **Automatic Logout**: Expired tokens trigger automatic logout and redirect
4. **State Preservation**: Intended destination is preserved for better UX

## Related Components

- `HRAuthContext` - Provides authentication state and methods
- `HRAuth` - Login page for HR users
- `HRDashboard` - Main dashboard (protected)
- `CandidateDetail` - Candidate detail page (protected)

## Dependencies

- `react-router-dom` - For navigation and routing
- `framer-motion` - For loading animations
- `HRAuthContext` - For authentication state

## Example: Complete Route Setup

```tsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { HRAuthProvider } from './contexts/HRAuthContext';
import HRProtectedRoute from './components/HRProtectedRoute';
import HRAuth from './pages/HRAuth';
import HRDashboard from './pages/HRDashboard';

function App() {
  return (
    <HRAuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/hr/auth" element={<HRAuth />} />
          
          {/* Protected routes */}
          <Route 
            path="/hr/dashboard" 
            element={
              <HRProtectedRoute>
                <HRDashboard />
              </HRProtectedRoute>
            } 
          />
        </Routes>
      </Router>
    </HRAuthProvider>
  );
}
```

## Testing

To test the protected route:

1. **Unauthenticated Access**: Navigate to `/hr/dashboard` without logging in
   - Should redirect to `/hr/auth`
   - Should preserve the intended destination

2. **Authenticated Access**: Log in and navigate to `/hr/dashboard`
   - Should display the dashboard
   - Should not show loading spinner after initial load

3. **Token Expiration**: Wait for token to expire
   - Should automatically redirect to login
   - Should clear stored authentication data

## Troubleshooting

### Route Not Protecting

Ensure the route is wrapped with `HRAuthProvider`:
```tsx
<HRAuthProvider>
  <Routes>
    <Route path="/hr/dashboard" element={<HRProtectedRoute>...</HRProtectedRoute>} />
  </Routes>
</HRAuthProvider>
```

### Infinite Loading

Check that `HRAuthContext` properly sets `isLoading` to `false` after auth check.

### Redirect Loop

Ensure `/hr/auth` route is NOT wrapped with `HRProtectedRoute`.
