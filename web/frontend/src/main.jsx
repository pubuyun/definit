import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";
import "./index.css";
import App from "./App.jsx";
import QuestionPage from "pages/QuestionPage.jsx";
import SyllabusSearchPage from "pages/SyllabusSearchPage.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path=":syllabusId">
          <Route index element={<SyllabusMain />} />
          <Route path="questions">
            <Route index element={<SyllabusSearchPage />} />
            <Route path=":id" element={<QuestionPage />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>
);
