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
  completeTask,
  createTask,
  deleteTask,
  getTasks,
  updateTask,
} from "../services/taskApi";


function formatTime(time) {
  if (!time) {
    return "No time";
  }

  return String(time).slice(0, 5);
}


function TasksPage() {
  const { showToast } = useToast();

  const [tasks, setTasks] = useState([]);

  const [filter, setFilter] =
    useState("ACTIVE");

  const [loading, setLoading] =
    useState(true);

  const [actionTaskId, setActionTaskId] =
    useState(null);

  const [error, setError] =
    useState("");

  const [creatingTask, setCreatingTask] =
  useState(false);

  const [editingTask, setEditingTask] =
    useState(null);

  const [deleteTarget, setDeleteTarget] =
    useState(null);

  const [editForm, setEditForm] =
    useState({
      title: "",
      description: "",
      dueDate: "",
      dueTime: "",
      durationMinutes: "",
      reminderBeforeMinutes: "",
      recurrence: "NONE",
    });


  // =========================================================
  // LOAD TASKS
  // =========================================================

  const loadTasks = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getTasks();

      setTasks(data);

    } catch (err) {

      const message =
        err.message ||
        "Failed to load tasks.";

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
    loadTasks();
  }, []);


  // =========================================================
  // TASK COUNTS
  // =========================================================

  const counts = useMemo(() => {
    return {
      all: tasks.length,

      active: tasks.filter(
        (task) =>
          task.status !== "COMPLETED" &&
          task.status !== "CANCELLED"
      ).length,

      completed: tasks.filter(
        (task) =>
          task.status === "COMPLETED"
      ).length,
    };
  }, [tasks]);


  // =========================================================
  // FILTER + SORT TASKS
  // =========================================================

  const visibleTasks = useMemo(() => {
    let filtered = tasks;

    if (filter === "ACTIVE") {
      filtered = tasks.filter(
        (task) =>
          task.status !== "COMPLETED" &&
          task.status !== "CANCELLED"
      );
    }

    if (filter === "COMPLETED") {
      filtered = tasks.filter(
        (task) =>
          task.status === "COMPLETED"
      );
    }

    return [...filtered].sort(
      (a, b) => {
        const dateA =
          a.dueDate || "9999-12-31";

        const dateB =
          b.dueDate || "9999-12-31";

        const dateCompare =
          dateA.localeCompare(dateB);

        if (dateCompare !== 0) {
          return dateCompare;
        }

        return (
          a.dueTime || "99:99"
        ).localeCompare(
          b.dueTime || "99:99"
        );
      }
    );
  }, [tasks, filter]);


  // =========================================================
  // COMPLETE TASK
  // =========================================================

  const handleComplete = async (
    taskId
  ) => {
    try {
      setActionTaskId(taskId);
      setError("");

      const updatedTask =
        await completeTask(taskId);

      setTasks((current) =>
        current.map((task) =>
          task.id === taskId
            ? updatedTask
            : task
        )
      );

      showToast(
        `Task ${taskId} completed successfully.`,
        "success"
      );

    } catch (err) {

      const message =
        err.message ||
        `Failed to complete task ${taskId}.`;

      setError(message);

      showToast(
        message,
        "error"
      );

    } finally {

      setActionTaskId(null);
    }
  };


  // =========================================================
  // DELETE TASK
  // =========================================================

  const requestDeleteTask = (task) => {
    setDeleteTarget(task);
  };


  const cancelDeleteTask = () => {
    setDeleteTarget(null);
  };


  const confirmDeleteTask = async () => {
    if (!deleteTarget) {
      return;
    }

    const taskId = deleteTarget.id;

    try {
      setActionTaskId(taskId);
      setError("");

      await deleteTask(taskId);

      setTasks((current) =>
        current.filter(
          (task) =>
            task.id !== taskId
        )
      );

      showToast(
        `Task ${taskId} deleted successfully.`,
        "success"
      );

      setDeleteTarget(null);

    } catch (err) {

      const message =
        err.message ||
        `Failed to delete task ${taskId}.`;

      setError(message);

      showToast(
        message,
        "error"
      );

    } finally {

      setActionTaskId(null);
    }
  };


  // =========================================================
  // OPEN EDIT MODAL
  // =========================================================

  const openCreateTask = () => {
    setCreatingTask(true);

    setEditingTask(null);

    setEditForm({
      title: "",
      description: "",
      dueDate: "",
      dueTime: "",
      durationMinutes: "",
      reminderBeforeMinutes: "",
      recurrence: "NONE",
    });

    setError("");
  };

  const openEditTask = (task) => {
    setEditingTask(task);

    setEditForm({
      title:
        task.title || "",

      description:
        task.description || "",

      dueDate:
        task.dueDate || "",

      dueTime:
        task.dueTime
          ? String(
              task.dueTime
            ).slice(0, 5)
          : "",

      durationMinutes:
        task.durationMinutes ?? "",

      reminderBeforeMinutes:
        task.reminderBeforeMinutes ?? "",

      recurrence:
        task.recurrence || "NONE",
    });

    setError("");
  };


  // =========================================================
  // CLOSE EDIT MODAL
  // =========================================================

  const closeEditTask = () => {
  setEditingTask(null);

  setCreatingTask(false);

  setEditForm({
    title: "",
    description: "",
    dueDate: "",
    dueTime: "",
    durationMinutes: "",
    reminderBeforeMinutes: "",
    recurrence: "NONE",
  });
};


  // =========================================================
  // EDIT FORM CHANGE
  // =========================================================

  const handleEditChange = (event) => {
    const {
      name,
      value,
    } = event.target;

    setEditForm((current) => ({
      ...current,
      [name]: value,
    }));
  };


  // =========================================================
  // UPDATE TASK
  // =========================================================

  const handleSaveTask = async (
  event
) => {
  event.preventDefault();

  if (!editForm.title.trim()) {
    const message =
      "Task title is required.";

    setError(message);

    showToast(
      message,
      "error"
    );

    return;
  }


  try {
    setError("");


    // CREATE TASK
    if (creatingTask) {

      setActionTaskId("CREATE");

      const createdTask =
        await createTask({
          ...editForm,

          title:
            editForm.title.trim(),
        });


      setTasks((current) => [
        ...current,
        createdTask,
      ]);


      showToast(
        `Task ${createdTask.id} created successfully.`,
        "success"
      );
    }


    // UPDATE TASK
    else if (editingTask) {

      setActionTaskId(
        editingTask.id
      );

      const updatedTask =
        await updateTask(
          editingTask.id,
          {
            ...editForm,

            title:
              editForm.title.trim(),
          }
        );


      setTasks((current) =>
        current.map((task) =>
          task.id ===
          editingTask.id
            ? updatedTask
            : task
        )
      );


      showToast(
        `Task ${editingTask.id} updated successfully.`,
        "success"
      );
    }


    closeEditTask();

  } catch (err) {

    const message =
      err.message ||
      "Failed to save task.";

    setError(message);

    showToast(
      message,
      "error"
    );

  } finally {

    setActionTaskId(null);
  }
};


  // =========================================================
  // UI
  // =========================================================

  return (
    <main className="page tasks-page">

      {/* =====================================================
          HEADER
          ===================================================== */}

      <header className="tasks-header">

        <div>

          <p className="page-eyebrow">
            Productivity
          </p>

          <h2>
            Tasks
          </h2>

          <p>
            View and manage your tasks.
          </p>

        </div>


        <div className="tasks-header-actions">

        <button
          className="refresh-button"
          onClick={loadTasks}
          disabled={loading}
        >
          {loading
            ? "Loading..."
            : "Refresh"}
        </button>


        <button
          className="primary-button"
          onClick={openCreateTask}
        >
          + New Task
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
          SUMMARY
          ===================================================== */}

      <section className="task-summary">

        <div>
          <span>
            Active
          </span>

          <strong>
            {counts.active}
          </strong>
        </div>


        <div>
          <span>
            Completed
          </span>

          <strong>
            {counts.completed}
          </strong>
        </div>


        <div>
          <span>
            Total
          </span>

          <strong>
            {counts.all}
          </strong>
        </div>

      </section>


      {/* =====================================================
          TASK CARD
          ===================================================== */}

      <section className="tasks-card">

        {/* ---------------------------------------------------
            FILTERS
            --------------------------------------------------- */}

        <div className="tasks-toolbar">

          <div className="task-filters">

            <button
              className={
                filter === "ACTIVE"
                  ? "task-filter active"
                  : "task-filter"
              }
              onClick={() =>
                setFilter("ACTIVE")
              }
            >
              Active
            </button>


            <button
              className={
                filter === "COMPLETED"
                  ? "task-filter active"
                  : "task-filter"
              }
              onClick={() =>
                setFilter("COMPLETED")
              }
            >
              Completed
            </button>


            <button
              className={
                filter === "ALL"
                  ? "task-filter active"
                  : "task-filter"
              }
              onClick={() =>
                setFilter("ALL")
              }
            >
              All
            </button>

          </div>


          <span className="task-count">
            {visibleTasks.length} tasks
          </span>

        </div>


        {/* ---------------------------------------------------
            TASK LIST
            --------------------------------------------------- */}

        {loading ? (

          <div className="tasks-loading">
            Loading tasks...
          </div>

        ) : visibleTasks.length === 0 ? (

          <div className="tasks-empty">
            No tasks found.
          </div>

        ) : (

          <div className="task-list">

            {visibleTasks.map((task) => {

              const isBusy =
                actionTaskId === task.id;

              const canComplete =
                task.status !==
                  "COMPLETED" &&
                task.status !==
                  "CANCELLED";


              return (
                <article
                  className="task-item"
                  key={task.id}
                >

                  {/* TASK ID */}

                  <div className="task-id">
                    #{task.id}
                  </div>


                  {/* TASK DETAILS */}

                  <div className="task-main">

                    <div className="task-title-row">

                      <h3>
                        {task.title}
                      </h3>


                      <span
                        className={
                          `status-pill status-${(
                            task.status ||
                            "pending"
                          ).toLowerCase()}`
                        }
                      >
                        {task.status}
                      </span>

                      {task.reminderBeforeMinutes != null && (
                        <span className="reminder-badge">
                          ⏰{" "}
                          {task.reminderBeforeMinutes === 0
                            ? "At due time"
                            : `${task.reminderBeforeMinutes} min reminder`}
                        </span>
                      )}

                    </div>


                    {task.description && (
                      <p className="task-description">
                        {task.description}
                      </p>
                    )}


                    <div className="task-meta">

                      <span>
                        📅{" "}
                        {
                          task.dueDate ||
                          "No date"
                        }
                      </span>


                      <span>
                        ◷{" "}
                        {
                          formatTime(
                            task.dueTime
                          )
                        }
                      </span>


                      {task.durationMinutes && (
                        <span>
                          ⏱{" "}
                          {
                            task.durationMinutes
                          }{" "}
                          min
                        </span>
                      )}

                    </div>

                  </div>


                  {/* TASK ACTIONS */}

                  <div className="task-actions">

                    <button
                      className="edit-button"
                      disabled={isBusy}
                      onClick={() =>
                        openEditTask(task)
                      }
                    >
                      Edit
                    </button>


                    {canComplete && (
                      <button
                        className="complete-button"
                        disabled={isBusy}
                        onClick={() =>
                          handleComplete(
                            task.id
                          )
                        }
                      >
                        {
                          isBusy
                            ? "..."
                            : "Complete"
                        }
                      </button>
                    )}


                    <button
                      className="delete-button"
                      disabled={isBusy}
                      onClick={() =>
                        requestDeleteTask(
                          task
                        )
                      }
                    >
                      Delete
                    </button>

                  </div>

                </article>
              );
            })}

          </div>

        )}

      </section>


      {/* =====================================================
          EDIT TASK MODAL
          ===================================================== */}

      {(editingTask || creatingTask) && (

        <div className="modal-overlay">

          <div className="task-modal">

            <div className="modal-header">

              <div>

                <p className="page-eyebrow">
                  {creatingTask
                    ? "New Task"
                    : "Edit Task"}
                </p>

                <h3>
                  {creatingTask
                    ? "Create Task"
                    : `Task #${editingTask.id}`}
                </h3>

              </div>


              <button
                type="button"
                className="modal-close"
                onClick={closeEditTask}
              >
                ×
              </button>

            </div>


            <form
              className="task-edit-form"
              onSubmit={handleSaveTask}
            >

              {/* TITLE */}

              <label>
                Title

                <input
                  type="text"
                  name="title"
                  value={editForm.title}
                  onChange={
                    handleEditChange
                  }
                  required
                />
              </label>


              {/* DESCRIPTION */}

              <label>
                Description

                <textarea
                  name="description"
                  value={
                    editForm.description
                  }
                  onChange={
                    handleEditChange
                  }
                  rows="3"
                />
              </label>


              {/* DATE / TIME */}

              <div className="form-row">

                <label>
                  Due Date

                  <input
                    type="date"
                    name="dueDate"
                    value={
                      editForm.dueDate
                    }
                    onChange={
                      handleEditChange
                    }
                  />
                </label>


                <label>
                  Due Time

                  <input
                    type="time"
                    name="dueTime"
                    value={
                      editForm.dueTime
                    }
                    onChange={
                      handleEditChange
                    }
                  />
                </label>

              </div>


              {/* DURATION */}

              <label>
                Duration (minutes)

                <input
                  type="number"
                  name="durationMinutes"
                  min="1"
                  max="1440"
                  value={
                    editForm.durationMinutes
                  }
                  onChange={
                    handleEditChange
                  }
                />
              </label>

              <div className="form-row">
                <label>
                  Reminder (minutes before)

                  <input
                    type="number"
                    name="reminderBeforeMinutes"
                    min="0"
                    value={editForm.reminderBeforeMinutes}
                    onChange={handleEditChange}
                  />
                </label>

                <label>
                  Recurrence

                  <select
                    name="recurrence"
                    value={editForm.recurrence}
                    onChange={handleEditChange}
                  >
                    <option value="NONE">Does not repeat</option>
                    <option value="DAILY">Daily</option>
                    <option value="WEEKLY">Weekly</option>
                    <option value="MONTHLY">Monthly</option>
                  </select>
                </label>
              </div>


              {/* ACTIONS */}

              <div className="modal-actions">

                <button
                  type="button"
                  className="cancel-button"
                  onClick={
                    closeEditTask
                  }
                >
                  Cancel
                </button>


                <button
                  type="submit"
                  className="save-button"
                  disabled={
                    actionTaskId !== null
                  }
                >
                  {
                    actionTaskId !== null
                      ? "Saving..."
                      : creatingTask
                      ? "Create Task"
                      : "Save Changes"
                  }
                </button>

              </div>

            </form>

          </div>

        </div>

      )}


      {/* =====================================================
          DELETE TASK CONFIRMATION
          ===================================================== */}

      <ConfirmDialog
        open={
          deleteTarget !== null
        }
        title="Delete Task?"
        message={
          deleteTarget
            ? `Are you sure you want to delete "${deleteTarget.title}"? This action cannot be undone.`
            : ""
        }
        confirmText="Delete"
        danger
        loading={
          deleteTarget
            ? actionTaskId ===
              deleteTarget.id
            : false
        }
        onConfirm={
          confirmDeleteTask
        }
        onCancel={
          cancelDeleteTask
        }
      />

    </main>
  );
}


export default TasksPage;