const mongoose = require("mongoose");
const syllabusSchema = require("../models/Syllabus");

class DatabaseService {
    constructor(name) {
        this.name = name;
        this.connection = mongoose.createConnection(process.env.MONGO_URI, {
            dbName: this.name,
        });
    }
    getConnection() {
        return this.connection;
    }
    getSyllabusModel() {
        return this.connection.model("Syllabus", syllabusSchema);
    }
    getPaperNames() {
        return this.connection.db
            .listCollections()
            .toArray()
            .then((collections) => {
                return collections
                    .map((col) => col.name)
                    .filter((name) => name !== "syllabus");
            });
    }
}
