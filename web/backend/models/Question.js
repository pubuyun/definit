const mongoose = require("mongoose");

const QuestionSchema = new mongoose.Schema({
    number: {
        type: Number,
        required: true,
    },
    text: {
        type: String,
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
        type: [Object],
    },
    paper_name: {
        type: String,
        required: true,
    },
});

module.exports = QuestionSchema;
