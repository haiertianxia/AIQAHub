import { Navigate } from "react-router-dom";

import { useAuth } from "../auth";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const auth = useAuth();

  if (auth.loading) {
    return (
      <div className="loading-screen">
        <div className="panel">Loading control plane...</div>
      </div>
    );
  }

  if (!auth.user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

