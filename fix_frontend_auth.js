// Script to fix frontend authentication for raseen2305
// Run this in the browser console

// CORRECT JWT token for user_id: thoshifraseen4 (the actual user_id in database)
const authToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0aG9zaGlmcmFzZWVuNCIsInVzZXJfdHlwZSI6ImRldmVsb3BlciIsImdpdGh1Yl91c2VybmFtZSI6InJhc2VlbjIzMDUiLCJleHAiOjE3NjU2MjczMzEsImlhdCI6MTc2NTU0MDkzMSwidHlwZSI6ImFjY2VzcyJ9.RCWxa2WrcYh4-tBaGXM_2cJGCQrsdR84I0U7H-RokzA';

// Set authentication token
localStorage.setItem('auth_token', authToken);

// Set user data (using correct user_id from database)
const userData = {
  id: 'thoshifraseen4',  // This is the actual user_id in the database
  username: 'raseen2305',
  email: 'raseen2305@test.com',
  user_type: 'developer'
};
localStorage.setItem('auth_user', JSON.stringify(userData));

console.log('✅ Authentication token set for raseen2305');
console.log('🔄 Please refresh the page to apply authentication');

// Test the authentication by making a request
fetch('http://localhost:8000/rankings', {
  headers: {
    'Authorization': `Bearer ${authToken}`,
    'Content-Type': 'application/json'
  }
})
.then(response => {
  console.log('🔸 Rankings endpoint status:', response.status);
  return response.json();
})
.then(data => {
  console.log('🔸 Rankings response:', data);
})
.catch(error => {
  console.error('❌ Rankings request failed:', error);
});