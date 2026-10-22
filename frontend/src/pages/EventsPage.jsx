import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useToast,
} from "../context/ToastContext";

import ConfirmDialog from "../components/ConfirmDialog";

import {
  createEvent,
  deleteEvent,
  getEvents,
  updateEvent,
} from "../services/eventApi";


function getToday() {
  const now = new Date();

  const year =
    now.getFullYear();

  const month =
    String(
      now.getMonth() + 1
    ).padStart(2, "0");

  const day =
    String(
      now.getDate()
    ).padStart(2, "0");

  return `${year}-${month}-${day}`;
}


function formatTime(time) {
  if (!time) {
    return "No time";
  }

  return String(time).slice(0, 5);
}


const emptyForm = {
  title: "",
  description: "",
  eventDate: "",
  startTime: "",
  endTime: "",
};


function EventsPage() {
  const { showToast } = useToast();

  const [events, setEvents] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [saving, setSaving] =
    useState(false);

  const [editingEvent, setEditingEvent] =
    useState(null);

  const [deleteTarget, setDeleteTarget] =
    useState(null);

  const [showModal, setShowModal] =
    useState(false);

  const [form, setForm] =
    useState(emptyForm);


  const today = getToday();


  // =========================================================
  // LOAD EVENTS
  // =========================================================

  const loadEvents = async () => {
    try {
      setLoading(true);
      setError("");

      const data =
        await getEvents();

      setEvents(data);

    } catch (err) {

      const message =
        err.message ||
        "Failed to load events.";

      setError(message);

      showToast(
        message,
        "error"
      );

    } finally {

      setLoading(false);
    }
  };


  useEffect(() => {
    loadEvents();
  }, []);


  // =========================================================
  // SORT EVENTS
  // =========================================================

  const sortedEvents = useMemo(() => {
    return [...events].sort(
      (a, b) => {

        const dateA =
          a.eventDate ||
          "9999-12-31";

        const dateB =
          b.eventDate ||
          "9999-12-31";

        const dateCompare =
          dateA.localeCompare(
            dateB
          );

        if (dateCompare !== 0) {
          return dateCompare;
        }

        return (
          a.startTime || "99:99"
        ).localeCompare(
          b.startTime || "99:99"
        );
      }
    );
  }, [events]);


  // =========================================================
  // COUNTS
  // =========================================================

  const upcomingCount =
    events.filter(
      (event) =>
        event.eventDate &&
        event.eventDate >= today
    ).length;


  const todayCount =
    events.filter(
      (event) =>
        event.eventDate === today
    ).length;


  // =========================================================
  // OPEN CREATE MODAL
  // =========================================================

  const openCreateModal = () => {
    setEditingEvent(null);

    setForm({
      ...emptyForm,
    });

    setError("");

    setShowModal(true);
  };


  // =========================================================
  // OPEN EDIT MODAL
  // =========================================================

  const openEditModal = (event) => {
    setEditingEvent(event);

    setForm({
      title:
        event.title || "",

      description:
        event.description || "",

      eventDate:
        event.eventDate || "",

      startTime:
        event.startTime
          ? String(
              event.startTime
            ).slice(0, 5)
          : "",

      endTime:
        event.endTime
          ? String(
              event.endTime
            ).slice(0, 5)
          : "",
    });

    setError("");

    setShowModal(true);
  };


  // =========================================================
  // CLOSE MODAL
  // =========================================================

  const closeModal = () => {
    setShowModal(false);

    setEditingEvent(null);

    setForm({
      ...emptyForm,
    });
  };


  // =========================================================
  // FORM CHANGE
  // =========================================================

  const handleChange = (event) => {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  };


  // =========================================================
  // CREATE / UPDATE EVENT
  // =========================================================

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    if (!form.title.trim()) {
      const message =
        "Event title is required.";

      setError(message);

      showToast(
        message,
        "error"
      );

      return;
    }


    if (
      form.startTime &&
      form.endTime &&
      form.endTime <=
        form.startTime
    ) {
      const message =
        "End time must be after start time.";

      setError(message);

      showToast(
        message,
        "error"
      );

      return;
    }


    try {
      setSaving(true);
      setError("");


      // -----------------------------------------------------
      // UPDATE EXISTING EVENT
      // -----------------------------------------------------

      if (editingEvent) {

        const updated =
          await updateEvent(
            editingEvent.id,
            {
              ...form,

              title:
                form.title.trim(),
            }
          );


        setEvents((current) =>
          current.map((item) =>
            item.id ===
            editingEvent.id
              ? updated
              : item
          )
        );


        showToast(
          `Event ${editingEvent.id} updated successfully.`,
          "success"
        );

      }

      // -----------------------------------------------------
      // CREATE NEW EVENT
      // -----------------------------------------------------

      else {

        const created =
          await createEvent({
            ...form,

            title:
              form.title.trim(),
          });


        setEvents((current) => [
          ...current,
          created,
        ]);


        showToast(
          "Event created successfully.",
          "success"
        );
      }


      closeModal();

    } catch (err) {

      const message =
        err.message ||
        "Failed to save event.";

      setError(message);

      showToast(
        message,
        "error"
      );

    } finally {

      setSaving(false);
    }
  };


  // =========================================================
  // DELETE EVENT
  // =========================================================

  const requestDeleteEvent = (event) => {
    setDeleteTarget(event);
  };


  const cancelDeleteEvent = () => {
    if (saving) {
      return;
    }

    setDeleteTarget(null);
  };


  const confirmDeleteEvent = async () => {
    if (!deleteTarget) {
      return;
    }

    const eventId =
      deleteTarget.id;

    try {
      setSaving(true);
      setError("");

      await deleteEvent(eventId);

      setEvents((current) =>
        current.filter(
          (event) =>
            event.id !== eventId
        )
      );

      showToast(
        `Event ${eventId} deleted successfully.`,
        "success"
      );

      setDeleteTarget(null);

    } catch (err) {

      const message =
        err.message ||
        `Failed to delete event ${eventId}.`;

      setError(message);

      showToast(
        message,
        "error"
      );

    } finally {

      setSaving(false);
    }
  };


  // =========================================================
  // UI
  // =========================================================

  return (
    <main className="page events-page">

      {/* =====================================================
          HEADER
          ===================================================== */}

      <header className="events-header">

        <div>

          <p className="page-eyebrow">
            Calendar
          </p>

          <h2>
            Events
          </h2>

          <p>
            Manage meetings,
            appointments and events.
          </p>

        </div>


        <div className="events-header-actions">

          <button
            className="refresh-button"
            onClick={loadEvents}
            disabled={loading}
          >
            {
              loading
                ? "Loading..."
                : "Refresh"
            }
          </button>


          <button
            className="primary-button"
            onClick={
              openCreateModal
            }
          >
            + New Event
          </button>

        </div>

      </header>


      {/* =====================================================
          ERROR
          ===================================================== */}

      {error && (
        <div className="dashboard-error">
          {error}
        </div>
      )}


      {/* =====================================================
          EVENT SUMMARY
          ===================================================== */}

      <section className="event-summary">

        <div>

          <span>
            Today
          </span>

          <strong>
            {todayCount}
          </strong>

        </div>


        <div>

          <span>
            Upcoming
          </span>

          <strong>
            {upcomingCount}
          </strong>

        </div>


        <div>

          <span>
            Total
          </span>

          <strong>
            {events.length}
          </strong>

        </div>

      </section>


      {/* =====================================================
          EVENTS CARD
          ===================================================== */}

      <section className="events-card">

        {loading ? (

          <div className="tasks-loading">
            Loading events...
          </div>

        ) : sortedEvents.length === 0 ? (

          <div className="tasks-empty">
            No events found.
          </div>

        ) : (

          <div className="event-list">

            {sortedEvents.map(
              (event) => (

                <article
                  className="event-item"
                  key={event.id}
                >

                  {/* EVENT DATE */}

                  <div className="event-date-box">

                    <strong>
                      {
                        event.eventDate ||
                        "No date"
                      }
                    </strong>

                    <span>
                      {
                        formatTime(
                          event.startTime
                        )
                      }
                    </span>

                  </div>


                  {/* EVENT DETAILS */}

                  <div className="event-main">

                    <div className="event-title-row">

                      <span className="event-id">
                        #{event.id}
                      </span>

                      <h3>
                        {event.title}
                      </h3>

                    </div>


                    {event.description && (
                      <p className="task-description">
                        {
                          event.description
                        }
                      </p>
                    )}


                    <div className="task-meta">

                      <span>
                        📅{" "}
                        {
                          event.eventDate ||
                          "No date"
                        }
                      </span>


                      <span>
                        ◷{" "}

                        {
                          formatTime(
                            event.startTime
                          )
                        }

                        {" - "}

                        {
                          formatTime(
                            event.endTime
                          )
                        }
                      </span>

                    </div>

                  </div>


                  {/* EVENT ACTIONS */}

                  <div className="task-actions">

                    <button
                      className="edit-button"
                      disabled={saving}
                      onClick={() =>
                        openEditModal(
                          event
                        )
                      }
                    >
                      Edit
                    </button>


                    <button
                      className="delete-button"
                      disabled={saving}
                      onClick={() =>
                        requestDeleteEvent(
                          event
                        )
                      }
                    >
                      Delete
                    </button>

                  </div>

                </article>

              )
            )}

          </div>

        )}

      </section>


      {/* =====================================================
          CREATE / EDIT EVENT MODAL
          ===================================================== */}

      {showModal && (

        <div className="modal-overlay">

          <div className="task-modal">

            <div className="modal-header">

              <div>

                <p className="page-eyebrow">
                  {
                    editingEvent
                      ? "Edit Event"
                      : "New Event"
                  }
                </p>

                <h3>
                  {
                    editingEvent
                      ? `Event #${editingEvent.id}`
                      : "Create Event"
                  }
                </h3>

              </div>


              <button
                type="button"
                className="modal-close"
                onClick={closeModal}
                disabled={saving}
              >
                ×
              </button>

            </div>


            <form
              className="task-edit-form"
              onSubmit={
                handleSubmit
              }
            >

              {/* TITLE */}

              <label>
                Title

                <input
                  type="text"
                  name="title"
                  value={
                    form.title
                  }
                  onChange={
                    handleChange
                  }
                  required
                />
              </label>


              {/* DESCRIPTION */}

              <label>
                Description

                <textarea
                  name="description"
                  rows="3"
                  value={
                    form.description
                  }
                  onChange={
                    handleChange
                  }
                />
              </label>


              {/* DATE */}

              <label>
                Date

                <input
                  type="date"
                  name="eventDate"
                  value={
                    form.eventDate
                  }
                  onChange={
                    handleChange
                  }
                />
              </label>


              {/* START / END TIME */}

              <div className="form-row">

                <label>
                  Start Time

                  <input
                    type="time"
                    name="startTime"
                    value={
                      form.startTime
                    }
                    onChange={
                      handleChange
                    }
                  />
                </label>


                <label>
                  End Time

                  <input
                    type="time"
                    name="endTime"
                    value={
                      form.endTime
                    }
                    onChange={
                      handleChange
                    }
                  />
                </label>

              </div>


              {/* ACTIONS */}

              <div className="modal-actions">

                <button
                  type="button"
                  className="cancel-button"
                  onClick={
                    closeModal
                  }
                  disabled={saving}
                >
                  Cancel
                </button>


                <button
                  type="submit"
                  className="save-button"
                  disabled={saving}
                >
                  {
                    saving
                      ? "Saving..."
                      : editingEvent
                      ? "Save Changes"
                      : "Create Event"
                  }
                </button>

              </div>

            </form>

          </div>

        </div>

      )}


      {/* =====================================================
          DELETE EVENT CONFIRMATION
          ===================================================== */}

      <ConfirmDialog
        open={
          deleteTarget !== null
        }
        title="Delete Event?"
        message={
          deleteTarget
            ? `Are you sure you want to delete "${deleteTarget.title}"? This action cannot be undone.`
            : ""
        }
        confirmText="Delete"
        danger
        loading={saving}
        onConfirm={
          confirmDeleteEvent
        }
        onCancel={
          cancelDeleteEvent
        }
      />

    </main>
  );
}


export default EventsPage;