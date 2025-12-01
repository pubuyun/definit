const mongoose = require("mongoose");
const fs = require("fs");
const path = require("path");
require("dotenv").config();

const Question = require("../models/Question");
const Syllabus = require("../models/Syllabus");

async function importSampleData() {
  try {
    console.log("Connecting to MongoDB...");
    await mongoose.connect(process.env.MONGO_URI);
    console.log("Connected to MongoDB");

    // Clear existing data
    console.log("Clearing existing data...");
    await Question.deleteMany({});
    await Syllabus.deleteMany({});
    console.log("Existing data cleared");

    // Import MCQ questions
    console.log("Importing MCQ questions...");
    const mcqFile = path.join(
      __dirname,
      "../igcse-biology-0610.0610_s20_qp_22_mcq.json"
    );
    const mcqData = JSON.parse(fs.readFileSync(mcqFile, "utf8"));

    const mcqQuestions = mcqData.map((q) => {
      // Extract paper info from filename
      const paper = "0610_s20_qp_22";
      const paperInfo = Question.parsePaperCode(paper);

      // Remove the _id field to let MongoDB generate new ones
      const { _id, ...questionData } = q;

      return {
        ...questionData,
        paper,
        paper_type: "mcq",
        ...paperInfo,
        topics: q.syllabus ? [q.syllabus.number] : [],
        keywords: extractKeywords(
          q.text + (q.options ? " " + q.options.join(" ") : "")
        ),
      };
    });

    const savedMcqQuestions = await Question.insertMany(mcqQuestions);
    console.log(`Imported ${savedMcqQuestions.length} MCQ questions`);

    // Import SQ questions
    console.log("Importing SQ questions...");
    const sqFile = path.join(
      __dirname,
      "../igcse-biology-0610.0610_s20_qp_32_sq.json"
    );
    const sqData = JSON.parse(fs.readFileSync(sqFile, "utf8"));

    const sqQuestions = sqData.map((q) => {
      const paper = "0610_s20_qp_32";
      const paperInfo = Question.parsePaperCode(paper);

      // Remove the _id field to let MongoDB generate new ones
      const { _id, ...questionData } = q;

      // Extract all syllabus topics
      const topics = new Set();
      if (q.syllabus && q.syllabus.number) {
        topics.add(q.syllabus.number);
      }
      if (q.subquestions) {
        q.subquestions.forEach((sub) => {
          if (sub.syllabus && sub.syllabus.number) {
            topics.add(sub.syllabus.number);
          }
          if (sub.subsubquestions) {
            sub.subsubquestions.forEach((subsub) => {
              if (subsub.syllabus && subsub.syllabus.number) {
                topics.add(subsub.syllabus.number);
              }
            });
          }
        });
      }

      return {
        ...questionData,
        paper,
        paper_type: "sq",
        ...paperInfo,
        topics: Array.from(topics),
        keywords: extractKeywords(q.text),
      };
    });

    const savedSqQuestions = await Question.insertMany(sqQuestions);
    console.log(`Imported ${savedSqQuestions.length} SQ questions`);

    // Extract and import unique syllabus topics
    console.log("Importing syllabus topics...");
    const allQuestions = [...savedMcqQuestions, ...savedSqQuestions];
    const syllabusMap = new Map();

    allQuestions.forEach((q) => {
      // Add main syllabus
      if (q.syllabus) {
        syllabusMap.set(q.syllabus.number, {
          number: q.syllabus.number,
          title: q.syllabus.title,
          content: q.syllabus.content || [],
          subject: "biology",
          curriculum: "igcse",
          subject_code: "0610",
          category: getCategoryFromTitle(q.syllabus.title),
          level: "both",
        });
      }

      // Add subquestion syllabus
      if (q.subquestions) {
        q.subquestions.forEach((sub) => {
          if (sub.syllabus) {
            syllabusMap.set(sub.syllabus.number, {
              number: sub.syllabus.number,
              title: sub.syllabus.title,
              content: sub.syllabus.content || [],
              subject: "biology",
              curriculum: "igcse",
              subject_code: "0610",
              category: getCategoryFromTitle(sub.syllabus.title),
              level: "both",
            });
          }

          // Add subsubquestion syllabus
          if (sub.subsubquestions) {
            sub.subsubquestions.forEach((subsub) => {
              if (subsub.syllabus) {
                syllabusMap.set(subsub.syllabus.number, {
                  number: subsub.syllabus.number,
                  title: subsub.syllabus.title,
                  content: subsub.syllabus.content || [],
                  subject: "biology",
                  curriculum: "igcse",
                  subject_code: "0610",
                  category: getCategoryFromTitle(subsub.syllabus.title),
                  level: "both",
                });
              }
            });
          }
        });
      }
    });

    const syllabusTopics = Array.from(syllabusMap.values()).map((s) => {
      const syllabus = new Syllabus(s);
      s.keywords = syllabus.extractKeywords();
      return s;
    });

    const savedSyllabus = await Syllabus.insertMany(syllabusTopics);
    console.log(`Imported ${savedSyllabus.length} syllabus topics`);

    // Print summary
    console.log("\n=== Import Summary ===");
    console.log(`MCQ Questions: ${savedMcqQuestions.length}`);
    console.log(`SQ Questions: ${savedSqQuestions.length}`);
    console.log(
      `Total Questions: ${savedMcqQuestions.length + savedSqQuestions.length}`
    );
    console.log(`Syllabus Topics: ${savedSyllabus.length}`);
    console.log("======================\n");

    console.log("Data import completed successfully!");
  } catch (error) {
    console.error("Error importing data:", error);
  } finally {
    await mongoose.disconnect();
    console.log("Disconnected from MongoDB");
  }
}

function extractKeywords(text) {
  if (!text) return [];

  // Remove HTML tags, punctuation, and convert to lowercase
  const cleanText = text
    .replace(/<[^>]*>/g, " ")
    .replace(/[^\w\s]/g, " ")
    .toLowerCase();

  // Split into words and filter
  const words = cleanText
    .split(/\s+/)
    .filter(
      (word) =>
        word.length > 3 &&
        ![
          "the",
          "and",
          "for",
          "are",
          "but",
          "not",
          "you",
          "all",
          "can",
          "her",
          "was",
          "one",
          "our",
          "had",
          "what",
          "were",
          "they",
          "this",
          "that",
          "have",
          "from",
          "with",
          "which",
          "will",
          "been",
          "their",
          "said",
          "each",
          "more",
          "than",
          "them",
          "many",
          "some",
          "time",
          "very",
          "when",
          "much",
          "then",
          "these",
          "only",
          "such",
          "made",
          "over",
          "also",
          "just",
          "most",
          "well",
          "even",
          "into",
          "after",
          "being",
          "other",
        ].includes(word)
    );

  // Return unique words, limited to top 10
  return [...new Set(words)].slice(0, 10);
}

function getCategoryFromTitle(title) {
  const titleLower = title.toLowerCase();

  if (
    titleLower.includes("cell") ||
    titleLower.includes("membrane") ||
    titleLower.includes("organelle")
  ) {
    return "Cell Biology";
  } else if (
    titleLower.includes("enzyme") ||
    titleLower.includes("respiration") ||
    titleLower.includes("photosynthesis")
  ) {
    return "Biochemistry";
  } else if (
    titleLower.includes("transport") ||
    titleLower.includes("circulation") ||
    titleLower.includes("blood")
  ) {
    return "Transport";
  } else if (
    titleLower.includes("reproduction") ||
    titleLower.includes("inheritance") ||
    titleLower.includes("gene")
  ) {
    return "Genetics & Reproduction";
  } else if (
    titleLower.includes("ecosystem") ||
    titleLower.includes("environment") ||
    titleLower.includes("food")
  ) {
    return "Ecology";
  } else if (
    titleLower.includes("coordination") ||
    titleLower.includes("hormone") ||
    titleLower.includes("nerve")
  ) {
    return "Coordination & Control";
  } else if (
    titleLower.includes("disease") ||
    titleLower.includes("immune") ||
    titleLower.includes("pathogen")
  ) {
    return "Disease & Immunity";
  } else {
    return "General Biology";
  }
}

// Run the import
if (require.main === module) {
  importSampleData();
}

module.exports = { importSampleData };
