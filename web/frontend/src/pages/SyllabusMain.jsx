import React from "react";
import { useParams } from "react-router-dom";
import ConditionsBar from "../components/Search/ConditionsBar";

const SyllabusMain = () => {
    const { syllabusId } = useParams();

    const onChange = (conditions) => {
        console.log("Search conditions changed:", conditions);
    };

    return <ConditionsBar subjectCode={syllabusId} onChange={onChange} />;
};

export default SyllabusMain;
