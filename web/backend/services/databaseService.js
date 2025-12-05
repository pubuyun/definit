const mongoose = require("mongoose");
const mongoose_fuzzy_searching = require("mongoose-fuzzy-searching");
const syllabusSchema = require("../models/Syllabus");
const QuestionSchema = require("../models/Question");
const MCQuestionSchema = require("../models/MCQuestion");
const sQuestionSchema = require("../models/sQuestion");
const ssQuestionSchema = require("../models/ssQuestion");
const { text } = require("express");

class DatabaseService {
    constructor(name) {
        this.name = name;
        this.initialized = false;
        this.connection = mongoose.createConnection(process.env.MONGO_URI, {
            dbName: this.name,
        });
    }
    async init() {
        console.log(`Connected to database: ${this.name}`);

        this.syllabusModel = this.connection.model(
            "syllabus",
            syllabusSchema,
            "syllabus"
        );

        this.questionsModel = this.connection.model(
            "questions",
            QuestionSchema,
            "questions"
        );

        this.sQuestionsModel = this.connection.model(
            "sub_questions",
            sQuestionSchema,
            "sub_questions"
        );

        this.ssQuestionsModel = this.connection.model(
            "sub_sub_questions",
            ssQuestionSchema,
            "sub_sub_questions"
        );

        this.mcQuestionsModel = this.connection.model(
            "mc_questions",
            MCQuestionSchema,
            "mc_questions"
        );

        this.paperNames = await this.getPaperNamesFromCollections();
        this.initialized = true;
    }

    async getPaperNamesFromCollections() {
        const paperNames = new Set();

        const questionPapers = await this.connection
            .collection("questions")
            .distinct("paper_name");
        const mcQuestionPapers = await this.connection
            .collection("mc_questions")
            .distinct("paper_name");

        questionPapers.forEach((name) => paperNames.add(name));
        mcQuestionPapers.forEach((name) => paperNames.add(name));

        return Array.from(paperNames);
    }
    getConnection() {
        return this.connection;
    }
    getSyllabuses() {
        return this.syllabusModel.find({}).exec();
    }
    getPaperNames() {
        return this.paperNames;
    }
    async getSyllabusByNum(num) {
        return this.syllabusModel.findOne({ number: num }).exec();
    }
    async findInAllPapers(query) {
        const results = [];
        const models = [
            { model: this.questionsModel, type: "questions" },
            { model: this.sQuestionsModel, type: "squestions" },
            { model: this.ssQuestionsModel, type: "ssquestions" },
            { model: this.mcQuestionsModel, type: "mcquestions" },
        ];

        for (const { model, type } of models) {
            try {
                const doc = await model.findOne(query).exec();
                if (doc) {
                    results.push({
                        paper: doc.paper_name || "unknown",
                        type: type,
                        data: doc,
                    });
                }
            } catch (error) {
                console.error(`Error searching ${type}:`, error);
            }
        }
        return results;
    }

    async getQuestionById(id) {
        return await this.findInAllPapers({
            _id: new mongoose.Types.ObjectId(id),
        });
    }

    async getQuestionsQuery(
        query = { paperName: [], type: [], syllabusNum: [], text: "" },
        pagination = {
            page: 1,
            limit: 20,
            sortBy: "syllabus.number",
            sortOrder: 1,
        }
    ) {
        const results = [];

        // Map type names to model instances
        const typeModelMap = {
            questions: this.questionsModel,
            mcquestions: this.mcQuestionsModel,
            squestions: this.sQuestionsModel,
            ssquestions: this.ssQuestionsModel,
        };

        const typesToSearch =
            query.type.length > 0
                ? query.type.filter((type) =>
                      Object.keys(typeModelMap).includes(type)
                  )
                : Object.keys(typeModelMap);

        const skip = (pagination.page - 1) * pagination.limit;
        let collected = 0;
        let totalCount = 0;

        for (const modelKey of typesToSearch) {
            if (collected >= pagination.limit) break;

            const model = typeModelMap[modelKey];

            const searchQuery = {
                ...(query.paperName.length > 0 && {
                    paper_name: { $in: query.paperName },
                }),
                ...(query.syllabusNum.length > 0 && {
                    syllabus: {
                        $elemMatch: {
                            number: { $in: query.syllabusNum },
                        },
                    },
                }),
                ...(query.text && {
                    $text: { $search: query.text },
                }),
            };

            console.log("Searching", modelKey, searchQuery);

            try {
                const count = await model.countDocuments(searchQuery);
                console.log(`Found ${count} documents in ${modelKey}`);
                totalCount += count;

                let skipForThisCollection = Math.max(0, skip - collected);
                if (skipForThisCollection >= count) {
                    continue;
                }

                let queryBuilder = model.find(searchQuery);

                if (pagination.sortBy) {
                    queryBuilder = queryBuilder.sort({
                        [pagination.sortBy]: pagination.sortOrder,
                    });
                }

                if (skipForThisCollection > 0) {
                    queryBuilder = queryBuilder.skip(skipForThisCollection);
                }

                const limit = pagination.limit - collected;
                const docs = await queryBuilder.limit(limit).exec();

                results.push(...docs);
                collected += docs.length;
            } catch (error) {
                console.error(`Error querying ${modelKey}:`, error);
                continue;
            }
        }

        return {
            data: results,
            total: totalCount,
        };
    }
    async getQuestionsByPaper(paperName) {
        const questions = await this.questionsModel.find({
            paper_name: paperName,
        });
        const mcQuestions = await this.mcQuestionsModel.find({
            paper_name: paperName,
        });

        return {
            questions: questions.length > 0 ? questions : mcQuestions,
        };
    }
}

module.exports = DatabaseService;
