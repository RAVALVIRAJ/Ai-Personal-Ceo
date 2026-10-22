import { useEffect, useMemo, useState } from "react";

import {
  getTasks,
  getEvents,
  getTodayFocus,
} from "../services/dashboardApi";


function getLocalDateString() {
  const now = new Date();

  const year = now.getFullYear();

  const month = String(
    now.getMonth() + 1
  ).padStart(2, "0");

  const day = String(
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


function DashboardPage() {
  const [tasks, setTasks] = useState([]);
  const [events, setEvents] = useState([]);

  const [todayFocus, setTodayFocus] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  const today = getLocalDateString();


  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      const [
        taskData,
        eventData,
        focusData,
      ] = await Promise.all([
        getTasks(),
        getEvents(),
        getTodayFocus(),
      ]);

      setTasks(taskData);
      setEvents(eventData);

      setTodayFocus(
        focusData.message ||
        "No AI plan available."
      );
    } catch (err) {
      setError(
        err.message ||
        "Failed to load dashboard."
      );
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadDashboard();
  }, []);


  const dashboardData = useMemo(() => {
    const activeTasks = tasks.filter(
      (task) =>
        task.status !== "COMPLETED" &&
        task.status !== "CANCELLED"
    );

    const completedTasks = tasks.filter(
      (task) =>
        task.status === "COMPLETED"
    );


    const todayEvents = events.filter(
      (event) =>
        event.eventDate === today
    );


    const upcomingTasks = activeTasks
      .filter(
        (task) =>
          task.dueDate &&
          task.dueDate >= today
      )
      .sort((a, b) => {
        const dateCompare =
          (a.dueDate || "").localeCompare(
            b.dueDate || ""
          );

        if (dateCompare !== 0) {
          return dateCompare;
        }

        return (
          a.dueTime || "99:99"
        ).localeCompare(
          b.dueTime || "99:99"
        );
      });


    const upcomingEvents = events
      .filter(
        (event) =>
          event.eventDate &&
          event.eventDate >= today
      )
      .sort((a, b) => {
        const dateCompare =
          (a.eventDate || "").localeCompare(
            b.eventDate || ""
          );

        if (dateCompare !== 0) {
          return dateCompare;
        }

        return (
          a.startTime || "99:99"
        ).localeCompare(
          b.startTime || "99:99"
        );
      });


    return {
      activeTasks,
      completedTasks,
      todayEvents,
      upcomingTasks,
      upcomingEvents,
    };
  }, [tasks, events, today]);


  if (loading) {
    return (
      <main className="page dashboard-page">
        <div className="page-loading">
          Loading your dashboard...
        </div>
      </main>
    );
  }


  return (
    <main className="page dashboard-page">

      {/* ============================================= */}
      {/* HEADER                                        */}
      {/* ============================================= */}

      <header className="dashboard-header">
        <div>
          <p className="page-eyebrow">
            Overview
          </p>

          <h2>Dashboard</h2>

          <p>
            Your tasks, events and AI plan in one place.
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={loadDashboard}
        >
          Refresh
        </button>
      </header>


      {error && (
        <div className="dashboard-error">
          {error}
        </div>
      )}


      {/* ============================================= */}
      {/* KPI CARDS                                     */}
      {/* ============================================= */}

      <section className="stats-grid">

        <div className="stat-card">
          <div className="stat-icon">
            ✓
          </div>

          <div>
            <span className="stat-label">
              Active Tasks
            </span>

            <strong>
              {
                dashboardData
                  .activeTasks.length
              }
            </strong>

            <small>
              Work still in progress
            </small>
          </div>
        </div>


        <div className="stat-card">
          <div className="stat-icon">
            ◷
          </div>

          <div>
            <span className="stat-label">
              Today's Events
            </span>

            <strong>
              {
                dashboardData
                  .todayEvents.length
              }
            </strong>

            <small>
              Events scheduled today
            </small>
          </div>
        </div>


        <div className="stat-card">
          <div className="stat-icon">
            ★
          </div>

          <div>
            <span className="stat-label">
              Completed
            </span>

            <strong>
              {
                dashboardData
                  .completedTasks.length
              }
            </strong>

            <small>
              Tasks completed
            </small>
          </div>
        </div>


        <div className="stat-card">
          <div className="stat-icon">
            →
          </div>

          <div>
            <span className="stat-label">
              Upcoming
            </span>

            <strong>
              {
                dashboardData
                  .upcomingTasks.length
                +
                dashboardData
                  .upcomingEvents.length
              }
            </strong>

            <small>
              Upcoming tasks and events
            </small>
          </div>
        </div>

      </section>


      {/* ============================================= */}
      {/* MAIN DASHBOARD                                */}
      {/* ============================================= */}

      <section className="dashboard-grid">

        {/* AI FOCUS */}

        <div className="dashboard-card focus-card">

          <div className="card-heading">
            <div>
              <span className="card-badge">
                AI
              </span>

              <h3>Today's Focus</h3>
            </div>
          </div>

          <div className="focus-content">
            {todayFocus}
          </div>

        </div>


        {/* UPCOMING TASKS */}

        <div className="dashboard-card">

          <div className="card-heading">
            <div>
              <h3>Upcoming Tasks</h3>

              <p>
                Your next active tasks
              </p>
            </div>
          </div>

          <div className="dashboard-list">

            {
              dashboardData
                .upcomingTasks.length === 0
              ? (
                <div className="empty-state">
                  No upcoming tasks.
                </div>
              )
              : (
                dashboardData
                  .upcomingTasks
                  .slice(0, 5)
                  .map((task) => (

                    <div
                      className="dashboard-list-item"
                      key={task.id}
                    >

                      <div className="list-time">
                        {
                          task.dueTime
                            ? formatTime(
                                task.dueTime
                              )
                            : "--:--"
                        }
                      </div>

                      <div className="list-details">
                        <strong>
                          {task.title}
                        </strong>

                        <span>
                          {task.dueDate}

                          {
                            task.durationMinutes
                              ? ` • ${task.durationMinutes} min`
                              : ""
                          }
                        </span>
                      </div>

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

                    </div>

                  ))
              )
            }

          </div>

        </div>


        {/* UPCOMING EVENTS */}

        <div className="dashboard-card">

          <div className="card-heading">
            <div>
              <h3>Upcoming Events</h3>

              <p>
                Meetings and scheduled events
              </p>
            </div>
          </div>

          <div className="dashboard-list">

            {
              dashboardData
                .upcomingEvents.length === 0
              ? (
                <div className="empty-state">
                  No upcoming events.
                </div>
              )
              : (
                dashboardData
                  .upcomingEvents
                  .slice(0, 5)
                  .map((event) => (

                    <div
                      className="dashboard-list-item"
                      key={event.id}
                    >

                      <div className="list-time">
                        {
                          formatTime(
                            event.startTime
                          )
                        }
                      </div>

                      <div className="list-details">
                        <strong>
                          {event.title}
                        </strong>

                        <span>
                          {event.eventDate}

                          {
                            event.endTime
                              ? ` • ${formatTime(
                                  event.startTime
                                )} - ${formatTime(
                                  event.endTime
                                )}`
                              : ""
                          }
                        </span>
                      </div>

                    </div>

                  ))
              )
            }

          </div>

        </div>

      </section>

    </main>
  );
}


export default DashboardPage;