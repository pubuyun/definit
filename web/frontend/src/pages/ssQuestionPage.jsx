import React from "react";
import { useParams } from "react-router";

const SSQuestionPage = () => {
    const { syllabusId, id } = useParams();

    return (
        <div>
            <h1>SS Question Page</h1>
            <p>Syllabus ID: {syllabusId}</p>
            <p>Question ID: {id}</p>
        </div>
    );
};

export default SSQuestionPage;
