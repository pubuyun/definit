const mongoose = require("mongoose");
const syllabusSchema = require("./Syllabus");

const MCQuestionSchema = new mongoose.Schema({
    number: {
        type: Number,
        required: true,
    },
    text: {
        type: String,
        required: true,
    },
    options: {
        type: [String],
        required: true,
    },
    marks: {
        type: Number,
    },
    answer: {
        type: String,
    },
    image: {
        type: String,
    },
    ms_image: {
        type: String,
    },
    syllabus: {
        type: syllabusSchema,
    },
});

module.exports = MCQuestionSchema;
