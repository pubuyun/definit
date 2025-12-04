const mongoose = require("mongoose");

const ssQuestionSchema = new mongoose.Schema({
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
        type: [Object],
    },
    paper_name: {
        type: String,
        required: true,
    },
    parent_id: {
        type: mongoose.Schema.Types.ObjectId,
        required: true,
    },
    parent_number: {
        type: String,
        required: true,
    },
});

module.exports = ssQuestionSchema;
