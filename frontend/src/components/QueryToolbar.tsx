import type { FormEvent, ReactNode } from "react";

type QueryToolbarProps = {
  children: ReactNode;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function QueryToolbar({ children, onSubmit }: QueryToolbarProps) {
  return (
    <form className="inline-form" onSubmit={onSubmit}>
      <div className="page-actions">{children}</div>
    </form>
  );
}
