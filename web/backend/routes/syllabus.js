const express = require("express");
const router = express.Router();
const Syllabus = require("../models/Syllabus");
const Question = require("../models/Question");

// GET /api/syllabus - Get all syllabus topics with filtering
router.get("/", async (req, res) => {
  try {
    const {
      page = 1,
      limit = 50,
      category,
      level,
      search,
      subject_code = "0610",
      curriculum = "igcse",
      subject = "biology",
    } = req.query;

    // Build filter object
    const filter = {
      subject_code,
      curriculum,
      subject,
    };

    if (category) filter.category = category;
    if (level && level !== "both") filter.level = level;
    if (search) {
      filter.$text = { $search: search };
    }

    // Calculate pagination
    const skip = (parseInt(page) - 1) * parseInt(limit);
    const limitNum = parseInt(limit);

    // Execute query
    const [syllabusItems, total] = await Promise.all([
      Syllabus.find(filter)
        .sort({ number: 1 })
        .skip(skip)
        .limit(limitNum)
        .lean(),
      Syllabus.countDocuments(filter),
    ]);

    res.json({
      success: true,
      data: {
        syllabus: syllabusItems,
        pagination: {
          current_page: parseInt(page),
          total_pages: Math.ceil(total / limitNum),
          total_items: total,
          items_per_page: limitNum,
        },
      },
    });
  } catch (error) {
    console.error("Error fetching syllabus:", error);
    res.status(500).json({
      success: false,
      error: {
        message: "Failed to fetch syllabus",
        details: error.message,
      },
    });
  }
});

// GET /api/syllabus/:number - Get specific syllabus topic
router.get("/:number", async (req, res) => {
  try {
    const { number } = req.params;
    const syllabusItem = await Syllabus.findOne({ number });

    if (!syllabusItem) {
      return res.status(404).json({
        success: false,
        error: {
          message: "Syllabus topic not found",
        },
      });
    }

    // Get related topics
    const relatedTopics = await Syllabus.findRelated(number);

    // Get questions for this topic
    const questionCount = await Question.countDocuments({
      $or: [
        { "syllabus.number": new RegExp(`^${number}`) },
        { "subquestions.syllabus.number": new RegExp(`^${number}`) },
        {
          "subquestions.subsubquestions.syllabus.number": new RegExp(
            `^${number}`
          ),
        },
      ],
    });

    res.json({
      success: true,
      data: {
        syllabus: syllabusItem,
        related_topics: relatedTopics.filter((item) => item.number !== number),
        question_count: questionCount,
      },
    });
  } catch (error) {
    console.error("Error fetching syllabus topic:", error);
    res.status(500).json({
      success: false,
      error: {
        message: "Failed to fetch syllabus topic",
        details: error.message,
      },
    });
  }
});

// GET /api/syllabus/:number/questions - Get questions for a specific syllabus topic
router.get("/:number/questions", async (req, res) => {
  try {
    const { number } = req.params;
    const {
      page = 1,
      limit = 20,
      paper_type,
      year,
      session,
      variant,
      difficulty,
    } = req.query;

    // Build filter object
    const filter = {
      $or: [
        { "syllabus.number": new RegExp(`^${number}`) },
        { "subquestions.syllabus.number": new RegExp(`^${number}`) },
        {
          "subquestions.subsubquestions.syllabus.number": new RegExp(
            `^${number}`
          ),
        },
      ],
    };

    // Add additional filters
    if (paper_type) filter.paper_type = paper_type;
    if (year) filter.year = year;
    if (session) filter.session = session;
    if (variant) filter.variant = variant;
    if (difficulty) filter.difficulty = difficulty;

    // Calculate pagination
    const skip = (parseInt(page) - 1) * parseInt(limit);
    const limitNum = parseInt(limit);

    // Execute query
    const [questions, total] = await Promise.all([
      Question.find(filter)
        .sort({ year: -1, paper: 1, number: 1 })
        .skip(skip)
        .limit(limitNum)
        .lean(),
      Question.countDocuments(filter),
    ]);

    res.json({
      success: true,
      data: {
        syllabus_number: number,
        questions,
        pagination: {
          current_page: parseInt(page),
          total_pages: Math.ceil(total / limitNum),
          total_questions: total,
          questions_per_page: limitNum,
        },
        filters: {
          paper_type,
          year,
          session,
          variant,
          difficulty,
        },
      },
    });
  } catch (error) {
    console.error("Error fetching questions for syllabus:", error);
    res.status(500).json({
      success: false,
      error: {
        message: "Failed to fetch questions for syllabus topic",
        details: error.message,
      },
    });
  }
});

// GET /api/syllabus/categories/list - Get all categories
router.get("/categories/list", async (req, res) => {
  try {
    const categories = await Syllabus.distinct("category");

    res.json({
      success: true,
      data: {
        categories: categories.filter((cat) => cat !== null),
      },
    });
  } catch (error) {
    console.error("Error fetching categories:", error);
    res.status(500).json({
      success: false,
      error: {
        message: "Failed to fetch categories",
        details: error.message,
      },
    });
  }
});

// GET /api/syllabus/tree - Get syllabus as hierarchical tree
router.get("/tree", async (req, res) => {
  try {
    const { subject_code = "0610" } = req.query;

    const syllabusItems = await Syllabus.find({ subject_code })
      .sort({ number: 1 })
      .lean();

    // Build hierarchical tree
    const tree = {};

    syllabusItems.forEach((item) => {
      const parts = item.number.split(".");
      const mainTopic = parts[0];
      const subTopic = parts[1];

      if (!tree[mainTopic]) {
        tree[mainTopic] = {
          number: mainTopic,
          title: item.title.split(" ").slice(1).join(" "), // Remove number prefix
          subtopics: {},
          items: [],
        };
      }

      if (subTopic) {
        if (!tree[mainTopic].subtopics[subTopic]) {
          tree[mainTopic].subtopics[subTopic] = {
            number: `${mainTopic}.${subTopic}`,
            title: item.title,
            items: [],
          };
        }
        tree[mainTopic].subtopics[subTopic].items.push(item);
      } else {
        tree[mainTopic].items.push(item);
      }
    });

    // Convert to array format
    const treeArray = Object.values(tree).map((topic) => ({
      ...topic,
      subtopics: Object.values(topic.subtopics),
    }));

    res.json({
      success: true,
      data: {
        tree: treeArray,
        total_topics: syllabusItems.length,
      },
    });
  } catch (error) {
    console.error("Error building syllabus tree:", error);
    res.status(500).json({
      success: false,
      error: {
        message: "Failed to build syllabus tree",
        details: error.message,
      },
    });
  }
});

// GET /api/syllabus/stats - Get syllabus statistics
router.get("/stats", async (req, res) => {
  try {
    const { subject_code = "0610" } = req.query;

    const [totalTopics, categoryStats, levelStats, topicsWithQuestions] =
      await Promise.all([
        Syllabus.countDocuments({ subject_code }),
        Syllabus.aggregate([
          { $match: { subject_code } },
          { $group: { _id: "$category", count: { $sum: 1 } } },
          { $sort: { count: -1 } },
        ]),
        Syllabus.aggregate([
          { $match: { subject_code } },
          { $group: { _id: "$level", count: { $sum: 1 } } },
        ]),
        Question.aggregate([
          {
            $group: {
              _id: "$syllabus.number",
              question_count: { $sum: 1 },
            },
          },
          { $match: { _id: { $ne: null } } },
          { $sort: { question_count: -1 } },
          { $limit: 20 },
        ]),
      ]);

    res.json({
      success: true,
      data: {
        overview: {
          total_topics: totalTopics,
        },
        stats: {
          by_category: categoryStats,
          by_level: levelStats,
          topics_with_most_questions: topicsWithQuestions,
        },
      },
    });
  } catch (error) {
    console.error("Error fetching syllabus stats:", error);
    res.status(500).json({
      success: false,
      error: {
        message: "Failed to fetch syllabus statistics",
        details: error.message,
      },
    });
  }
});

// POST /api/syllabus - Create new syllabus topic
router.post("/", async (req, res) => {
  try {
    const syllabusData = req.body;

    // Auto-extract keywords if not provided
    const syllabus = new Syllabus(syllabusData);
    if (!syllabusData.keywords || syllabusData.keywords.length === 0) {
      syllabus.keywords = syllabus.extractKeywords();
    }

    const savedSyllabus = await syllabus.save();

    res.status(201).json({
      success: true,
      data: savedSyllabus,
      message: "Syllabus topic created successfully",
    });
  } catch (error) {
    console.error("Error creating syllabus:", error);
    res.status(400).json({
      success: false,
      error: {
        message: "Failed to create syllabus topic",
        details: error.message,
      },
    });
  }
});

// POST /api/syllabus/bulk - Bulk import syllabus topics
router.post("/bulk", async (req, res) => {
  try {
    const { syllabus } = req.body;

    if (!Array.isArray(syllabus)) {
      return res.status(400).json({
        success: false,
        error: {
          message: "Syllabus must be an array",
        },
      });
    }

    const processedSyllabus = syllabus.map((s) => {
      const syllabusItem = new Syllabus(s);
      if (!s.keywords || s.keywords.length === 0) {
        s.keywords = syllabusItem.extractKeywords();
      }
      return s;
    });

    const result = await Syllabus.insertMany(processedSyllabus, {
      ordered: false,
    });

    res.status(201).json({
      success: true,
      data: {
        inserted_count: result.length,
        inserted_ids: result.map((s) => s._id),
      },
      message: `Successfully imported ${result.length} syllabus topics`,
    });
  } catch (error) {
    console.error("Error bulk importing syllabus:", error);
    res.status(400).json({
      success: false,
      error: {
        message: "Failed to import syllabus topics",
        details: error.message,
      },
    });
  }
});

module.exports = router;
