import React from "react";
import { Link } from "react-router";
import Box from "@mui/joy/Box";
import Typography from "@mui/joy/Typography";

const containerSx = {
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
    padding: "12px 14px",
    border: "1px solid rgba(0,0,0,0.08)",
    borderRadius: 8,
    background: "#fff",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
    minWidth: 180,
    cursor: "pointer",
    transition: "all 0.2s ease-in-out",
    "&:hover": {
        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
        transform: "translateY(-1px)",
    },
};

const descSx = {
    fontSize: 13,
    color: "#6b7280",
    lineHeight: 1.2,
};

export default function QuestionCard({ question }) {
    return (
        <Link to={`question/${question._id}`}>
            <Box sx={containerSx} role="group" aria-label={`${question.code}`}>
                <Typography level="body3" sx={descSx}>
                    {question.text}
                </Typography>
                <Typography
                    level="body4"
                    sx={{ marginTop: 1, color: "#9ca3af" }}
                >
                    {question.syllabus
                        .map((syllabus) => syllabus.number)
                        .join(", ")}
                </Typography>
            </Box>
        </Link>
    );
}
