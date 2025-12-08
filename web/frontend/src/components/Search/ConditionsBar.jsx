import React, { useEffect, useMemo } from "react";
import Input from "@mui/joy/Input";
import IconButton from "@mui/joy/IconButton";
import Box from "@mui/joy/Box";
import SearchIcon from "@mui/icons-material/Search";
import Select from "@mui/joy/Select";
import Option from "@mui/joy/Option";
import Chip from "@mui/joy/Chip";

const ConditionsLineStyle = {
    display: "flex",
    alignItems: "center",
    gap: "8px",
};

const getPaperYears = (paperList) => {
    if (!paperList.length) return null;
    let earliest = Infinity;
    let latest = -Infinity;
    paperList.forEach((paper) => {
        // 0610_s23_qp_42
        const match = paper.match(/\d{4}_\w(\d\d)_\w+_\d+/);
        if (match) {
            const year = parseInt(match[1]);
            if (year < earliest) earliest = year;
            if (year > latest) latest = year;
        }
    });
    return [
        ...Array.from(
            { length: latest - earliest + 1 },
            (_, i) => earliest + i
        ),
    ];
};

const filterPapersByYear = (paperList, startYear, endYear) => {
    return paperList.filter((paper) => {
        const match = paper.match(/\d{4}_\w(\d\d)_\w+_\d+/);
        if (match) {
            const year = parseInt(match[1]);
            return year >= startYear && year <= endYear;
        }
        return false;
    });
};

const ConditionsBar = ({ subjectCode, onChange }) => {
    subjectCode = "0610";
    const [paperList, setPaperList] = React.useState([]);
    const [syllabusList, setSyllabusList] = React.useState([]);
    const [textQuery, setTextQuery] = React.useState("");
    const [selectedQuestionTypes, setSelectedQuestionTypes] = React.useState([
        "questions",
        "mcquestions",
        "squestions",
        "ssquestions",
    ]);
    const [selectedStartYear, setSelectedStartYear] = React.useState(-Infinity);
    const [selectedEndYear, setSelectedEndYear] = React.useState(Infinity);
    const [selectedSyllabuses, setSelectedSyllabuses] = React.useState([]);
    useEffect(() => {
        fetch(`/api/${subjectCode}/papers`)
            .then((res) => res.json())
            .then((data) => {
                setPaperList(data);
            });
        fetch(`/api/${subjectCode}/syllabus`)
            .then((res) => res.json())
            .then((data) => {
                setSyllabusList(data.data || data);
            });
    }, [subjectCode]);

    const availableYears = useMemo(() => {
        console.log("paperList", getPaperYears(paperList));
        return getPaperYears(paperList);
    }, [paperList]);

    const filteredPapers = useMemo(() => {
        if (selectedStartYear != -Infinity || selectedEndYear != Infinity) {
            return filterPapersByYear(
                paperList,
                selectedStartYear,
                selectedEndYear
            );
        }
        return [];
    }, [paperList, selectedStartYear, selectedEndYear]);

    useEffect(() => {
        if (onChange) {
            //  query = { paperName: [], type: [], syllabusNum: [], text: "" },
            onChange({
                paperName: filteredPapers,
                type: selectedQuestionTypes,
                syllabusNum: selectedSyllabuses,
                text: textQuery,
            });
        }
    }, [
        textQuery,
        selectedQuestionTypes,
        filteredPapers,
        selectedSyllabuses,
        onChange,
    ]);

    return (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Box sx={ConditionsLineStyle}>
                <Input
                    placeholder="Search questions..."
                    value={textQuery}
                    onChange={(e, newValue) => setTextQuery(newValue)}
                    endDecorator={
                        <IconButton>
                            <SearchIcon />
                        </IconButton>
                    }
                    sx={{ flexGrow: 1 }}
                />
            </Box>
            <Box sx={ConditionsLineStyle}>
                <Select
                    placeholder="From"
                    onChange={(e, newValue) => setSelectedStartYear(newValue)}
                >
                    {availableYears?.map((year) => (
                        <Option key={year} value={year}>
                            {year}
                        </Option>
                    ))}
                </Select>
                <Select
                    placeholder="To"
                    onChange={(e, newValue) => setSelectedEndYear(newValue)}
                >
                    {availableYears?.map((year) => (
                        <Option key={year} value={year}>
                            {year}
                        </Option>
                    ))}
                </Select>
            </Box>
            <Box sx={ConditionsLineStyle}>
                <Select
                    multiple
                    defaultValue={[]}
                    onChange={(e, newValue) => setSelectedSyllabuses(newValue)}
                >
                    {syllabusList.map((syllabus) => (
                        <Option key={syllabus.number} value={syllabus.number}>
                            {syllabus.title}
                        </Option>
                    ))}
                </Select>
            </Box>
            <Box sx={ConditionsLineStyle}>
                <Select
                    multiple
                    defaultValue={[
                        "questions",
                        "mcquestions",
                        "squestions",
                        "ssquestions",
                    ]}
                    renderValue={(selected) => (
                        <Box sx={{ display: "flex", gap: "0.25rem" }}>
                            {selected.map((selectedOption) => (
                                <Chip
                                    key={selectedOption.value}
                                    variant="soft"
                                    color="primary"
                                >
                                    {selectedOption.label}
                                </Chip>
                            ))}
                        </Box>
                    )}
                    sx={{ minWidth: "15rem" }}
                    slotProps={{
                        listbox: {
                            sx: {
                                width: "100%",
                            },
                        },
                    }}
                    onChange={(e, newValue) =>
                        setSelectedQuestionTypes(newValue)
                    }
                >
                    <Option value="questions" key="questions">
                        Question (1)
                    </Option>
                    <Option value="mcquestions" key="mcquestions">
                        Multiple Choice Question
                    </Option>
                    <Option value="squestions" key="squestions">
                        Sub Question (a)
                    </Option>
                    <Option value="ssquestions" key="ssquestions">
                        SubSub Question (i)
                    </Option>
                </Select>
            </Box>
        </Box>
    );
};

export default ConditionsBar;
