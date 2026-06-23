// backend/server.js
const express = require('express');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { Pool } = require('pg');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// ============================================
// MIDDLEWARE
// ============================================
app.use(cors({
    origin: 'http://localhost:3000',
    credentials: true
}));
app.use(express.json());

// ============================================
// DATABASE CONNECTION
// ============================================
const pool = new Pool({
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'coffeeshop',
    password: process.env.DB_PASSWORD,
    port: process.env.DB_PORT || 5432,
});

// Test database connection
pool.connect((err, client, release) => {
    if (err) {
        console.error('❌ Error connecting to PostgreSQL:', err.stack);
        console.log('📌 Make sure PostgreSQL is running and credentials are correct');
        console.log(`   DB_USER: ${process.env.DB_USER || 'postgres'}`);
        console.log(`   DB_NAME: ${process.env.DB_NAME || 'coffeeshop'}`);
        console.log(`   DB_HOST: ${process.env.DB_HOST || 'localhost'}`);
    } else {
        console.log('✅ Connected to PostgreSQL database');
        release();
    }
});

// ============================================
// HEALTH CHECK
// ============================================
app.get('/api/health', (req, res) => {
    res.json({ status: 'OK', message: 'Server is running' });
});

// ============================================
// REGISTER ENDPOINT
// ============================================
app.post('/api/register', async (req, res) => {
    try {
        const { username, email, password } = req.body;

        if (!username || !email || !password) {
            return res.status(400).json({ 
                success: false,
                message: 'All fields are required' 
            });
        }

        // Check if user exists
        const userExists = await pool.query(
            'SELECT * FROM users WHERE email = $1 OR username = $2',
            [email, username]
        );

        if (userExists.rows.length > 0) {
            return res.status(400).json({ 
                success: false,
                message: 'User already exists with this email or username' 
            });
        }

        // Hash password
        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash(password, salt);

        // Insert user
        const result = await pool.query(
            `INSERT INTO users (username, email, password) 
             VALUES ($1, $2, $3) 
             RETURNING id, username, email, created_at`,
            [username, email, hashedPassword]
        );

        const newUser = result.rows[0];

        res.status(201).json({
            success: true,
            message: 'User registered successfully',
            user: {
                id: newUser.id,
                username: newUser.username,
                email: newUser.email,
                created_at: newUser.created_at
            }
        });

    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({ 
            success: false,
            message: 'Server error during registration' 
        });
    }
});

// ============================================
// LOGIN ENDPOINT
// ============================================
app.post('/api/login', async (req, res) => {
    try {
        const { email, password } = req.body;

        if (!email || !password) {
            return res.status(400).json({ 
                success: false,
                message: 'Email and password are required' 
            });
        }

        // Find user
        const result = await pool.query(
            'SELECT * FROM users WHERE email = $1',
            [email]
        );

        if (result.rows.length === 0) {
            return res.status(400).json({ 
                success: false,
                message: 'Invalid credentials' 
            });
        }

        const user = result.rows[0];

        // Check password
        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) {
            return res.status(400).json({ 
                success: false,
                message: 'Invalid credentials' 
            });
        }

        // Create JWT token
        const token = jwt.sign(
            { 
                userId: user.id, 
                email: user.email,
                username: user.username
            },
            process.env.JWT_SECRET || 'your_secret_key',
            { expiresIn: '1h' }
        );

        res.json({
            success: true,
            message: 'Login successful',
            token: token,
            user: {
                id: user.id,
                username: user.username,
                email: user.email
            }
        });

    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ 
            success: false,
            message: 'Server error during login' 
        });
    }
});

// ============================================
// START SERVER WITH ERROR HANDLING
// ============================================
app.listen(5000, () => {
    console.log(`🚀 Server running on http://localhost:5000`);
    console.log(`📡 Endpoints:`);
    console.log(`   GET  http://localhost:5000/api/health`);
    console.log(`   POST http://localhost:5000/api/register`);
    console.log(`   POST http://localhost:5000/api/login`);
}).on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        console.log(`❌ Port 5000 is already in use!`);
        console.log(`💡 Try changing PORT in .env file`);
    } else {
        console.log('❌ Server error:', err);
    }
});

// Catch unhandled errors
process.on('unhandledRejection', (err) => {
    console.error('Unhandled Rejection:', err);
});

process.on('uncaughtException', (err) => {
    console.error('Uncaught Exception:', err);
});
