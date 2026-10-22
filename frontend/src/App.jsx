import {
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router";
import SchedulePage from "./pages/SchedulePage";
import Sidebar from "./components/Sidebar";
import EventsPage from "./pages/EventsPage";
import ChatPage from "./pages/ChatPage";
import DashboardPage from "./pages/DashboardPage";
import TasksPage from "./pages/TasksPage";


function App() {
  const location = useLocation();

  return (
    <div className="app">

      <Sidebar />

      <div
        style={{
          display:
            location.pathname === "/chat"
              ? "contents"
              : "none",
        }}
      >
        <ChatPage />
      </div>

      <Routes>

        <Route
          path="/"
          element={
            <Navigate
              to="/dashboard"
              replace
            />
          }
        />

        <Route
          path="/dashboard"
          element={<DashboardPage />}
        />

        <Route
          path="/chat"
          element={null}
        />

        <Route
          path="/tasks"
          element={<TasksPage />}
        />

        <Route
          path="*"
          element={
            <Navigate
              to="/dashboard"
              replace
            />
          }
        />

          <Route
            path="/events"
            element={<EventsPage />}
          />

          <Route
            path="/schedule"
            element={<SchedulePage />}
          />

      </Routes>

    </div>
  );
}


export default App;