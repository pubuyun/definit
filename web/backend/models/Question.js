const mongoose = require("mongoose");

// Syllabus schema
const syllabusSchema = new mongoose.Schema({
  number: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  content: {
    type: [String],
    default: [],
  },
});

// Sub-sub-question schema
const subSubQuestionSchema = new mongoose.Schema({
  number: {
    type: String,
    required: true,
  },
  text: {
    type: String,
    required: true,
  },
  marks: {
    type: Number,
    default: 0,
  },
  answer: {
    type: String,
    default: null,
  },
  image: {
    type: mongoose.Schema.Types.Mixed, // Can be string or array of strings
    default: null,
  },
  ms_image: {
    type: String,
    default: null,
  },
  syllabus: syllabusSchema,
});

// Sub-question schema
const subQuestionSchema = new mongoose.Schema({
  number: {
    type: String,
    required: true,
  },
  text: {
    type: String,
    required: true,
  },
  subsubquestions: {
    type: [subSubQuestionSchema],
    default: null,
  },
  answer: {
    type: String,
    default: null,
  },
  marks: {
    type: Number,
    default: 0,
  },
  image: {
    type: mongoose.Schema.Types.Mixed, // Can be string or array of strings
    default: null,
  },
  ms_image: {
    type: String,
    default: null,
  },
  syllabus: syllabusSchema,
});

// Main question schema
const questionSchema = new mongoose.Schema(
  {
    number: {
      type: Number,
      required: true,
    },
    text: {
      type: String,
      required: true,
    },
    subquestions: {
      type: [subQuestionSchema],
      default: null,
    },
    marks: {
      type: Number,
      default: 0,
    },
    answer: {
      type: String,
      default: null,
    },
    image: {
      type: mongoose.Schema.Types.Mixed, // Can be string or array of strings
      default: null,
    },
    ms_image: {
      type: String,
      default: null,
    },
    syllabus: {
      type: syllabusSchema,
      default: null,
    },
    // MCQ specific fields
    options: {
      type: [String],
      default: null,
    },
    // Additional metadata
    paper: {
      type: String, // e.g., "0610_s20_qp_32", "0610_s20_qp_22"
      required: true,
    },
    paper_type: {
      type: String,
      enum: ["mcq", "sq", "atp", "as", "a2"],
      required: true,
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
    session: {
      type: String, // s20, w20, m20, etc.
    },
    year: {
      type: String, // 2020, 2021, etc.
    },
    variant: {
      type: String, // 32, 22, etc.
    },
    // Search and filter tags
    topics: {
      type: [String],
      default: [],
    },
    difficulty: {
      type: String,
      enum: ["easy", "medium", "hard"],
      default: "medium",
    },
    keywords: {
      type: [String],
      default: [],
    },
  },
  {
    timestamps: true,
    collection: "questions",
  }
);

// Indexes for better query performance
questionSchema.index({ paper_type: 1 });
questionSchema.index({ subject_code: 1 });
questionSchema.index({ session: 1 });
questionSchema.index({ year: 1 });
questionSchema.index({ "syllabus.number": 1 });
questionSchema.index({ topics: 1 });
questionSchema.index({ keywords: 1 });
questionSchema.index({ paper: 1 });

// Text search index
questionSchema.index({
  text: "text",
  "subquestions.text": "text",
  "subquestions.subsubquestions.text": "text",
  keywords: "text",
});

// Virtual for question type
questionSchema.virtual("question_type").get(function () {
  if (this.options && this.options.length > 0) {
    return "mcq";
  }
  if (this.subquestions && this.subquestions.length > 0) {
    return "structured";
  }
  return "short";
});

// Method to extract syllabus topics
questionSchema.methods.extractTopics = function () {
  const topics = new Set();

  // Add from main syllabus
  if (this.syllabus && this.syllabus.number) {
    topics.add(this.syllabus.number);
  }

  // Add from subquestions
  if (this.subquestions) {
    this.subquestions.forEach((sub) => {
      if (sub.syllabus && sub.syllabus.number) {
        topics.add(sub.syllabus.number);
      }
      // Add from subsubquestions
      if (sub.subsubquestions) {
        sub.subsubquestions.forEach((subsub) => {
          if (subsub.syllabus && subsub.syllabus.number) {
            topics.add(subsub.syllabus.number);
          }
        });
      }
    });
  }

  return Array.from(topics);
};

// Static method to parse paper code
questionSchema.statics.parsePaperCode = function (paperCode) {
  // Example: "0610_s20_qp_32" -> { subject_code: "0610", session: "s20", variant: "32" }
  const parts = paperCode.split("_");
  if (parts.length >= 4) {
    const year = "20" + parts[1].slice(1); // s20 -> 2020
    return {
      subject_code: parts[0],
      session: parts[1],
      year: year,
      variant: parts[3],
    };
  }
  return {};
};

module.exports = mongoose.model("Question", questionSchema);
