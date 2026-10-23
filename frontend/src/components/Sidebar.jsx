import {
  useEffect,
  useState,
} from "react";

import {
  NavLink,
} from "react-router";

import {
  getServiceStatus,
} from "../services/statusApi";


const offlineStatus = {
  overall: "OFFLINE",

  services: {
    ai_service: {
      online: false,
    },

    backend: {
      online: false,
    },

    ollama: {
      online: false,
      model_available: false,
      model: "llama3.2:3b",
    },
  },
};


function StatusItem({
  name,
  online,
}) {
  return (
    <div className="service-status-row">

      <span
        className={
          online
            ? "service-dot online"
            : "service-dot offline"
        }
      />

      <span className="service-name">
        {name}
      </span>

      <span
        className={
          online
            ? "service-state online-text"
            : "service-state offline-text"
        }
      >
        {online
          ? "Online"
          : "Offline"}
      </span>

    </div>
  );
}


function Sidebar() {
  const [
    status,
    setStatus,
  ] = useState(offlineStatus);

  const [
    checking,
    setChecking,
  ] = useState(true);




  const loadStatus = async () => {
    try {
      const data =
        await getServiceStatus();

      setStatus(data);

    } catch {
      setStatus(
        offlineStatus
      );

    } finally {
      setChecking(false);
    }
  };


  useEffect(() => {
    loadStatus();

    const interval =
      setInterval(
        loadStatus,
        15000
      );

    return () =>
      clearInterval(interval);
  }, []);


  const services =
    status.services ||
    offlineStatus.services;


  const overallOnline =
    services.ai_service?.online &&
    services.backend?.online &&
    services.ollama?.online;


  return (
    <aside className="sidebar">

      {/* =====================================================
          BRAND
          ===================================================== */}

      <div className="brand">

        <div className="brand-logo">
          AI
        </div>

        <div>

          <h1>
            Personal Manager
          </h1>

          <p>
            AI-powered productivity
          </p>

        </div>

      </div>


      {/* =====================================================
          NAVIGATION
          ===================================================== */}

      <nav className="navigation">

        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            isActive
              ? "nav-item active"
              : "nav-item"
          }
        >
          <span className="nav-icon">
            ▦
          </span>

          Dashboard
        </NavLink>


        <NavLink
          to="/chat"
          className={({ isActive }) =>
            isActive
              ? "nav-item active"
              : "nav-item"
          }
        >
          <span className="nav-icon">
            ✦
          </span>

          AI Chat
        </NavLink>


        <NavLink
          to="/tasks"
          className={({ isActive }) =>
            isActive
              ? "nav-item active"
              : "nav-item"
          }
        >
          <span className="nav-icon">
            ✓
          </span>

          Tasks
        </NavLink>


        <NavLink
          to="/events"
          className={({ isActive }) =>
            isActive
              ? "nav-item active"
              : "nav-item"
          }
        >
          <span className="nav-icon">
            ◷
          </span>

          Events
        </NavLink>


        <NavLink
          to="/schedule"
          className={({ isActive }) =>
            isActive
              ? "nav-item active"
              : "nav-item"
          }
        >
          <span className="nav-icon">
            ▤
          </span>

          Schedule
        </NavLink>

      </nav>


      {/* =====================================================
          REAL SERVICE STATUS
          ===================================================== */}

      <div className="sidebar-footer service-panel">

        <div className="service-panel-header">

          <div
            className={
              overallOnline
                ? "status-dot"
                : "status-dot status-offline"
            }
          />

          <div>

            <strong>
              {
                checking
                  ? "Checking Services..."
                  : overallOnline
                  ? "Local Services"
                  : "Service Issue"
              }
            </strong>

            <span>
              System status
            </span>

          </div>

        </div>


        <div className="service-status-list">

          <StatusItem
            name="AI Service"
            online={
              services.ai_service
                ?.online
            }
          />

          <StatusItem
            name="Backend"
            online={
              services.backend
                ?.online
            }
          />

          <StatusItem
            name="Ollama"
            online={
              services.ollama
                ?.online
            }
          />

        </div>


        <div className="model-status">

          <span>
            Model
          </span>

          <strong>
            {
              services.ollama
                ?.model ||
              "llama3.2:3b"
            }
          </strong>


          {services.ollama
            ?.online && (

            <span
              className={
                services.ollama
                  ?.model_available
                  ? "model-ready"
                  : "model-missing"
              }
            >
              {
                services.ollama
                  ?.model_available
                  ? "Ready"
                  : "Not found"
              }
            </span>

          )}

        </div>

      </div>

    </aside>
  );
}


export default Sidebar;