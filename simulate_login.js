// 🧪 SRIE06 LOGIN SIMULATION SCRIPT
// Run this in the browser console on localhost:3000

console.log("🔍 Simulating Srie06 login...");

// Clear any existing auth data to start fresh
localStorage.removeItem('auth_token');
localStorage.removeItem('auth_user');
localStorage.removeItem('refresh_token');
localStorage.removeItem('dashboard_scan_results');
localStorage.removeItem('dashboard_scan_timestamp');

// Set up Srie06 user data (matches database records)
const srie06User = {
    id: "693c4c00d4469c49d0a88a5b",
    githubUsername: "Srie06",
    email: "srie06@example.com",
    name: "SREIMATHI MG"
};

// Set up proper JWT token (24-hour expiry, matches backend secret)
const validToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTNjNGMwMGQ0NDY5YzQ5ZDBhODhhNWIiLCJ1c2VyX2lkIjoiNjkzYzRjMDBkNDQ2OWM0OWQwYTg4YTViIiwiZ2l0aHViX3VzZXJuYW1lIjoiU3JpZTA2IiwicHJlZmVycmVkX3VzZXJuYW1lIjoiU3JpZTA2IiwiZW1haWwiOiJzcmllMDZAZXhhbXBsZS5jb20iLCJleHAiOjE3NjU2OTkyMDAsImlhdCI6MTc2NTYxMjgwMCwidXNlcl90eXBlIjoiZGV2ZWxvcGVyIiwidHlwZSI6ImFjY2VzcyJ9.BNATJ4y3Lw-I4aiD8heszXj-efcOzmjAxpb0MVL4h9U";

// Store in localStorage (exactly as the React app does)
localStorage.setItem('auth_token', validToken);
localStorage.setItem('auth_user', JSON.stringify(srie06User));

console.log("✅ Srie06 login simulation complete!");
console.log("👤 User:", srie06User.githubUsername, `(${srie06User.name})`);
console.log("🔑 Token:", validToken.substring(0, 50) + "...");

// Test the dashboard API directly
console.log("\n🧪 Testing dashboard API...");
fetch('http://localhost:8000/profile/dashboard-data', {
    headers: {
        'Authorization': `Bearer ${validToken}`,
        'Content-Type': 'application/json'
    }
})
.then(response => {
    console.log("📡 API Response status:", response.status);
    return response.json();
})
.then(data => {
    console.log("📊 API Response data:", data);
    
    if (data.has_data) {
        console.log("✅ Dashboard API Success!");
        console.log("  📈 Overall Score:", data.overallScore);
        console.log("  📁 Repositories:", data.repositories?.length || 0);
        console.log("  👤 Target User:", data.targetUsername);
        console.log("  ✅ Profile Complete:", data.profile?.completed);
        console.log("  🏆 Rankings Available:", data.rankings?.available);
        console.log("  🔍 Evaluated Count:", data.evaluatedCount);
        console.log("  ⚡ Analyzed:", data.analyzed);
        
        console.log("\n🎯 EXPECTED RESULT:");
        console.log("  - Dashboard should show Overall Score: 72.3");
        console.log("  - Should show 5 repositories with analysis");
        console.log("  - Should NOT show 'Welcome back, ready to scan?' message");
        console.log("  - Should display actual data immediately");
    } else {
        console.log("❌ No dashboard data found");
        console.log("  Message:", data.message);
    }
})
.catch(error => {
    console.error("❌ API test failed:", error);
});

console.log("\n📋 NEXT STEPS:");
console.log("1. Navigate to /developer/dashboard");
console.log("2. Check if loadDefaultProfile() is called");
console.log("3. Verify profileAPI.getDashboardData() response");
console.log("4. Confirm setScanResults() is called with dashboard data");
console.log("5. Check if Overview component displays the data correctly");

// Reload the page to trigger the authentication flow
console.log("\n🔄 Reloading page to trigger auth flow...");
setTimeout(() => {
    window.location.reload();
}, 2000);