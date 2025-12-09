import Typography from "@mui/joy/Typography";
import React, { use, useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import Accordion from "@mui/joy/Accordion";
import AccordionSummary from "@mui/joy/AccordionSummary";
import AccordionDetails from "@mui/joy/AccordionDetails";

const SubQuestionCard = (id) => {
    const { syllabusId, id: questionId } = useParams();
    const [SubQuestion, setSubQuestion] = useState();
    const [image, setImage] = useState(null);

    useEffect(() => {
        fetch(`/api/${syllabusId}/questions/id/${id}`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        })
            .then((res) => res.json())
            .then((data) => setSubQuestion(data.data[0].data || {}));
    }, [syllabusId, id]);

    useEffect(() => {
        if (SubQuestion && SubQuestion.image) {
            const imageName = `i-${syllabusId}/${SubQuestion.image}`;
            fetch(`/api/image?image=${imageName}`, {
                method: "GET",
            })
                .then((res) => res.json())
                .then((data) => {
                    setImage(data.imageUrl);
                });
        }
    }, [SubQuestion, syllabusId]);

    return (
        <Link to={`/${syllabusId}/question/${questionId}`}>
            <Card>
                <img src={image} alt="subquestion" />
            </Card>
        </Link>
    );
};

export default SubQuestionCard;
