// 🔧 COMPREHENSIVE DASHBOARD DEBUG SCRIPT
// Run this in the browser console to diagnose the Srie06 dashboard issue

console.log("🔧 DEBUGGING SRIE06 DASHBOARD ISSUE...");

// Step 1: Check current authentication state
console.log("\n📋 STEP 1: Current Authentication State");
const authToken = localStorage.getItem('auth_token');
const authUser = localStorage.getItem('auth_user');

console.log("Auth Token:", authToken ? authToken.substring(0, 50) + "..." : "❌ MISSING");
console.log("Auth User:", authUser ? JSON.parse(authUser) : "❌ MISSING");

// Step 2: Test ALL API endpoints that affect the dashboard
console.log("\n📋 STEP 2: Testing All Relevant API Endpoints");

if (!authToken) {
    console.error("❌ No auth token found. Setting up Srie06 login...");
    
    // Auto-setup Srie06 login
    const srie06User = {
        id: "693c4c00d4469c49d0a88a5b",
        githubUsername: "Srie06",
        email: "srie06@example.com",
        name: "SREIMATHI MG"
    };
    
    const validToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTNjNGMwMGQ0NDY5YzQ5ZDBhODhhNWIiLCJ1c2VyX2lkIjoiNjkzYzRjMDBkNDQ2OWM0OWQwYTg4YTViIiwiZ2l0aHViX3VzZXJuYW1lIjoiU3JpZTA2IiwicHJlZmVycmVkX3VzZXJuYW1lIjoiU3JpZTA2IiwiZW1haWwiOiJzcmllMDZAZXhhbXBsZS5jb20iLCJleHAiOjE3NjU2OTkyMDAsImlhdCI6MTc2NTYxMjgwMCwidXNlcl90eXBlIjoiZGV2ZWxvcGVyIiwidHlwZSI6ImFjY2VzcyJ9.BNATJ4y3Lw-I4aiD8heszXj-efcOzmjAxpb0MVL4h9U";
    
    localStorage.setItem('auth_token', validToken);
    localStorage.setItem('auth_user', JSON.stringify(srie06User));
    
    console.log("✅ Srie06 login set up. Reloading page...");
    setTimeout(() => window.location.reload(), 1000);
    
} else {
    const headers = {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
    };

    // Test 1: Profile Status (determines if profile modal shows)
    console.log("🧪 1. Testing /profile/status...");
    fetch('http://localhost:8000/profile/status', { headers })
        .then(response => response.json())
        .then(data => {
            console.log("📊 Profile Status:", data);
            if (data.has_profile) {
                console.log("✅ User HAS profile - modal should NOT show");
            } else {
                console.log("❌ User has NO profile - modal WILL show");
            }
        })
        .catch(error => console.error("❌ Profile Status Error:", error));

    // Test 2: Dashboard Data (main data source)
    console.log("🧪 2. Testing /profile/dashboard-data...");
    fetch('http://localhost:8000/profile/dashboard-data', { headers })
        .then(response => response.json())
        .then(data => {
            console.log("📊 Dashboard Data:", data);
            if (data.has_data) {
                console.log("✅ Dashboard data available:");
                console.log("  - Overall Score:", data.overallScore);
                console.log("  - Repositories:", data.repositories?.length);
                console.log("  - Profile Completed:", data.profile?.completed);
                console.log("  - Rankings Available:", data.rankings?.available);
                console.log("🎯 This should be passed to setScanResults()");
            } else {
                console.log("❌ No dashboard data:", data.message);
            }
        })
        .catch(error => console.error("❌ Dashboard Data Error:", error));

    // Test 3: Rankings API (what RankingWidget calls)
    console.log("🧪 3. Testing /rankings (RankingWidget endpoint)...");
    fetch('http://localhost:8000/rankings', { headers })
        .then(response => {
            console.log("📡 Rankings Response Status:", response.status);
            return response.json();
        })
        .then(data => {
            console.log("📊 Rankings Data:", data);
            if (data.regional_ranking && data.university_ranking) {
                console.log("✅ Rankings available - RankingWidget should work");
                console.log("  - Regional rank:", data.regional_ranking.rank_in_region);
                console.log("  - University rank:", data.university_ranking.rank_in_university);
            } else {
                console.log("❌ Rankings not available - RankingWidget will show profile setup");
            }
        })
        .catch(error => {
            console.error("❌ Rankings Error:", error);
            console.log("🔍 This error will make RankingWidget show profile setup modal");
        });
}

// Step 3: Check React component states
console.log("\n📋 STEP 3: React Component State Checks");
console.log("Open React DevTools and check:");
console.log("1. AuthContext Provider - user and token values");
console.log("2. DeveloperDashboard component - scanResults state");
console.log("3. Overview component - userStats and isProfileModalOpen states");
console.log("4. RankingWidget component - hasProfile and rankings states");

// Step 4: Expected vs Actual behavior
console.log("\n📋 STEP 4: Expected vs Actual Behavior");
console.log("EXPECTED (when working correctly):");
console.log("  ✅ Dashboard shows Overall Score: 72.3");
console.log("  ✅ Shows 5 repositories with analysis");
console.log("  ✅ Profile modal does NOT appear");
console.log("  ✅ Rankings widget shows regional/university rankings");
console.log("  ✅ No 'Welcome back, ready to scan?' message");

console.log("\nACTUAL (current problem):");
console.log("  ❌ Profile setup modal is showing");
console.log("  ❌ Dashboard might show zeros or loading state");
console.log("  ❌ RankingWidget is triggering profile setup");

// Step 5: Debugging helpers
console.log("\n📋 STEP 5: Debugging Helpers");

// Helper to check localStorage
window.checkStorage = () => {
    console.log("💾 Current localStorage:");
    console.log("  auth_token:", localStorage.getItem('auth_token')?.substring(0, 50) + "...");
    console.log("  auth_user:", JSON.parse(localStorage.getItem('auth_user') || '{}'));
    console.log("  dashboard_scan_results:", localStorage.getItem('dashboard_scan_results') ? 'Present' : 'None');
};

// Helper to force reload with clean state
window.forceCleanReload = () => {
    localStorage.clear();
    window.location.reload();
};

// Helper to setup Srie06 and navigate to dashboard
window.setupSrie06Dashboard = () => {
    const srie06User = {
        id: "693c4c00d4469c49d0a88a5b",
        githubUsername: "Srie06",
        email: "srie06@example.com",
        name: "SREIMATHI MG"
    };
    
    const validToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTNjNGMwMGQ0NDY5YzQ5ZDBhODhhNWIiLCJ1c2VyX2lkIjoiNjkzYzRjMDBkNDQ2OWM0OWQwYTg4YTViIiwiZ2l0aHViX3VzZXJuYW1lIjoiU3JpZTA2IiwicHJlZmVycmVkX3VzZXJuYW1lIjoiU3JpZTA2IiwiZW1haWwiOiJzcmllMDZAZXhhbXBsZS5jb20iLCJleHAiOjE3NjU2OTkyMDAsImlhdCI6MTc2NTYxMjgwMCwidXNlcl90eXBlIjoiZGV2ZWxvcGVyIiwidHlwZSI6ImFjY2VzcyJ9.BNATJ4y3Lw-I4aiD8heszXj-efcOzmjAxpb0MVL4h9U";
    
    localStorage.clear();
    localStorage.setItem('auth_token', validToken);
    localStorage.setItem('auth_user', JSON.stringify(srie06User));
    
    console.log("✅ Srie06 setup complete. Navigating to dashboard...");
    window.location.href = '/developer/dashboard';
};

console.log("\n🛠️ Available Helper Functions:");
console.log("  checkStorage() - Check current localStorage");
console.log("  forceCleanReload() - Clear storage and reload");
console.log("  setupSrie06Dashboard() - Setup Srie06 and go to dashboard");

console.log("\n🎯 RECOMMENDED NEXT STEPS:");
console.log("1. Review API test results above");
console.log("2. Run setupSrie06Dashboard() to test the complete flow");
console.log("3. Check React DevTools for component states");
console.log("4. Look for the root cause of profile modal appearing");