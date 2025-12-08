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

const codeSx = {
    fontSize: 14,
    fontWeight: 700,
    color: "#111827",
    marginBottom: "6px",
};

const descSx = {
    fontSize: 13,
    color: "#6b7280",
    lineHeight: 1.2,
};

export default function SyllabusBox({ code, subjectDesc }) {
    return (
        <Link
            to={`/${code}`}
            style={{ textDecoration: "none", color: "inherit" }}
        >
            <Box
                sx={containerSx}
                role="group"
                aria-label={`${code} ${subjectDesc}`}
            >
                <Typography level="body2" sx={codeSx}>
                    {code}
                </Typography>
                <Typography level="body3" sx={descSx}>
                    {subjectDesc}
                </Typography>
            </Box>
        </Link>
    );
}
