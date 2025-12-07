import React from "react";
import { useParams } from "react-router";

const SQuestionPage = () => {
    const { syllabusId, id } = useParams();

    return (
        <div>
            <h1>Structured Question Page</h1>
            <p>Syllabus ID: {syllabusId}</p>
            <p>Question ID: {id}</p>
        </div>
    );
};

export default SQuestionPage;
