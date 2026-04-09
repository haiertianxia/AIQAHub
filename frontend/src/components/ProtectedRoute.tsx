import { Navigate } from "react-router-dom";

import { useAuth } from "../auth";
import { PageState } from "./PageState";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const auth = useAuth();

  if (auth.loading) {
    return (
      <div className="loading-screen">
        <div style={{ width: "min(720px, 100%)" }}>
          <PageState kind="loading" message="Loading control plane..." />
        </div>
      </div>
    );
  }

  if (!auth.user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
