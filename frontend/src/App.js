import React, { useEffect, useState } from 'react';
import { ConfigProvider, theme } from 'antd';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Files from './pages/Files';
import AdminDashboard from './pages/AdminDashboard';
import AuthHandler from './components/AuthHandler';
import './App.css';
import PublicSharePage from "./pages/ShareFilePage";
import apiClient from './services/apiClient';
import authService from './services/authService';
import { Helmet, HelmetProvider } from 'react-helmet-async';
import Icon from './assets/Icon.png';

function App() {
    const [isDarkMode, setIsDarkMode] = useState(() => {
        const savedTheme = localStorage.getItem('isDarkMode');
        return savedTheme ? JSON.parse(savedTheme) : true;
    });
    const [user, setUser] = useState(null);

    const toggleTheme = () => {
        setIsDarkMode((prev) => {
            const newTheme = !prev;
            localStorage.setItem('isDarkMode', JSON.stringify(newTheme));
            return newTheme;
        });
    };

    useEffect(() => {
        const body = document.body;
        if (isDarkMode) {
            body.classList.add('dark-mode');
            document.documentElement.style.setProperty('--background-color', '#333');
            document.documentElement.style.setProperty('--text-color', '#fff');
        } else {
            body.classList.remove('dark-mode');
            document.documentElement.style.setProperty('--background-color', '#fff');
            document.documentElement.style.setProperty('--text-color', '#000');
        }
    }, [isDarkMode]);

    useEffect(() => {
        // Only fetch user data if authenticated
        if (authService.isAuthenticated()) {
            apiClient.get('/jwt/validate')
                .then(response => {
                    if (response.data.isAuthenticated) {
                        console.log("User data from validate:", response.data.user);
                        setUser(response.data.user);
                    } else {
                        authService.clearTokens();
                    }
                }).catch(err => {
                console.error(err);
                authService.clearTokens();
            });
        }
    }, []);

    return (
        <HelmetProvider>
            <Helmet>
                <link rel="icon" type="image/png" href={Icon} sizes="32x32" />
            </Helmet>
            <ConfigProvider
                theme={{
                    algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
                    token: {
                        colorPrimary: isDarkMode ? '#00b96b' : '#1677ff',
                        borderRadius: 2,
                    },
                }}
            >
                <Router>
                    <Routes>
                        <Route path="/" element={<Login isDarkMode={isDarkMode}/>} />
                        <Route path="/auth" element={<AuthHandler />} />
                        <Route
                            path="/files"
                            element={<Files toggleTheme={toggleTheme} isDarkMode={isDarkMode} user={user} />}
                        />
                        <Route
                            path="/admin"
                            element={<AdminDashboard toggleTheme={toggleTheme} isDarkMode={isDarkMode} user={user} />}
                        />
                        <Route path="/share/:shareKey" element={<PublicSharePage />} />
                    </Routes>
                </Router>
            </ConfigProvider>
        </HelmetProvider>
    );
}

export default App;