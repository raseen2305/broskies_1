<<<<<<< HEAD
import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Trophy,
  TrendingUp,
  Users,
  Award,
  BarChart3,
  Target,
  Crown,
  Medal,
} from "lucide-react";
import axios from "axios";
=======
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Trophy, TrendingUp, Users, Award, BarChart3, Target, Crown, Medal } from 'lucide-react';
import axios from 'axios';
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085

interface RankingData {
  user_info: {
    github_username: string;
    name: string;
    overall_score: number;
  };
  regional_ranking?: {
    rank: number;
    total_users: number;
    percentile: number;
    region: string;
    state: string;
    avg_score: number;
    median_score: number;
    display_text: string;
  };
  university_ranking?: {
    rank: number;
    total_users: number;
    percentile: number;
    university: string;
    avg_score: number;
    median_score: number;
    display_text: string;
  };
}

interface LeaderboardEntry {
<<<<<<< HEAD
  rank?: number;
  score?: number;
  percentile?: number;
  is_current_user: boolean;
  name?: string;
  github_username?: string;
  // Backend field names
  rank_position?: number;
  overall_score?: number;
  percentile_score?: number;
=======
  rank: number;
  score: number;
  percentile: number;
  is_current_user: boolean;
  name?: string;
  github_username?: string;
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
}

interface Statistics {
  total_users: number;
  avg_score: number;
  median_score: number;
  min_score: number;
  max_score: number;
  score_distribution: {
<<<<<<< HEAD
    "0-20": number;
    "20-40": number;
    "40-60": number;
    "60-80": number;
    "80-100": number;
=======
    '0-20': number;
    '20-40': number;
    '40-60': number;
    '60-80': number;
    '80-100': number;
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
  };
}

interface RankingsPageProps {
  scanResults?: any;
}

const RankingsPage: React.FC<RankingsPageProps> = ({ scanResults }) => {
  const [rankingData, setRankingData] = useState<RankingData | null>(null);
<<<<<<< HEAD
  const [regionalLeaderboard, setRegionalLeaderboard] = useState<
    LeaderboardEntry[]
  >([]);
  const [universityLeaderboard, setUniversityLeaderboard] = useState<
    LeaderboardEntry[]
  >([]);
  const [regionalStats, setRegionalStats] = useState<Statistics | null>(null);
  const [universityStats, setUniversityStats] = useState<Statistics | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"regional" | "university">(
    "regional"
  );

  // Check if this is an external scan (HR viewing candidate)
  const isExternalScan =
    scanResults?.isExternalScan || scanResults?.scanType === "other";
=======
  const [regionalLeaderboard, setRegionalLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [universityLeaderboard, setUniversityLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [regionalStats, setRegionalStats] = useState<Statistics | null>(null);
  const [universityStats, setUniversityStats] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'regional' | 'university'>('regional');

  // Check if this is an external scan (HR viewing candidate)
  const isExternalScan = scanResults?.isExternalScan || scanResults?.scanType === 'other';
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085

  useEffect(() => {
    if (isExternalScan && scanResults?.targetUsername) {
      // For external scans, fetch rankings by GitHub username
      fetchExternalRankingData(scanResults.targetUsername);
    } else {
      // For authenticated users, fetch their own rankings
      fetchRankingData();
    }
  }, [isExternalScan, scanResults]);

  const fetchExternalRankingData = async (githubUsername: string) => {
    try {
      setLoading(true);
<<<<<<< HEAD

      console.log(`📡 Fetching external rankings for: ${githubUsername}`);

=======
      
      console.log(`📡 Fetching external rankings for: ${githubUsername}`);
      
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
      // Use the public endpoint that doesn't require authentication
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/rankings/check/${githubUsername}`
      );
<<<<<<< HEAD

      console.log("✅ External ranking data:", response.data);

=======
      
      console.log('✅ External ranking data:', response.data);
      
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
      if (response.data.has_ranking_data) {
        // Transform the data to match RankingData interface
        const transformedData: RankingData = {
          user_info: {
            github_username: githubUsername,
            name: response.data.profile?.full_name || githubUsername,
<<<<<<< HEAD
            overall_score:
              response.data.regional_ranking?.overall_score ||
              response.data.university_ranking?.overall_score ||
              0,
          },
        };

=======
            overall_score: response.data.regional_ranking?.overall_score || 
                          response.data.university_ranking?.overall_score || 0
          }
        };
        
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
        if (response.data.regional_ranking) {
          transformedData.regional_ranking = {
            rank: response.data.regional_ranking.rank_in_region,
            total_users: response.data.regional_ranking.total_users_in_region,
            percentile: response.data.regional_ranking.percentile_region,
            region: response.data.regional_ranking.region,
            state: response.data.regional_ranking.state,
            avg_score: response.data.regional_ranking.overall_score,
            median_score: response.data.regional_ranking.overall_score,
<<<<<<< HEAD
            display_text:
              response.data.regional_percentile_text ||
              `Rank #${response.data.regional_ranking.rank_in_region} in ${response.data.regional_ranking.region}`,
          };
        }

        if (response.data.university_ranking) {
          transformedData.university_ranking = {
            rank: response.data.university_ranking.rank_in_university,
            total_users:
              response.data.university_ranking.total_users_in_university,
=======
            display_text: response.data.regional_percentile_text || 
                         `Rank #${response.data.regional_ranking.rank_in_region} in ${response.data.regional_ranking.region}`
          };
        }
        
        if (response.data.university_ranking) {
          transformedData.university_ranking = {
            rank: response.data.university_ranking.rank_in_university,
            total_users: response.data.university_ranking.total_users_in_university,
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            percentile: response.data.university_ranking.percentile_university,
            university: response.data.university_ranking.university,
            avg_score: response.data.university_ranking.overall_score,
            median_score: response.data.university_ranking.overall_score,
<<<<<<< HEAD
            display_text:
              response.data.university_percentile_text ||
              `Rank #${response.data.university_ranking.rank_in_university} in ${response.data.university_ranking.university}`,
          };
        }

        setRankingData(transformedData);
      }

      setLoading(false);
    } catch (error) {
      console.error("Failed to fetch external rankings:", error);
=======
            display_text: response.data.university_percentile_text || 
                         `Rank #${response.data.university_ranking.rank_in_university} in ${response.data.university_ranking.university}`
          };
        }
        
        setRankingData(transformedData);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch external rankings:', error);
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
      setLoading(false);
    }
  };

  const fetchRankingData = async () => {
    try {
      setLoading(true);
<<<<<<< HEAD

      // Get token from localStorage (try multiple possible keys)
      let token =
        localStorage.getItem("token") ||
        localStorage.getItem("auth_token") ||
        localStorage.getItem("access_token");

      if (!token) {
        console.error("No authentication token found");
=======
      
      // Get token from localStorage (try multiple possible keys)
      let token = localStorage.getItem('token') || 
                  localStorage.getItem('auth_token') || 
                  localStorage.getItem('access_token');
      
      if (!token) {
        console.error('No authentication token found');
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
        setLoading(false);
        return;
      }

<<<<<<< HEAD
      const config = {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      };

      console.log(
        "Fetching rankings with token:",
        token.substring(0, 20) + "..."
      );

      // Fetch detailed rankings
      const rankingsRes = await axios.get(
        `${import.meta.env.VITE_API_URL}/rankings/detailed?type=regional`,
        config
      );

      // Transform the backend response to match RankingData interface
      const regionalData = rankingsRes.data;

      // Also try to fetch university rankings
      let universityData = null;
      try {
        const universityRes = await axios.get(
          `${import.meta.env.VITE_API_URL}/rankings/detailed?type=university`,
          config
        );
        universityData = universityRes.data;
      } catch (error) {
        console.warn("University rankings not available:", error);
      }

      const transformedData: RankingData = {
        user_info: {
          github_username:
            regionalData.github_username ||
            universityData?.github_username ||
            "",
          name: regionalData.name || universityData?.name || "",
          overall_score:
            regionalData.overall_score || universityData?.overall_score || 0,
        },
        regional_ranking: regionalData
          ? {
              rank: regionalData.rank_position,
              total_users: regionalData.total_users,
              percentile: regionalData.percentile_score,
              region: regionalData.comparison_context,
              state: "",
              avg_score: regionalData.avg_score || 0,
              median_score: regionalData.median_score || 0,
              display_text: `Rank #${regionalData.rank_position} in ${regionalData.comparison_context}`,
            }
          : undefined,
        university_ranking: universityData
          ? {
              rank: universityData.rank_position,
              total_users: universityData.total_users,
              percentile: universityData.percentile_score,
              university: universityData.comparison_context,
              avg_score: universityData.avg_score || 0,
              median_score: universityData.median_score || 0,
              display_text: `Rank #${universityData.rank_position} in ${universityData.comparison_context}`,
            }
          : undefined,
      };

      setRankingData(transformedData);
=======
      const config = { 
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        } 
      };

      console.log('Fetching rankings with token:', token.substring(0, 20) + '...');

      // Fetch detailed rankings
      const rankingsRes = await axios.get(
        `${import.meta.env.VITE_API_URL}/rankings/v2/detailed`,
        config
      );
      setRankingData(rankingsRes.data);
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085

      // Fetch regional leaderboard (with error handling)
      try {
        const regionalLeaderboardRes = await axios.get(
<<<<<<< HEAD
          `${
            import.meta.env.VITE_API_URL
          }/rankings/leaderboard/regional?limit=10`,
          config
        );
        console.log(
          "🔍 Regional leaderboard data:",
          regionalLeaderboardRes.data.leaderboard
        );
        setRegionalLeaderboard(regionalLeaderboardRes.data.leaderboard || []);
      } catch (leaderboardError) {
        console.warn("Failed to fetch regional leaderboard:", leaderboardError);
=======
          `${import.meta.env.VITE_API_URL}/rankings/v2/leaderboard?type=regional&limit=10`,
          config
        );
        setRegionalLeaderboard(regionalLeaderboardRes.data.leaderboard || []);
      } catch (leaderboardError) {
        console.warn('Failed to fetch regional leaderboard:', leaderboardError);
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
        setRegionalLeaderboard([]);
      }

      // Fetch university leaderboard (with error handling)
      try {
        const universityLeaderboardRes = await axios.get(
<<<<<<< HEAD
          `${
            import.meta.env.VITE_API_URL
          }/rankings/leaderboard/university?limit=10`,
          config
        );
        console.log(
          "🔍 University leaderboard data:",
          universityLeaderboardRes.data.leaderboard
        );
        setUniversityLeaderboard(
          universityLeaderboardRes.data.leaderboard || []
        );
      } catch (leaderboardError) {
        console.warn(
          "Failed to fetch university leaderboard:",
          leaderboardError
        );
=======
          `${import.meta.env.VITE_API_URL}/rankings/v2/leaderboard?type=university&limit=10`,
          config
        );
        setUniversityLeaderboard(universityLeaderboardRes.data.leaderboard || []);
      } catch (leaderboardError) {
        console.warn('Failed to fetch university leaderboard:', leaderboardError);
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
        setUniversityLeaderboard([]);
      }

      // Fetch regional statistics (with error handling)
      try {
        const regionalStatsRes = await axios.get(
<<<<<<< HEAD
          `${import.meta.env.VITE_API_URL}/rankings/stats/regional`,
=======
          `${import.meta.env.VITE_API_URL}/rankings/v2/statistics?type=regional`,
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
          config
        );
        setRegionalStats(regionalStatsRes.data.statistics);
      } catch (statsError) {
<<<<<<< HEAD
        console.warn("Failed to fetch regional statistics:", statsError);
=======
        console.warn('Failed to fetch regional statistics:', statsError);
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
        setRegionalStats(null);
      }

      // Fetch university statistics (with error handling)
      try {
        const universityStatsRes = await axios.get(
<<<<<<< HEAD
          `${import.meta.env.VITE_API_URL}/rankings/stats/university`,
=======
          `${import.meta.env.VITE_API_URL}/rankings/v2/statistics?type=university`,
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
          config
        );
        setUniversityStats(universityStatsRes.data.statistics);
      } catch (statsError) {
<<<<<<< HEAD
        console.warn("Failed to fetch university statistics:", statsError);
        setUniversityStats(null);
      }
    } catch (error: any) {
      console.error("Error fetching ranking data:", error);

      // If new API fails, try fallback to old API
      if (error.response?.status === 401) {
        console.error("Authentication failed. Please login again.");
        // Optionally redirect to login
        // window.location.href = '/developer/auth';
      } else if (error.response?.status === 404) {
        console.log("New API not available, trying fallback to old API...");
        try {
          const token =
            localStorage.getItem("token") ||
            localStorage.getItem("auth_token") ||
            localStorage.getItem("access_token");
          const config = {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          };

=======
        console.warn('Failed to fetch university statistics:', statsError);
        setUniversityStats(null);
      }

    } catch (error: any) {
      console.error('Error fetching ranking data:', error);
      
      // If new API fails, try fallback to old API
      if (error.response?.status === 401) {
        console.error('Authentication failed. Please login again.');
        // Optionally redirect to login
        // window.location.href = '/developer/auth';
      } else if (error.response?.status === 404) {
        console.log('New API not available, trying fallback to old API...');
        try {
          const token = localStorage.getItem('token') || 
                        localStorage.getItem('auth_token') || 
                        localStorage.getItem('access_token');
          const config = { 
            headers: { 
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json'
            } 
          };
          
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
          // Try old API endpoint
          const oldRankingsRes = await axios.get(
            `${import.meta.env.VITE_API_URL}/rankings`,
            config
          );
<<<<<<< HEAD

=======
          
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
          // Transform old API response to new format
          const oldData = oldRankingsRes.data;
          const transformedData: RankingData = {
            user_info: {
<<<<<<< HEAD
              github_username:
                oldData.regional_ranking?.name ||
                oldData.university_ranking?.name ||
                "",
              name:
                oldData.regional_ranking?.name ||
                oldData.university_ranking?.name ||
                "",
              overall_score:
                oldData.regional_ranking?.overall_score ||
                oldData.university_ranking?.overall_score ||
                0,
            },
            regional_ranking: oldData.regional_ranking
              ? {
                  rank: oldData.regional_ranking.rank_in_region,
                  total_users: oldData.regional_ranking.total_users_in_region,
                  percentile: oldData.regional_ranking.percentile_region,
                  region: "",
                  state: "",
                  avg_score: 0,
                  median_score: 0,
                  display_text: oldData.regional_percentile_text,
                }
              : undefined,
            university_ranking: oldData.university_ranking
              ? {
                  rank: oldData.university_ranking.rank_in_university,
                  total_users:
                    oldData.university_ranking.total_users_in_university,
                  percentile: oldData.university_ranking.percentile_university,
                  university: "",
                  avg_score: 0,
                  median_score: 0,
                  display_text: oldData.university_percentile_text,
                }
              : undefined,
          };

          setRankingData(transformedData);
          console.log("Successfully loaded data from old API");
        } catch (fallbackError) {
          console.error("Fallback API also failed:", fallbackError);
=======
              github_username: '',
              name: '',
              overall_score: 0
            },
            regional_ranking: oldData.regional_ranking ? {
              rank: oldData.regional_ranking.rank_in_region,
              total_users: oldData.regional_ranking.total_users_in_region,
              percentile: oldData.regional_ranking.percentile_region,
              region: '',
              state: '',
              avg_score: 0,
              median_score: 0,
              display_text: oldData.regional_percentile_text
            } : undefined,
            university_ranking: oldData.university_ranking ? {
              rank: oldData.university_ranking.rank_in_university,
              total_users: oldData.university_ranking.total_users_in_university,
              percentile: oldData.university_ranking.percentile_university,
              university: '',
              avg_score: 0,
              median_score: 0,
              display_text: oldData.university_percentile_text
            } : undefined
          };
          
          setRankingData(transformedData);
          console.log('Successfully loaded data from old API');
        } catch (fallbackError) {
          console.error('Fallback API also failed:', fallbackError);
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
        }
      }
    } finally {
      setLoading(false);
    }
  };

<<<<<<< HEAD
  const ScoreWheel: React.FC<{ score: number; size?: number }> = ({
    score,
    size = 200,
  }) => {
=======
  const ScoreWheel: React.FC<{ score: number; size?: number }> = ({ score, size = 200 }) => {
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
    const radius = size / 2 - 10;
    const circumference = 2 * Math.PI * radius;
    const progress = (score / 100) * circumference;

    return (
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#1f2937"
            strokeWidth="12"
          />
          {/* Progress circle */}
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="url(#scoreGradient)"
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: circumference - progress }}
            transition={{ duration: 1.5, ease: "easeOut" }}
          />
          <defs>
<<<<<<< HEAD
            <linearGradient
              id="scoreGradient"
              x1="0%"
              y1="0%"
              x2="100%"
              y2="100%"
            >
=======
            <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
              <stop offset="0%" stopColor="#3b82f6" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.5, type: "spring" }}
            className="text-4xl font-bold text-white"
          >
            {score.toFixed(1)}
          </motion.div>
          <div className="text-sm text-gray-400">ACID Score</div>
        </div>
      </div>
    );
  };

  const RankCard: React.FC<{
    title: string;
    rank: number;
    total: number;
    percentile: number;
    context: string;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, rank, total, percentile, context, icon, color }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-gray-800 rounded-xl p-6 border-2 border-${color}-500/20 hover:border-${color}-500/40 transition-all`}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <div className={`text-${color}-400`}>{icon}</div>
      </div>
<<<<<<< HEAD

=======
      
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
      <div className="space-y-3">
        <div>
          <div className="text-3xl font-bold text-white">#{rank}</div>
          <div className="text-sm text-gray-400">out of {total} students</div>
        </div>
<<<<<<< HEAD

        <div
          className={`inline-block px-3 py-1 rounded-full bg-${color}-500/10 text-${color}-400 text-sm font-medium`}
        >
          Top {percentile.toFixed(1)}%
        </div>

=======
        
        <div className={`inline-block px-3 py-1 rounded-full bg-${color}-500/10 text-${color}-400 text-sm font-medium`}>
          Top {percentile.toFixed(1)}%
        </div>
        
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
        <div className="text-sm text-gray-400">{context}</div>
      </div>
    </motion.div>
  );

<<<<<<< HEAD
  const LeaderboardTable: React.FC<{
    entries: LeaderboardEntry[];
    type: string;
  }> = ({ entries, type }) => (
=======
  const LeaderboardTable: React.FC<{ entries: LeaderboardEntry[]; type: string }> = ({ entries, type }) => (
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
    <div className="bg-gray-800 rounded-xl overflow-hidden">
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Trophy className="w-5 h-5 text-yellow-400" />
<<<<<<< HEAD
          {type === "regional" ? "Regional" : "University"} Leaderboard
        </h3>
      </div>

=======
          {type === 'regional' ? 'Regional' : 'University'} Leaderboard
        </h3>
      </div>
      
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-900/50">
            <tr>
<<<<<<< HEAD
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                Rank
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                Score
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                Percentile
              </th>
=======
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Rank</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Score</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Percentile</th>
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {entries.map((entry, index) => (
              <motion.tr
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`${
                  entry.is_current_user
<<<<<<< HEAD
                    ? "bg-blue-500/10 border-l-4 border-blue-500"
                    : "hover:bg-gray-700/50"
=======
                    ? 'bg-blue-500/10 border-l-4 border-blue-500'
                    : 'hover:bg-gray-700/50'
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
                } transition-colors`}
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
<<<<<<< HEAD
                    {(entry.rank || entry.rank_position) === 1 && (
                      <Crown className="w-5 h-5 text-yellow-400" />
                    )}
                    {(entry.rank || entry.rank_position) === 2 && (
                      <Medal className="w-5 h-5 text-gray-300" />
                    )}
                    {(entry.rank || entry.rank_position) === 3 && (
                      <Medal className="w-5 h-5 text-amber-600" />
                    )}
                    <span className="text-white font-semibold">
                      #{entry.rank || entry.rank_position || 0}
                    </span>
                    {entry.is_current_user && (
                      <span className="text-xs bg-blue-500 text-white px-2 py-0.5 rounded-full">
                        You
                      </span>
=======
                    {entry.rank === 1 && <Crown className="w-5 h-5 text-yellow-400" />}
                    {entry.rank === 2 && <Medal className="w-5 h-5 text-gray-300" />}
                    {entry.rank === 3 && <Medal className="w-5 h-5 text-amber-600" />}
                    <span className="text-white font-semibold">#{entry.rank}</span>
                    {entry.is_current_user && (
                      <span className="text-xs bg-blue-500 text-white px-2 py-0.5 rounded-full">You</span>
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
<<<<<<< HEAD
                  <span className="text-white font-medium">
                    {(entry.score || entry.overall_score || 0).toFixed(1)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-gray-300">
                    Top{" "}
                    {(entry.percentile || entry.percentile_score || 0).toFixed(
                      1
                    )}
                    %
                  </span>
=======
                  <span className="text-white font-medium">{entry.score.toFixed(1)}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-gray-300">Top {entry.percentile.toFixed(1)}%</span>
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

<<<<<<< HEAD
  const StatisticsCard: React.FC<{ stats: Statistics; type: string }> = ({
    stats,
    type,
  }) => {
=======
  const StatisticsCard: React.FC<{ stats: Statistics; type: string }> = ({ stats, type }) => {
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
    // Safety check for stats
    if (!stats) {
      return (
        <div className="bg-gray-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-400" />
<<<<<<< HEAD
            {type === "regional" ? "Regional" : "University"} Statistics
=======
            {type === 'regional' ? 'Regional' : 'University'} Statistics
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
          </h3>
          <div className="text-gray-400">No statistics available</div>
        </div>
      );
    }

    return (
      <div className="bg-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-purple-400" />
<<<<<<< HEAD
          {type === "regional" ? "Regional" : "University"} Statistics
        </h3>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <div className="text-2xl font-bold text-white">
              {stats.total_users || 0}
            </div>
            <div className="text-sm text-gray-400">Total Students</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">
              {stats.avg_score?.toFixed(1) || "0.0"}
            </div>
            <div className="text-sm text-gray-400">Average Score</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">
              {stats.median_score?.toFixed(1) || "0.0"}
            </div>
            <div className="text-sm text-gray-400">Median Score</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">
              {stats.max_score?.toFixed(1) || "0.0"}
            </div>
            <div className="text-sm text-gray-400">Highest Score</div>
          </div>
        </div>

        {stats.score_distribution && (
          <div>
            <h4 className="text-sm font-medium text-gray-400 mb-3">
              Score Distribution
            </h4>
            <div className="space-y-2">
              {Object.entries(stats.score_distribution).map(
                ([range, count]) => {
                  const percentage =
                    stats.total_users > 0
                      ? (count / stats.total_users) * 100
                      : 0;
                  return (
                    <div key={range}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-400">{range}</span>
                        <span className="text-white">{count} students</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${percentage}%` }}
                          transition={{ duration: 0.8, delay: 0.2 }}
                          className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                        />
                      </div>
                    </div>
                  );
                }
              )}
=======
          {type === 'regional' ? 'Regional' : 'University'} Statistics
        </h3>
        
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <div className="text-2xl font-bold text-white">{stats.total_users || 0}</div>
            <div className="text-sm text-gray-400">Total Students</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats.avg_score?.toFixed(1) || '0.0'}</div>
            <div className="text-sm text-gray-400">Average Score</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats.median_score?.toFixed(1) || '0.0'}</div>
            <div className="text-sm text-gray-400">Median Score</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats.max_score?.toFixed(1) || '0.0'}</div>
            <div className="text-sm text-gray-400">Highest Score</div>
          </div>
        </div>
        
        {stats.score_distribution && (
          <div>
            <h4 className="text-sm font-medium text-gray-400 mb-3">Score Distribution</h4>
            <div className="space-y-2">
              {Object.entries(stats.score_distribution).map(([range, count]) => {
                const percentage = stats.total_users > 0 ? (count / stats.total_users) * 100 : 0;
                return (
                  <div key={range}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-400">{range}</span>
                      <span className="text-white">{count} students</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percentage}%` }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                      />
                    </div>
                  </div>
                );
              })}
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            </div>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading rankings...</div>
      </div>
    );
  }

  if (!rankingData) {
    // External scan - user doesn't have profile
    if (isExternalScan) {
      return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center">
          <div className="text-center max-w-md mx-auto p-6">
            <Trophy className="w-16 h-16 text-amber-500 mx-auto mb-4" />
<<<<<<< HEAD
            <h2 className="text-2xl font-bold text-white mb-2">
              User Doesn't Have a Profile
            </h2>
            <p className="text-gray-400">
              This user hasn't set up their profile yet. Rankings are only
              available for users who have completed their profile setup and
              repository scan.
=======
            <h2 className="text-2xl font-bold text-white mb-2">User Doesn't Have a Profile</h2>
            <p className="text-gray-400">
              This user hasn't set up their profile yet. Rankings are only available for users who have completed their profile setup and repository scan.
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            </p>
          </div>
        </div>
      );
    }
<<<<<<< HEAD

=======
    
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
    // Internal scan - redirect to profile setup
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <Trophy className="w-16 h-16 text-gray-600 mx-auto mb-4" />
<<<<<<< HEAD
          <h2 className="text-2xl font-bold text-white mb-2">
            Complete Your Profile
          </h2>
          <p className="text-gray-400 mb-6">
            Set up your profile with your region and university information to
            see your rankings and compare with peers.
          </p>
          <button
            onClick={() => (window.location.href = "/developer/profile")}
=======
          <h2 className="text-2xl font-bold text-white mb-2">Complete Your Profile</h2>
          <p className="text-gray-400 mb-6">
            Set up your profile with your region and university information to see your rankings and compare with peers.
          </p>
          <button
            onClick={() => window.location.href = '/developer/profile'}
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Setup Profile
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <Trophy className="w-10 h-10 text-yellow-400" />
            Your Rankings
          </h1>
          <p className="text-gray-400">
            See how you compare with peers in your region and university
          </p>
        </motion.div>

        {/* Score Wheel Section */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex justify-center mb-8"
        >
          <div className="bg-gray-800 rounded-2xl p-8 inline-block">
<<<<<<< HEAD
            <ScoreWheel
              score={rankingData.user_info?.overall_score || 0}
              size={220}
            />
            <div className="text-center mt-4">
              <div className="text-white font-semibold">
                {rankingData.user_info?.name || "Unknown User"}
              </div>
              <div className="text-gray-400 text-sm">
                @{rankingData.user_info?.github_username || "unknown"}
              </div>
=======
            <ScoreWheel score={rankingData.user_info.overall_score} size={220} />
            <div className="text-center mt-4">
              <div className="text-white font-semibold">{rankingData.user_info.name}</div>
              <div className="text-gray-400 text-sm">@{rankingData.user_info.github_username}</div>
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            </div>
          </div>
        </motion.div>

        {/* Ranking Cards */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {rankingData.regional_ranking && (
            <RankCard
              title="Regional Ranking"
              rank={rankingData.regional_ranking.rank}
              total={rankingData.regional_ranking.total_users}
              percentile={rankingData.regional_ranking.percentile}
              context={`${rankingData.regional_ranking.region}, ${rankingData.regional_ranking.state}`}
              icon={<Target className="w-6 h-6" />}
              color="blue"
            />
          )}
<<<<<<< HEAD

=======
          
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
          {rankingData.university_ranking && (
            <RankCard
              title="University Ranking"
              rank={rankingData.university_ranking.rank}
              total={rankingData.university_ranking.total_users}
              percentile={rankingData.university_ranking.percentile}
              context={rankingData.university_ranking.university}
              icon={<Award className="w-6 h-6" />}
              color="purple"
            />
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-4 border-b border-gray-700 mb-6">
          <button
<<<<<<< HEAD
            onClick={() => setActiveTab("regional")}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === "regional"
                ? "text-blue-400 border-b-2 border-blue-400"
                : "text-gray-400 hover:text-white"
=======
            onClick={() => setActiveTab('regional')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'regional'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            }`}
          >
            Regional
          </button>
          <button
<<<<<<< HEAD
            onClick={() => setActiveTab("university")}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === "university"
                ? "text-purple-400 border-b-2 border-purple-400"
                : "text-gray-400 hover:text-white"
=======
            onClick={() => setActiveTab('university')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'university'
                ? 'text-purple-400 border-b-2 border-purple-400'
                : 'text-gray-400 hover:text-white'
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            }`}
          >
            University
          </button>
        </div>

        {/* Content based on active tab */}
        <div className="grid lg:grid-cols-2 gap-6">
<<<<<<< HEAD
          {activeTab === "regional" ? (
            <>
              <LeaderboardTable entries={regionalLeaderboard} type="regional" />
              {regionalStats && (
                <StatisticsCard stats={regionalStats} type="regional" />
              )}
            </>
          ) : (
            <>
              <LeaderboardTable
                entries={universityLeaderboard}
                type="university"
              />
              {universityStats && (
                <StatisticsCard stats={universityStats} type="university" />
              )}
=======
          {activeTab === 'regional' ? (
            <>
              <LeaderboardTable entries={regionalLeaderboard} type="regional" />
              {regionalStats && <StatisticsCard stats={regionalStats} type="regional" />}
            </>
          ) : (
            <>
              <LeaderboardTable entries={universityLeaderboard} type="university" />
              {universityStats && <StatisticsCard stats={universityStats} type="university" />}
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default RankingsPage;
