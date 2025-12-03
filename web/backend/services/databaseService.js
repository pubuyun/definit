const mongoose = require("mongoose");
const mongoose_fuzzy_searching = require("mongoose-fuzzy-searching");
const syllabusSchema = require("../models/Syllabus");
const QuestionSchema = require("../models/Question");
const sQuestionSchema = require("../models/sQuestion");
const ssQuestionSchema = require("../models/ssQuestion");

class DatabaseService {
    constructor(name) {
        this.name = name;
        this.connection = mongoose.createConnection(process.env.MONGO_URI, {
            dbName: this.name,
        });
        this.syllabusModel = this.connection.model(
            "syllabus",
            syllabusSchema,
            "syllabus"
        );
        this.modelsByPaper = {};
        this.paperNames = this.connection.db
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
        this.models = {
            questions: this.connection.model("question", questionSchema),
            sQuestions: this.connection.model("sQuestion", sQuestionSchema),
            ssQuestions: this.connection.model("ssQuestion", ssQuestionSchema),
        };
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
    async getQuestionById(id) {
        return this.models.reduce(async (prevPromise, model) => {
            const prevResult = await prevPromise;
            if (prevResult) return prevResult;
            return model.findById(id).exec();
        }, Promise.resolve(null));
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
