import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../services/apiClient';
import { DiscordLoginButton } from 'react-social-login-buttons';
import { Helmet } from 'react-helmet-async';
import '../css/Login.css';
import Logo from "../assets/Logo.png";

const Login = ({ isDarkMode }) => {
    const [authUrl, setAuthUrl] = useState(null);
    const navigate = useNavigate();

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
                    {authUrl ? (
                        <DiscordLoginButton onClick={handleLogin}/>
                    ) : (
                        <p>Loading...</p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Login;