const express = require("express");
const router = express.Router();
const Question = require("../models/Question");

// GET /api/questions - Get questions with filtering and pagination
router.get("/", async (req, res) => {
  try {
    const {
      page = 1,
      limit = 20,
      paper_type,
      year,
      session,
      variant,
      syllabus,
      topic,
      difficulty,
      search,
      subject_code = "0610",
      curriculum = "igcse",
      subject = "biology",
      sort = "number",
      order = "asc",
    } = req.query;

    // Build filter object
    const filter = {
      subject_code,
      curriculum,
      subject,
    };

    // Add filters if provided
    if (paper_type) {
      if (Array.isArray(paper_type)) {
        filter.paper_type = { $in: paper_type };
      } else {
        filter.paper_type = paper_type;
      }
    }

    if (year) {
      if (Array.isArray(year)) {
        filter.year = { $in: year };
      } else {
        filter.year = year;
      }
    }

    if (session) {
      if (Array.isArray(session)) {
        filter.session = { $in: session };
      } else {
        filter.session = session;
      }
    }

    if (variant) {
      if (Array.isArray(variant)) {
        filter.variant = { $in: variant };
      } else {
        filter.variant = variant;
      }
    }

    if (syllabus) {
      const syllabusRegex = Array.isArray(syllabus)
        ? new RegExp(`^(${syllabus.join("|")})`)
        : new RegExp(`^${syllabus}`);
      filter.$or = [
        { "syllabus.number": syllabusRegex },
        { "subquestions.syllabus.number": syllabusRegex },
        { "subquestions.subsubquestions.syllabus.number": syllabusRegex },
      ];
    }

    if (topic) {
      filter.topics = Array.isArray(topic) ? { $in: topic } : topic;
    }

    if (difficulty) {
      filter.difficulty = difficulty;
    }

    // Text search
    if (search) {
      filter.$text = { $search: search };
    }

    // Build sort object
    const sortOrder = order === "desc" ? -1 : 1;
    const sortObj = {};
    sortObj[sort] = sortOrder;

    // Calculate pagination
    const skip = (parseInt(page) - 1) * parseInt(limit);
    const limitNum = parseInt(limit);

    // Execute query with pagination
    const [questions, total] = await Promise.all([
      Question.find(filter).sort(sortObj).skip(skip).limit(limitNum).lean(),
      Question.countDocuments(filter),
    ]);

    // Calculate pagination info
    const totalPages = Math.ceil(total / limitNum);
    const hasNext = page < totalPages;
    const hasPrev = page > 1;

    res.json({
      success: true,
      data: {
        questions,
        pagination: {
          current_page: parseInt(page),
          total_pages: totalPages,
          total_questions: total,
          questions_per_page: limitNum,
          has_next: hasNext,
          has_previous: hasPrev,
        },
        filters: {
          paper_type,
          year,
          session,
          variant,
          syllabus,
          topic,
          difficulty,
          search,
        },
      },
    });
  } catch (error) {
    console.error("Error fetching questions:", error);
    res.status(500).json({
      success: false,
      error: {
        message: "Failed to fetch questions",
        details: error.message,
      },
    });
  }
});

// GET /api/questions/search - Search questions by text
router.get("/search", async (req, res) => {
  try {
    const {
      q, // search query
      page = 1,
      limit = 20,
      paper_type,
      year,
      session,
      syllabus,
      difficulty,
      sort = "relevance", // relevance or number
    } = req.query;

    if (!q || q.trim() === "") {
      return res.status(400).json({
        success: false,
        error: {
          message: "Search query is required",
        },
      });
    }

    // Build filter object
    const filter = {
      $text: { $search: q },
    };

    // Add additional filters if provided
    if (paper_type) filter.paper_type = paper_type;
    if (year) filter.year = year;
    if (session) filter.session = session;
    if (difficulty) filter.difficulty = difficulty;
    if (syllabus) {
      const syllabusRegex = new RegExp(`^${syllabus}`);
      filter.$or = [
        { "syllabus.number": syllabusRegex },
        { "subquestions.syllabus.number": syllabusRegex },
        { "subquestions.subsubquestions.syllabus.number": syllabusRegex },
      ];
    }

    // Build sort object
    const sortObj =
      sort === "relevance" ? { score: { $meta: "textScore" } } : { number: 1 };

    // Calculate pagination
    const skip = (parseInt(page) - 1) * parseInt(limit);
    const limitNum = parseInt(limit);

    // Execute search
    const [questions, total] = await Promise.all([
      Question.find(filter, { score: { $meta: "textScore" } })
        .sort(sortObj)
        .skip(skip)
        .limit(limitNum)
        .lean(),
      Question.countDocuments(filter),
    ]);

    res.json({
      success: true,
      data: {
        questions,
        search_query: q,
        pagination: {
          current_page: parseInt(page),
          total_pages: Math.ceil(total / limitNum),
          total_results: total,
          results_per_page: limitNum,
        },
        filters: { paper_type, year, session, syllabus, difficulty },
      },
    });
  } catch (error) {
    console.error("Error searching questions:", error);
    res.status(500).json({
      success: false,
      error: {
        message: "Failed to search questions",
        details: error.message,
      },
    });
  }
});

// GET /api/questions/:id - Get specific question by ID
router.get("/:id", async (req, res) => {
  try {
    const { id } = req.params;
    const question = await Question.findById(id);

    if (!question) {
      return res.status(404).json({
        success: false,
        error: {
          message: "Question not found",
        },
      });
    }

    res.json({
      success: true,
      data: question,
    });
  } catch (error) {
    console.error("Error fetching question:", error);
    res.status(500).json({
      success: false,
      error: {
        message: "Failed to fetch question",
        details: error.message,
      },
    });
  }
});

// GET /api/questions/paper/:paper - Get questions by paper code
router.get("/paper/:paper", async (req, res) => {
  try {
    const { paper } = req.params;
    const { page = 1, limit = 50 } = req.query;

    const skip = (parseInt(page) - 1) * parseInt(limit);
    const limitNum = parseInt(limit);

    const [questions, total] = await Promise.all([
      Question.find({ paper })
        .sort({ number: 1 })
        .skip(skip)
        .limit(limitNum)
        .lean(),
      Question.countDocuments({ paper }),
    ]);

    if (questions.length === 0) {
      return res.status(404).json({
        success: false,
        error: {
          message: "No questions found for this paper",
        },
      });
    }

    res.json({
      success: true,
      data: {
        questions,
        paper,
        total_questions: total,
        pagination: {
          current_page: parseInt(page),
          total_pages: Math.ceil(total / limitNum),
          total_questions: total,
          questions_per_page: limitNum,
        },
      },
    });
  } catch (error) {
    console.error("Error fetching questions by paper:", error);
    res.status(500).json({
      success: false,
      error: {
        message: "Failed to fetch questions by paper",
        details: error.message,
      },
    });
  }
});

// GET /api/questions/stats/overview - Get statistics overview
router.get("/stats/overview", async (req, res) => {
  try {
    const [
      totalQuestions,
      mcqCount,
      sqCount,
      yearStats,
      syllabusStats,
      paperTypeStats,
    ] = await Promise.all([
      Question.countDocuments(),
      Question.countDocuments({ paper_type: "mcq" }),
      Question.countDocuments({ paper_type: "sq" }),
      Question.aggregate([
        {
          $group: {
            _id: "$year",
            count: { $sum: 1 },
          },
        },
        { $sort: { _id: 1 } },
      ]),
      Question.aggregate([
        { $unwind: "$topics" },
        {
          $group: {
            _id: "$topics",
            count: { $sum: 1 },
          },
        },
        { $sort: { count: -1 } },
        { $limit: 20 },
      ]),
      Question.aggregate([
        {
          $group: {
            _id: "$paper_type",
            count: { $sum: 1 },
          },
        },
      ]),
    ]);

    res.json({
      success: true,
      data: {
        overview: {
          total_questions: totalQuestions,
          mcq_questions: mcqCount,
          sq_questions: sqCount,
        },
        stats: {
          by_year: yearStats,
          by_topic: syllabusStats,
          by_paper_type: paperTypeStats,
        },
      },
    });
  } catch (error) {
    console.error("Error fetching question stats:", error);
    res.status(500).json({
      success: false,
      error: {
        message: "Failed to fetch question statistics",
        details: error.message,
      },
    });
  }
});

// GET /api/questions/random - Get random questions
router.get("/random", async (req, res) => {
  try {
    const { count = 10, paper_type, syllabus, difficulty, year } = req.query;

    // Build filter object
    const filter = {};
    if (paper_type) filter.paper_type = paper_type;
    if (difficulty) filter.difficulty = difficulty;
    if (year) filter.year = year;
    if (syllabus) {
      filter.$or = [
        { "syllabus.number": new RegExp(`^${syllabus}`) },
        { "subquestions.syllabus.number": new RegExp(`^${syllabus}`) },
      ];
    }

    const questions = await Question.aggregate([
      { $match: filter },
      { $sample: { size: parseInt(count) } },
    ]);

    res.json({
      success: true,
      data: {
        questions,
        count: questions.length,
        filters: { count, paper_type, syllabus, difficulty, year },
      },
    });
  } catch (error) {
    console.error("Error fetching random questions:", error);
    res.status(500).json({
      success: false,
      error: {
        message: "Failed to fetch random questions",
        details: error.message,
      },
    });
  }
});

// POST /api/questions - Create new question (for admin/data import)
router.post("/", async (req, res) => {
  try {
    const questionData = req.body;

    // Parse paper code to extract metadata
    if (questionData.paper) {
      const paperInfo = Question.parsePaperCode(questionData.paper);
      Object.assign(questionData, paperInfo);
    }

    // Extract topics from syllabus
    const question = new Question(questionData);
    if (!questionData.topics || questionData.topics.length === 0) {
      question.topics = question.extractTopics();
    }

    const savedQuestion = await question.save();

    res.status(201).json({
      success: true,
      data: savedQuestion,
      message: "Question created successfully",
    });
  } catch (error) {
    console.error("Error creating question:", error);
    res.status(400).json({
      success: false,
      error: {
        message: "Failed to create question",
        details: error.message,
      },
    });
  }
});

// POST /api/questions/bulk - Bulk import questions
router.post("/bulk", async (req, res) => {
  try {
    const { questions } = req.body;

    if (!Array.isArray(questions)) {
      return res.status(400).json({
        success: false,
        error: {
          message: "Questions must be an array",
        },
      });
    }

    const processedQuestions = questions.map((q) => {
      // Parse paper code
      if (q.paper) {
        const paperInfo = Question.parsePaperCode(q.paper);
        Object.assign(q, paperInfo);
      }

      // Extract topics
      const question = new Question(q);
      if (!q.topics || q.topics.length === 0) {
        q.topics = question.extractTopics();
      }

      return q;
    });

    const result = await Question.insertMany(processedQuestions, {
      ordered: false,
    });

    res.status(201).json({
      success: true,
      data: {
        inserted_count: result.length,
        inserted_ids: result.map((q) => q._id),
      },
      message: `Successfully imported ${result.length} questions`,
    });
  } catch (error) {
    console.error("Error bulk importing questions:", error);
    res.status(400).json({
      success: false,
      error: {
        message: "Failed to import questions",
        details: error.message,
      },
    });
  }
});

module.exports = router;
