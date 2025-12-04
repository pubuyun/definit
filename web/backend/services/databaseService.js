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
        this.modelsByPaper = {};
        this.paperNames = await this.connection.db
            .listCollections()
            .toArray()
            .then((collections) => {
                return collections
                    .map((col) => col.name)
                    .filter((name) => name !== "syllabus");
            });
        for (const paper of this.paperNames) {
            if (paper.endsWith("mcq")) {
                this.modelsByPaper[paper] = {
                    mcQuestions: this.connection.model(
                        paper + "mcq",
                        MCQuestionSchema,
                        paper
                    ),
                };
            } else {
                this.modelsByPaper[paper] = {
                    questions: this.connection.model(
                        paper + "q",
                        QuestionSchema,
                        paper
                    ),
                    sQuestions: this.connection.model(
                        paper + "sq",
                        sQuestionSchema,
                        paper
                    ),
                    ssQuestions: this.connection.model(
                        paper + "ssq",
                        ssQuestionSchema,
                        paper
                    ),
                };
            }
        }
        this.initialized = true;
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
        for (const paper of this.paperNames) {
            for (modelKey of Object.keys(this.modelsByPaper[paper])) {
                const model = this.modelsByPaper[paper][modelKey];
                const doc = await model.findOne(query).exec();
                if (doc) {
                    results.push({
                        paper,
                        type: modelKey,
                        data: doc,
                    });
                }
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
        const papersToSearch =
            query.paperName.length > 0
                ? query.paperName.filter((paper) =>
                      this.paperNames.includes(paper)
                  )
                : this.paperNames;
        const typesToSearch =
            query.type.length > 0
                ? query.type.filter((type) =>
                      [
                          "questions",
                          "mcQuestions",
                          "sQuestions",
                          "ssQuestions",
                      ].includes(type)
                  )
                : ["questions", "mcQuestions", "sQuestions", "ssQuestions"];
        const skip = (pagination.page - 1) * pagination.limit;
        let collected = 0;
        let needToSkip = skip;

        for (const paper of papersToSearch) {
            for (const modelKey of typesToSearch) {
                if (!(modelKey in this.modelsByPaper[paper])) continue;
                const model = this.modelsByPaper[paper][modelKey];
                const searchQuery = {
                    ...(query.syllabusNum.length > 0 && {
                        "syllabus.number": { $in: query.syllabusNum },
                    }),
                    ...(query.text && {
                        $text: { $search: query.text },
                    }),
                };
                console.log("Searching", paper, modelKey, searchQuery);

                try {
                    const count = await model.countDocuments(searchQuery);
                    console.log(
                        `Found ${count} documents in ${paper}.${modelKey}`
                    );
                    if (needToSkip >= count) {
                        needToSkip -= count;
                        continue;
                    }

                    let queryBuilder = model.find(searchQuery);

                    if (pagination.sortBy)
                        queryBuilder = queryBuilder.sort({
                            [pagination.sortBy]: pagination.sortOrder,
                        });

                    if (needToSkip > 0) {
                        queryBuilder = queryBuilder.skip(needToSkip);
                        needToSkip = 0;
                    }

                    const docs = await queryBuilder
                        .limit(pagination.limit - collected)
                        .exec();

                    results.push(...docs);
                    collected += docs.length;

                    if (collected >= pagination.limit) {
                        break;
                    }
                } catch (error) {
                    console.error(
                        `Error querying ${paper}.${modelKey}:`,
                        error
                    );
                    continue;
                }

                if (collected >= pagination.limit) break;
            }

            if (collected >= pagination.limit) break;
        }

        return {
            data: results.slice(0, pagination.limit),
            total: results.length,
        };
    }
}

module.exports = DatabaseService;
