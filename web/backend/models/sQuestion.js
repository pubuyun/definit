const mongoose = require("mongoose");
const syllabusSchema = require("./Syllabus");
const ssQuestionSchema = require("./ssQuestion");

const sQuestionSchema = new mongoose.Schema({
    number: {
        type: String,
        match: /^[a-z]+$/,
        required: true,
    },
    text: {
        type: String,
        required: true,
    },
    subsubquestions: {
        type: [ssQuestionSchema],
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

module.exports = sQuestionSchema;
