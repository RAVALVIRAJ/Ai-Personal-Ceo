import { useEffect, useState } from "react";

import ChatMessage from "../components/ChatMessage";
import QuickCreateModal from "../components/QuickCreateModal";
import { sendMessage } from "../services/aiApi";

const CHAT_STORAGE_KEY = "ai-personal-ceo-chat-messages";
const CONVERSATION_ID_KEY = "ai-personal-ceo-conversation-id";
const MAX_SAVED_MESSAGES = 100;

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
      return parsedMessages.slice(-MAX_SAVED_MESSAGES);
    }
  } catch (error) {
    console.warn("Unable to restore saved chat history.", error);
  }

  return [WELCOME_MESSAGE];
}

function createConversationId() {
  return window.crypto.randomUUID();
}

function loadConversationId() {
  try {
    const stored = window.localStorage.getItem(CONVERSATION_ID_KEY);
    if (stored) {
      return stored;
    }
  } catch (error) {
    console.warn("Unable to restore the saved conversation.", error);
  }

  return createConversationId();
}

function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState(loadChatMessages);
  const [loading, setLoading] = useState(false);
  const [quickCreateType, setQuickCreateType] = useState(null);
  const [conversationId, setConversationId] = useState(loadConversationId);

  useEffect(() => {
    try {
      window.localStorage.setItem(
        CHAT_STORAGE_KEY,
        JSON.stringify(messages.slice(-MAX_SAVED_MESSAGES))
      );
    } catch (error) {
      console.error("Unable to save chat history.", error);
    }
  }, [messages]);

  useEffect(() => {
    try {
      window.localStorage.setItem(CONVERSATION_ID_KEY, conversationId);
    } catch (error) {
      console.error("Unable to save the conversation.", error);
    }
  }, [conversationId]);

  const sendChatMessage = async (text) => {
    const trimmedMessage = text.trim();
    if (!trimmedMessage || loading) {
      return;
    }

    const timestamp = Date.now();
    setMessages((currentMessages) => [
      ...currentMessages,
      {
        id: `${timestamp}-user`,
        role: "user",
        content: trimmedMessage,
        intent: null,
        task: null,
        event: null,
      },
    ]);
    setInput("");
    setLoading(true);

    try {
      const response = await sendMessage(trimmedMessage, conversationId);
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `${Date.now()}-assistant`,
          role: "assistant",
          content: response.message,
          intent: response.intent || null,
          task: response.task || null,
          event: response.event || null,
        },
      ]);
    } catch (error) {
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `${Date.now()}-error`,
          role: "assistant",
          content:
            "I couldn't connect to the AI service.\n\n" +
            (error.message || "Please make sure the AI service is running."),
          intent: null,
          task: null,
          event: null,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await sendChatMessage(input);
  };

  const runQuickAction = async (text) => {
    if (!loading) {
      await sendChatMessage(text);
    }
  };

  const startNewChat = () => {
    setMessages([WELCOME_MESSAGE]);
    setConversationId(createConversationId());
  };

  return (
    <main className="chat-page">
      <header className="chat-header">
        <div>
          <h2>AI Personal Manager</h2>
          <p>Manage your tasks and schedule using natural language.</p>
        </div>
        <div className="ai-status">
          <span className="online-indicator" />
          AI Service
        </div>
        <button
          type="button"
          className="cancel-button"
          onClick={startNewChat}
          disabled={loading}
        >
          New chat
        </button>
      </header>

      <section className="chat-content">
        <div className="messages-container">
          {messages.map((item) => (
            <ChatMessage
              key={item.id}
              role={item.role}
              content={item.content}
              intent={item.intent}
              task={item.task}
              event={item.event}
            />
          ))}

          {loading && (
            <div className="message-row message-row-ai">
              <div className="message-bubble ai-message">
                <div className="message-label">AI Personal Manager</div>
                <div className="typing-indicator">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="suggestions">
        <button
          type="button"
          disabled={loading}
          onClick={() => runQuickAction("What should I focus on today?")}
        >
          ✦ Plan my day
        </button>
        <button
          type="button"
          disabled={loading}
          onClick={() => runQuickAction("What do I have tomorrow?")}
        >
          ◷ Tomorrow
        </button>
        <button
          type="button"
          disabled={loading}
          onClick={() => setQuickCreateType("task")}
        >
          + New task
        </button>
        <button
          type="button"
          disabled={loading}
          onClick={() => setQuickCreateType("event")}
        >
          + New event
        </button>
      </section>

      <form className="chat-input-container" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Ask your AI Personal Manager..."
          value={input}
          onChange={(event) => setInput(event.target.value)}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? "Thinking..." : "Send"}
        </button>
      </form>

      <QuickCreateModal
        open={quickCreateType !== null}
        type={quickCreateType}
        loading={loading}
        onClose={() => {
          if (!loading) {
            setQuickCreateType(null);
          }
        }}
        onSubmit={async (prompt) => {
          setQuickCreateType(null);
          await sendChatMessage(prompt);
        }}
      />
    </main>
  );
}

export default ChatPage;
