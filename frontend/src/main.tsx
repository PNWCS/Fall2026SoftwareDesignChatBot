import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

function App() {
  return <main>PNW Student Information Chatbot</main>;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
