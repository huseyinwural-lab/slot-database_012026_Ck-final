export const Modal = ({ open, title, children, onClose }) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/70" data-testid="modal-overlay">
      <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-[#0d111a] p-6" data-testid="modal-content">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold" data-testid="modal-title">{title}</h3>
          <button onClick={onClose} className="text-white/60" data-testid="modal-close">Kapat</button>
        </div>
        <div className="mt-4">{children}</div>
      </div>
    </div>
  );
};
