import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./layouts/Layout";
import LoginPage from "./pages/LoginPage";
import PingPage from "./pages/PingPage";
import ChatPage from "./pages/ChatPage";
import FoldersPage from "./pages/FoldersPage";
import AssistModesPage from "./pages/AssistModesPage";
import AdminPage from "./pages/AdminPage";
import AIResponsesPage from "./pages/AIResponsesPage";

function App() {
  return (
    <BrowserRouter future={{ v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/chat" replace />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="chat/:conversationId" element={<ChatPage />} />
          <Route path="ai-responses" element={<AIResponsesPage />} />
          <Route path="folders" element={<FoldersPage />} />
          <Route path="assist" element={<AssistModesPage />} />
          <Route path="admin" element={<AdminPage />} />
          <Route path="ping" element={<PingPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
