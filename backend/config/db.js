const mongoose = require('mongoose');

const connectDB = async () => {
  const uri = process.env.MONGO_URI;

  if (!uri) {
    console.error('❌ MONGO_URI is not set in .env file');
    process.exit(1);
  }

  try {
    const conn = await mongoose.connect(uri, {
      serverSelectionTimeoutMS: 15000,
      socketTimeoutMS: 45000,
      family: 4, // Force IPv4 — fixes DNS issues on some networks
    });
    console.log(`✅ MongoDB Connected: ${conn.connection.host}`);
    console.log(`📦 Database: ${conn.connection.name}`);
  } catch (err) {
    console.error(`❌ MongoDB Connection Failed: ${err.message}`);
    console.error('\n🔧 Fix checklist:');
    console.error('  1. MongoDB Atlas → Network Access → Add 0.0.0.0/0');
    console.error('  2. Try switching to mobile hotspot (WiFi may block port 27017)');
    console.error('  3. Check password in .env is correct\n');
    // Don't exit — let server run so APIs return proper error
    console.error('⚠️  Server running WITHOUT database. Fix connection to enable APIs.\n');
  }
};

module.exports = connectDB;
