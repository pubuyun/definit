const express = require("express");
const { MongoClient } = require("mongodb");
const cors = require("cors");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB connection
let db;
const mongoUri = process.env.MONGO_URI;
const dbName = "igcse-biology-0610";

MongoClient.connect(mongoUri)
  .then((client) => {
    console.log("Connected to MongoDB");
    db = client.db(dbName);
  })
  .catch((error) => console.error("MongoDB connection error:", error));

// Helper function to get all collections
async function getCollections() {
  try {
    const collections = await db.listCollections().toArray();
    return collections.map((col) => col.name);
  } catch (error) {
    console.error("Error getting collections:", error);
    return [];
  }
}

// API Endpoints

/**
 * GET /api/papers
 * Get list of all available papers (collections)
 */
app.get("/api/papers", async (req, res) => {
  try {
    const collections = await getCollections();
    res.json({
      success: true,
      data: collections,
      count: collections.length,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: "Failed to fetch papers",
      details: error.message,
    });
  }
});

/**
 * GET /api/syllabus
 * Get unique syllabus topics from all questions
 */
app.get("/api/syllabus", async (req, res) => {
  try {
    const collections = await getCollections();
    const syllabusSet = new Set();

    for (const collectionName of collections) {
      const collection = db.collection(collectionName);

      // Aggregate to get all unique syllabus entries
      const pipeline = [
        { $match: { "subquestions.syllabus": { $exists: true } } },
        { $unwind: "$subquestions" },
        { $match: { "subquestions.syllabus": { $ne: null } } },
        {
          $group: {
            _id: {
              number: "$subquestions.syllabus.number",
              title: "$subquestions.syllabus.title",
            },
          },
        },
      ];

      const results = await collection.aggregate(pipeline).toArray();
      results.forEach((result) => {
        if (result._id.number && result._id.title) {
          syllabusSet.add(
            JSON.stringify({
              number: result._id.number,
              title: result._id.title,
            })
          );
        }
      });

      // Also check subsubquestions
      const subsubPipeline = [
        {
          $match: {
            "subquestions.subsubquestions.syllabus": { $exists: true },
          },
        },
        { $unwind: "$subquestions" },
        { $unwind: "$subquestions.subsubquestions" },
        { $match: { "subquestions.subsubquestions.syllabus": { $ne: null } } },
        {
          $group: {
            _id: {
              number: "$subquestions.subsubquestions.syllabus.number",
              title: "$subquestions.subsubquestions.syllabus.title",
            },
          },
        },
      ];

      const subsubResults = await collection
        .aggregate(subsubPipeline)
        .toArray();
      subsubResults.forEach((result) => {
        if (result._id.number && result._id.title) {
          syllabusSet.add(
            JSON.stringify({
              number: result._id.number,
              title: result._id.title,
            })
          );
        }
      });
    }

    const syllabusList = Array.from(syllabusSet).map((item) =>
      JSON.parse(item)
    );
    syllabusList.sort((a, b) => a.number.localeCompare(b.number));

    res.json({
      success: true,
      data: syllabusList,
      count: syllabusList.length,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: "Failed to fetch syllabus list",
      details: error.message,
    });
  }
});

/**
 * GET /api/questions/by-syllabus/:syllabusNumber
 * Get questions filtered by syllabus number
 */
app.get("/api/questions/by-syllabus/:syllabusNumber", async (req, res) => {
  try {
    const { syllabusNumber } = req.params;
    const { page = 1, limit = 10, paper } = req.query;
    const skip = (parseInt(page) - 1) * parseInt(limit);

    const collections = paper ? [paper] : await getCollections();
    let allQuestions = [];

    for (const collectionName of collections) {
      const collection = db.collection(collectionName);

      // Find questions with matching syllabus in subquestions or subsubquestions
      const pipeline = [
        {
          $match: {
            $or: [
              { "subquestions.syllabus.number": syllabusNumber },
              {
                "subquestions.subsubquestions.syllabus.number": syllabusNumber,
              },
            ],
          },
        },
        {
          $addFields: {
            paper: collectionName,
          },
        },
      ];

      const questions = await collection.aggregate(pipeline).toArray();
      allQuestions = allQuestions.concat(questions);
    }

    const total = allQuestions.length;
    const paginatedQuestions = allQuestions.slice(skip, skip + parseInt(limit));

    res.json({
      success: true,
      data: paginatedQuestions,
      pagination: {
        currentPage: parseInt(page),
        totalPages: Math.ceil(total / parseInt(limit)),
        totalItems: total,
        itemsPerPage: parseInt(limit),
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: "Failed to fetch questions by syllabus",
      details: error.message,
    });
  }
});

/**
 * GET /api/questions/by-paper/:paperName
 * Get all questions from a specific paper
 */
app.get("/api/questions/by-paper/:paperName", async (req, res) => {
  try {
    const { paperName } = req.params;
    const { page = 1, limit = 10 } = req.query;
    const skip = (parseInt(page) - 1) * parseInt(limit);

    const collection = db.collection(paperName);

    const total = await collection.countDocuments();
    const questions = await collection
      .find({})
      .skip(skip)
      .limit(parseInt(limit))
      .toArray();

    res.json({
      success: true,
      data: questions,
      pagination: {
        currentPage: parseInt(page),
        totalPages: Math.ceil(total / parseInt(limit)),
        totalItems: total,
        itemsPerPage: parseInt(limit),
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: "Failed to fetch questions from paper",
      details: error.message,
    });
  }
});

/**
 * GET /api/questions/:questionNumber
 * Get a specific question by number from a paper
 */
app.get("/api/questions/:questionNumber", async (req, res) => {
  try {
    const { questionNumber } = req.params;
    const { paper } = req.query;

    if (!paper) {
      return res.status(400).json({
        success: false,
        error: "Paper parameter is required",
      });
    }

    const collection = db.collection(paper);
    const question = await collection.findOne({
      number: parseInt(questionNumber),
    });

    if (!question) {
      return res.status(404).json({
        success: false,
        error: "Question not found",
      });
    }

    res.json({
      success: true,
      data: question,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: "Failed to fetch question",
      details: error.message,
    });
  }
});

/**
 * POST /api/questions/search
 * Search questions by text content
 */
app.post("/api/questions/search", async (req, res) => {
  try {
    const { query, papers, syllabusNumbers, page = 1, limit = 10 } = req.body;
    const skip = (parseInt(page) - 1) * parseInt(limit);

    if (!query) {
      return res.status(400).json({
        success: false,
        error: "Search query is required",
      });
    }

    const collections =
      papers && papers.length > 0 ? papers : await getCollections();
    let allQuestions = [];

    for (const collectionName of collections) {
      const collection = db.collection(collectionName);

      let matchConditions = {
        $or: [
          { text: { $regex: query, $options: "i" } },
          { "subquestions.text": { $regex: query, $options: "i" } },
          {
            "subquestions.subsubquestions.text": {
              $regex: query,
              $options: "i",
            },
          },
        ],
      };

      // Add syllabus filter if provided
      if (syllabusNumbers && syllabusNumbers.length > 0) {
        matchConditions.$and = [
          matchConditions,
          {
            $or: [
              { "subquestions.syllabus.number": { $in: syllabusNumbers } },
              {
                "subquestions.subsubquestions.syllabus.number": {
                  $in: syllabusNumbers,
                },
              },
            ],
          },
        ];
      }

      const pipeline = [
        { $match: matchConditions },
        {
          $addFields: {
            paper: collectionName,
          },
        },
      ];

      const questions = await collection.aggregate(pipeline).toArray();
      allQuestions = allQuestions.concat(questions);
    }

    const total = allQuestions.length;
    const paginatedQuestions = allQuestions.slice(skip, skip + parseInt(limit));

    res.json({
      success: true,
      data: paginatedQuestions,
      pagination: {
        currentPage: parseInt(page),
        totalPages: Math.ceil(total / parseInt(limit)),
        totalItems: total,
        itemsPerPage: parseInt(limit),
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: "Failed to search questions",
      details: error.message,
    });
  }
});

/**
 * POST /api/questions/filter
 * Conditional query by syllabus, papers, questionTypes (sq, mcq), paperTypes (paper1, paper2, paper3...)
 */
app.post("/api/questions/filter", async (req, res) => {
  try {
    const {
      syllabusNumbers = [],
      papers = [],
      questionTypes = [],
      paperTypes = [],
      page = 1,
      limit = 10,
    } = req.body;

    // Basic validation
    if (
      (syllabusNumbers && !Array.isArray(syllabusNumbers)) ||
      (papers && !Array.isArray(papers)) ||
      (questionTypes && !Array.isArray(questionTypes)) ||
      (paperTypes && !Array.isArray(paperTypes))
    ) {
      return res.status(400).json({
        success: false,
        error:
          "Invalid request: syllabusNumbers, papers, questionTypes, paperTypes must be arrays",
      });
    }

    let itemsPerPage = parseInt(limit);
    let currentPage = parseInt(page);

    if (Number.isNaN(itemsPerPage) || itemsPerPage <= 0) itemsPerPage = 10;
    if (itemsPerPage > 100) itemsPerPage = 100;
    if (Number.isNaN(currentPage) || currentPage <= 0) currentPage = 1;

    const skip = (currentPage - 1) * itemsPerPage;

    const allCollections =
      Array.isArray(papers) && papers.length > 0
        ? papers
        : await getCollections();

    const normalizedQuestionTypes = Array.isArray(questionTypes)
      ? questionTypes.map((t) => String(t).toLowerCase())
      : [];

    // Accept formats like "paper1" or "1"
    const normalizedPaperTypes = Array.isArray(paperTypes)
      ? paperTypes
          .map((p) => {
            const m = String(p).match(/(\d+)/);
            return m ? m[1] : null;
          })
          .filter(Boolean)
      : [];

    // Filter collections by question type suffix (_sq/_mcq) and paper type (first digit after _qp_)
    const candidateCollections = allCollections.filter((name) => {
      let ok = true;
      const lower = name.toLowerCase();

      if (normalizedQuestionTypes.length > 0) {
        ok = normalizedQuestionTypes.some((t) => lower.endsWith(`_${t}`));
      }

      if (ok && normalizedPaperTypes.length > 0) {
        const m = lower.match(/_qp_(\d{2})_/i);
        if (m && m[1]) {
          const paperDigit = m[1][0]; // first digit indicates paper type (1,2,3,...)
          ok = normalizedPaperTypes.includes(paperDigit);
        } else {
          ok = false;
        }
      }

      return ok;
    });

    if (candidateCollections.length === 0) {
      return res.json({
        success: true,
        data: [],
        pagination: {
          currentPage,
          totalPages: 0,
          totalItems: 0,
          itemsPerPage,
        },
      });
    }

    const useSyllabusFilter =
      Array.isArray(syllabusNumbers) && syllabusNumbers.length > 0;

    let allQuestions = [];

    for (const collectionName of candidateCollections) {
      const collection = db.collection(collectionName);

      const matchConditions = useSyllabusFilter
        ? {
            $or: [
              { "subquestions.syllabus.number": { $in: syllabusNumbers } },
              {
                "subquestions.subsubquestions.syllabus.number": {
                  $in: syllabusNumbers,
                },
              },
            ],
          }
        : {};

      const pipeline = [];
      if (Object.keys(matchConditions).length > 0) {
        pipeline.push({ $match: matchConditions });
      }
      pipeline.push({
        $addFields: {
          paper: collectionName,
        },
      });

      const questions = await collection.aggregate(pipeline).toArray();
      allQuestions = allQuestions.concat(questions);
    }

    const total = allQuestions.length;
    const paginated = allQuestions.slice(skip, skip + itemsPerPage);

    res.json({
      success: true,
      data: paginated,
      pagination: {
        currentPage,
        totalPages: Math.ceil(total / itemsPerPage),
        totalItems: total,
        itemsPerPage,
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: "Failed to filter questions",
      details: error.message,
    });
  }
});

/**
 * GET /api/stats
 * Get database statistics
 */
app.get("/api/stats", async (req, res) => {
  try {
    const collections = await getCollections();
    const stats = {
      totalPapers: collections.length,
      totalQuestions: 0,
      paperStats: [],
    };

    for (const collectionName of collections) {
      const collection = db.collection(collectionName);
      const count = await collection.countDocuments();
      stats.totalQuestions += count;
      stats.paperStats.push({
        paper: collectionName,
        questionCount: count,
      });
    }

    res.json({
      success: true,
      data: stats,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: "Failed to fetch statistics",
      details: error.message,
    });
  }
});

// Health check endpoint
app.get("/api/health", (req, res) => {
  res.json({
    success: true,
    message: "Server is running",
    timestamp: new Date().toISOString(),
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error("Unhandled error:", err);
  res.status(500).json({
    success: false,
    error: "Internal server error",
    details: process.env.NODE_ENV === "development" ? err.message : undefined,
  });
});

// 404 handler
app.use("*", (req, res) => {
  res.status(404).json({
    success: false,
    error: "Endpoint not found",
  });
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/api/health`);
});

module.exports = app;
