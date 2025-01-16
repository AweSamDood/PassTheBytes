import React from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from "../services/apiClient";
import '../css/NavBar.css';

const Navbar = ({ toggleTheme, isDarkMode, user }) => {
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
            <div className="brand" onClick={() => navigate('/files')}>PassTheBytes</div>
            <div>
                {user && user.admin && (
                    <button className="adminButton" onClick={() => navigate('/admin')}>
                        <span className="adminButtonText">Admin Dashboard</span>
                    </button>
                )}
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