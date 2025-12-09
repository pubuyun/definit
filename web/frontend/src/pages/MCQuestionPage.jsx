import Typography from "@mui/joy/Typography";
import React, { use, useEffect, useState } from "react";
import { useParams } from "react-router";
import Accordion from "@mui/joy/Accordion";
import AccordionSummary from "@mui/joy/AccordionSummary";
import AccordionDetails from "@mui/joy/AccordionDetails";

const MCQuestionPage = () => {
    const { syllabusId, id } = useParams();
    const [MCQuestion, setMCQuestion] = useState();
    const [image, setImage] = useState(null);

    useEffect(() => {
        fetch(`/api/${syllabusId}/questions/id/${id}`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        })
            .then((res) => res.json())
            .then((data) => setMCQuestion(data.data[0].data || {}));
    }, [syllabusId, id]);

    useEffect(() => {
        if (MCQuestion) {
            console.log("MCQuestion:", MCQuestion);
        }
    }, [MCQuestion]);

    useEffect(() => {
        if (MCQuestion && MCQuestion.image) {
            const imageName = `i-${syllabusId}/${MCQuestion.image}`;
            console.log("Fetching image with name:", imageName);
            fetch(`/api/image?image=${imageName}`, {
                method: "GET",
            })
                .then((res) => res.json())
                .then((data) => {
                    setImage(data.imageUrl);
                });
        }
    }, [MCQuestion, syllabusId]);

    return (
        <>
            <Typography level="h4" gutterBottom>
                MCQ
            </Typography>
            <img src={image} alt="Multiple Choice Question" />
            <Accordion>
                <AccordionSummary>Answer</AccordionSummary>
                <AccordionDetails>
                    <img src={image} alt="Answer" />
                </AccordionDetails>
            </Accordion>
        </>
    );
};

export default MCQuestionPage;
