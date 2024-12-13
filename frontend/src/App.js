import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'; // Import these
import Login from './pages/Login';
import './App.css';
import Files from "./pages/Files";

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Login />} />
                <Route path="/files" element={<Files />} />
            </Routes>
        </Router>
    );
}

export default App;
