import type { ReactNode } from "react";

type SectionProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
};

export function Section({ title, description, action, children }: SectionProps) {
  return (
    <section className="panel" style={{ marginBottom: 16 }}>
      <div className="topbar" style={{ marginBottom: 0 }}>
        <div>
          <h3>{title}</h3>
          {description ? <p className="subtle" style={{ marginTop: 6 }}>{description}</p> : null}
        </div>
        {action ? <div>{action}</div> : null}
      </div>
      <div style={{ marginTop: 16 }}>{children}</div>
    </section>
  );
}
