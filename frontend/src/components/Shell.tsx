import type { ReactNode } from "react";

type ShellProps = {
  title: string;
  subtitle: string;
  nav: ReactNode;
  children: ReactNode;
};

export function Shell({ title, subtitle, nav, children }: ShellProps) {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" />
          <div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
        </div>
        {nav}
      </aside>
      <main className="main">
        <div className="topbar">
          <div className="badge ok">Platform online</div>
          <div className="subtle">API / Execution / AI / Gate unified control plane</div>
        </div>
        {children}
      </main>
    </div>
  );
}

