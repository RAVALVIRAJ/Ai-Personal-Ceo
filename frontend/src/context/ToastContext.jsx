import {
  createContext,
  useCallback,
  useContext,
  useState,
} from "react";


const ToastContext = createContext(null);


export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);


  const removeToast = useCallback((id) => {
    setToasts((current) =>
      current.filter(
        (toast) => toast.id !== id
      )
    );
  }, []);


  const showToast = useCallback(
    (
      message,
      type = "success",
      duration = 3000
    ) => {
      const id =
        `${Date.now()}-${Math.random()}`;

      const toast = {
        id,
        message,
        type,
      };

      setToasts((current) => [
        ...current,
        toast,
      ]);

      setTimeout(() => {
        removeToast(id);
      }, duration);
    },
    [removeToast]
  );


  return (
    <ToastContext.Provider
      value={{
        showToast,
      }}
    >
      {children}

      <div className="toast-container">

        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={
              `toast toast-${toast.type}`
            }
          >
            <span className="toast-icon">
              {toast.type === "success"
                ? "✓"
                : toast.type === "error"
                ? "×"
                : "!"}
            </span>

            <span className="toast-message">
              {toast.message}
            </span>

            <button
              className="toast-close"
              onClick={() =>
                removeToast(toast.id)
              }
            >
              ×
            </button>
          </div>
        ))}

      </div>

    </ToastContext.Provider>
  );
}


export function useToast() {
  const context =
    useContext(ToastContext);

  if (!context) {
    throw new Error(
      "useToast must be used inside ToastProvider"
    );
  }

  return context;
}