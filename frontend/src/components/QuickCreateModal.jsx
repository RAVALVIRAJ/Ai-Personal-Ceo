import { useEffect, useState } from "react";


function QuickCreateModal({
  open,
  type,
  loading,
  onClose,
  onSubmit,
}) {
  const [title, setTitle] =
    useState("");

  const [when, setWhen] =
    useState("");

  const [duration, setDuration] =
    useState("");


  useEffect(() => {
    if (open) {
      setTitle("");
      setWhen("");
      setDuration("");
    }
  }, [open]);


  if (!open) {
    return null;
  }


  const isTask =
    type === "task";


  const handleSubmit = (event) => {
    event.preventDefault();

    const cleanTitle =
      title.trim();

    const cleanWhen =
      when.trim();

    if (!cleanTitle) {
      return;
    }


    let prompt = "";

    if (isTask) {
      prompt =
        `Create a task to ${cleanTitle}`;
    } else {
      prompt =
        `Create an event for ${cleanTitle}`;
    }


    if (cleanWhen) {
      prompt += ` ${cleanWhen}`;
    }


    if (duration) {
      prompt +=
        ` for ${duration} minutes`;
    }


    onSubmit(prompt);
  };


  return (
    <div className="modal-overlay">

      <div className="quick-create-modal">

        <div className="modal-header">

          <div>
            <p className="page-eyebrow">
              AI Quick Action
            </p>

            <h3>
              {isTask
                ? "Create Task"
                : "Create Event"}
            </h3>
          </div>


          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            disabled={loading}
          >
            ×
          </button>

        </div>


        <form
          className="quick-create-form"
          onSubmit={handleSubmit}
        >

          <label>
            {isTask
              ? "What do you need to do?"
              : "Event name"}

            <input
              type="text"
              placeholder={
                isTask
                  ? "Prepare project report"
                  : "Project review meeting"
              }
              value={title}
              onChange={(event) =>
                setTitle(
                  event.target.value
                )
              }
              autoFocus
              required
            />
          </label>


          <label>
            When?

            <input
              type="text"
              placeholder="Tomorrow at 5 PM"
              value={when}
              onChange={(event) =>
                setWhen(
                  event.target.value
                )
              }
            />

            <span className="quick-field-help">
              Examples: tomorrow at 5 PM,
              today at 7 PM, Monday at 10 AM
            </span>
          </label>


          <label>
            Duration

            <div className="duration-input-row">

              <input
                type="number"
                min="1"
                max="1440"
                placeholder="60"
                value={duration}
                onChange={(event) =>
                  setDuration(
                    event.target.value
                  )
                }
              />

              <span>
                minutes
              </span>

            </div>
          </label>


          <div className="quick-duration-options">

            {[30, 45, 60, 90].map(
              (minutes) => (

                <button
                  key={minutes}
                  type="button"
                  className={
                    String(minutes) ===
                    duration
                      ? "quick-duration active"
                      : "quick-duration"
                  }
                  onClick={() =>
                    setDuration(
                      String(minutes)
                    )
                  }
                >
                  {minutes} min
                </button>

              )
            )}

          </div>


          <div className="modal-actions">

            <button
              type="button"
              className="cancel-button"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>


            <button
              type="submit"
              className="save-button"
              disabled={
                loading ||
                !title.trim()
              }
            >
              {loading
                ? "Sending..."
                : "Ask AI"}
            </button>

          </div>

        </form>

      </div>

    </div>
  );
}


export default QuickCreateModal;