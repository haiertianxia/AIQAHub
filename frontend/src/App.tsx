import { Navigate, NavLink, Route, Routes } from "react-router-dom";

import { useAuth } from "./auth";
import { Shell } from "./components/Shell";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { DashboardPage } from "./pages/DashboardPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { ProjectDetailPage } from "./pages/ProjectDetailPage";
import { SuitesPage } from "./pages/SuitesPage";
import { ExecutionsPage } from "./pages/ExecutionsPage";
import { ReportsPage } from "./pages/ReportsPage";
import { ExecutionDetailPage } from "./pages/ExecutionDetailPage";
import { GatesPage } from "./pages/GatesPage";
import { AiPage } from "./pages/AiPage";
import { AiHistoryPage } from "./pages/AiHistoryPage";
import { AssetsPage } from "./pages/AssetsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { AuditPage } from "./pages/AuditPage";
import { LoginPage } from "./pages/LoginPage";

const navItems = [
  { to: "/dashboard", label: "总览" },
  { to: "/projects", label: "项目" },
  { to: "/suites", label: "套件" },
  { to: "/executions", label: "执行" },
  { to: "/reports", label: "报告" },
  { to: "/gates", label: "门禁" },
  { to: "/ai", label: "AI" },
  { to: "/ai/history", label: "AI 历史" },
  { to: "/assets", label: "资产" },
  { to: "/settings", label: "配置" },
  { to: "/audit", label: "审计" },
];

export default function App() {
  const auth = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="*"
        element={
          <ProtectedRoute>
            <Shell
              title="AIQAHub"
              subtitle={auth.user ? auth.user.name : "AI quality assurance control plane"}
              nav={
                <nav className="nav">
                  {navItems.map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
                    >
                      {item.label}
                    </NavLink>
                  ))}
                  <button className="nav-link nav-button" onClick={auth.logout} type="button">
                    退出登录
                  </button>
                </nav>
              }
            >
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/projects" element={<ProjectsPage />} />
                <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
                <Route path="/suites" element={<SuitesPage />} />
                <Route path="/executions" element={<ExecutionsPage />} />
                <Route path="/executions/:executionId" element={<ExecutionDetailPage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/gates" element={<GatesPage />} />
                <Route path="/ai" element={<AiPage />} />
                <Route path="/ai/history" element={<AiHistoryPage />} />
                <Route path="/assets" element={<AssetsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/audit" element={<AuditPage />} />
              </Routes>
            </Shell>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
