import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Loader2,
  CheckCircle,
  Github,
  Brain,
  TrendingUp,
  AlertCircle,
  RefreshCw,
  ArrowLeft,
  User,
  GitBranch,
  Clock,
  Code,
  GitPullRequest,
  FileText,
  Star,
  Activity,
  Calculator,
} from "lucide-react";
import { scanAPI } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import { useEnhancedScanProgress } from "../hooks/useEnhancedScanProgress";
import LiveFeedPanel from "../components/LiveFeedPanel";

interface ScanningProgressProps {
  scanType: "self" | "other";
  githubUrl?: string;
  username?: string;
}

const ScanningProgress: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const { scanType, githubUrl, username } =
    (location.state as ScanningProgressProps) || {};

  const [scanId, setScanId] = useState<string>("");
  const [error, setError] = useState<any>(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [scanResults, setScanResults] = useState<any>(null);

  // Simulated progress state (for when WebSocket is not available)
  const [simulatedProgress, setSimulatedProgress] = useState(0);
  const [simulatedPhase, setSimulatedPhase] = useState("connecting");
  const [simulatedFeedItems, setSimulatedFeedItems] = useState<any[]>([]);
  const [simulatedAccountInfo, setSimulatedAccountInfo] = useState<any>(null);
  const [simulatedRepoProgress, setSimulatedRepoProgress] = useState<any>(null);
  const [, setIsSimulating] = useState(false);
  const [maxSimulatedProgress, setMaxSimulatedProgress] = useState(0);

  // Use enhanced scan progress hook
  const {
    isConnected,
    isPaused,
    scanDuration,
    estimatedTimeRemaining,
    liveFeedItems,
    accountInfo,
    repositoryProgress,
    currentRepository,
    repositoriesProcessed,
    totalRepositories,
    prProgress,
    issueProgress,
    analysisMetrics,
    currentPhase,
    currentOperation,
    progressPercentage,
    startScan,
    stopScan,
    togglePause,
  } = useEnhancedScanProgress({
    scanId,
    onComplete: (finalProgress) => {
      console.log("Scan completed:", finalProgress);
    },
    onError: (errorMsg) => {
      console.error("Scan error:", errorMsg);
    },
  });

  useEffect(() => {
    if (!scanType) {
      navigate("/developer/auth");
      return;
    }
    startScanning();
  }, [scanType, githubUrl, username]);

  const addSimulatedFeedItem = (
    title: string,
    description: string,
    type: "info" | "success" = "info"
  ) => {
    const newItem = {
      id: `feed-${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
      type,
      title,
      description,
      status: type === "success" ? "completed" : "in_progress",
    };
    setSimulatedFeedItems((prev) => [...prev, newItem]);
  };

  // Helper function to ensure progress only moves forward
  const updateSimulatedProgress = (newProgress: number) => {
    setSimulatedProgress((currentProgress) => {
      const finalProgress = Math.max(currentProgress, newProgress);
      setMaxSimulatedProgress(finalProgress);
      return finalProgress;
    });
  };

  const simulateProgress = async (targetUsername: string, userInfo: any) => {
    setIsSimulating(true);
    // Reset progress tracking for new scan
    setMaxSimulatedProgress(0);
    setSimulatedProgress(0);

    // Phase 1: Connecting (0-10%)
    setSimulatedPhase("connecting");
    updateSimulatedProgress(5);
    addSimulatedFeedItem(
      "Connecting to GitHub",
      "Establishing secure connection..."
    );
    await new Promise((resolve) => setTimeout(resolve, 800));

    updateSimulatedProgress(10);
    addSimulatedFeedItem(
      "Connection Established",
      "Successfully connected to GitHub API",
      "success"
    );
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Phase 2: Fetching Profile (10-20%)
    setSimulatedPhase("fetching_profile");
    updateSimulatedProgress(12);
    addSimulatedFeedItem(
      "Fetching Profile",
      `Loading ${targetUsername}'s profile...`
    );
    await new Promise((resolve) => setTimeout(resolve, 600));

    // Set account info
    setSimulatedAccountInfo({
      username: targetUsername,
      accountType: "User",
      avatarUrl:
        userInfo.avatar_url || `https://github.com/${targetUsername}.png`,
      followers: userInfo.followers || 0,
      following: userInfo.following || 0,
      publicRepos: userInfo.public_repos || 0,
      totalStars: 0,
      contributionStreak: 0,
    });

    updateSimulatedProgress(20);
    addSimulatedFeedItem(
      "Profile Loaded",
      `Found ${userInfo.public_repos} repositories`,
      "success"
    );
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Phase 3: Fetching Repositories (20-60%)
    setSimulatedPhase("fetching_repos");
    const repoCount = userInfo.public_repos || 10;
    const reposToSimulate = Math.min(repoCount, 5); // Simulate first 5 repos

    for (let i = 0; i < reposToSimulate; i++) {
      const progress = 20 + ((i + 1) / reposToSimulate) * 40;
      updateSimulatedProgress(progress);
      setSimulatedRepoProgress({
        current: i + 1,
        total: repoCount,
        currentRepo: {
          name: `repository-${i + 1}`,
          fullName: `${targetUsername}/repository-${i + 1}`,
          description: "Analyzing repository...",
          language: "TypeScript",
          stars: Math.floor(Math.random() * 100),
          forks: Math.floor(Math.random() * 20),
          size: Math.floor(Math.random() * 1000),
          lastUpdated: new Date().toISOString(),
        },
      });
      addSimulatedFeedItem(
        "Fetching Repository",
        `Loading ${targetUsername}/repository-${i + 1}...`
      );
      await new Promise((resolve) => setTimeout(resolve, 800));

      addSimulatedFeedItem(
        "Repository Fetched",
        `Analyzed repository-${i + 1}`,
        "success"
      );
      await new Promise((resolve) => setTimeout(resolve, 400));
    }

    // Phase 4: Analyzing Code (60-80%)
    setSimulatedPhase("analyzing_code");
    updateSimulatedProgress(65);
    addSimulatedFeedItem(
      "Analyzing Code",
      "Scanning files and calculating metrics..."
    );
    await new Promise((resolve) => setTimeout(resolve, 1000));

    updateSimulatedProgress(75);
    addSimulatedFeedItem(
      "Code Analysis",
      "Processing language statistics...",
      "success"
    );
    await new Promise((resolve) => setTimeout(resolve, 800));

    // Phase 5: Calculating Scores (80-95%)
    setSimulatedPhase("calculating_scores");
    updateSimulatedProgress(85);
    addSimulatedFeedItem(
      "Calculating Scores",
      "Running ACID scoring algorithm..."
    );
    await new Promise((resolve) => setTimeout(resolve, 1000));

    updateSimulatedProgress(92);
    addSimulatedFeedItem(
      "Scores Calculated",
      "ACID metrics computed successfully",
      "success"
    );
    await new Promise((resolve) => setTimeout(resolve, 600));

    // Phase 6: Generating Insights (95-100%)
    setSimulatedPhase("generating_insights");
    updateSimulatedProgress(96);
    addSimulatedFeedItem(
      "Generating Insights",
      "Creating skill assessment and roadmap..."
    );
    await new Promise((resolve) => setTimeout(resolve, 800));

    updateSimulatedProgress(100);
    setSimulatedPhase("completed");
    addSimulatedFeedItem(
      "Scan Complete",
      "All analysis completed successfully!",
      "success"
    );

    setIsSimulating(false);
  };

  const startScanning = async () => {
    try {
      setError(null);

      let targetUsername = username;

      if (scanType === "other" && githubUrl) {
        const urlMatch = githubUrl.match(/github\.com\/([a-zA-Z0-9_-]+)/);
        if (!urlMatch) {
          throw new Error("Invalid GitHub URL format");
        }
        targetUsername = urlMatch[1];
      } else if (scanType === "self") {
        targetUsername = username || user?.githubUsername;
      }

      if (!targetUsername) {
        throw new Error("No username found for scanning");
      }

      console.log("Starting scan for username:", targetUsername);

      // Generate scan ID and start tracking
      const newScanId = `scan-${Date.now()}-${targetUsername}`;
      setScanId(newScanId);
      startScan(newScanId);

      // Get user info first for simulation
      const userInfo = await scanAPI.getUserInfo(targetUsername);

      // Use the actual GitHub username from the API response (preserves case)
      const actualUsername = userInfo.login || targetUsername;

      // Start simulated progress in parallel with actual scan
      simulateProgress(actualUsername, userInfo);

      // Start the actual scan
      let scanData;
      try {
        const mlStatus = await scanAPI.getMLStatus();
        if (mlStatus.ml_status?.available) {
          scanData = await scanAPI.evaluateWithML({
            github_url: githubUrl || `https://github.com/${actualUsername}`,
            username: actualUsername,
          });
        } else {
          throw new Error("ML not available");
        }
      } catch (mlError) {
        // Force fresh scan - always fetch from GitHub, not cache
        scanData = await scanAPI.scanExternalUser(actualUsername, true);
      }

      // Extract data from response if it's wrapped
      const actualScanData = scanData.data || scanData;

      console.log("📊 [ScanningProgress] Scan data structure:", {
        hasData: !!scanData.data,
        hasRepositories: !!actualScanData.repositories,
        repositoryCount: actualScanData.repositories?.length,
        hasSummary: !!actualScanData.summary,
        summary: actualScanData.summary,
      });

      const results = {
        ...actualScanData,
        userInfo,
        scanType,
        targetUsername: actualUsername, // Use actual GitHub username with proper case
        repositoryCount:
          actualScanData.repositoriesCount ||
          actualScanData.repositoryCount ||
          userInfo.public_repos,
      };

      setScanResults(results);

      // Navigate to developer dashboard with scan results after a brief delay
      setTimeout(() => {
        console.log("🎯 Navigating to developer dashboard with scan results");
        console.log("📊 Scan results being passed:", results);
        navigate("/developer/dashboard", {
          state: { scanResults: results },
          replace: true, // Replace current history entry to prevent back navigation issues
        });
      }, 2000);
    } catch (err: any) {
      console.error("Scanning error:", err);
      setError({
        type: "Scanning Error",
        message: err.response?.data?.detail || err.message || "Scanning failed",
        code: "SCAN_ERROR",
      });
      setIsSimulating(false);
    }
  };

  const retryScanning = () => {
    setIsRetrying(true);
    setError(null);
    setScanResults(null);
    setTimeout(() => {
      setIsRetrying(false);
      startScanning();
    }, 1000);
  };

  const handleCancel = () => {
    stopScan();
    navigate("/developer/auth");
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const getPhaseIcon = (phase: string) => {
    const icons: Record<string, any> = {
      connecting: Github,
      fetching_profile: User,
      fetching_repos: GitBranch,
      fetching_prs: GitPullRequest,
      fetching_issues: FileText,
      analyzing_code: Code,
      calculating_scores: Calculator,
      generating_insights: Brain,
      completed: CheckCircle,
    };
    return icons[phase] || Activity;
  };

  // Use simulated data if WebSocket is not connected
  const displayPhase = isConnected ? currentPhase : simulatedPhase;
  const displayProgress = isConnected ? progressPercentage : simulatedProgress;
  const displayFeedItems = isConnected ? liveFeedItems : simulatedFeedItems;
  const displayAccountInfo = isConnected ? accountInfo : simulatedAccountInfo;
  const displayRepoProgress = isConnected
    ? repositoryProgress
    : simulatedRepoProgress;
  const displayReposProcessed = isConnected
    ? repositoriesProcessed
    : simulatedRepoProgress?.current || 0;
  const displayTotalRepos = isConnected
    ? totalRepositories
    : simulatedRepoProgress?.total || 0;
  const displayCurrentRepo = isConnected
    ? currentRepository
    : simulatedRepoProgress?.currentRepo;

  const PhaseIcon = getPhaseIcon(displayPhase);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 p-4 overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse"
          style={{ top: "10%", left: "10%" }}
        />
        <div
          className="absolute w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse"
          style={{ top: "60%", right: "10%", animationDelay: "1s" }}
        />
      </div>

      <div className="relative max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full mb-6 shadow-lg shadow-blue-500/50">
            <PhaseIcon className="h-10 w-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-4">
            {scanType === "self"
              ? "Scanning Your Profile"
              : "Analyzing GitHub Profile"}
          </h1>
          <p className="text-xl text-blue-200 mb-2">
            AI-Powered Repository Analysis in Progress
          </p>
          {isConnected ? (
            <div className="inline-flex items-center gap-2 text-green-400 text-sm">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span>Connected to live updates</span>
            </div>
          ) : (
            <div className="inline-flex items-center gap-2 text-yellow-400 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Connecting...</span>
            </div>
          )}
        </motion.div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Progress & Metrics */}
          <div className="lg:col-span-2 space-y-6">
            {/* Progress Overview Card */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-6 border border-white/20"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold text-white">
                  Scan Progress
                </h2>
                <span className="text-4xl font-bold text-blue-400">
                  {Math.round(displayProgress)}%
                </span>
              </div>

              {/* Progress Bar */}
              <div className="relative w-full bg-gray-700/50 rounded-full h-4 mb-6 overflow-hidden">
                <motion.div
                  className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${displayProgress}%` }}
                  transition={{ duration: 0.5 }}
                />
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
              </div>

              {/* Current Phase */}
              <div className="bg-blue-500/20 rounded-xl p-4 mb-4 border border-blue-400/30">
                <div className="flex items-center gap-3 mb-2">
                  <PhaseIcon className="w-6 h-6 text-blue-400" />
                  <span className="text-lg font-medium text-white capitalize">
                    {displayPhase.replace(/_/g, " ")}
                  </span>
                </div>
                {currentOperation && (
                  <p className="text-sm text-blue-200 ml-9">
                    {currentOperation.details}
                  </p>
                )}
              </div>

              {/* Time Stats */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white/5 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                    <Clock className="w-4 h-4" />
                    <span>Elapsed Time</span>
                  </div>
                  <div className="text-2xl font-bold text-white">
                    {formatTime(scanDuration)}
                  </div>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                    <TrendingUp className="w-4 h-4" />
                    <span>Est. Remaining</span>
                  </div>
                  <div className="text-2xl font-bold text-white">
                    {estimatedTimeRemaining
                      ? formatTime(estimatedTimeRemaining)
                      : "--:--"}
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Account Info Card */}
            {displayAccountInfo && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-6 border border-white/20"
              >
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <User className="w-5 h-5" />
                  Account Information
                </h3>
                <div className="flex items-center gap-4 mb-4">
                  <img
                    src={displayAccountInfo.avatarUrl}
                    alt={displayAccountInfo.username}
                    className="w-16 h-16 rounded-full border-2 border-blue-400"
                  />
                  <div>
                    <h4 className="text-lg font-bold text-white">
                      {displayAccountInfo.username}
                    </h4>
                    <span className="text-sm text-blue-300">
                      {displayAccountInfo.accountType}
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-400">
                      {displayAccountInfo.publicRepos}
                    </div>
                    <div className="text-xs text-gray-400">Repositories</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-400">
                      {displayAccountInfo.followers}
                    </div>
                    <div className="text-xs text-gray-400">Followers</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-pink-400">
                      {displayAccountInfo.totalStars}
                    </div>
                    <div className="text-xs text-gray-400">Total Stars</div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Repository Progress Card */}
            {displayRepoProgress && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-6 border border-white/20"
              >
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <GitBranch className="w-5 h-5" />
                  Repository Analysis
                </h3>
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-300 mb-2">
                    <span>Progress</span>
                    <span>
                      {displayReposProcessed} / {displayTotalRepos}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700/50 rounded-full h-2">
                    <div
                      className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full transition-all duration-500"
                      style={{
                        width: `${
                          displayTotalRepos > 0
                            ? (displayReposProcessed / displayTotalRepos) * 100
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                </div>
                {displayCurrentRepo && (
                  <div className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-lg p-4 border border-blue-400/30">
                    <div className="flex items-start gap-3">
                      <GitBranch className="w-5 h-5 text-blue-400 mt-1" />
                      <div className="flex-1">
                        <h4 className="font-semibold text-white mb-1">
                          {displayCurrentRepo.name}
                        </h4>
                        <p className="text-sm text-gray-300 mb-2">
                          {displayCurrentRepo.description || "No description"}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          <span className="px-2 py-1 bg-blue-500/30 rounded text-xs text-blue-200">
                            {displayCurrentRepo.language}
                          </span>
                          <span className="px-2 py-1 bg-yellow-500/30 rounded text-xs text-yellow-200 flex items-center gap-1">
                            <Star className="w-3 h-3" />
                            {displayCurrentRepo.stars}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {/* Analysis Metrics Card */}
            {analysisMetrics && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-6 border border-white/20"
              >
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <Code className="w-5 h-5" />
                  Analysis Metrics
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-sm text-gray-400 mb-1">
                      Files Analyzed
                    </div>
                    <div className="text-xl font-bold text-white">
                      {analysisMetrics.filesAnalyzed}
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-sm text-gray-400 mb-1">
                      Lines of Code
                    </div>
                    <div className="text-xl font-bold text-white">
                      {analysisMetrics.linesOfCode.toLocaleString()}
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-sm text-gray-400 mb-1">API Calls</div>
                    <div className="text-xl font-bold text-white">
                      {analysisMetrics.apiCallsMade}
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-sm text-gray-400 mb-1">Rate Limit</div>
                    <div className="text-xl font-bold text-white">
                      {analysisMetrics.apiCallsRemaining}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* PR/Issue Progress */}
            {(prProgress || issueProgress) && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-6 border border-white/20"
              >
                <h3 className="text-xl font-semibold text-white mb-4">
                  Activity Analysis
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  {prProgress && (
                    <div className="bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-lg p-4 border border-indigo-400/30">
                      <div className="flex items-center gap-2 mb-3">
                        <GitPullRequest className="w-5 h-5 text-indigo-400" />
                        <span className="font-semibold text-white">
                          Pull Requests
                        </span>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-300">Open</span>
                          <span className="text-green-400 font-bold">
                            {prProgress.openCount}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-300">Merged</span>
                          <span className="text-purple-400 font-bold">
                            {prProgress.mergedCount}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-300">Closed</span>
                          <span className="text-gray-400 font-bold">
                            {prProgress.closedCount}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                  {issueProgress && (
                    <div className="bg-gradient-to-br from-orange-500/20 to-red-500/20 rounded-lg p-4 border border-orange-400/30">
                      <div className="flex items-center gap-2 mb-3">
                        <FileText className="w-5 h-5 text-orange-400" />
                        <span className="font-semibold text-white">Issues</span>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-300">Open</span>
                          <span className="text-green-400 font-bold">
                            {issueProgress.openCount}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-300">Closed</span>
                          <span className="text-gray-400 font-bold">
                            {issueProgress.closedCount}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-300">Total</span>
                          <span className="text-white font-bold">
                            {issueProgress.total}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </div>

          {/* Right Column - Live Feed */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="sticky top-4"
            >
              <LiveFeedPanel
                items={displayFeedItems}
                maxItems={50}
                autoScroll={true}
                isPaused={isPaused}
                onPauseToggle={togglePause}
                className="bg-white/10 backdrop-blur-lg border-white/20"
              />
            </motion.div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 bg-red-500/20 backdrop-blur-lg rounded-2xl shadow-2xl p-6 border border-red-400/30"
          >
            <div className="flex items-start gap-4">
              <AlertCircle className="h-6 w-6 text-red-400 mt-1 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-semibold text-red-200 mb-2">
                  {error.type}
                </h3>
                <p className="text-red-300 mb-4">{error.message}</p>
                <div className="flex gap-3">
                  <button
                    onClick={retryScanning}
                    disabled={isRetrying}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isRetrying ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4 mr-2" />
                    )}
                    Retry Scan
                  </button>
                  <button
                    onClick={handleCancel}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-gray-600 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Go Back
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Success Display */}
        {scanResults && !error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-6 bg-green-500/20 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-green-400/30 text-center"
          >
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-500 rounded-full mb-4">
              <CheckCircle className="h-8 w-8 text-white" />
            </div>
            <h3 className="text-2xl font-semibold text-white mb-3">
              Scan Complete!
            </h3>
            <p className="text-green-200 mb-4">
              Successfully analyzed {scanResults.repositoryCount} repositories
            </p>
            <div className="flex items-center justify-center gap-2 text-green-300">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="font-medium">Redirecting to dashboard...</span>
            </div>
          </motion.div>
        )}

        {/* Cancel Button */}
        {!scanResults && !error && (
          <div className="text-center mt-6">
            <button
              onClick={handleCancel}
              className="inline-flex items-center text-gray-300 hover:text-white text-sm font-medium transition-colors"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Cancel Scan
            </button>
          </div>
        )}
      </div>

      {/* Custom Animations */}
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(-10px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        .animate-slideIn {
          animation: slideIn 0.3s ease-out;
        }
        @keyframes progress {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-progress {
          animation: progress 1.5s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
};

export default ScanningProgress;
