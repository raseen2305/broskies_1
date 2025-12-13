#!/usr/bin/env node

/**
 * Toggle Dev Login Script
 * 
 * Quick script to enable/disable dev login in .env file
 * 
 * Usage:
 *   node toggle-dev-login.js on   # Enable dev login
 *   node toggle-dev-login.js off  # Disable dev login
 */

const fs = require('fs');
const path = require('path');

const ENV_FILE = path.join(__dirname, '.env');
const DEV_LOGIN_LINE = 'VITE_ENABLE_DEV_LOGIN=true';
const DEV_LOGIN_OFF = 'VITE_ENABLE_DEV_LOGIN=false';

function toggleDevLogin(enable) {
  try {
    // Read .env file
    if (!fs.existsSync(ENV_FILE)) {
      console.error('❌ .env file not found!');
      console.log('💡 Create a .env file first or copy from .env.example');
      process.exit(1);
    }

    let content = fs.readFileSync(ENV_FILE, 'utf8');

    if (enable) {
      // Enable dev login
      if (content.includes('VITE_ENABLE_DEV_LOGIN=true')) {
        console.log('✅ Dev login is already enabled!');
        return;
      }

      if (content.includes('VITE_ENABLE_DEV_LOGIN=false')) {
        content = content.replace(/VITE_ENABLE_DEV_LOGIN=false/g, 'VITE_ENABLE_DEV_LOGIN=true');
      } else if (content.includes('VITE_ENABLE_DEV_LOGIN')) {
        content = content.replace(/VITE_ENABLE_DEV_LOGIN=.*/g, 'VITE_ENABLE_DEV_LOGIN=true');
      } else {
        // Add dev login config
        content += '\n\n# Development Login (TESTING ONLY - Remove after testing!)\n';
        content += '# WARNING: This bypasses OAuth authentication. Only for development/testing.\n';
        content += 'VITE_ENABLE_DEV_LOGIN=true\n';
      }

      fs.writeFileSync(ENV_FILE, content);
      console.log('✅ Dev login ENABLED!');
      console.log('');
      console.log('📝 Test Credentials:');
      console.log('   Email: test.hr@devonly.local');
      console.log('   Password: DevTest2024!Secure');
      console.log('');
      console.log('🔄 Restart your dev server to see changes');
      console.log('   npm run dev');
      console.log('');
      console.log('🌐 Navigate to: http://localhost:5173/hr/auth');
    } else {
      // Disable dev login
      if (content.includes('VITE_ENABLE_DEV_LOGIN=false')) {
        console.log('✅ Dev login is already disabled!');
        return;
      }

      if (content.includes('VITE_ENABLE_DEV_LOGIN=true')) {
        content = content.replace(/VITE_ENABLE_DEV_LOGIN=true/g, 'VITE_ENABLE_DEV_LOGIN=false');
      } else if (content.includes('VITE_ENABLE_DEV_LOGIN')) {
        content = content.replace(/VITE_ENABLE_DEV_LOGIN=.*/g, 'VITE_ENABLE_DEV_LOGIN=false');
      }

      fs.writeFileSync(ENV_FILE, content);
      console.log('✅ Dev login DISABLED!');
      console.log('');
      console.log('🔄 Restart your dev server to see changes');
      console.log('   npm run dev');
    }
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

// Parse command line arguments
const args = process.argv.slice(2);
const command = args[0]?.toLowerCase();

if (!command || !['on', 'off', 'enable', 'disable'].includes(command)) {
  console.log('Usage:');
  console.log('  node toggle-dev-login.js on   # Enable dev login');
  console.log('  node toggle-dev-login.js off  # Disable dev login');
  process.exit(1);
}

const enable = ['on', 'enable'].includes(command);
toggleDevLogin(enable);
