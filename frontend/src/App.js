import React, { useEffect, useState } from 'react';
import { ConfigProvider, theme } from 'antd';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Files from './pages/Files';
import AdminDashboard from './pages/AdminDashboard';
import './App.css';
import PublicSharePage from "./pages/ShareFilePage";
import apiClient from './services/apiClient';

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
        apiClient.get('/user')
            .then(response => {
                setUser(response.data.user);
            }).catch(err => console.error(err));
    }, []);

    return (
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
                    <Route path="/" element={<Login />} />
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
    );
}

export default App;