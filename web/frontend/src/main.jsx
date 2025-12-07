import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router";
import "./index.css";
import App from "./App.jsx";
import QuestionPage from "./pages/QuestionPage.jsx";
import SQuestionPage from "./pages/sQuestionPage.jsx";
import SSQuestionPage from "./pages/ssQuestionPage.jsx";
import MCQuestionPage from "./pages/MCQuestionPage.jsx";
import SyllabusMain from "./pages/SyllabusMain.jsx";

createRoot(document.getElementById("root")).render(
    <StrictMode>
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<App />} />
                <Route path="/:syllabusId" element={<SyllabusMain />}>
                    <Route path="question/:id" element={<QuestionPage />} />
                    <Route path="squestion/:id" element={<SQuestionPage />} />
                    <Route path="ssquestion/:id" element={<SSQuestionPage />} />
                    <Route path="mcquestion/:id" element={<MCQuestionPage />} />
                </Route>
            </Routes>
        </BrowserRouter>
    </StrictMode>
);
