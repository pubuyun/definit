import Typography from "@mui/joy/Typography";
import React, { useEffect, useState } from "react";
import { useParams } from "react-router";
import Accordion from "@mui/joy/Accordion";
import AccordionSummary from "@mui/joy/AccordionSummary";
import AccordionDetails from "@mui/joy/AccordionDetails";

const QuestionPage = (question) => {
    const { syllabusId } = useParams();
    const [image, setImage] = useState(null);
    const [answerImage, setAnswerImage] = useState(null);

    useEffect(() => {
        if (question && question.image) {
            const imageName = `i-${syllabusId}/${question.image}`;
            fetch(`/api/image?image=${imageName}`, {
                method: "GET",
            })
                .then((res) => res.json())
                .then((data) => {
                    setImage(data.imageUrl);
                });
        }
        if (question && question.ms_image) {
            const answerImageName = `i-${syllabusId}/${question.ms_image}`;
            fetch(`/api/image?image=${answerImageName}`, {
                method: "GET",
            })
                .then((res) => res.json())
                .then((data) => {
                    setAnswerImage(data.imageUrl);
                });
        }
    }, [question, syllabusId]);

    return (
        <>
            <Typography level="h4" gutterBottom>
                Question
            </Typography>
            <img src={image} alt="Multiple Choice question" />
            <Accordion>
                <AccordionSummary>Answer</AccordionSummary>
                <AccordionDetails>
                    <img
                        src={answerImage}
                        alt={question ? question.answer : "Answer"}
                    />
                </AccordionDetails>
            </Accordion>
        </>
    );
};

export default QuestionPage;
