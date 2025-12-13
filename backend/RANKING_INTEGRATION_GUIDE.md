# 🎯 Ranking System Integration Guide

## 📋 Overview

The unified ranking system is now fully implemented and provides comprehensive university and regional rankings. Here's how to integrate it with your frontend.

## 🔗 API Endpoints

### 1. **Check Ranking Status**
```
GET /rankings/status
```
**Purpose**: Check if rankings are available or being calculated

**Response**:
```json
{
  "user_id": "user123",
  "has_complete_profile": true,
  "has_regional_ranking": true,
  "has_university_ranking": true,
  "ranking_status": "available", // "available" | "calculating" | "pending_scan" | "pending_profile"
  "profile_info": {
    "name": "John Doe",
    "university": "iit-madras",
    "district": "Chennai",
    "overall_score": 85.5
  }
}
```

### 2. **Get User Rankings**
```
GET /rankings
```
**Purpose**: Get complete ranking information

**Response when available**:
```json
{
  "status": "available",
  "message": "Rankings available",
  "has_complete_profile": true,
  "regional_percentile_text": "Top 25.0% in Chennai",
  "regional_ranking": {
    "rank_in_region": 3,
    "total_users_in_region": 12,
    "percentile_region": 75.0,
    "overall_score": 85.5,
    "name": "John Doe",
    "district": "Chennai",
    "state": "Tamil Nadu",
    "region": "IN-Tamil Nadu",
    "avg_score": 78.2,
    "median_score": 80.1
  },
  "university_percentile_text": "Top 15.0% in IIT Madras",
  "university_ranking": {
    "rank_in_university": 2,
    "total_users_in_university": 15,
    "percentile_university": 85.0,
    "overall_score": 85.5,
    "name": "John Doe",
    "university": "Indian Institute of Technology Madras",
    "university_short": "iit-madras",
    "avg_score": 82.1,
    "median_score": 83.5
  }
}
```

**Response when calculating**:
```json
{
  "status": "calculating",
  "message": "Your rankings are being calculated. This may take a few moments.",
  "has_complete_profile": true,
  "regional_ranking": null,
  "university_ranking": null
}
```

### 3. **Manually Trigger Ranking Calculation**
```
POST /rankings/calculate
```
**Purpose**: Force recalculation of rankings

**Response**:
```json
{
  "success": true,
  "message": "Rankings calculated successfully",
  "regional_updated": true,
  "university_updated": true
}
```

## 🎨 Frontend Integration Flow

### 1. **After Profile Setup**
```javascript
// After user completes profile setup
const handleProfileComplete = async () => {
  // Profile setup automatically triggers ranking calculation
  // Show loading state and start polling for rankings
  setRankingStatus('calculating');
  pollForRankings();
};
```

### 2. **Polling for Rankings**
```javascript
const pollForRankings = async () => {
  const maxAttempts = 30; // 30 attempts = 5 minutes
  let attempts = 0;
  
  const poll = async () => {
    try {
      const response = await fetch('/rankings/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const status = await response.json();
      
      if (status.ranking_status === 'available') {
        // Rankings are ready, fetch them
        fetchRankings();
        return;
      } else if (status.ranking_status === 'calculating') {
        // Still calculating, continue polling
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 10000); // Poll every 10 seconds
        } else {
          // Timeout, show manual refresh option
          setRankingStatus('timeout');
        }
      } else {
        // Pending profile or other status
        setRankingStatus(status.ranking_status);
      }
    } catch (error) {
      console.error('Error polling rankings:', error);
      setRankingStatus('error');
    }
  };
  
  poll();
};
```

### 3. **Fetch Rankings**
```javascript
const fetchRankings = async () => {
  try {
    const response = await fetch('/rankings', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.ok) {
      const rankings = await response.json();
      setRankings(rankings);
      setRankingStatus('available');
    } else if (response.status === 404) {
      // Rankings not available yet
      setRankingStatus('calculating');
    }
  } catch (error) {
    console.error('Error fetching rankings:', error);
    setRankingStatus('error');
  }
};
```

### 4. **Manual Refresh**
```javascript
const refreshRankings = async () => {
  setRankingStatus('calculating');
  
  try {
    // Trigger manual calculation
    await fetch('/rankings/calculate', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    // Start polling again
    pollForRankings();
  } catch (error) {
    console.error('Error refreshing rankings:', error);
    setRankingStatus('error');
  }
};
```

## 🎯 UI States

### 1. **Loading State** (`calculating`)
```jsx
<div className="ranking-widget">
  <div className="loading-spinner" />
  <h3>Calculating Your Rankings</h3>
  <p>We're analyzing your performance compared to peers in your university and region. This may take a few moments.</p>
</div>
```

### 2. **Available State** (`available`)
```jsx
<div className="ranking-widget">
  <div className="ranking-section">
    <h3>🎓 University Ranking</h3>
    <div className="rank-display">
      <span className="percentile">{rankings.university_percentile_text}</span>
      <span className="rank">Rank {rankings.university_ranking.rank_in_university} of {rankings.university_ranking.total_users_in_university}</span>
    </div>
  </div>
  
  <div className="ranking-section">
    <h3>📍 Regional Ranking</h3>
    <div className="rank-display">
      <span className="percentile">{rankings.regional_percentile_text}</span>
      <span className="rank">Rank {rankings.regional_ranking.rank_in_region} of {rankings.regional_ranking.total_users_in_region}</span>
    </div>
  </div>
</div>
```

### 3. **Pending Scan State** (`pending_scan`)
```jsx
<div className="ranking-widget">
  <h3>Complete Repository Scan</h3>
  <p>Your profile is complete! Please scan your GitHub repositories to see your rankings.</p>
  <button onClick={() => navigate('/scan')}>Scan Repositories</button>
</div>
```

### 4. **Pending Profile State** (`pending_profile`)
```jsx
<div className="ranking-widget">
  <h3>Complete Your Profile</h3>
  <p>Complete your profile to see your rankings.</p>
  <button onClick={() => navigate('/profile')}>Complete Profile</button>
</div>
```

### 5. **Error/Timeout State**
```jsx
<div className="ranking-widget">
  <h3>Rankings Unavailable</h3>
  <p>We're having trouble calculating your rankings. Please try refreshing.</p>
  <button onClick={refreshRankings}>Refresh Rankings</button>
</div>
```

## 🔄 Complete Integration Example

```jsx
import React, { useState, useEffect } from 'react';

const RankingWidget = ({ user, token }) => {
  const [rankings, setRankings] = useState(null);
  const [status, setStatus] = useState('loading');
  
  useEffect(() => {
    checkRankingStatus();
  }, []);
  
  const checkRankingStatus = async () => {
    try {
      const response = await fetch('/rankings/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const statusData = await response.json();
      
      if (statusData.ranking_status === 'available') {
        fetchRankings();
      } else if (statusData.ranking_status === 'calculating') {
        setStatus('calculating');
        setTimeout(checkRankingStatus, 10000); // Poll every 10 seconds
      } else if (statusData.ranking_status === 'pending_scan') {
        setStatus('pending_scan');
      } else if (statusData.ranking_status === 'pending_profile') {
        setStatus('pending_profile');
      } else {
        setStatus(statusData.ranking_status);
      }
    } catch (error) {
      setStatus('error');
    }
  };
  
  const fetchRankings = async () => {
    try {
      const response = await fetch('/rankings', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const rankingData = await response.json();
        setRankings(rankingData);
        setStatus('available');
      } else {
        setStatus('calculating');
        setTimeout(checkRankingStatus, 10000);
      }
    } catch (error) {
      setStatus('error');
    }
  };
  
  const refreshRankings = async () => {
    setStatus('calculating');
    try {
      await fetch('/rankings/calculate', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setTimeout(checkRankingStatus, 5000);
    } catch (error) {
      setStatus('error');
    }
  };
  
  if (status === 'calculating') {
    return (
      <div className="ranking-widget calculating">
        <div className="spinner" />
        <h3>Calculating Your Rankings</h3>
        <p>Analyzing your performance compared to peers...</p>
      </div>
    );
  }
  
  if (status === 'available' && rankings) {
    return (
      <div className="ranking-widget available">
        {rankings.university_ranking && (
          <div className="ranking-section">
            <h3>🎓 University Ranking</h3>
            <div className="percentile-badge">
              {rankings.university_percentile_text}
            </div>
            <div className="rank-details">
              Rank {rankings.university_ranking.rank_in_university} of {rankings.university_ranking.total_users_in_university}
            </div>
          </div>
        )}
        
        {rankings.regional_ranking && (
          <div className="ranking-section">
            <h3>📍 Regional Ranking</h3>
            <div className="percentile-badge">
              {rankings.regional_percentile_text}
            </div>
            <div className="rank-details">
              Rank {rankings.regional_ranking.rank_in_region} of {rankings.regional_ranking.total_users_in_region}
            </div>
          </div>
        )}
      </div>
    );
  }
  
  if (status === 'pending_scan') {
    return (
      <div className="ranking-widget pending">
        <h3>Complete Repository Scan</h3>
        <p>Your profile is complete! Please scan your repositories to see your rankings.</p>
        <button onClick={() => navigate('/scan')}>Scan Repositories</button>
      </div>
    );
  }
  
  if (status === 'pending_profile') {
    return (
      <div className="ranking-widget pending">
        <h3>Complete Your Profile</h3>
        <p>Complete your profile to see your rankings</p>
        <button onClick={() => navigate('/profile')}>Complete Profile</button>
      </div>
    );
  }
  
  return (
    <div className="ranking-widget error">
      <h3>Rankings Unavailable</h3>
      <button onClick={refreshRankings}>Refresh</button>
    </div>
  );
};

export default RankingWidget;
```

## 🎨 CSS Styling Example

```css
.ranking-widget {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin: 16px 0;
}

.ranking-section {
  margin-bottom: 20px;
}

.percentile-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: bold;
  display: inline-block;
  margin-bottom: 8px;
}

.rank-details {
  color: #666;
  font-size: 14px;
}

.calculating .spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

## ✅ Summary

The unified ranking system is now fully functional and provides:

1. **Automatic ranking calculation** after profile completion
2. **Real-time status checking** with polling support
3. **Complete ranking data** including percentiles and statistics
4. **Manual refresh capability** for users
5. **Proper loading states** and error handling

The system will automatically show rankings once the user completes their profile and has GitHub scan data. The frontend should implement polling to check for ranking availability and provide appropriate loading states.