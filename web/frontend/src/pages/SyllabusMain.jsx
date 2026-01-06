import React, { useCallback } from "react";
import { useParams } from "react-router";
import ConditionsBar from "../components/Search/ConditionsBar";
import QuestionCard from "../components/Question/QuestionCard";
import Box from "@mui/joy/Box";
import Button from "@mui/joy/Button";
import Typography from "@mui/joy/Typography";
import AddIcon from "@mui/icons-material/Add";
import RemoveIcon from "@mui/icons-material/Remove";
import Input from "@mui/joy/Input";

/*          
pagination query:
            page = 1,
            limit = 10,
            sortBy = "syllabus.number",
            sortOrder = "desc",
*/
const SyllabusMain = () => {
    const { syllabusId } = useParams();
    // const syllabusId = "0610"; // For testing purposes
    const [conditions, setConditions] = React.useState({});
    const [results, setResults] = React.useState([]);
    const [page, setPage] = React.useState(1);
    const [inputPage, setInputPage] = React.useState(1);

    const onConditionsChange = useCallback((newConditions) => {
        // if (newConditions == conditions) return;
        console.log("Search conditions changed:", newConditions);
        setConditions(newConditions);
    }, []);
    React.useEffect(() => {
        console.log(
            "Fetching questions with conditions:",
            `/api/${syllabusId}/questions/query?` +
                new URLSearchParams(conditions) +
                `&page=${page}`
        );
        fetch(
            `/api/${syllabusId}/questions/query?` +
                new URLSearchParams(conditions) +
                `&page=${page}`,
            {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                },
            }
        )
            .then((res) => res.json())
            .then((data) => setResults(data || []))
            .then(() => {
                console.log("Fetched results:", results);
            });
    }, [conditions, syllabusId, page]);

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
                {results.data?.map((result) => (
                    <QuestionCard
                        key={result.id}
                        question={result}
                    ></QuestionCard>
                ))}
            </Box>
            <Box
                sx={{
                    display: "flex",
                    justifyContent: "center",
                    gap: 2,
                    marginTop: 2,
                }}
            >
                <Button
                    onClick={() => {
                        setPage(page - 1);
                        setInputPage(page - 1);
                    }}
                    startDecorator={<RemoveIcon />}
                />
                <Typography
                    level="body2"
                    sx={{ alignSelf: "center", flexDirection: "row" }}
                >
                    Page
                    {
                        <Input
                            value={inputPage}
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    const newPage = parseInt(e.target.value);
                                    if (
                                        !isNaN(newPage) &&
                                        newPage >= 1 &&
                                        newPage <= Math.ceil(results.total / 10)
                                    ) {
                                        setPage(newPage);
                                    }
                                }
                            }}
                            onClick={(e) => e.target.select()}
                            onChange={(e) =>
                                setInputPage(Number(e.target.value))
                            }
                            sx={{
                                width: "4em",
                                fontSize: 14,
                                textAlign: "center",
                            }}
                        />
                    }
                    /{Math.ceil(results.total / 10)}
                </Typography>
                <Button
                    onClick={() => {
                        setPage(page + 1);
                        setInputPage(page + 1);
                    }}
                    startDecorator={<AddIcon />}
                />
            </Box>
        </Box>
    );
};

export default SyllabusMain;
