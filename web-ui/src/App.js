import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import Dashboard from './pages/Dashboard';
import Events from './pages/Events';
import Alerts from './pages/Alerts';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="nav-container">
            <div className="nav-brand">
              <h1>🛡️ Enterprise SIEM</h1>
            </div>
            <ul className="nav-menu">
              <li><Link to="/">Dashboard</Link></li>
              <li><Link to="/events">Events</Link></li>
              <li><Link to="/alerts">Alerts</Link></li>
            </ul>
          </div>
        </nav>

        <div className="content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/events" element={<Events />} />
            <Route path="/alerts" element={<Alerts />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
