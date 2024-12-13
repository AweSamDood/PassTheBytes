import React from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../services/apiClient';

const Navbar = () => {
    const navigate = useNavigate();

    const handleLogout = () => {
        apiClient.post('/api/logout')
            .then(() => {
                navigate('/'); // Redirect to login page
            })
            .catch((error) => console.error('Error logging out:', error));
    };

    return (
        <nav style={styles.navbar}>
            <div style={styles.brand}>PassTheBytes</div>
            <button style={styles.logoutButton} onClick={handleLogout}>Logout</button>
        </nav>
    );
};

const styles = {
    navbar: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 20px',
        backgroundColor: '#333',
        color: '#fff',
        boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)',
    },
    brand: {
        fontSize: '1.5rem',
        fontWeight: 'bold',
    },
    logoutButton: {
        padding: '8px 16px',
        backgroundColor: '#ff4d4f',
        color: '#fff',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
    },
};

export default Navbar;
