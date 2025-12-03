const mongoose = require("mongoose");
const mongoose_fuzzy_searching = require("mongoose-fuzzy-searching");
const syllabusSchema = require("../models/Syllabus");
const QuestionSchema = require("../models/Question");
const MCQuestionSchema = require("../models/MCQuestion");
const sQuestionSchema = require("../models/sQuestion");
const ssQuestionSchema = require("../models/ssQuestion");

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
            this.modelsByPaper[paper] = {
                questions: this.connection.model(
                    paper + "q",
                    QuestionSchema,
                    paper
                ),
                mcQuestions: this.connection.model(
                    paper + "mcq",
                    MCQuestionSchema,
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
            for (const modelKey of [
                "questions",
                "mcQuestions",
                "sQuestions",
                "ssQuestions",
            ]) {
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

    async getQuestionsBySyllabus(syllabusNum) {
        const [questions, sQuestions, ssQuestions] = Promise.all([
            this.models.questions
                .find({ "syllabus.number": syllabusNum })
                .exec(),
            this.models.sQuestions
                .find({ "syllabus.number": syllabusNum })
                .exec(),
            this.models.ssQuestions
                .find({ "syllabus.number": syllabusNum })
                .exec(),
        ]);
        return { questions, sQuestions, ssQuestions };
    }

    async findByPaper(paperName) {
        const [questions, sQuestions, ssQuestions] = Promise.all([
            this.modelsByPaper[paperName][0]
                .find({})
                .sort({ number: 1 })
                .exec(),
            this.modelsByPaper[paperName][1]
                .find({})
                .sort({ number: 1 })
                .exec(),
            this.modelsByPaper[paperName][2]
                .find({})
                .sort({ number: 1 })
                .exec(),
        ]);
        return { questions, sQuestions, ssQuestions };
    }
}

module.exports = DatabaseService;
