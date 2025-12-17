import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  TrendingUp,
  GitBranch,
  Code,
  Shield,
  Award,
  Activity,
  Calendar,
} from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { scanAPI } from "../../services/api";
import RankingWidget from "../RankingWidget";
import ExternalRankingWidget from "../ExternalRankingWidget";
import ProfileSetupModal from "../ProfileSetupModal";
import {
  useScoreSync,
  dispatchScanCompleteEvent,
} from "../../hooks/useScoreSync";
import AnalyzeButton from "../AnalyzeButton";
import AnalysisProgress from "../AnalysisProgress";
import AnimatedQualityWheel from "./AnimatedQualityWheel";
import GitHubActivityCalendar from "../GitHubActivityCalendar";

interface UserStats {
  overallScore: number;
  repositoryCount: number;
  lastScanDate: string | null;
  languages: Array<{
    language: string;
    percentage: number;
    linesOfCode?: number;
    repositories: number;
    stars?: number;
  }>;
  githubProfile?: {
    username: string;
    name: string | null;
    bio: string | null;
    location: string | null;
    company: string | null;
    blog: string | null;
    public_repos: number;
    followers: number;
    following: number;
    created_at: string | null;
    avatar_url: string | null;
  };
}

interface OverviewProps {
  scanResults?: any;
}

const Overview: React.FC<OverviewProps> = ({ scanResults }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [syncNotification, setSyncNotification] = useState<string | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Score sync hook
  const { triggerSync } = useScoreSync({
    onSyncSuccess: (data) => {
      console.log("Score synced successfully:", data);
      setSyncNotification("Rankings updated successfully!");
      setTimeout(() => setSyncNotification(null), 3000);
    },
    onSyncError: (error) => {
      console.error("Score sync failed:", error);
    },
    autoSync: true,
  });

  // Check if user has profile (no longer auto-opens modal)
  const checkAndShowProfileModal = async () => {
    try {
      console.log("🔍 Checking if user has profile...");
      const response = await fetch(
        `${
          import.meta.env.VITE_API_URL || "http://localhost:8000"
        }/profile/status`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        console.log("📋 Profile status:", data);

        if (!data.has_profile) {
          console.log("✨ No profile found - user can click button to set up");
        } else {
          console.log("✅ User already has profile");
        }
      } else {
        console.warn("⚠️ Profile status check failed:", response.status);
      }
    } catch (error) {
      console.error("❌ Failed to check profile status:", error);
    }
  };

  useEffect(() => {
    const loadUserStats = async () => {
      // If scan results are provided, use them directly
      if (scanResults) {
        console.log("📊 Using provided scan results:", scanResults);

        // Clear any previous errors
        setError(null);

        // Extract language data from the actual scan results structure
        let languagesData: Array<{
          language: string;
          percentage: number;
          linesOfCode?: number;
          repositories: number;
          stars?: number;
        }> = [];

        if (scanResults.languages && scanResults.languages.length > 0) {
          // Use direct languages array if available
          languagesData = scanResults.languages;
        } else if (
          scanResults.languageStatistics &&
          scanResults.languageStatistics.language_breakdown
        ) {
          // Transform language_breakdown to expected format
          const breakdown = scanResults.languageStatistics.language_breakdown;
          languagesData = Object.entries(breakdown)
            .map(([language, data]: [string, any]) => ({
              language,
              percentage: data.percentage || 0,
              linesOfCode: data.lines_of_code || 0,
              repositories: data.repository_count || 0,
              stars: 0,
            }))
            .sort((a, b) => b.percentage - a.percentage);
        }

        // Get overall score from scan results or rankings
        let overallScore =
          scanResults.overallScore || scanResults.hybrid_score || 0;

        // If no overall score in scan results, try to get it from rankings
        if (overallScore === 0) {
          try {
            const { rankingAPI } = await import("../../services/profileAPI");
            const rankingsData = await rankingAPI.getRankings();
            if (rankingsData.status === "available") {
              const regionalScore =
                rankingsData.regional_ranking?.overall_score;
              const universityScore =
                rankingsData.university_ranking?.overall_score;
              overallScore = regionalScore || universityScore || 0;
              console.log(
                "📊 Using overall score from rankings:",
                overallScore
              );
            }
          } catch (error) {
            console.log(
              "⚠️ Could not fetch rankings data for overall score:",
              error
            );
          }
        }

        // Transform scan results to match UserStats interface
        const transformedStats: UserStats = {
          overallScore: overallScore,
          repositoryCount: scanResults.repositoryCount || 0,
          lastScanDate: new Date().toISOString(), // Current scan
          languages: languagesData,
          githubProfile: scanResults.userInfo
            ? {
                username:
                  scanResults.userInfo.login ||
                  scanResults.userInfo.username ||
                  scanResults.targetUsername,
                name: scanResults.userInfo.name,
                bio: scanResults.userInfo.bio,
                location: scanResults.userInfo.location,
                company: scanResults.userInfo.company,
                blog: scanResults.userInfo.blog,
                public_repos:
                  scanResults.userInfo.public_repos ||
                  scanResults.repositoryCount,
                followers: scanResults.userInfo.followers || 0,
                following: scanResults.userInfo.following || 0,
                created_at: scanResults.userInfo.created_at,
                avatar_url: scanResults.userInfo.avatar_url,
              }
            : undefined,
        };

        setUserStats(transformedStats);
        setIsLoading(false);

        // Dispatch scan complete event for score synchronization
        if (user?.id && transformedStats.overallScore > 0) {
          dispatchScanCompleteEvent(user.id, transformedStats.overallScore);

          // For internal scans (user scanning their own repos), check if user has profile
          // If not, show profile setup modal
          // Check if this is an internal scan (not scanning someone else)
          const isInternalScan =
            scanResults.scanType === "self" ||
            scanResults.scanType === "myself" ||
            (scanResults.scanType !== "external_user" &&
              scanResults.scanType !== "external" &&
              !scanResults.isExternalScan &&
              (!scanResults.targetUsername ||
                scanResults.targetUsername === user.githubUsername));

          console.log("🔍 Scan type check:", {
            scanType: scanResults.scanType,
            targetUsername: scanResults.targetUsername,
            userGithubUsername: user.githubUsername,
            isInternalScan,
          });

          if (isInternalScan) {
            console.log("✅ Internal scan detected, checking profile...");
            checkAndShowProfileModal();
          } else {
            console.log("🔄 External scan detected, skipping profile check");
          }
        }

        return;
      }

      // Only load authenticated user data if no scan results are expected
      // and we're not in a scanning/external user context
      if (!user?.id) {
        setError(
          "Please log in to view your dashboard or scan a GitHub profile."
        );
        setIsLoading(false);
        return;
      }

      // Don't automatically load authenticated user data
      // Let the user explicitly scan their own profile if needed
      setError(
        "Welcome! Please scan a GitHub profile to view detailed analytics and insights."
      );
      setIsLoading(false);
    };

    loadUserStats();
  }, [user?.id, scanResults]);

  // Calculate derived stats - Only show Overall Score if repos have been evaluated
  const stats = userStats
    ? [
        // Only include Overall Score if repos have been evaluated
        ...(scanResults &&
        (scanResults.evaluatedCount > 0 || scanResults.analyzed)
          ? [
              {
                label: "Overall Score",
                value: userStats.overallScore.toFixed(1),
                icon: Award,
                color: "text-primary-500",
                bgColor: "bg-primary-50",
                change: userStats.lastScanDate ? "Live Data" : "GitHub Data",
              },
            ]
          : []),
        {
          label: "Public Repositories",
          value: userStats.repositoryCount.toString(),
          icon: GitBranch,
          color: "text-secondary-500",
          bgColor: "bg-secondary-50",
          change: userStats.githubProfile
            ? `${userStats.githubProfile.public_repos} total`
            : "GitHub",
        },
        {
          label: "Languages Used",
          value: userStats.languages.length.toString(),
          icon: Code,
          color: "text-accent-500",
          bgColor: "bg-accent-50",
          change:
            userStats.languages.length > 0
              ? `${userStats.languages[0]?.language} primary`
              : "Various",
        },
        {
          label: "GitHub Followers",
          value: userStats.githubProfile?.followers?.toString() || "0",
          icon: Activity,
          color: "text-success-500",
          bgColor: "bg-success-50",
          change: userStats.githubProfile?.following
            ? `${userStats.githubProfile.following} following`
            : "GitHub",
        },
      ]
    : [];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <div className="h-8 bg-gray-200 rounded w-48 mb-2 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-64 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-16"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    const isLoadingError = error.includes("loading");

    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Dashboard Overview
          </h1>
          <p className="text-gray-600">
            {isLoadingError
              ? "Your account is being prepared"
              : "Scan a GitHub profile to get started"}
          </p>
        </div>
        <div className="card p-8 text-center">
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
              <Shield className="h-12 w-12 mx-auto" />
            )}
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {isLoadingError ? "Account Loading" : "No Profile Data"}
          </h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">{error}</p>
          <div className="space-y-3">
            <button
              onClick={() => (window.location.href = "/developer/auth")}
              className="bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
            >
              Scan a GitHub Profile
            </button>
            {isLoadingError && (
              <div className="text-sm text-gray-500 mt-4">
                <p>
                  If this persists, try refreshing the page or scanning a
                  different profile.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Sync Notification */}
      {syncNotification && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="fixed top-4 right-4 z-50 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg"
        >
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5" />
            <span className="font-medium">{syncNotification}</span>
          </div>
        </motion.div>
      )}

      <div className="space-y-6">
        <div>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {scanResults?.targetUsername
                  ? `${scanResults.targetUsername}'s Profile`
                  : "Dashboard Overview"}
              </h1>
              <p className="text-gray-600">
                {scanResults?.targetUsername
                  ? `Analysis of ${scanResults.targetUsername}'s GitHub profile`
                  : "Your coding profile at a glance"}
              </p>
            </div>
            {scanResults && (
              <div className="flex items-center space-x-2">
                {scanResults.targetUsername && (
                  <div className="flex items-center space-x-2 bg-blue-50 text-blue-700 px-4 py-2 rounded-lg border border-blue-200 mr-2">
                    <span className="text-sm font-medium">
                      {scanResults.scanType === "self"
                        ? "Your Profile"
                        : "External Profile Scan"}
                    </span>
                  </div>
                )}
                <div className="flex items-center space-x-2 bg-green-50 text-green-700 px-4 py-2 rounded-lg border border-green-200">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium">
                    Fresh Scan Results
                    {scanResults.evaluation_method?.includes("ml") && (
                      <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                        AI Enhanced
                      </span>
                    )}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="card p-6 hover:shadow-lg transition-shadow duration-200"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
                <div className="text-right">
                  <div className="text-xs text-green-600 font-medium">
                    {stat.change}
                  </div>
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">
                  {stat.label}
                </p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Get Scores Button - Show above stats when no scores */}
        {scanResults &&
          (!scanResults.overallScore ||
            (scanResults.evaluatedCount === 0 && !scanResults.analyzed)) &&
          scanResults.targetUsername && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{
                opacity: 1,
                y: 0,
                scale: [1, 1.02, 1], // Subtle pulse effect
              }}
              transition={{
                scale: {
                  repeat: Infinity,
                  duration: 2,
                  ease: "easeInOut",
                },
              }}
              className="mb-4"
            >
              <AnalyzeButton
                username={scanResults.targetUsername}
                analyzed={false}
                onAnalysisComplete={() => {
                  setIsAnalyzing(false);
                  window.location.reload();
                }}
              />
            </motion.div>
          )}

        {/* View Repositories Button - Show after analysis with scores */}
        {scanResults &&
          scanResults.overallScore > 0 &&
          scanResults.repositories &&
          scanResults.repositories.some(
            (r: any) => r.analysis?.acid_scores?.overall
          ) && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4"
            >
              <div className="card p-4 sm:p-5 bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 mt-1">
                        <svg
                          className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm sm:text-base font-semibold text-gray-900 mb-1">
                          Analysis Complete!
                        </h3>
                        <p className="text-xs sm:text-sm text-gray-700 mb-2">
                          To view each repository's individual scores and
                          detailed metrics, move to the Repositories tab.
                        </p>
                        <p className="text-xs text-blue-700 flex flex-wrap gap-x-2">
                          <span>
                            {
                              scanResults.repositories.filter(
                                (r: any) => r.category === "flagship"
                              ).length
                            }{" "}
                            Flagship
                          </span>
                          <span>•</span>
                          <span>
                            {
                              scanResults.repositories.filter(
                                (r: any) => r.category === "significant"
                              ).length
                            }{" "}
                            Significant
                          </span>
                          <span>•</span>
                          <span>
                            {
                              scanResults.repositories.filter(
                                (r: any) => r.analysis?.acid_scores?.overall
                              ).length
                            }{" "}
                            Evaluated
                          </span>
                        </p>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() =>
                      navigate("/developer/dashboard/repositories")
                    }
                    className="w-full sm:w-auto sm:ml-4 px-4 sm:px-5 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2 shadow-md hover:shadow-lg"
                  >
                    <GitBranch className="h-4 w-4" />
                    <span className="text-sm sm:text-base">
                      View Repositories
                    </span>
                  </button>
                </div>
              </div>
            </motion.div>
          )}

        {/* Analysis Section - Show quality metrics ONLY for evaluated scans */}
        {scanResults &&
          scanResults.overallScore > 0 &&
          (scanResults.evaluatedCount > 0 || scanResults.analyzed) && (
            <>
              {/* Show Analyze Button if not analyzed (external scans only) */}
              {scanResults?.scanType === "other" &&
                !scanResults?.analyzed &&
                !isAnalyzing && (
                  <AnalyzeButton
                    username={scanResults.targetUsername}
                    analyzed={false}
                    onAnalysisComplete={() => {
                      setIsAnalyzing(false);
                      window.location.reload();
                    }}
                  />
                )}

              {/* Show Analysis Progress if in progress (external scans only) */}
              {scanResults?.scanType === "other" &&
                isAnalyzing &&
                analysisStatus && (
                  <AnalysisProgress
                    status={analysisStatus.status}
                    progress={analysisStatus.progress}
                    message={analysisStatus.message}
                    error={analysisStatus.error}
                  />
                )}

              {/* Show Animated Quality Wheel ONLY after repositories have been evaluated */}
              {scanResults?.overallScore &&
                (scanResults.evaluatedCount > 0 || scanResults.analyzed) &&
                // Show for internal scans (self/myself) OR external scans that have been analyzed
                (scanResults.scanType === "myself" ||
                  scanResults.scanType === "self" ||
                  scanResults.analyzed) && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="card p-8 bg-gradient-to-br from-primary-50 to-blue-50"
                  >
                    <div className="text-center mb-6">
                      <h2 className="text-2xl font-bold text-gray-900 mb-2">
                        {scanResults.scanType === "myself" ||
                        scanResults.scanType === "self"
                          ? "Your Code Quality Score"
                          : "Code Quality Analysis"}
                      </h2>
                      <p className="text-gray-600">
                        Based on{" "}
                        {scanResults.evaluatedCount ||
                          scanResults.repositoryCount ||
                          0}{" "}
                        evaluated repositories
                        {scanResults.analyzedAt && (
                          <span className="ml-2 text-sm">
                            • Analyzed{" "}
                            {new Date(
                              scanResults.analyzedAt
                            ).toLocaleDateString()}
                          </span>
                        )}
                        {!scanResults.analyzedAt && (
                          <span className="ml-2 text-sm">
                            • Scanned just now
                          </span>
                        )}
                      </p>
                    </div>

                    {/* Animated Quality Wheel */}
                    <div
                      className="flex items-center justify-center mb-8"
                      style={{ minHeight: "500px" }}
                    >
                      <AnimatedQualityWheel
                        qualityMetrics={{
                          readability:
                            scanResults.qualityMetrics?.readability ||
                            scanResults.repositories?.[0]?.evaluation
                              ?.quality_metrics?.readability ||
                            75,
                          maintainability:
                            scanResults.qualityMetrics?.maintainability ||
                            scanResults.repositories?.[0]?.evaluation
                              ?.quality_metrics?.maintainability ||
                            70,
                          security:
                            scanResults.qualityMetrics?.security ||
                            scanResults.repositories?.[0]?.evaluation
                              ?.quality_metrics?.security ||
                            85,
                          test_coverage:
                            scanResults.qualityMetrics?.test_coverage ||
                            scanResults.repositories?.[0]?.evaluation
                              ?.quality_metrics?.test_coverage ||
                            60,
                          documentation:
                            scanResults.qualityMetrics?.documentation ||
                            scanResults.repositories?.[0]?.evaluation
                              ?.quality_metrics?.documentation ||
                            65,
                          performance: 75,
                          complexity: 70,
                          best_practices: 80,
                        }}
                        overallScore={scanResults.overallScore}
                        flagshipCount={scanResults.flagshipCount || 0}
                        significantCount={scanResults.significantCount || 0}
                        supportingCount={scanResults.supportingCount || 0}
                      />
                    </div>

                    {/* Repository Distribution */}
                    {(scanResults.flagshipCount > 0 ||
                      scanResults.significantCount > 0) && (
                      <div className="grid grid-cols-3 gap-4 mb-6">
                        <div className="text-center p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                          <div className="text-3xl font-bold text-yellow-700">
                            {scanResults.flagshipCount || 0}
                          </div>
                          <div className="text-sm text-yellow-600 font-medium">
                            🏆 Flagship
                          </div>
                        </div>
                        <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
                          <div className="text-3xl font-bold text-blue-700">
                            {scanResults.significantCount || 0}
                          </div>
                          <div className="text-sm text-blue-600 font-medium">
                            ⭐ Significant
                          </div>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg border border-gray-200">
                          <div className="text-3xl font-bold text-gray-700">
                            {scanResults.supportingCount || 0}
                          </div>
                          <div className="text-sm text-gray-600 font-medium">
                            📋 Supporting
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Score Breakdown */}
                    {scanResults.scoreBreakdown && (
                      <div className="space-y-3">
                        <h3 className="text-sm font-semibold text-gray-700 mb-2">
                          Score Breakdown
                        </h3>
                        {scanResults.scoreBreakdown.components?.map(
                          (component: any) => (
                            <div
                              key={component.category}
                              className="flex items-center justify-between"
                            >
                              <div className="flex items-center space-x-2">
                                <span className="text-sm font-medium text-gray-700">
                                  {component.category === "flagship"
                                    ? "🏆"
                                    : "⭐"}{" "}
                                  {component.category.charAt(0).toUpperCase() +
                                    component.category.slice(1)}
                                </span>
                                <span className="text-xs text-gray-500">
                                  ({component.count} repos,{" "}
                                  {component.percentage} weight)
                                </span>
                              </div>
                              <div className="flex items-center space-x-2">
                                <div className="text-sm font-semibold text-gray-900">
                                  {component.average_score.toFixed(1)}
                                </div>
                                <div className="text-xs text-gray-500">
                                  → {component.contribution.toFixed(1)} pts
                                </div>
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    )}
                  </motion.div>
                )}
            </>
          )}

        {/* GitHub Profile Section */}
        {userStats?.githubProfile && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {scanResults?.scanType === "other"
                  ? "User Profile"
                  : "Your GitHub Profile"}
              </h3>
              <a
                href={`https://github.com/${userStats.githubProfile.username}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800"
              >
                View on GitHub
                <svg
                  className="w-4 h-4 ml-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
              </a>
            </div>
            <div className="flex items-start space-x-6">
              {userStats.githubProfile.avatar_url && (
                <div className="flex-shrink-0">
                  <img
                    src={userStats.githubProfile.avatar_url}
                    alt="GitHub Avatar"
                    className="w-20 h-20 rounded-full border-2 border-gray-200"
                  />
                </div>
              )}
              <div className="flex-1">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-xl font-semibold text-gray-900">
                      {userStats.githubProfile.name ||
                        userStats.githubProfile.username}
                    </h4>
                    <p className="text-sm text-gray-600 mb-2">
                      @{userStats.githubProfile.username}
                    </p>
                    {userStats.githubProfile.bio && (
                      <p className="text-sm text-gray-700 mb-4 leading-relaxed">
                        {userStats.githubProfile.bio}
                      </p>
                    )}
                    <div className="space-y-2">
                      {userStats.githubProfile.location && (
                        <div className="flex items-center text-sm text-gray-600">
                          <span className="mr-2">📍</span>
                          <span>{userStats.githubProfile.location}</span>
                        </div>
                      )}
                      {userStats.githubProfile.company && (
                        <div className="flex items-center text-sm text-gray-600">
                          <span className="mr-2">🏢</span>
                          <span>{userStats.githubProfile.company}</span>
                        </div>
                      )}
                      {userStats.githubProfile.blog && (
                        <div className="flex items-center text-sm text-gray-600">
                          <span className="mr-2">🔗</span>
                          <a
                            href={
                              userStats.githubProfile.blog.startsWith("http")
                                ? userStats.githubProfile.blog
                                : `https://${userStats.githubProfile.blog}`
                            }
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800"
                          >
                            {userStats.githubProfile.blog}
                          </a>
                        </div>
                      )}
                      {userStats.githubProfile.created_at && (
                        <div className="flex items-center text-sm text-gray-600">
                          <span className="mr-2">📅</span>
                          <span>
                            Joined{" "}
                            {new Date(
                              userStats.githubProfile.created_at
                            ).toLocaleDateString("en-US", {
                              year: "numeric",
                              month: "long",
                            })}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">
                        {userStats.githubProfile.public_repos}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        Public Repos
                      </div>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">
                        {userStats.githubProfile.followers}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        Followers
                      </div>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">
                        {userStats.githubProfile.following}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        Following
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* GitHub Activity Calendar - Show between profile and rankings */}
        {userStats?.githubProfile && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <GitHubActivityCalendar
              username={userStats.githubProfile.username}
              githubToken={user?.githubToken} // Use user's GitHub token if available
              className="mb-6"
            />
          </motion.div>
        )}

        {/* Ranking Widget - Show for both internal and external scans */}
        {(() => {
          // Determine if this is an internal or external scan
          const isInternalScan =
            !scanResults ||
            scanResults.scanType === "self" ||
            scanResults.scanType === "myself" ||
            (scanResults.scanType !== "external_user" &&
              scanResults.scanType !== "external" &&
              !scanResults.isExternalScan &&
              (!scanResults.targetUsername ||
                scanResults.targetUsername === user?.githubUsername));

          const isExternalScan =
            scanResults && !isInternalScan && scanResults.targetUsername;

          console.log("🎯 Ranking Widget Display Logic:", {
            isInternalScan,
            isExternalScan,
            scanType: scanResults?.scanType,
            targetUsername: scanResults?.targetUsername,
            userGithubUsername: user?.githubUsername,
          });

          if (isInternalScan) {
            // Internal scan - show authenticated user's rankings
            return (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                <RankingWidget
                  onSetupProfile={() => setIsProfileModalOpen(true)}
                />
              </motion.div>
            );
          } else if (isExternalScan) {
            // External scan - show scanned user's rankings by GitHub username
            return (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                <ExternalRankingWidget
                  githubUsername={scanResults.targetUsername}
                />
              </motion.div>
            );
          }

          return null;
        })()}

        {/* Contribution Statistics */}
        {scanResults?.contributionStats && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="card p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-900">
                Contribution Activity
              </h3>
              <div className="text-sm text-gray-500">Last 365 days</div>
            </div>

            {/* Contribution Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {scanResults.contributionStats.contribution_streaks
                    ?.current_streak || 0}
                </div>
                <div className="text-xs text-gray-600 mt-1">Current Streak</div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {scanResults.contributionStats.contribution_streaks
                    ?.longest_streak || 0}
                </div>
                <div className="text-xs text-gray-600 mt-1">Longest Streak</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {scanResults.contributionStats.contribution_patterns
                    ?.total_active_days || 0}
                </div>
                <div className="text-xs text-gray-600 mt-1">Active Days</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">
                  {scanResults.contributionStats.contribution_patterns
                    ?.most_active_day?.day || "N/A"}
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  Most Active Day
                </div>
              </div>
            </div>

            {/* Contribution Calendar Preview */}
            {scanResults.contributionStats.calendar_data && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">
                  Recent Activity
                </h4>
                <div className="flex flex-wrap gap-1">
                  {scanResults.contributionStats.calendar_data
                    .slice(-84)
                    .map((day: any, index: number) => (
                      <div
                        key={day.date}
                        className="w-3 h-3 rounded-sm"
                        style={{ backgroundColor: day.color }}
                        title={`${day.date}: ${day.count} contributions`}
                      />
                    ))}
                </div>
                <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                  <span>Less</span>
                  <div className="flex gap-1">
                    <div className="w-3 h-3 rounded-sm bg-gray-100"></div>
                    <div className="w-3 h-3 rounded-sm bg-green-200"></div>
                    <div className="w-3 h-3 rounded-sm bg-green-400"></div>
                    <div className="w-3 h-3 rounded-sm bg-green-600"></div>
                    <div className="w-3 h-3 rounded-sm bg-green-800"></div>
                  </div>
                  <span>More</span>
                </div>
              </div>
            )}

            {/* Top Contributing Repositories */}
            {scanResults.contributionStats.commit_repositories && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">
                  Top Contributing Repositories
                </h4>
                <div className="space-y-2">
                  {scanResults.contributionStats.commit_repositories
                    .slice(0, 5)
                    .map((repo: any) => (
                      <div
                        key={repo.name}
                        className="flex items-center justify-between p-2 bg-gray-50 rounded"
                      >
                        <div className="flex items-center space-x-3">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: repo.language_color }}
                          />
                          <span className="text-sm font-medium">
                            {repo.name}
                          </span>
                          <span className="text-xs text-gray-500">
                            {repo.language}
                          </span>
                        </div>
                        <span className="text-sm text-gray-600">
                          {repo.contributions} commits
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Language Distribution */}
        {userStats && userStats.languages.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="card p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-900">
                Language Distribution
              </h3>
              <button
                onClick={() =>
                  (window.location.href = "/developer/dashboard/languages")
                }
                className="text-primary-500 hover:text-primary-600 text-sm font-medium"
              >
                View All →
              </button>
            </div>
            <div className="space-y-4">
              {userStats.languages.slice(0, 5).map((lang, index) => (
                <div
                  key={lang.language}
                  className="flex items-center space-x-4"
                >
                  <div className="w-20 text-sm font-medium text-gray-700">
                    {lang.language}
                  </div>
                  <div className="flex-1 bg-gray-200 rounded-full h-3">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${lang.percentage}%` }}
                      transition={{ delay: 1.0 + index * 0.1, duration: 0.8 }}
                      className="h-3 rounded-full bg-gradient-to-r from-primary-500 to-secondary-500"
                    />
                  </div>
                  <div className="w-16 text-sm font-semibold text-gray-900 text-right">
                    {lang.percentage.toFixed(1)}%
                  </div>
                  <div className="w-20 text-xs text-gray-500 text-right">
                    {lang.repositories} repos
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Profile Summary */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-6"
        >
          <div className="card p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              {scanResults?.targetUsername
                ? `${scanResults.targetUsername}'s Summary`
                : "Profile Summary"}
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">GitHub Username</span>
                <span className="font-medium text-gray-900">
                  {scanResults?.targetUsername || user?.githubUsername || "N/A"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Repositories Analyzed</span>
                <span className="font-medium text-gray-900">
                  {userStats?.repositoryCount || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Scan Date</span>
                <span className="font-medium text-gray-900">
                  {scanResults
                    ? "Just now"
                    : userStats?.lastScanDate
                    ? new Date(userStats.lastScanDate).toLocaleDateString()
                    : "Never"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Primary Language</span>
                <span className="font-medium text-gray-900">
                  {userStats?.languages[0]?.language || "N/A"}
                </span>
              </div>
              {scanResults?.evaluation_method && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Evaluation Method</span>
                  <span className="font-medium text-gray-900">
                    {scanResults.evaluation_method.includes("ml")
                      ? "AI + ACID"
                      : "ACID Scoring"}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Repository Overview Stats */}
          {scanResults?.repositoryOverview && (
            <div className="card p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Repository Overview
              </h3>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <div className="text-lg font-bold text-blue-600">
                      {scanResults.repositoryOverview.original_repositories ||
                        0}
                    </div>
                    <div className="text-xs text-gray-600">Original Repos</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="text-lg font-bold text-green-600">
                      {scanResults.repositoryOverview.total_stars || 0}
                    </div>
                    <div className="text-xs text-gray-600">Total Stars</div>
                  </div>
                </div>

                {scanResults.repositoryOverview.most_starred && (
                  <div className="p-3 bg-yellow-50 rounded-lg">
                    <div className="text-sm font-medium text-gray-900">
                      Most Starred Repository
                    </div>
                    <div className="text-sm text-gray-600">
                      <strong>
                        {scanResults.repositoryOverview.most_starred.name}
                      </strong>
                      {scanResults.repositoryOverview.most_starred.language && (
                        <span className="ml-2 text-xs bg-gray-200 px-2 py-1 rounded">
                          {scanResults.repositoryOverview.most_starred.language}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {scanResults.repositoryOverview.recently_updated &&
                  scanResults.repositoryOverview.recently_updated.length >
                    0 && (
                    <div>
                      <div className="text-sm font-medium text-gray-900 mb-2">
                        Recently Updated
                      </div>
                      <div className="space-y-1">
                        {scanResults.repositoryOverview.recently_updated
                          .slice(0, 3)
                          .map((repo: any) => (
                            <div
                              key={repo.name}
                              className="flex items-center justify-between text-sm"
                            >
                              <span className="text-gray-700">{repo.name}</span>
                              <span className="text-xs text-gray-500">
                                {new Date(repo.updated_at).toLocaleDateString()}
                              </span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
              </div>
            </div>
          )}

          <div className="card p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              {scanResults?.targetUsername ? "Analysis Insights" : "Next Steps"}
            </h3>
            <div className="space-y-3">
              {scanResults?.targetUsername ? (
                <>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
                    <div>
                      <p className="font-medium text-gray-900">
                        Profile Analysis Complete
                      </p>
                      <p className="text-sm text-gray-600">
                        Analyzed {userStats?.repositoryCount || 0} repositories
                        from {scanResults.targetUsername}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-secondary-500 rounded-full mt-2"></div>
                    <div>
                      <p className="font-medium text-gray-900">
                        Technology Stack Identified
                      </p>
                      <p className="text-sm text-gray-600">
                        Primary focus on{" "}
                        {userStats?.languages[0]?.language ||
                          "various technologies"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-accent-500 rounded-full mt-2"></div>
                    <div>
                      <p className="font-medium text-gray-900">
                        Scan Another User
                      </p>
                      <p className="text-sm text-gray-600">
                        <button
                          onClick={() =>
                            (window.location.href = "/developer/auth")
                          }
                          className="text-blue-600 hover:text-blue-800"
                        >
                          Analyze another GitHub profile
                        </button>
                      </p>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-secondary-500 rounded-full mt-2"></div>
                    <div>
                      <p className="font-medium text-gray-900">
                        Explore your tech stack
                      </p>
                      <p className="text-sm text-gray-600">
                        See what technologies you're using across projects
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-accent-500 rounded-full mt-2"></div>
                    <div>
                      <p className="font-medium text-gray-900">
                        Check your roadmap
                      </p>
                      <p className="text-sm text-gray-600">
                        Get personalized learning recommendations
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
                    <div>
                      <p className="font-medium text-gray-900">
                        View detailed repositories
                      </p>
                      <p className="text-sm text-gray-600">
                        Explore individual repository analysis and metrics
                      </p>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Profile Setup Modal */}
      <ProfileSetupModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        onSuccess={() => {
          setIsProfileModalOpen(false);
          // Optionally refresh rankings or show success message
        }}
      />
    </>
  );
};

export default Overview;
