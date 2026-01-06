import Typography from "@mui/joy/Typography";
import React, { useEffect, useState } from "react";
import { useParams } from "react-router";
import QuestionPage from "./QuestionPage.jsx";
import QuestionWithSub from "./QuestionWithSub.jsx";

const QuestionMain = () => {
    const { syllabusId, id } = useParams();
    const [Question, setQuestion] = useState();

    useEffect(() => {
        fetch(`/api/${syllabusId}/questions/id/${id}`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        })
            .then((res) => res.json())
            .then((data) => setQuestion(data.data[0].data || {}));
    }, [syllabusId, id]);

    useEffect(() => {
        if (Question) {
            console.log("Question:", Question);
        }
    }, [Question]);
    let hasChildren = false;
    if (Question) {
        hasChildren = Question.subquestions || Question.subsubquestions;
        hasChildren = hasChildren && hasChildren.length > 0;
    }

    return hasChildren ? (
        <QuestionWithSub {...Question} />
    ) : (
        <QuestionPage {...Question} />
    );
};

export default QuestionMain;
