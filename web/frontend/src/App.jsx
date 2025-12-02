import "./App.css";
import React from "react";
import { Routes, Route } from "react-router-dom";
import SyllabusBox from "components/SyllabusBox.jsx";
import Typography from "@mui/joy/Typography";
import SearchBar from "./components/SearchBar";

function App() {
    const [syllabuses, setSyllabuses] = React.useState();

    return (
        <>
            <Typography>CIE Question Database by Syllabus</Typography>
            <SearchBar
                onSearch={(query) => console.log("Searching for:", query)}
            />
        </>
    );
}

export default App;
