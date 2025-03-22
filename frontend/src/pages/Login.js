import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DiscordLoginButton } from 'react-social-login-buttons';
import { Helmet } from 'react-helmet-async';
import '../css/Login.css';
import Logo from "../assets/Logo.png";
import authService from '../services/authService';

const Login = ({ isDarkMode }) => {
    const [authUrl, setAuthUrl] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        let isMounted = true;
        const controller = new AbortController();

        const init = async () => {
            // Set loading state first
            setLoading(true);

            try {
                // Check if already authenticated
                if (authService.isAuthenticated()) {
                    const isValid = await authService.validateToken();
                    if (isMounted) {
                        if (isValid) {
                            navigate('/files');
                            return;
                        } else {
                            // Token invalid, clear it
                            authService.clearTokens();
                        }
                    }
                }

                // Fetch login URL with abort signal to prevent duplicate requests
                if (isMounted) {
                    const url = await authService.login();
                    setAuthUrl(url);
                }
            } catch (err) {
                if (isMounted) {
                    console.error("Login initialization error:", err);
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };

        // Run once
        init();

        return () => {
            isMounted = false;
            controller.abort();
        };
    }, [navigate]);

    const handleLogin = () => {
        if (authUrl) {
            window.location.href = authUrl; // Redirect to Discord OAuth
        }
    };

    return (
        <div className="main-login">
            <Helmet>
                <title>Login | PassTheBytes</title>
                <meta
                    name="description"
                    content="Log in to PassTheBytes using Discord. Secure and private access to your personal file-sharing platform."
                />
                <meta property="og:title" content="Login | PassTheBytes" />
                <meta
                    property="og:description"
                    content="Log in to PassTheBytes using Discord. Secure and private access to your personal file-sharing platform."
                />
            </Helmet>
            <div className={`login-container ${isDarkMode ? '' : 'light-mode'}`}>
                <div>
                    <img src={Logo} alt="Logo" className="login-logo"/>
                </div>
                <div className="logo-buttons">
                    {loading ? (
                        <p>Loading...</p>
                    ) : authUrl ? (
                        <DiscordLoginButton onClick={handleLogin}/>
                    ) : (
                        <p>Unable to connect to authentication service.</p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Login;