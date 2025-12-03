const express = require("express");

module.exports = function (databaseService) {
    const router = express.Router();
    router.get("/", async (req, res) => {
        console.log("Fetching syllabuses");
        const syllabuses = await databaseService.getSyllabuses();
        res.json({
            success: true,
            data: syllabuses,
        });
    });

    router.get("/questions/:id", async (req, res) => {
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

    return router;
};
