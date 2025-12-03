const mongoose = require("mongoose");
require("dotenv").config();

async function checkCollections() {
    try {
        await mongoose.connect(process.env.MONGO_URI, {
            dbName: "igcse-biology-0610",
        });
        const collections = await mongoose.connection.db
            .listCollections()
            .toArray();
        console.log(
            "Collections:",
            collections.map((c) => c.name)
        );

        const id = "69294db88d940b878ee80431";
        console.log("Searching for ID:", id);

        for (const col of collections) {
            if (col.name !== "syllabus") {
                try {
                    const count = await mongoose.connection.db
                        .collection(col.name)
                        .countDocuments({
                            _id: new mongoose.Types.ObjectId(id),
                        });
                    if (count > 0) {
                        console.log("Found ID", id, "in collection:", col.name);
                    }
                } catch (err) {
                    console.log(
                        "Error checking collection",
                        col.name,
                        ":",
                        err.message
                    );
                }
            }
        }

        process.exit(0);
    } catch (error) {
        console.error("Error:", error);
        process.exit(1);
    }
}

checkCollections();
