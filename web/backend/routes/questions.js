const express = require("express");

module.exports = function (databaseService) {
    const router = express.Router();
    router.get("/syllabuses", async (req, res) => {
        console.log("Fetching syllabuses");
        const syllabuses = await databaseService.getSyllabuses();
        res.json({
            success: true,
            data: syllabuses,
        });
    });

    router.get("/questions/id/:id", async (req, res) => {
        const { id } = req.params;
        const question = await databaseService.getQuestionById(id);

        if (!question) {
            return res.status(404).json({
                error: "Question not found",
            });
        }

        res.json({
            success: true,
            data: question,
        });
    });

    router.get("/questions/query", async (req, res) => {
        const {
            paperName,
            type,
            syllabusNum,
            text,
            page = 1,
            limit = 10,
            sortBy = "syllabus.number",
            sortOrder = "desc",
        } = req.query;

        const parseArray = (param) => {
            if (!param) return [];
            return param.split(",").map((s) => s.trim());
        };

        const query = {
            paperName: parseArray(paperName),
            type: parseArray(type),
            syllabusNum: parseArray(syllabusNum),
            text: text || "",
        };
        const pagination = {
            page: parseInt(page),
            limit: parseInt(limit),
            sortBy,
            sortOrder: sortOrder === "desc" ? -1 : 1,
        };
        const results = await databaseService.getQuestionsQuery(
            query,
            pagination
        );
        res.json({
            success: true,
            data: results.data,
            total: results.total,
        });
    });

    return router;
};
