import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Calendar, TrendingUp, Flame, Target } from "lucide-react";
import {
  fetchGitHubContributions,
  getContributionColor,
  formatContributionCount,
  getContributionStats,
} from "../services/githubGraphQL";

interface GitHubActivityCalendarProps {
  username: string;
  githubToken?: string;
  className?: string;
}

interface ContributionDay {
  contributionCount: number;
  date: string;
  color: string;
  contributionLevel:
    | "NONE"
    | "FIRST_QUARTILE"
    | "SECOND_QUARTILE"
    | "THIRD_QUARTILE"
    | "FOURTH_QUARTILE";
}

interface ContributionWeek {
  contributionDays: ContributionDay[];
}

interface ContributionCalendar {
  totalContributions: number;
  weeks: ContributionWeek[];
}

const GitHubActivityCalendar: React.FC<GitHubActivityCalendarProps> = ({
  username,
  githubToken,
  className = "",
}) => {
  const [calendar, setCalendar] = useState<ContributionCalendar | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredDay, setHoveredDay] = useState<ContributionDay | null>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const loadContributions = async () => {
      if (!username) return;

      setIsLoading(true);
      setError(null);

      try {
        const contributionData = await fetchGitHubContributions(
          username,
          githubToken
        );

        if (contributionData) {
          setCalendar(contributionData);
        } else {
          setError("Unable to load contribution data");
        }
      } catch (err) {
        console.error("Error loading GitHub contributions:", err);
        setError("Failed to load contribution data");
      } finally {
        setIsLoading(false);
      }
    };

    loadContributions();
  }, [username, githubToken]);

  const handleMouseEnter = (day: ContributionDay, event: React.MouseEvent) => {
    setHoveredDay(day);
    setMousePosition({ x: event.clientX, y: event.clientY });
  };

  const handleMouseLeave = () => {
    setHoveredDay(null);
  };

  const handleMouseMove = (event: React.MouseEvent) => {
    if (hoveredDay) {
      setMousePosition({ x: event.clientX, y: event.clientY });
    }
  };

  if (isLoading) {
    return (
      <div className={`card p-6 ${className}`}>
        <div className="flex items-center space-x-3 mb-4">
          <Calendar className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            GitHub Activity
          </h3>
        </div>
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
        </div>
      </div>
    );
  }

  if (error || !calendar) {
    return (
      <div className={`card p-6 ${className}`}>
        <div className="flex items-center space-x-3 mb-4">
          <Calendar className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            GitHub Activity
          </h3>
        </div>
        <div className="text-center py-8">
          <p className="text-gray-500 text-sm">
            {error || "No contribution data available"}
          </p>
        </div>
      </div>
    );
  }

  const stats = getContributionStats(calendar);
  const monthLabels = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  const dayLabels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`card p-6 ${className}`}
      onMouseMove={handleMouseMove}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Calendar className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            GitHub Activity
          </h3>
        </div>
        <div className="text-sm text-gray-500">
          {stats.totalContributions} contributions in the last year
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="flex items-center justify-center mb-1">
            <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
            <span className="text-lg font-bold text-green-600">
              {stats.totalContributions}
            </span>
          </div>
          <div className="text-xs text-gray-600">Total</div>
        </div>

        <div className="text-center p-3 bg-orange-50 rounded-lg">
          <div className="flex items-center justify-center mb-1">
            <Flame className="h-4 w-4 text-orange-600 mr-1" />
            <span className="text-lg font-bold text-orange-600">
              {stats.currentStreak}
            </span>
          </div>
          <div className="text-xs text-gray-600">Current Streak</div>
        </div>

        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center justify-center mb-1">
            <Target className="h-4 w-4 text-blue-600 mr-1" />
            <span className="text-lg font-bold text-blue-600">
              {stats.longestStreak}
            </span>
          </div>
          <div className="text-xs text-gray-600">Longest Streak</div>
        </div>

        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <div className="flex items-center justify-center mb-1">
            <span className="text-lg font-bold text-purple-600">
              {stats.activityPercentage}%
            </span>
          </div>
          <div className="text-xs text-gray-600">Active Days</div>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          {/* Month labels */}
          <div className="flex mb-2">
            <div className="w-8"></div> {/* Space for day labels */}
            {Array.from({ length: 53 }, (_, weekIndex) => {
              const firstDayOfWeek =
                calendar.weeks[weekIndex]?.contributionDays[0];
              if (!firstDayOfWeek)
                return <div key={weekIndex} className="w-3 mx-0.5"></div>;

              const date = new Date(firstDayOfWeek.date);
              const isFirstWeekOfMonth = date.getDate() <= 7;

              return (
                <div
                  key={weekIndex}
                  className="w-3 mx-0.5 text-xs text-gray-500 text-center"
                >
                  {isFirstWeekOfMonth ? monthLabels[date.getMonth()] : ""}
                </div>
              );
            })}
          </div>

          {/* Calendar grid */}
          <div className="flex">
            {/* Day labels */}
            <div className="flex flex-col mr-2">
              {dayLabels.map((day, index) => (
                <div
                  key={day}
                  className="h-3 mb-0.5 text-xs text-gray-500 flex items-center"
                >
                  {index % 2 === 1 ? day : ""}
                </div>
              ))}
            </div>

            {/* Contribution squares */}
            <div className="flex">
              {calendar.weeks.map((week, weekIndex) => (
                <div key={weekIndex} className="flex flex-col mx-0.5">
                  {week.contributionDays.map((day) => (
                    <motion.div
                      key={day.date}
                      className="w-3 h-3 mb-0.5 rounded-sm cursor-pointer transition-all duration-200 hover:ring-2 hover:ring-gray-400"
                      style={{
                        backgroundColor:
                          day.color ||
                          getContributionColor(day.contributionLevel),
                      }}
                      whileHover={{ scale: 1.2 }}
                      onMouseEnter={(e) => handleMouseEnter(day, e)}
                      onMouseLeave={handleMouseLeave}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
            <span>Less</span>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 rounded-sm bg-gray-100"></div>
              <div className="w-3 h-3 rounded-sm bg-green-200"></div>
              <div className="w-3 h-3 rounded-sm bg-green-400"></div>
              <div className="w-3 h-3 rounded-sm bg-green-600"></div>
              <div className="w-3 h-3 rounded-sm bg-green-800"></div>
            </div>
            <span>More</span>
          </div>
        </div>
      </div>

      {/* Tooltip */}
      {hoveredDay && (
        <div
          className="fixed z-50 bg-gray-900 text-white text-xs px-2 py-1 rounded shadow-lg pointer-events-none"
          style={{
            left: mousePosition.x + 10,
            top: mousePosition.y - 30,
          }}
        >
          <div className="font-medium">
            {formatContributionCount(hoveredDay.contributionCount)}
          </div>
          <div className="text-gray-300">
            {new Date(hoveredDay.date).toLocaleDateString("en-US", {
              weekday: "short",
              month: "short",
              day: "numeric",
              year: "numeric",
            })}
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default GitHubActivityCalendar;
