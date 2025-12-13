import React, { useState, useEffect } from "react";
import { Routes, Route, useLocation, useNavigate } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";
import Overview from "../components/dashboard/Overview";
import Languages from "../components/dashboard/Languages";
import TechStack from "../components/dashboard/TechStack";
import Repositories from "../components/dashboard/Repositories";
import RepositoryDetail from "../components/dashboard/RepositoryDetail";
import ContributionCalendar from "../components/dashboard/ContributionCalendar";
import PullRequestAnalysis from "../components/dashboard/PullRequestAnalysis";
import IssueAnalysis from "../components/dashboard/IssueAnalysis";
import RankingsPage from "./RankingsPage";
import AuthDebugPanel from "../components/AuthDebugPanel";

interface ScanResults {
  userInfo: any;
  repositories: any[];
  evaluation: any;
  scanType: "self" | "other";
  targetUsername: string;
  repositoryCount: number;
  overallScore: number;
  languages: any[];
  techStack: any[];
  roadmap: any[];
  evaluation_method?: string;
  ml_available?: boolean;
  hybrid_score?: number;
  ml_insights?: any;
  acid_scores?: any;
}

interface DeveloperDashboardProps {
  scanResults?: ScanResults | null;
}

const DeveloperDashboard: React.FC<DeveloperDashboardProps> = ({
  scanResults: propScanResults,
}) => {
  const location = useLocation();
  const navigate = useNavigate();

  // If scanResults are provided as props (from modal), use them directly
  // Otherwise, try to restore from localStorage
  const [scanResults, setScanResults] = useState<ScanResults | null>(() => {
    // If scanResults provided as prop, use them (HR viewing candidate)
    if (propScanResults) {
      console.log(
        "✅ [Dashboard] Using scanResults from props (external view)"
      );
      return propScanResults;
    }

    // Otherwise, try to restore from localStorage (developer's own dashboard)
    try {
      const stored = localStorage.getItem("dashboard_scan_results");
      if (stored) {
        const parsed = JSON.parse(stored);
        // Check if data is not too old (24 hours)
        const timestamp = localStorage.getItem("dashboard_scan_timestamp");
        if (timestamp) {
          const age = Date.now() - parseInt(timestamp);
          if (age < 24 * 60 * 60 * 1000) {
            // 24 hours
            console.log(
              "✅ [Dashboard] Restored scan results from localStorage"
            );
            console.log(
              "📊 [Dashboard] Total repos:",
              parsed.repositories?.length
            );
            console.log(
              "📊 [Dashboard] With categories:",
              parsed.repositories?.filter((r: any) => r.category).length
            );
            console.log("📊 [Dashboard] Analyzed:", parsed.analyzed);
            return parsed;
          } else {
            console.log("⏰ Stored scan results expired, clearing");
            localStorage.removeItem("dashboard_scan_results");
            localStorage.removeItem("dashboard_scan_timestamp");
          }
        }
      }
    } catch (error) {
      console.error("Failed to restore scan results:", error);
    }
    return null;
  });
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Update scanResults when props change (for modal view)
  useEffect(() => {
    if (propScanResults) {
      console.log(
        "🔄 [Dashboard] Updating scanResults from props:",
        propScanResults.targetUsername
      );
      setScanResults(propScanResults);
    }
  }, [propScanResults]);

  // Persist scan results to localStorage whenever they change (only if not from props)
  useEffect(() => {
    if (scanResults && !propScanResults) {
      try {
        localStorage.setItem(
          "dashboard_scan_results",
          JSON.stringify(scanResults)
        );
        localStorage.setItem("dashboard_scan_timestamp", Date.now().toString());
        console.log("💾 Scan results saved to localStorage");
      } catch (error) {
        console.error("Failed to save scan results to localStorage:", error);
      }
    }
  }, [scanResults, propScanResults]);

  useEffect(() => {
    console.log(
      "🔍 DeveloperDashboard useEffect triggered, location.state:",
      location.state
    );

    // Check if scan results were passed from ScanningProgress
    if (location.state && location.state.scanResults) {
      console.log("✅ Scan results found from navigation, setting them");
      setScanResults(location.state.scanResults);
      console.log(
        "📊 Dashboard received scan results:",
        location.state.scanResults
      );

      // Clear any existing error when scan results are provided
      setError(null);
      setIsLoadingProfile(false);

      // Clear the location state to prevent issues on refresh
      window.history.replaceState({}, document.title);
    } else if (!scanResults && !propScanResults) {
      // Only load default profile if we don't have any scan results yet
      console.log("❌ No scan results, loading default profile");
      loadDefaultProfile();
    } else {
      // We have scan results from props, clear any loading state
      console.log(
        "✅ Scan results available from props, clearing loading state"
      );
      setIsLoadingProfile(false);
      setError(null);
    }
  }, [location.state, propScanResults]);

  const loadDefaultProfile = async () => {
    try {
      setIsLoadingProfile(true);

      // Check if user is authenticated and has GitHub username
      let authUser: any = {};
      try {
        authUser = JSON.parse(localStorage.getItem("auth_user") || "{}");
      } catch (error) {
        console.error("Failed to parse auth_user from localStorage:", error);
      }

      if (authUser?.githubUsername) {
        // User is authenticated but no scan results - offer to scan their profile
        console.log(
          "🔍 Authenticated user without scan results, offering to scan profile"
        );
        setError(
          `Welcome back, ${authUser.githubUsername}! Ready to analyze your GitHub repositories?`
        );
      } else {
        // No authenticated user - general welcome message
        console.log("🚫 No authenticated user, showing general welcome");
        setError(
          "Welcome! Please connect your GitHub account to view detailed analytics and insights."
        );
      }
    } catch (error) {
      console.error("❌ Failed to load profile:", error);
      setError(
        "Unable to load profile. Please try scanning a GitHub profile or refresh the page."
      );
    } finally {
      setIsLoadingProfile(false);
    }
  };

  // Show loading state while loading default profile
  if (isLoadingProfile) {
    return (
      <DashboardLayout scanResults={null}>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Loading GitHub Profile
            </h3>
            <p className="text-gray-600">Preparing dashboard...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // Show error state if loading failed (but not if we have scan results or are expecting them)
  if (
    error &&
    !scanResults &&
    !propScanResults &&
    !(location.state && location.state.scanResults)
  ) {
    const isLoadingError = error.includes("loading");

    return (
      <DashboardLayout scanResults={null}>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center max-w-md">
            <div
              className={`${
                isLoadingError ? "text-blue-500" : "text-orange-500"
              } mb-4`}
            >
              {isLoadingError ? (
                <svg
                  className="h-12 w-12 mx-auto"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              ) : (
                <svg
                  className="h-12 w-12 mx-auto"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              )}
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {isLoadingError ? "Account Loading" : "No Profile Data"}
            </h3>
            <p className="text-gray-600 mb-6 leading-relaxed">{error}</p>
            <div className="space-y-3">
              {(() => {
                let authUserData: any = {};
                try {
                  authUserData = JSON.parse(
                    localStorage.getItem("auth_user") || "{}"
                  );
                } catch (error) {
                  console.error(
                    "Failed to parse auth_user from localStorage:",
                    error
                  );
                }
                if (authUserData?.githubUsername) {
                  // User is authenticated - offer to scan their profile
                  return (
                    <>
                      <button
                        onClick={() => {
                          // Navigate to scanning progress with proper state
                          navigate("/scanning-progress", {
                            state: {
                              scanType: "self",
                              username: authUserData.githubUsername,
                            },
                          });
                        }}
                        className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
                      >
                        Scan My Repositories
                      </button>
                      <button
                        onClick={() =>
                          (window.location.href = "/developer/auth")
                        }
                        className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-6 rounded-lg transition-colors"
                      >
                        Scan Other Profiles
                      </button>
                    </>
                  );
                } else {
                  // No authenticated user - show connect GitHub option
                  return (
                    <button
                      onClick={() => (window.location.href = "/developer/auth")}
                      className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
                    >
                      Connect GitHub & Scan
                    </button>
                  );
                }
              })()}
              {isLoadingError && (
                <button
                  onClick={() => window.location.reload()}
                  className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-6 rounded-lg transition-colors"
                >
                  Refresh Page
                </button>
              )}
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout scanResults={scanResults}>
      <Routes>
        <Route path="/" element={<Overview scanResults={scanResults} />} />
        <Route
          path="/overview"
          element={<Overview scanResults={scanResults} />}
        />
        <Route
          path="/rankings"
          element={<RankingsPage scanResults={scanResults} />}
        />
        <Route
          path="/languages"
          element={<Languages scanResults={scanResults} />}
        />
        <Route
          path="/tech-stack"
          element={<TechStack scanResults={scanResults} />}
        />
        <Route
          path="/repositories"
          element={<Repositories scanResults={scanResults} />}
        />
        <Route
          path="/repositories/:repositoryName"
          element={<RepositoryDetail scanResults={scanResults} />}
        />
        <Route
          path="/activity"
          element={<ContributionCalendar scanResults={scanResults} />}
        />
        <Route
          path="/pull-requests"
          element={<PullRequestAnalysis scanResults={scanResults} />}
        />
        <Route
          path="/issues"
          element={<IssueAnalysis scanResults={scanResults} />}
        />
      </Routes>
      
      {/* Development Authentication Debug Panel */}
      <AuthDebugPanel />
    </DashboardLayout>
  );
};

export default DeveloperDashboard;
