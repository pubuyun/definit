import Typography from "@mui/joy/Typography";
import React, { use, useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import Card from "@mui/joy/Card";
import Box from "@mui/joy/Box";

const SubQuestionCard = ({ id }) => {
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

    // useEffect(() => {
    //     if (SubQuestion && SubQuestion.image) {
    //         const imageName = `i-${syllabusId}/${SubQuestion.image}`;
    //         fetch(`/api/image?image=${imageName}`, {
    //             method: "GET",
    //         })
    //             .then((res) => res.json())
    //             .then((data) => {
    //                 setImage(data.imageUrl);
    //             });
    //     }
    // }, [SubQuestion, syllabusId]);

    return (
        <Link to={`/${syllabusId}/question/${id}`}>
            <Card>
                {/* <img src={image} alt="subquestion" /> */}
                {SubQuestion && (
                    <Box>
                        <Typography level="body3" sx={{ fontSize: 14 }}>
                            {SubQuestion.text}
                        </Typography>
                        <Typography
                            level="body2"
                            sx={{ fontSize: 12, color: "blue" }}
                        >
                            {SubQuestion.syllabus
                                .map((syllabus) => syllabus.number)
                                .join(", ")}
                        </Typography>
                    </Box>
                )}
            </Card>
        </Link>
    );
};

export default SubQuestionCard;
