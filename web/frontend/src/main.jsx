import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router";
import "./index.css";
import App from "./App.jsx";
import QuestionMain from "./pages/QuestionMain.jsx";
import SyllabusMain from "./pages/SyllabusMain.jsx";

createRoot(document.getElementById("root")).render(
    <StrictMode>
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<App />} />
                <Route path="/:syllabusId">
                    <Route index element={<SyllabusMain />} />
                    <Route path="question/:id" element={<QuestionMain />} />
                </Route>
            </Routes>
        </BrowserRouter>
    </StrictMode>
);
