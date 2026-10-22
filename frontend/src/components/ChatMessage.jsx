function formatTime(time) {
  if (!time) {
    return null;
  }

  return String(time).slice(0, 5);
}


function TaskCard({ task }) {
  if (!task) {
    return null;
  }

  return (
    <div className="chat-result-card task-result-card">

      <div className="chat-result-card-header">

        <div className="chat-result-label">
          <span>✓</span>
          TASK
        </div>

        {task.task_id && (
          <span className="chat-result-id">
            #{task.task_id}
          </span>
        )}

      </div>


      {task.title && (
        <h4>
          {task.title}
        </h4>
      )}


      <div className="chat-result-details">

        {task.date && (
          <span>
            📅 {task.date}
          </span>
        )}

        {task.time && (
          <span>
            ◷ {formatTime(task.time)}
          </span>
        )}

        {task.duration_minutes && (
          <span>
            ⏱ {task.duration_minutes} minutes
          </span>
        )}

      </div>

    </div>
  );
}


function EventCard({ event }) {
  if (!event) {
    return null;
  }

  return (
    <div className="chat-result-card event-result-card">

      <div className="chat-result-card-header">

        <div className="chat-result-label">
          <span>◷</span>
          EVENT
        </div>

        {event.event_id && (
          <span className="chat-result-id">
            #{event.event_id}
          </span>
        )}

      </div>


      {event.title && (
        <h4>
          {event.title}
        </h4>
      )}


      <div className="chat-result-details">

        {event.date && (
          <span>
            📅 {event.date}
          </span>
        )}

        {(event.start_time ||
          event.end_time) && (

          <span>
            ◷{" "}
            {formatTime(event.start_time) ||
              "No time"}

            {event.end_time &&
              ` - ${formatTime(
                event.end_time
              )}`}
          </span>
        )}

      </div>

    </div>
  );
}


function ChatMessage({
  role,
  content,
  intent,
  task,
  event,
}) {
  const isUser =
    role === "user";


  return (
    <div
      className={
        isUser
          ? "message-row message-row-user"
          : "message-row message-row-ai"
      }
    >

      <div
        className={
          isUser
            ? "message-bubble user-message"
            : "message-bubble ai-message"
        }
      >

        <div className="message-label">
          {isUser
            ? "You"
            : "AI Personal Manager"}
        </div>


        <div className="message-text">
          {content}
        </div>


        {!isUser && task && (
          <TaskCard task={task} />
        )}


        {!isUser && event && (
          <EventCard event={event} />
        )}


        {!isUser &&
          intent &&
          intent !== "GENERAL_CHAT" &&
          intent !== "UNKNOWN" && (

            <div className="chat-intent">
              {intent.replaceAll(
                "_",
                " "
              )}
            </div>

          )}

      </div>

    </div>
  );
}


export default ChatMessage;