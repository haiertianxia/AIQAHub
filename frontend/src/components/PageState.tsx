import type { ReactNode } from "react";

type PageStateProps = {
  kind: "loading" | "empty" | "error";
  message: string;
  action?: ReactNode;
};

export function PageState({ kind, message, action }: PageStateProps) {
  const prefix = kind === "loading" ? "Loading" : kind === "error" ? "Error" : "Empty";
  return (
    <div className={`panel soft state-${kind}`} style={{ marginTop: 16 }}>
      <div className="subtle" style={{ fontWeight: 600 }}>
        {prefix}
      </div>
      <div style={{ marginTop: 8 }}>{message}</div>
      {action ? <div style={{ marginTop: 12 }}>{action}</div> : null}
    </div>
  );
}
