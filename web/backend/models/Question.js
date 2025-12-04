const mongoose = require("mongoose");
const syllabusSchema = require("./Syllabus");
const sQuestionSchema = require("./sQuestion");

const QuestionSchema = new mongoose.Schema({
    number: {
        type: Number,
        required: true,
    },
    text: {
        type: String,
        required: true,
    },
    subquestions: {
        type: [sQuestionSchema],
        required: true,
    },
    marks: {
        type: Number,
    },
    answer: {
        type: String,
    },
    image: {
        type: [String],
    },
    ms_image: {
        type: [String],
    },
    syllabus: {
        type: syllabusSchema,
    },
});

module.exports = QuestionSchema;
