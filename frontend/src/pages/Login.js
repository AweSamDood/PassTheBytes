import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom'; // For navigation
import apiClient from '../services/apiClient';
import { DiscordLoginButton } from 'react-social-login-buttons';

const Login = () => {
    const [authUrl, setAuthUrl] = useState(null);
    const navigate = useNavigate(); // React Router hook for redirection

    useEffect(() => {
        let isMounted = true;

        apiClient.get('/authenticated')
            .then(response => {
                if (isMounted) {
                    if (response.data.isAuthenticated) {
                        navigate('/files');
                    } else {
                        apiClient.get('/login')
                            .then(response => {
                                if (isMounted) {
                                    setAuthUrl(response.data.authorization_url);
                                }
                            })
                            .catch(err => console.error(err));
                    }
                }
            })
            .catch(err => console.error(err));

        return () => {
            isMounted = false;
        };
    }, [navigate]);

    // Redirect to Discord login when user clicks
    const handleLogin = () => {
        if (authUrl) {
            window.location.href = authUrl; // Redirect to Discord OAuth
        }
    };

    return (
        <div style={styles.login}>
            <h1>PassTheBytes</h1>
            {authUrl ? (
                <DiscordLoginButton onClick={handleLogin} />
            ) : (
                <p>Loading...</p>
            )}
        </div>
    );
};

const styles = {
    login: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        maxWidth: '250px',
        margin: '0 auto',
        textAlign: 'center',
    },
};

export default Login;