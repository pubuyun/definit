import React from "react";
import { useParams } from "react-router";
import SubQuestionCard from "../components/Question/SubQuestionCard";

const QuestionWithSub = (question) => {
    const { syllabusId } = useParams();
    const childrenIds = question.subquestions || question.subsubquestions;
    console.log("Rendering QuestionWithSub for question:", question);
    console.log("Subquestion IDs:", childrenIds);
    console.log("question.subquestions:", question.subquestions);
    console.log("question.subsubquestions:", question.subsubquestions);

    return (
        <div>
            {childrenIds?.map((subId) => (
                <SubQuestionCard key={subId} id={subId}></SubQuestionCard>
            ))}
        </div>
    );
};

export default QuestionWithSub;
