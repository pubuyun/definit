const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");
require("dotenv").config();

const app = express();

// Import routes
const questionRoutes = require("./routes/questions");
const databaseService = require("./services/databaseService");

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // limit each IP to 100 requests per windowMs
    message: "Too many requests from this IP, please try again later.",
});
app.use(limiter);

async function setupDatabaseServices() {
    const adminDb = mongoose.connection.db.admin();
    const result = await adminDb.listDatabases();
    const databaseNames = result.databases.map((db) => db.name);
}

// MongoDB connection
mongoose
    .connect(process.env.MONGO_URI)
    .then(() => {
        console.log("Connected to MongoDB");
    })
    .catch((error) => {
        console.error("MongoDB connection error:", error);
        process.exit(1);
    });

// Routes

// Health check endpoint
app.get("/api/health", (req, res) => {
    res.json({
        status: "OK",
        timestamp: new Date().toISOString(),
        database:
            mongoose.connection.readyState === 1 ? "Connected" : "Disconnected",
    });
});

// Error handling middleware
app.use((error, req, res, next) => {
    console.error("Error:", error);
    res.status(error.status || 500).json({
        error: {
            message: error.message || "Internal Server Error",
            status: error.status || 500,
        },
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        error: {
            message: "Route not found",
            status: 404,
        },
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

module.exports = app;
