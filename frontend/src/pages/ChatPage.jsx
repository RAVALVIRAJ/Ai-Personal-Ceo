import { useEffect, useState } from "react";

import ChatMessage from "../components/ChatMessage";
import QuickCreateModal from "../components/QuickCreateModal";

import {
  sendMessage,
} from "../services/aiApi";

const CHAT_STORAGE_KEY = "ai-personal-ceo-chat-messages";

const WELCOME_MESSAGE = {
  id: "welcome",
  role: "assistant",
  content:
    "Hello! I'm your AI Personal Manager.\n\n" +
    "I can create tasks, manage events, update your schedule, " +
    "and help you decide what to focus on.",
  intent: null,
  task: null,
  event: null,
};

function loadChatMessages() {
  try {
    const savedMessages = window.localStorage.getItem(CHAT_STORAGE_KEY);
    if (!savedMessages) {
      return [WELCOME_MESSAGE];
    }

    const parsedMessages = JSON.parse(savedMessages);
    if (
      Array.isArray(parsedMessages) &&
      parsedMessages.every(
        (message) =>
          message &&
          typeof message.id === "string" &&
          (message.role === "assistant" || message.role === "user") &&
          typeof message.content === "string"
      )
    ) {
      return parsedMessages;
    }
  } catch (error) {
    console.warn("Unable to restore saved chat history.", error);
  }

  return [WELCOME_MESSAGE];
}

function ChatPage() {
  const [input, setInput] =
    useState("");

  const [messages, setMessages] =
    useState(loadChatMessages);

  const [loading, setLoading] =
    useState(false);

  const [
    quickCreateType,
    setQuickCreateType,
  ] = useState(null);

  useEffect(() => {
    try {
      window.localStorage.setItem(
        CHAT_STORAGE_KEY,
        JSON.stringify(messages)
      );
    } catch (error) {
      console.error("Unable to save chat history.", error);
    }
  }, [messages]);


  // =========================================================
  // SEND MESSAGE
  // =========================================================

  const sendChatMessage = async (
    text
  ) => {
    const trimmedMessage =
      text.trim();

    if (
      !trimmedMessage ||
      loading
    ) {
      return;
    }


    const timestamp =
      Date.now();


    // -------------------------------------------------------
    // ADD USER MESSAGE
    // -------------------------------------------------------

    const userMessage = {
      id:
        `${timestamp}-user`,

      role: "user",

      content:
        trimmedMessage,

      intent: null,
      task: null,
      event: null,
    };


    setMessages(
      (currentMessages) => [
        ...currentMessages,
        userMessage,
      ]
    );


    setInput("");
    setLoading(true);


    try {

      // -----------------------------------------------------
      // FASTAPI
      // -----------------------------------------------------

      const response =
        await sendMessage(
          trimmedMessage
        );


      const aiMessage = {
        id:
          `${Date.now()}-assistant`,

        role: "assistant",

        content:
          response.message,

        intent:
          response.intent || null,

        task:
          response.task || null,

        event:
          response.event || null,
      };


      setMessages(
        (currentMessages) => [
          ...currentMessages,
          aiMessage,
        ]
      );

    } catch (error) {

      const errorMessage = {
        id:
          `${Date.now()}-error`,

        role: "assistant",

        content:
          "I couldn't connect to the AI service.\n\n" +
          (
            error.message ||
            "Please make sure FastAPI is running."
          ),

        intent: null,
        task: null,
        event: null,
      };


      setMessages(
        (currentMessages) => [
          ...currentMessages,
          errorMessage,
        ]
      );

    } finally {

      setLoading(false);
    }
  };


  // =========================================================
  // NORMAL INPUT SUBMIT
  // =========================================================

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    await sendChatMessage(
      input
    );
  };


  // =========================================================
  // DIRECT QUICK ACTION
  // =========================================================

  const runQuickAction = async (
    text
  ) => {
    if (loading) {
      return;
    }

    await sendChatMessage(
      text
    );
  };


  // =========================================================
  // QUICK CREATE
  // =========================================================

  const openQuickCreate = (
    type
  ) => {
    setQuickCreateType(type);
  };


  const closeQuickCreate = () => {
    if (loading) {
      return;
    }

    setQuickCreateType(null);
  };


  const submitQuickCreate = async (
    prompt
  ) => {
    setQuickCreateType(null);

    await sendChatMessage(
      prompt
    );
  };


  return (
    <main className="chat-page">

      {/* =====================================================
          HEADER
          ===================================================== */}

      <header className="chat-header">

        <div>

          <h2>
            AI Personal Manager
          </h2>

          <p>
            Manage your tasks and schedule
            using natural language.
          </p>

        </div>


        <div className="ai-status">

          <span className="online-indicator">
          </span>

          AI Service

        </div>

      </header>


      {/* =====================================================
          MESSAGES
          ===================================================== */}

      <section className="chat-content">

        <div className="messages-container">

          {messages.map(
            (item) => (

              <ChatMessage
                key={item.id}

                role={
                  item.role
                }

                content={
                  item.content
                }

                intent={
                  item.intent
                }

                task={
                  item.task
                }

                event={
                  item.event
                }
              />

            )
          )}


          {/* TYPING INDICATOR */}

          {loading && (

            <div className="message-row message-row-ai">

              <div className="message-bubble ai-message">

                <div className="message-label">
                  AI Personal Manager
                </div>


                <div className="typing-indicator">

                  <span></span>
                  <span></span>
                  <span></span>

                </div>

              </div>

            </div>

          )}

        </div>

      </section>


      {/* =====================================================
          QUICK ACTIONS
          ===================================================== */}

      <section className="suggestions">

        <button
          type="button"
          disabled={loading}
          onClick={() =>
            runQuickAction(
              "What should I focus on today?"
            )
          }
        >
          ✦ Plan my day
        </button>


        <button
          type="button"
          disabled={loading}
          onClick={() =>
            runQuickAction(
              "What do I have tomorrow?"
            )
          }
        >
          ◷ Tomorrow
        </button>


        <button
          type="button"
          disabled={loading}
          onClick={() =>
            openQuickCreate(
              "task"
            )
          }
        >
          + New task
        </button>


        <button
          type="button"
          disabled={loading}
          onClick={() =>
            openQuickCreate(
              "event"
            )
          }
        >
          + New event
        </button>

      </section>


      {/* =====================================================
          INPUT
          ===================================================== */}

      <form
        className="chat-input-container"
        onSubmit={
          handleSubmit
        }
      >

        <input
          type="text"

          placeholder=
            "Ask your AI Personal Manager..."

          value={input}

          onChange={
            (event) =>
              setInput(
                event.target.value
              )
          }

          disabled={loading}
        />


        <button
          type="submit"

          disabled={
            loading ||
            !input.trim()
          }
        >
          {loading
            ? "Thinking..."
            : "Send"}
        </button>

      </form>


      {/* =====================================================
          QUICK CREATE MODAL
          ===================================================== */}

      <QuickCreateModal
        open={
          quickCreateType !== null
        }

        type={
          quickCreateType
        }

        loading={loading}

        onClose={
          closeQuickCreate
        }

        onSubmit={
          submitQuickCreate
        }
      />

    </main>
  );
}


export default ChatPage;