import React from "react";
import { useParams } from "react-router";

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
                <div key={subId}>
                    <h3>Subquestion ID: {subId}</h3>
                    {/* Here you can render the subquestion component, e.g., <QuestionPage id={subId} /> */}
                </div>
            ))}
        </div>
    );
};

export default QuestionWithSub;
