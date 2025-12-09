import React, { useCallback } from "react";
import { useParams } from "react-router";
import ConditionsBar from "../components/Search/ConditionsBar";
import QuestionBox from "../components/Search/QuestionBox";
import Box from "@mui/joy/Box";

const SyllabusMain = () => {
    const { syllabusId } = useParams();
    // const syllabusId = "0610"; // For testing purposes
    const [conditions, setConditions] = React.useState({});
    const [results, setResults] = React.useState([]);

    const onConditionsChange = useCallback((newConditions) => {
        // if (newConditions == conditions) return;
        console.log("Search conditions changed:", newConditions);
        setConditions(newConditions);
    }, []);
    React.useEffect(() => {
        console.log(
            "Fetching questions with conditions:",
            `/api/${syllabusId}/questions/query?` +
                new URLSearchParams(conditions)
        );
        fetch(
            `/api/${syllabusId}/questions/query?` +
                new URLSearchParams(conditions),
            {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                },
            }
        )
            .then((res) => res.json())
            .then((data) => setResults(data.data || []))
            .then(() => {
                console.log("Fetched results:", results);
            });
    }, [conditions, syllabusId]);

    return (
        <Box
            sx={{
                padding: 2,
                display: "flex",
                flexDirection: "column",
                gap: 2,
            }}
        >
            <ConditionsBar
                subjectCode={syllabusId}
                onChange={onConditionsChange}
            />
            <Box sx={{ flexGrow: 1 }}>
                {results.map((result) => (
                    <QuestionBox
                        key={result.id}
                        question={result}
                    ></QuestionBox>
                ))}
            </Box>
        </Box>
    );
};

export default SyllabusMain;
