import type { ReactNode } from "react";

type HighlightProps = {
  text: string;
  query: string;
};

export function Highlight({ text, query }: HighlightProps) {
  if (!query) {
    return <>{text}</>;
  }

  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase();
  const parts: ReactNode[] = [];
  let start = 0;

  while (true) {
    const index = lowerText.indexOf(lowerQuery, start);
    if (index === -1) {
      parts.push(text.slice(start));
      break;
    }
    if (index > start) {
      parts.push(text.slice(start, index));
    }
    parts.push(
      <mark key={`${index}-${start}`} style={{ background: "rgba(91, 231, 196, 0.2)", color: "inherit" }}>
        {text.slice(index, index + query.length)}
      </mark>,
    );
    start = index + query.length;
  }

  return <>{parts}</>;
}
