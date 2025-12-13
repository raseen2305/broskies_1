/**
 * HR Authentication Context
 * Manages authentication state for HR users with Google OAuth
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { isDevSession } from "../utils/devAuth";

// Types
interface HRUser {
  id: string;
  email: string;
  full_name?: string;
  profile_picture?: string;
  company?: string;
  role?: string;
  is_approved: boolean;
  created_at: string;
  last_login?: string;
}

interface HRAuthContextType {
  hrUser: HRUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshToken: () => Promise<void>;
  clearError: () => void;
}

// Create context
const HRAuthContext = createContext<HRAuthContextType | undefined>(undefined);

// Storage keys
const STORAGE_KEYS = {
  ACCESS_TOKEN: "hr_access_token",
  REFRESH_TOKEN: "hr_refresh_token",
  USER: "hr_user",
};

// API base URL
const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";

/**
 * HR Authentication Provider Component
 */
export const HRAuthProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [hrUser, setHrUser] = useState<HRUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = !!hrUser;

  /**
   * Load user from localStorage on mount
   */
  useEffect(() => {
    const loadUser = async () => {
      try {
        const storedUser = localStorage.getItem(STORAGE_KEYS.USER);
        const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);

        if (storedUser && accessToken) {
          const user = JSON.parse(storedUser);
          setHrUser(user);

          // Verify token is still valid (skips for dev sessions)
          // Don't throw errors here to avoid console spam
          try {
            await verifyToken(accessToken);
          } catch (verifyErr) {
            // Token verification failed, silently clear auth data
            console.log("🔄 Session expired, clearing authentication data");
            clearAuthData();
          }
        }
      } catch (err) {
        console.error("Failed to load user:", err);
        clearAuthData();
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();

    // Listen for storage changes (for dev login)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === STORAGE_KEYS.USER || e.key === STORAGE_KEYS.ACCESS_TOKEN) {
        console.log("🔄 Storage changed, reloading user...");
        loadUser();
      }
    };

    window.addEventListener("storage", handleStorageChange);

    // Also listen for custom event (for same-window changes)
    const handleAuthChange = () => {
      console.log("🔄 Auth changed, reloading user...");
      loadUser();
    };

    window.addEventListener("hr-auth-changed", handleAuthChange);

    return () => {
      window.removeEventListener("storage", handleStorageChange);
      window.removeEventListener("hr-auth-changed", handleAuthChange);
    };
  }, []);

  /**
   * Verify token with backend
   */
  const verifyToken = async (token: string): Promise<void> => {
    // Skip backend verification for dev sessions
    if (isDevSession()) {
      console.log("✅ Dev session detected, skipping backend verification");
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/hr/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token is expired or invalid, try to refresh
          console.log("🔄 Token expired, attempting refresh...");
          const refreshTokenValue = localStorage.getItem(
            STORAGE_KEYS.REFRESH_TOKEN
          );
          if (refreshTokenValue) {
            try {
              await refreshToken();
              return; // Successfully refreshed
            } catch (refreshErr) {
              console.log("Token refresh also failed, clearing auth data");
            }
          }
        }
        throw new Error("Token verification failed");
      }

      const userData = await response.json();
      setHrUser(userData);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
    } catch (err) {
      // Only log actual errors, not expected 401s
      if (
        err instanceof Error &&
        !err.message.includes("Token verification failed")
      ) {
        console.error("Unexpected token verification error:", err);
      }
      clearAuthData();
      throw err;
    }
  };

  /**
   * Sign in with Google OAuth
   */
  const signInWithGoogle = async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      // Get authorization URL from backend
      const response = await fetch(`${API_BASE_URL}/auth/hr/google/authorize`);

      if (!response.ok) {
        throw new Error("Failed to get authorization URL");
      }

      const data = await response.json();
      const authUrl = data.authorization_url;

      // Redirect to Google OAuth
      window.location.href = authUrl;
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to initiate Google sign-in";
      setError(errorMessage);
      setIsLoading(false);
      throw err;
    }
  };

  /**
   * Handle OAuth callback
   */
  const handleOAuthCallback = async (code: string): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      console.log("🔄 Handling OAuth callback...");
      console.log("   API URL:", API_BASE_URL);
      console.log("   Code:", code.substring(0, 20) + "...");

      // Exchange code for tokens
      const url = `${API_BASE_URL}/auth/hr/google/callback`;
      console.log("   Calling:", url);

      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code }),
      });

      console.log("   Response status:", response.status);

      if (!response.ok) {
        const errorData = await response.json();
        console.error("   Error response:", errorData);
        throw new Error(
          errorData.detail ||
            errorData.error?.message ||
            "Authentication failed"
        );
      }

      const data = await response.json();
      console.log("   ✅ Authentication successful");

      // Store tokens and user data
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, data.access_token);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(data.user));

      setHrUser(data.user);
    } catch (err) {
      console.error("❌ OAuth callback error:", err);
      const errorMessage =
        err instanceof Error ? err.message : "Authentication failed";

      // Check for network errors
      if (err instanceof TypeError && err.message.includes("fetch")) {
        setError(
          "Cannot connect to server. Please ensure the backend is running on " +
            API_BASE_URL
        );
      } else {
        setError(errorMessage);
      }

      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Sign out
   */
  const signOut = async (): Promise<void> => {
    try {
      setIsLoading(true);
      const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);

      if (accessToken) {
        // Call logout endpoint
        await fetch(`${API_BASE_URL}/auth/hr/logout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
      }
    } catch (err) {
      console.error("Logout error:", err);
    } finally {
      clearAuthData();
      setIsLoading(false);
    }
  };

  /**
   * Refresh access token
   */
  const refreshToken = async (): Promise<void> => {
    try {
      const refreshTokenValue = localStorage.getItem(
        STORAGE_KEYS.REFRESH_TOKEN
      );

      if (!refreshTokenValue) {
        throw new Error("No refresh token available");
      }

      const response = await fetch(`${API_BASE_URL}/auth/hr/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Token refresh failed");
      }

      const data = await response.json();

      // Update tokens and user data
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, data.access_token);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(data.user));

      setHrUser(data.user);
      console.log("✅ Token refreshed successfully");
    } catch (err) {
      console.error("Token refresh failed:", err);
      clearAuthData();
      throw err;
    }
  };

  /**
   * Clear authentication data
   */
  const clearAuthData = (): void => {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER);
    setHrUser(null);
    setError(null);
  };

  /**
   * Check if tokens exist and are potentially valid
   */
  const hasValidTokens = (): boolean => {
    const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
    return !!(accessToken && refreshToken);
  };

  /**
   * Clear error
   */
  const clearError = (): void => {
    setError(null);
  };

  // Expose handleOAuthCallback for use in OAuth callback page
  useEffect(() => {
    // Check if we're on the OAuth callback page
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get("code");
    const currentPath = window.location.pathname;

    console.log("🔍 HRAuthContext useEffect triggered");
    console.log("   Current path:", currentPath);
    console.log("   Has code param:", !!code);
    console.log(
      "   Code value:",
      code ? code.substring(0, 20) + "..." : "none"
    );

    // Process OAuth code on both /hr/auth and /hr/auth/callback paths
    if (
      code &&
      (currentPath === "/hr/auth/callback" || currentPath === "/hr/auth")
    ) {
      console.log("📍 ✅ On OAuth callback page, processing code...");
      console.log("   Full URL:", window.location.href);

      // Store in sessionStorage so we can see it even after redirect
      sessionStorage.setItem(
        "oauth_callback_attempt",
        new Date().toISOString()
      );
      sessionStorage.setItem("oauth_code", code.substring(0, 30));

      // Add a small delay to ensure everything is loaded
      setTimeout(() => {
        console.log("🔄 Starting OAuth callback handler...");
        handleOAuthCallback(code)
          .then(() => {
            console.log(
              "✅ OAuth callback successful, redirecting to dashboard..."
            );
            sessionStorage.setItem("oauth_success", "true");
            // Redirect to dashboard after successful authentication
            window.location.href = "/hr/dashboard";
          })
          .catch((err) => {
            console.error("❌ OAuth callback error:", err);
            sessionStorage.setItem(
              "oauth_error",
              err.message || "Unknown error"
            );

            // Show more specific error message
            const errorMsg = err.message || "Authentication failed";
            if (errorMsg.includes("Cannot connect to server")) {
              window.location.href = "/hr/auth?error=server_unavailable";
            } else if (errorMsg.includes("not approved")) {
              window.location.href = "/hr/auth?error=not_approved";
            } else {
              window.location.href = "/hr/auth?error=auth_failed";
            }
          });
      }, 500); // Wait 500ms for everything to load
    } else if (code) {
      console.log(
        "⚠️ Has code but not on auth path. Current path:",
        currentPath
      );
    } else if (currentPath === "/hr/auth/callback") {
      console.log("⚠️ On callback path but no code parameter");
    }
  }, []);

  const value: HRAuthContextType = {
    hrUser,
    isAuthenticated,
    isLoading,
    error,
    signInWithGoogle,
    signOut,
    refreshToken,
    clearError,
  };

  return (
    <HRAuthContext.Provider value={value}>{children}</HRAuthContext.Provider>
  );
};

/**
 * Hook to use HR authentication context
 */
export const useHRAuth = (): HRAuthContextType => {
  const context = useContext(HRAuthContext);

  if (context === undefined) {
    throw new Error("useHRAuth must be used within an HRAuthProvider");
  }

  return context;
};

/**
 * Get access token from localStorage
 */
export const getHRAccessToken = (): string | null => {
  return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
};

/**
 * Check if user is authenticated
 */
export const isHRAuthenticated = (): boolean => {
  return !!localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
};
