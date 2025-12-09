const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");
require("dotenv").config();

const app = express();

const questionRoutes = require("./routes/questions");
const databaseService = require("./services/databaseService");
const imageService = require("./services/imageService");

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));

// const limiter = rateLimit({
//     windowMs: 15 * 60 * 1000,
//     max: 100,
//     message: "Too many requests from this IP, please try again later.",
// });
// app.use(limiter);

async function setupDatabaseServices() {
    const adminDb = mongoose.connection.db.admin();
    const result = await adminDb.listDatabases();
    const databaseNames = result.databases.map((db) => db.name);
    // igcse-biology-0610, etc.
    const dbServices = {};
    const dbNames = {};
    for (const dbName of databaseNames) {
        const match = dbName.match(/.+\-.+\-(\d+)/);
        if (match) {
            const subjectCode = match[1];
            dbServices[subjectCode] = new databaseService(dbName);
            await new Promise((resolve) => {
                dbServices[subjectCode].connection.once("open", resolve);
            });
            await dbServices[subjectCode].init();
            app.use(
                `/api/${subjectCode}`,
                questionRoutes(dbServices[subjectCode])
            );
            dbNames[subjectCode] = dbName;
            console.log(
                `Registered subject code: ${subjectCode} (database: ${dbName}, routes at /api/${subjectCode})`
            );
        }
    }
    return { dbServices, dbNames };
}

async function setupImageService() {
    const imgService = new imageService();
    app.get("/api/image", async (req, res, next) => {
        const imageName = req.query.image;
        try {
            const imageUrl = await imgService.getImageUrl(imageName);
            console.log("Generated image URL:", imageUrl);
            res.json({ imageUrl });
        } catch (error) {
            return next(error);
        }
    });
    return imageService;
}

function initializeApi() {
    // Endpoint to get available syllabuses
    app.get("/api/syllabuses", (req, res) => {
        const syllabuses = Object.keys(app.locals.dbServices).map((code) => {
            return {
                subjectCode: code,
                databaseName: app.locals.dbNames[code],
            };
        });
        res.json(syllabuses);
    });

    // Health check endpoint
    app.get("/api/health", (req, res) => {
        res.json({
            status: "OK",
            timestamp: new Date().toISOString(),
            database:
                mongoose.connection.readyState === 1
                    ? "Connected"
                    : "Disconnected",
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
}

// MongoDB connection
mongoose.connect(process.env.MONGO_URI).then(async () => {
    console.log("Connected to MongoDB");
    const { dbServices, dbNames } = await setupDatabaseServices();
    const imageServiceInstance = await setupImageService();
    app.locals.dbServices = dbServices;
    app.locals.dbNames = dbNames;
    app.locals.imageService = imageServiceInstance;
    initializeApi();
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

module.exports = app;
