import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom'; // For navigation
import apiClient from '../services/apiClient';

const Login = () => {
    const [authUrl, setAuthUrl] = useState(null);
    const navigate = useNavigate(); // React Router hook for redirection

    useEffect(() => {
        // Fetch the Discord login URL
        apiClient.get('/login')
            .then(response => {
                setAuthUrl(response.data.authorization_url);
            })
            .catch(err => console.error(err));
    }, []);

    useEffect(() => {
        // Check if the user is already authenticated
        apiClient.get('/authenticated') // Backend should implement this
            .then(response => {
                if (response.data.isAuthenticated) {
                    navigate('/files'); // Redirect to files page
                }
            })
            .catch(err => console.error(err));
    }, [navigate]);

    // Redirect to Discord login when user clicks
    const handleLogin = () => {
        if (authUrl) {
            window.location.href = authUrl; // Redirect to Discord OAuth
        }
    };

    return (
        <div>
            <h1>Login</h1>
            {authUrl ? (
                <button onClick={handleLogin}>Login with Discord</button>
            ) : (
                <p>Loading...</p>
            )}
        </div>
    );
};

export default Login;
