import { UserRankings, UserProfile } from '../types';

// Demo data for when authentication is not available or backend is down
export const demoProfile: UserProfile = {
  full_name: "Demo User",
  university: "Indian Institute of Technology Delhi",
  university_short: "IIT Delhi",
  description: "Software engineer passionate about full-stack development and machine learning.",
  nationality: "IN",
  state: "Delhi",
  district: "New Delhi",
  region: "IN"
};

export const demoRankings: UserRankings = {
  regional_percentile_text: "Top 7% in IN",
  university_percentile_text: "Top 1% in IIT Delhi",
  regional_ranking: {
    rank_in_region: 1250,
    total_users_in_region: 18500,
    percentile_region: 93.2
  },
  university_ranking: {
    rank_in_university: 2,
    total_users_in_university: 150,
    percentile_university: 98.7
  }
};

export const isDemoMode = () => {
  // Check if we're in demo mode (no auth token or backend unavailable)
  const token = localStorage.getItem('auth_token');
  return !token;
};

export const getDemoData = () => ({
  profile: demoProfile,
  rankings: demoRankings,
  hasProfile: true
});