import "./App.css";
import React from "react";
import SyllabusBox from "./components/SyllabusBox.jsx";
import Typography from "@mui/joy/Typography";
import SearchBar from "./components/Search/SearchBar";
import Box from "@mui/joy/Box";

function App() {
    const [syllabuses, setSyllabuses] = React.useState([]);
    const [searchText, setSearchText] = React.useState("");

    React.useEffect(() => {
        fetch("/api/syllabuses")
            .then((res) => res.json())
            .then((data) => {
                setSyllabuses(data);
                console.log("Fetched syllabuses:", data);
            });
    }, []);

    const SyllabusBoxes = syllabuses.map(
        (syllabus) =>
            (syllabus.subjectCode
                .toLowerCase()
                .includes(searchText.toLowerCase()) ||
                syllabus.databaseName
                    .toLowerCase()
                    .includes(searchText.toLowerCase())) && (
                <SyllabusBox
                    key={syllabus.subjectCode}
                    code={syllabus.subjectCode}
                    subjectDesc={syllabus.databaseName}
                />
            )
    );

    return (
        <>
            <Typography>CIE Question Database</Typography>
            <SearchBar
                onSearch={(query) => {
                    setSearchText(query);
                }}
            />
            <Box
                sx={{
                    display: "grid",
                    gridTemplateColumns:
                        "repeat(auto-fill, minmax(180px, 1fr))",
                    gap: 2,
                }}
            >
                {SyllabusBoxes}
            </Box>
        </>
    );
}

export default App;
