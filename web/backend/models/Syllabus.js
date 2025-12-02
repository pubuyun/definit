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
    },
    {
        collection: "syllabus",
    }
);

module.exports = syllabusSchema;
