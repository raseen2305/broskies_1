/**
 * GitHub GraphQL API Service
 * Fetches contribution calendar data using GitHub's GraphQL API
 */

interface ContributionDay {
  contributionCount: number;
  date: string;
  color: string;
  contributionLevel: 'NONE' | 'FIRST_QUARTILE' | 'SECOND_QUARTILE' | 'THIRD_QUARTILE' | 'FOURTH_QUARTILE';
}

interface ContributionWeek {
  contributionDays: ContributionDay[];
}

interface ContributionCalendar {
  totalContributions: number;
  weeks: ContributionWeek[];
}

interface GitHubContributionResponse {
  data: {
    user: {
      contributionsCollection: {
        contributionCalendar: ContributionCalendar;
      };
    };
  };
}

// GitHub GraphQL endpoint
const GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql';

// GraphQL query to fetch contribution calendar
const CONTRIBUTION_CALENDAR_QUERY = `
  query($username: String!, $from: DateTime!, $to: DateTime!) {
    user(login: $username) {
      contributionsCollection(from: $from, to: $to) {
        contributionCalendar {
          totalContributions
          weeks {
            contributionDays {
              contributionCount
              date
              color
              contributionLevel
            }
          }
        }
      }
    }
  }
`;

/**
 * Fetch GitHub contribution calendar data
 */
export const fetchGitHubContributions = async (
  username: string,
  githubToken?: string
): Promise<ContributionCalendar | null> => {
  try {
    // Calculate date range (last 365 days)
    const to = new Date();
    const from = new Date();
    from.setFullYear(from.getFullYear() - 1);

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Add authorization if token is available
    if (githubToken) {
      headers['Authorization'] = `Bearer ${githubToken}`;
    }

    const response = await fetch(GITHUB_GRAPHQL_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        query: CONTRIBUTION_CALENDAR_QUERY,
        variables: {
          username,
          from: from.toISOString(),
          to: to.toISOString(),
        },
      }),
    });

    if (!response.ok) {
      console.error('GitHub GraphQL API error:', response.status, response.statusText);
      return null;
    }

    const data: GitHubContributionResponse = await response.json();

    if (data.data?.user?.contributionsCollection?.contributionCalendar) {
      return data.data.user.contributionsCollection.contributionCalendar;
    }

    return null;
  } catch (error) {
    console.error('Error fetching GitHub contributions:', error);
    return null;
  }
};

/**
 * Get contribution level color (GitHub's color scheme)
 */
export const getContributionColor = (level: ContributionDay['contributionLevel']): string => {
  switch (level) {
    case 'NONE':
      return '#ebedf0';
    case 'FIRST_QUARTILE':
      return '#9be9a8';
    case 'SECOND_QUARTILE':
      return '#40c463';
    case 'THIRD_QUARTILE':
      return '#30a14e';
    case 'FOURTH_QUARTILE':
      return '#216e39';
    default:
      return '#ebedf0';
  }
};

/**
 * Format contribution count for display
 */
export const formatContributionCount = (count: number): string => {
  if (count === 0) return 'No contributions';
  if (count === 1) return '1 contribution';
  return `${count} contributions`;
};

/**
 * Get contribution statistics
 */
export const getContributionStats = (calendar: ContributionCalendar) => {
  const allDays = calendar.weeks.flatMap(week => week.contributionDays);
  
  const totalDays = allDays.length;
  const activeDays = allDays.filter(day => day.contributionCount > 0).length;
  const maxContributions = Math.max(...allDays.map(day => day.contributionCount));
  const averageContributions = calendar.totalContributions / totalDays;

  // Calculate current streak
  let currentStreak = 0;
  for (let i = allDays.length - 1; i >= 0; i--) {
    if (allDays[i].contributionCount > 0) {
      currentStreak++;
    } else {
      break;
    }
  }

  // Calculate longest streak
  let longestStreak = 0;
  let tempStreak = 0;
  for (const day of allDays) {
    if (day.contributionCount > 0) {
      tempStreak++;
      longestStreak = Math.max(longestStreak, tempStreak);
    } else {
      tempStreak = 0;
    }
  }

  return {
    totalContributions: calendar.totalContributions,
    totalDays,
    activeDays,
    maxContributions,
    averageContributions: Math.round(averageContributions * 100) / 100,
    currentStreak,
    longestStreak,
    activityPercentage: Math.round((activeDays / totalDays) * 100),
  };
};