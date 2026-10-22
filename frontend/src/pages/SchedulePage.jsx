import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getTasks,
  getEvents,
} from "../services/dashboardApi";


function toLocalDateString(date) {
  const year = date.getFullYear();

  const month = String(
    date.getMonth() + 1
  ).padStart(2, "0");

  const day = String(
    date.getDate()
  ).padStart(2, "0");

  return `${year}-${month}-${day}`;
}


function formatTime(time) {
  if (!time) {
    return "No time";
  }

  return String(time).slice(0, 5);
}


function getMonday(date) {
  const result = new Date(date);

  const day = result.getDay();

  const difference =
    day === 0
      ? -6
      : 1 - day;

  result.setDate(
    result.getDate() + difference
  );

  return result;
}


function SchedulePage() {
  const [tasks, setTasks] = useState([]);
  const [events, setEvents] = useState([]);

  const [view, setView] = useState("TODAY");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  const loadSchedule = async () => {
    try {
      setLoading(true);
      setError("");

      const [
        taskData,
        eventData,
      ] = await Promise.all([
        getTasks(),
        getEvents(),
      ]);

      setTasks(taskData);
      setEvents(eventData);
    } catch (err) {
      setError(
        err.message ||
        "Failed to load schedule."
      );
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadSchedule();
  }, []);


  const activeTasks = useMemo(
    () =>
      tasks.filter(
        (task) =>
          task.status !== "COMPLETED" &&
          task.status !== "CANCELLED"
      ),
    [tasks]
  );


  const scheduleDays = useMemo(() => {
    const today = new Date();

    if (view === "TODAY") {
      return [
        toLocalDateString(today),
      ];
    }


    if (view === "TOMORROW") {
      const tomorrow =
        new Date(today);

      tomorrow.setDate(
        tomorrow.getDate() + 1
      );

      return [
        toLocalDateString(tomorrow),
      ];
    }


    const monday =
      getMonday(today);

    const days = [];

    for (
      let index = 0;
      index < 7;
      index++
    ) {
      const date =
        new Date(monday);

      date.setDate(
        monday.getDate() + index
      );

      days.push(
        toLocalDateString(date)
      );
    }

    return days;
  }, [view]);


  const schedule = useMemo(() => {
    return scheduleDays.map(
      (date) => {

        const dayTasks =
          activeTasks
            .filter(
              (task) =>
                task.dueDate === date
            )
            .sort((a, b) =>
              (
                a.dueTime ||
                "99:99"
              ).localeCompare(
                b.dueTime ||
                "99:99"
              )
            );


        const dayEvents =
          events
            .filter(
              (event) =>
                event.eventDate ===
                date
            )
            .sort((a, b) =>
              (
                a.startTime ||
                "99:99"
              ).localeCompare(
                b.startTime ||
                "99:99"
              )
            );


        return {
          date,
          tasks: dayTasks,
          events: dayEvents,
        };
      }
    );
  }, [
    scheduleDays,
    activeTasks,
    events,
  ]);


  const totalItems =
    schedule.reduce(
      (total, day) =>
        total +
        day.tasks.length +
        day.events.length,
      0
    );


  return (
    <main className="page schedule-page">

      <header className="schedule-header">

        <div>
          <p className="page-eyebrow">
            Planner
          </p>

          <h2>Schedule</h2>

          <p>
            See your tasks and events
            in one timeline.
          </p>
        </div>


        <button
          className="refresh-button"
          onClick={loadSchedule}
        >
          Refresh
        </button>

      </header>


      {error && (
        <div className="dashboard-error">
          {error}
        </div>
      )}


      <section className="schedule-toolbar">

        <div className="schedule-tabs">

          <button
            className={
              view === "TODAY"
                ? "schedule-tab active"
                : "schedule-tab"
            }
            onClick={() =>
              setView("TODAY")
            }
          >
            Today
          </button>


          <button
            className={
              view === "TOMORROW"
                ? "schedule-tab active"
                : "schedule-tab"
            }
            onClick={() =>
              setView("TOMORROW")
            }
          >
            Tomorrow
          </button>


          <button
            className={
              view === "WEEK"
                ? "schedule-tab active"
                : "schedule-tab"
            }
            onClick={() =>
              setView("WEEK")
            }
          >
            This Week
          </button>

        </div>


        <span className="schedule-count">
          {totalItems} scheduled items
        </span>

      </section>


      {loading ? (

        <div className="schedule-loading">
          Loading schedule...
        </div>

      ) : (

        <section className="schedule-days">

          {schedule.map((day) => {

            const dateObject =
              new Date(
                `${day.date}T00:00:00`
              );

            const dayName =
              dateObject.toLocaleDateString(
                undefined,
                {
                  weekday: "long",
                }
              );


            const hasItems =
              day.tasks.length > 0 ||
              day.events.length > 0;


            return (
              <article
                className="schedule-day"
                key={day.date}
              >

                <div className="schedule-day-header">

                  <div>
                    <span className="schedule-day-name">
                      {dayName}
                    </span>

                    <strong>
                      {day.date}
                    </strong>
                  </div>


                  <span className="schedule-day-count">
                    {
                      day.tasks.length +
                      day.events.length
                    }{" "}
                    items
                  </span>

                </div>


                {!hasItems ? (

                  <div className="schedule-empty">
                    Nothing scheduled.
                  </div>

                ) : (

                  <div className="timeline">

                    {[
                      ...day.tasks.map(
                        (task) => ({
                          type: "TASK",
                          id: `task-${task.id}`,
                          time:
                            task.dueTime,
                          title:
                            task.title,
                          duration:
                            task.durationMinutes,
                          status:
                            task.status,
                        })
                      ),

                      ...day.events.map(
                        (event) => ({
                          type: "EVENT",
                          id: `event-${event.id}`,
                          time:
                            event.startTime,
                          endTime:
                            event.endTime,
                          title:
                            event.title,
                        })
                      ),
                    ]
                      .sort((a, b) =>
                        (
                          a.time ||
                          "99:99"
                        ).localeCompare(
                          b.time ||
                          "99:99"
                        )
                      )
                      .map((item) => (

                        <div
                          className="timeline-item"
                          key={item.id}
                        >

                          <div className="timeline-time">
                            {
                              formatTime(
                                item.time
                              )
                            }
                          </div>


                          <div
                            className={
                              item.type ===
                              "TASK"
                                ? "timeline-marker task-marker"
                                : "timeline-marker event-marker"
                            }
                          ></div>


                          <div className="timeline-content">

                            <div className="timeline-title-row">

                              <span
                                className={
                                  item.type ===
                                  "TASK"
                                    ? "type-badge task-type"
                                    : "type-badge event-type"
                                }
                              >
                                {
                                  item.type
                                }
                              </span>

                              <strong>
                                {
                                  item.title
                                }
                              </strong>

                            </div>


                            <div className="timeline-meta">

                              {
                                item.type ===
                                  "TASK" &&
                                item.duration && (
                                  <span>
                                    {
                                      item.duration
                                    }{" "}
                                    minutes
                                  </span>
                                )
                              }


                              {
                                item.type ===
                                  "TASK" &&
                                item.status && (
                                  <span>
                                    {
                                      item.status
                                    }
                                  </span>
                                )
                              }


                              {
                                item.type ===
                                  "EVENT" &&
                                item.endTime && (
                                  <span>
                                    {
                                      formatTime(
                                        item.time
                                      )
                                    }
                                    {" - "}
                                    {
                                      formatTime(
                                        item.endTime
                                      )
                                    }
                                  </span>
                                )
                              }

                            </div>

                          </div>

                        </div>

                      ))}

                  </div>

                )}

              </article>
            );
          })}

        </section>

      )}

    </main>
  );
}


export default SchedulePage;