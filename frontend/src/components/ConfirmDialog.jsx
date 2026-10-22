function ConfirmDialog({
  open,
  title = "Are you sure?",
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  danger = false,
  loading = false,
  onConfirm,
  onCancel,
}) {
  if (!open) {
    return null;
  }

  return (
    <div className="modal-overlay">

      <div className="confirm-dialog">

        <div className="confirm-icon">
          !
        </div>

        <h3>
          {title}
        </h3>

        <p>
          {message}
        </p>

        <div className="confirm-actions">

          <button
            type="button"
            className="cancel-button"
            onClick={onCancel}
            disabled={loading}
          >
            {cancelText}
          </button>

          <button
            type="button"
            className={
              danger
                ? "confirm-danger-button"
                : "save-button"
            }
            onClick={onConfirm}
            disabled={loading}
          >
            {loading
              ? "Please wait..."
              : confirmText}
          </button>

        </div>

      </div>

    </div>
  );
}

export default ConfirmDialog;