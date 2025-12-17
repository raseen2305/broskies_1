import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Search, Users, LogOut, RefreshCw } from "lucide-react";
import { useHRAuth } from "../contexts/HRAuthContext";
import CandidateCard, { CandidateCardData } from "../components/CandidateCard";
import FilterPanel, { CandidateFilters } from "../components/FilterPanel";
import hrCandidatesApiService from "../services/hrCandidatesApi";

/**
 * HRDashboard Component
 *
 * Main dashboard for HR users to search and filter developer candidates.
 *
 * Features:
 * - Dashboard layout with header, sidebar, and main content
 * - Navigation bar with user info and sign-out button
 * - Candidate grid display using CandidateCard components
 * - Search bar for filtering by username/skills
 * - Sort controls (by score, upvotes, recent activity)
 * - Pagination controls
 * - Real-time data refresh every 30 seconds
 * - Filter panel integration
 *
 * Requirements: 4.1-4.5, 5.1-5.5, 6.1-6.5, 9.1-9.5, 10.1-10.5
 */
const HRDashboard: React.FC = () => {
  const { hrUser, signOut, isLoading: authLoading } = useHRAuth();

  // State management
  const [candidates, setCandidates] = useState<CandidateCardData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState<CandidateFilters>({});
  const [sortBy, setSortBy] = useState<"score" | "upvotes" | "recent">("score");
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCandidates, setTotalCandidates] = useState(0);

  /**
   * Fetch candidates from API
   */
  const fetchCandidates = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Call real backend API
      const response = await hrCandidatesApiService.getCandidates({
        page,
        limit,
        search: searchQuery,
        sort_by: sortBy,
        ...filters,
      });

      setCandidates(response.candidates);
      setTotalCandidates(response.total);
      setTotalPages(response.total_pages);
    } catch (err: any) {
      console.error("Failed to fetch candidates:", err);
      setError(err.message || "Failed to load candidates");

      // Set empty state on error
      setCandidates([]);
      setTotalCandidates(0);
      setTotalPages(1);
    } finally {
      setIsLoading(false);
    }
  }, [page, limit, searchQuery, filters, sortBy]);

  /**
   * Initial load and refresh on filter/search changes
   */
  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  // Removed automatic refresh - users can manually refresh using the refresh button

  /**
   * Handle sign out
   */
  const handleSignOut = async () => {
    try {
      await signOut();
      window.location.href = "/hr/auth";
    } catch (err) {
      console.error("Sign out failed:", err);
    }
  };

  /**
   * Handle manual refresh
   */
  const handleRefresh = () => {
    fetchCandidates();
  };

  // Paginated candidates
  const paginatedCandidates = candidates.slice(
    (page - 1) * limit,
    page * limit
  );

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f8fafc] via-[#f1f5f9] to-[#e0e7ff] transition-all duration-500">
      {/* Navigation Header */}
      <nav className="bg-white/90 backdrop-blur-md shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo and Title */}
            <div className="flex items-center space-x-3">
              <Users className="h-8 w-8 text-primary-600" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  HR Dashboard
                </h1>
                <p className="text-xs text-gray-500">
                  Talent Discovery Platform
                </p>
              </div>
            </div>

            {/* User Info and Actions */}
            <div className="flex items-center space-x-4">
              <button
                onClick={handleRefresh}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                title="Refresh data"
              >
                <RefreshCw className="h-5 w-5" />
              </button>

              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  {hrUser?.full_name || hrUser?.email}
                </p>
                <p className="text-xs text-gray-500">
                  {hrUser?.company || "HR Manager"}
                </p>
              </div>

              <button
                onClick={handleSignOut}
                className="flex items-center space-x-2 px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <LogOut className="h-4 w-4" />
                <span className="text-sm font-medium">Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Header Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="mb-10"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-4xl font-extrabold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-3">
                Find Top Developers
              </h2>
              <p className="text-lg text-gray-700 font-medium">
                Search and filter candidates based on their skills and code
                quality
              </p>
            </div>
            <div className="text-right bg-white/80 backdrop-blur-sm rounded-2xl px-8 py-6 shadow-lg border border-indigo-100">
              <p className="text-5xl font-extrabold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                {totalCandidates}
              </p>
              <p className="text-sm text-gray-600 font-semibold mt-1">
                Candidates Found
              </p>
            </div>
          </div>
        </motion.div>

        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6, ease: "easeOut" }}
          className="mb-8"
        >
          <div className="flex items-center space-x-4">
            {/* Search Input */}
            <div className="flex-1 relative group">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 group-focus-within:text-indigo-500 transition-colors duration-200" />
              <input
                type="text"
                placeholder="Search by username, name, or programming language..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white/90 backdrop-blur-sm shadow-md hover:shadow-lg transition-all duration-200 text-gray-900 placeholder-gray-500 font-medium"
              />
            </div>

            {/* Sort Dropdown */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
              className="px-6 py-4 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white/90 backdrop-blur-sm shadow-md hover:shadow-lg transition-all duration-200 font-semibold text-gray-700 cursor-pointer"
            >
              <option value="score">Highest Score</option>
              <option value="upvotes">Most Upvotes</option>
              <option value="recent">Recently Active</option>
            </select>
          </div>
        </motion.div>

        {/* Main Layout: Sidebar + Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar: Filter Panel */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.6, ease: "easeOut" }}
            className="lg:col-span-1"
          >
            <FilterPanel filters={filters} onFilterChange={setFilters} />
          </motion.div>

          {/* Main Content: Candidate Grid */}
          <div className="lg:col-span-3">
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg"
              >
                <p className="text-red-800 text-sm">{error}</p>
              </motion.div>
            )}

            {isLoading ? (
              // Loading State
              <div className="space-y-5">
                {[...Array(3)].map((_, i) => (
                  <div
                    key={i}
                    className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 animate-pulse shadow-lg border border-gray-100"
                  >
                    <div className="flex items-start space-x-4">
                      <div className="w-16 h-16 bg-gradient-to-br from-gray-200 to-gray-300 rounded-full"></div>
                      <div className="flex-1 space-y-3">
                        <div className="h-5 bg-gradient-to-r from-gray-200 to-gray-300 rounded-lg w-1/3"></div>
                        <div className="h-4 bg-gradient-to-r from-gray-200 to-gray-300 rounded-lg w-1/2"></div>
                        <div className="h-4 bg-gradient-to-r from-gray-200 to-gray-300 rounded-lg w-2/3"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : paginatedCandidates.length === 0 ? (
              // Empty State
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="text-center py-16 bg-white/80 backdrop-blur-sm rounded-2xl border-2 border-gray-200 shadow-xl"
              >
                <Users className="h-20 w-20 text-indigo-400 mx-auto mb-6" />
                <h3 className="text-2xl font-bold text-gray-900 mb-3">
                  No candidates found
                </h3>
                <p className="text-gray-600 mb-6 text-lg">
                  Try adjusting your search criteria or filters
                </p>
                <button
                  onClick={() => {
                    setSearchQuery("");
                    setFilters({});
                  }}
                  className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                >
                  Clear Filters
                </button>
              </motion.div>
            ) : (
              // Candidate Cards
              <>
                <div className="space-y-5 mb-8">
                  {paginatedCandidates.map((candidate, index) => (
                    <motion.div
                      key={candidate.username}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{
                        delay: index * 0.08,
                        duration: 0.5,
                        ease: "easeOut",
                      }}
                    >
                      <CandidateCard candidate={candidate} />
                    </motion.div>
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="flex items-center justify-between bg-white/80 backdrop-blur-sm rounded-xl border-2 border-gray-200 p-5 shadow-lg"
                  >
                    <div className="text-sm text-gray-700 font-medium">
                      Showing {(page - 1) * limit + 1} to{" "}
                      {Math.min(page * limit, totalCandidates)} of{" "}
                      {totalCandidates} candidates
                    </div>
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="px-4 py-2 border-2 border-gray-300 rounded-lg hover:bg-indigo-50 hover:border-indigo-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold text-gray-700 hover:text-indigo-700"
                      >
                        Previous
                      </button>
                      <span className="text-sm text-gray-700 font-bold px-3">
                        Page {page} of {totalPages}
                      </span>
                      <button
                        onClick={() =>
                          setPage((p) => Math.min(totalPages, p + 1))
                        }
                        disabled={page === totalPages}
                        className="px-4 py-2 border-2 border-gray-300 rounded-lg hover:bg-indigo-50 hover:border-indigo-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold text-gray-700 hover:text-indigo-700"
                      >
                        Next
                      </button>
                    </div>
                  </motion.div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HRDashboard;
