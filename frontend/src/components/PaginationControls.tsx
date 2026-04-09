type PaginationControlsProps = {
  page: number;
  pageSize: number;
  itemCount: number;
  onPrevious: () => void;
  onNext: () => void;
};

export function PaginationControls({ page, pageSize, itemCount, onPrevious, onNext }: PaginationControlsProps) {
  return (
    <div className="page-actions" style={{ marginTop: 16 }}>
      <button className="badge" type="button" disabled={page <= 1} onClick={onPrevious}>
        Previous
      </button>
      <span className="subtle">Page {page}</span>
      <button className="badge" type="button" disabled={itemCount < pageSize} onClick={onNext}>
        Next
      </button>
    </div>
  );
}
