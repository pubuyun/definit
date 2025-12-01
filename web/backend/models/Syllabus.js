const mongoose = require("mongoose");

const syllabusSchema = new mongoose.Schema(
  {
    number: {
      type: String,
      required: true,
      unique: true,
    },
    title: {
      type: String,
      required: true,
    },
    content: {
      type: [String],
      default: [],
    },
    subject: {
      type: String,
      default: "biology",
    },
    curriculum: {
      type: String,
      default: "igcse",
    },
    subject_code: {
      type: String,
      default: "0610",
    },
    level: {
      type: String,
      enum: ["core", "supplement", "both"],
      default: "both",
    },
    category: {
      type: String, // e.g., "Cell Biology", "Genetics", "Ecology"
    },
    description: {
      type: String,
    },
    prerequisites: {
      type: [String], // Array of syllabus numbers that should be learned first
      default: [],
    },
    keywords: {
      type: [String],
      default: [],
    },
  },
  {
    timestamps: true,
    collection: "syllabus",
  }
);

// Indexes
syllabusSchema.index({ number: 1 });
syllabusSchema.index({ subject_code: 1 });
syllabusSchema.index({ category: 1 });
syllabusSchema.index({ keywords: 1 });
syllabusSchema.index({ title: "text", content: "text", keywords: "text" });

// Static method to find related topics
syllabusSchema.statics.findRelated = function (syllabusNumber) {
  const baseNumber = syllabusNumber.split(".")[0]; // Get main topic number
  return this.find({
    number: { $regex: `^${baseNumber}\\.` },
  });
};

// Method to extract keywords from content
syllabusSchema.methods.extractKeywords = function () {
  const keywords = new Set();

  // Extract from title
  const titleWords = this.title.toLowerCase().split(/\s+/);
  titleWords.forEach((word) => {
    if (word.length > 3) keywords.add(word);
  });

  // Extract from content
  this.content.forEach((item) => {
    const words = item.toLowerCase().split(/\s+/);
    words.forEach((word) => {
      // Remove common words and extract meaningful terms
      if (
        word.length > 4 &&
        !["describe", "explain", "state", "identify"].includes(word)
      ) {
        keywords.add(word);
      }
    });
  });

  return Array.from(keywords);
};

module.exports = mongoose.model("Syllabus", syllabusSchema);
