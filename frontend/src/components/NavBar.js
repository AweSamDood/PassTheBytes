import React from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from "../services/apiClient";
import '../css/NavBar.css';

const Navbar = ({ toggleTheme, isDarkMode, fetchFiles }) => {
    const navigate = useNavigate();
    const handleLogout = () => {
        apiClient.post('/logout')
            .then(() => {
                navigate('/'); // Redirect to login page
            })
            .catch((error) => console.error('Error logging out:', error));
    };
    return (
        <nav className="navbar">
            <div className="brand" onClick={() => fetchFiles(null)}>PassTheBytes</div>
            <div>
                <button className="toggleButton" onClick={toggleTheme}>
                    {isDarkMode ? 'Light Theme' : 'Dark Theme'}
                </button>
                <button className="logoutButton" onClick={handleLogout}>
                    Logout
                </button>
            </div>
        </nav>
    );
};

export default Navbar;