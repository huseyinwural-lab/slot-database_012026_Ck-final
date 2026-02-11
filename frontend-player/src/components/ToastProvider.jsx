import { createContext, useContext, useMemo, useState } from 'react';

const ToastContext = createContext(null);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const api = useMemo(() => ({
    push: (message, type = 'info') => {
      const id = `${Date.now()}-${Math.random()}`;
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
      }, 4000);
    },
  }), []);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="fixed right-6 top-6 z-50 space-y-2" data-testid="toast-stack">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="rounded-lg border border-white/10 bg-black/80 px-4 py-2 text-sm"
            data-testid={`toast-${toast.type}`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('ToastProvider is missing');
  }
  return ctx;
};
