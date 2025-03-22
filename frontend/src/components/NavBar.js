import React from 'react';
import { useNavigate } from 'react-router-dom';
import authService from "../services/authService";
import '../css/NavBar.css';
import Logo from '../assets/Logo.png';

const Navbar = ({ toggleTheme, isDarkMode, user }) => {
    const navigate = useNavigate();

    // Add debugging for user object
    console.log("NavBar - User object:", user);

    const handleLogout = () => {
        authService.logout();
        navigate('/'); // Redirect to login page
    };

    return (
        <nav className="navbar">
            <div className="brand-nav" onClick={() => navigate('/files')}>
                <img src={Logo} alt="Logo" className="logo-nav" />
            </div>
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