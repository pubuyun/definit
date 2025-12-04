const mongoose = require("mongoose");
const syllabusSchema = require("./Syllabus");
const ssQuestionSchema = new mongoose.Schema(
    {
        number: {
            type: String,
            match: /^[ixvcl]+$/,
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
            type: String,
        },
        ms_image: {
            type: String,
        },
        syllabus: {
            type: syllabusSchema,
        },
    },
    { strict: true }
);

module.exports = ssQuestionSchema;
