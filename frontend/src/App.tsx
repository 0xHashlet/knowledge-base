import { Navigate, Route, Routes } from "react-router-dom";

import { LoginPage } from "./pages/LoginPage";
import { KnowledgeBasePage } from "./pages/KnowledgeBasePage";
import { useAuth } from "./state/auth";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const auth = useAuth();
  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/app/*"
        element={
          <ProtectedRoute>
            <KnowledgeBasePage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  );
}
