const axios = require('axios');

const API_BASE_URL = 'http://192.168.29.199:8000/api';
let token = ''; // Will be set after login

// Function to log in and get token
async function login(email, password) {
  try {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await axios.post(`${API_BASE_URL}/users/login`, formData);
    token = response.data.access_token;
    console.log('Login successful, token acquired.');
    return token;
  } catch (error) {
    console.error('Login failed:', error.response?.data || error.message);
    process.exit(1);
  }
}

// Function to get current user
async function getCurrentUser() {
  try {
    const response = await axios.get(`${API_BASE_URL}/users/me`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    console.log('Current user:', response.data);
    return response.data;
  } catch (error) {
    console.error('Get current user failed:', error.response?.data || error.message);
  }
}

// Function to create a test user
async function createTestUser(username, email, password) {
  try {
    const userData = { username, email, password };
    const response = await axios.post(`${API_BASE_URL}/users/register`, userData);
    console.log(`Test user ${username} created:`, response.data);
    return response.data;
  } catch (error) {
    if (error.response?.status === 400 && error.response?.data?.detail?.includes('already')) {
      console.log(`User ${username} already exists, continuing...`);
      return { username, email };
    }
    console.error(`Create test user ${username} failed:`, error.response?.data || error.message);
  }
}

// Function to follow a user
async function followUser(userId) {
  try {
    const response = await axios.post(`${API_BASE_URL}/users/${userId}/follow`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
    console.log(`Successfully followed user ${userId}:`, response.data);
    return response.data;
  } catch (error) {
    console.error(`Follow user ${userId} failed:`, error.response?.data || error.message);
  }
}

// Function to unfollow a user
async function unfollowUser(userId) {
  try {
    const response = await axios.delete(`${API_BASE_URL}/users/${userId}/follow`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    console.log(`Successfully unfollowed user ${userId}`);
    return response.data;
  } catch (error) {
    console.error(`Unfollow user ${userId} failed:`, error.response?.data || error.message);
  }
}

// Function to get followers
async function getFollowers(userId) {
  try {
    const response = await axios.get(`${API_BASE_URL}/users/${userId}/followers`);
    console.log(`Followers of user ${userId}:`, response.data);
    return response.data;
  } catch (error) {
    console.error(`Get followers for ${userId} failed:`, error.response?.data || error.message);
  }
}

// Function to get following
async function getFollowing(userId) {
  try {
    const response = await axios.get(`${API_BASE_URL}/users/${userId}/following`);
    console.log(`Users that ${userId} is following:`, response.data);
    return response.data;
  } catch (error) {
    console.error(`Get following for ${userId} failed:`, error.response?.data || error.message);
  }
}

// Function to check if following
async function checkIsFollowing(userId) {
  try {
    const response = await axios.get(`${API_BASE_URL}/users/${userId}/is-following`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    console.log(`Is following user ${userId}:`, response.data);
    return response.data;
  } catch (error) {
    console.error(`Check if following ${userId} failed:`, error.response?.data || error.message);
  }
}

// Function to get follow stats
async function getFollowStats(userId) {
  try {
    const response = await axios.get(`${API_BASE_URL}/users/${userId}/follow-stats`);
    console.log(`Follow stats for user ${userId}:`, response.data);
    return response.data;
  } catch (error) {
    console.error(`Get follow stats for ${userId} failed:`, error.response?.data || error.message);
  }
}

// Main test function
async function runTests() {
  try {
    // Create test users
    const user1 = await createTestUser('testuser1', 'testuser1@example.com', 'password123');
    const user2 = await createTestUser('testuser2', 'testuser2@example.com', 'password123');
    
    // Login as user1
    await login('testuser1@example.com', 'password123');
    const currentUser = await getCurrentUser();
    
    // Check follow stats before following
    await getFollowStats(currentUser.user_id);
    
    // Follow user2
    await followUser(user2.user_id);
    
    // Check if following
    await checkIsFollowing(user2.user_id);
    
    // Get following
    await getFollowing(currentUser.user_id);
    
    // Get followers of user2
    await getFollowers(user2.user_id);
    
    // Check follow stats after following
    await getFollowStats(currentUser.user_id);
    await getFollowStats(user2.user_id);
    
    // Unfollow user2
    await unfollowUser(user2.user_id);
    
    // Check if following after unfollow
    await checkIsFollowing(user2.user_id);
    
    // Check follow stats after unfollowing
    await getFollowStats(currentUser.user_id);
    await getFollowStats(user2.user_id);
    
    console.log('All tests completed!');
  } catch (error) {
    console.error('Test error:', error);
  }
}

// Extract command line arguments
const args = process.argv.slice(2);
if (args.length > 0) {
  // Run specific test if specified
  const testName = args[0];
  if (testName === 'login') {
    login('testuser1@example.com', 'password123').then(console.log);
  } else if (testName === 'follow' && args[1]) {
    login('testuser1@example.com', 'password123')
      .then(() => followUser(args[1]));
  } else if (testName === 'unfollow' && args[1]) {
    login('testuser1@example.com', 'password123')
      .then(() => unfollowUser(args[1]));
  } else if (testName === 'followers' && args[1]) {
    getFollowers(args[1]);
  } else if (testName === 'following' && args[1]) {
    getFollowing(args[1]);
  } else if (testName === 'is-following' && args[1]) {
    login('testuser1@example.com', 'password123')
      .then(() => checkIsFollowing(args[1]));
  } else if (testName === 'stats' && args[1]) {
    getFollowStats(args[1]);
  } else {
    console.log('Invalid command. Available commands:');
    console.log('login');
    console.log('follow <userId>');
    console.log('unfollow <userId>');
    console.log('followers <userId>');
    console.log('following <userId>');
    console.log('is-following <userId>');
    console.log('stats <userId>');
  }
} else {
  // Run all tests
  runTests();
}
