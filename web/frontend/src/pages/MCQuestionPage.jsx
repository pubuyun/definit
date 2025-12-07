import React from "react";
import { useParams } from "react-router";

const MCQuestionPage = () => {
    const { syllabusId, id } = useParams();

    return (
        <div>
            <h1>Multiple Choice Question Page</h1>
            <p>Syllabus ID: {syllabusId}</p>
            <p>Question ID: {id}</p>
        </div>
    );
};

export default MCQuestionPage;
