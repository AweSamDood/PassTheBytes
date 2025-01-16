import React, { useEffect, useState } from 'react';
import { ConfigProvider, theme } from 'antd';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Files from './pages/Files';
import './App.css';
import PublicSharePage from "./pages/ShareFilePage";

function App() {
    const [isDarkMode, setIsDarkMode] = useState(() => {
        // Retrieve the theme preference from localStorage
        const savedTheme = localStorage.getItem('isDarkMode');
        return savedTheme ? JSON.parse(savedTheme) : false;
    });

    const toggleTheme = () => {
        setIsDarkMode((prev) => {
            const newTheme = !prev;
            // Save the theme preference to localStorage
            localStorage.setItem('isDarkMode', JSON.stringify(newTheme));
            return newTheme;
        });
    };

    useEffect(() => {
        const body = document.body;
        if (isDarkMode) {
            body.classList.add('dark-mode');
        } else {
            body.classList.remove('dark-mode');
        }
    }, [isDarkMode]);

    return (
        <ConfigProvider
            theme={{
                algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
                token: {
                    colorPrimary: isDarkMode ? '#00b96b' : '#1677ff',
                    borderRadius: 2,
                    // Add other tokens as needed
                },
            }}
        >
            <Router>
                <Routes>
                    <Route path="/" element={<Login />} />
                    <Route
                        path="/files"
                        element={<Files toggleTheme={toggleTheme} isDarkMode={isDarkMode} />}
                    />
                    <Route path="/share/:shareKey" element={<PublicSharePage />} />
                </Routes>
            </Router>
        </ConfigProvider>
    );
}

export default App;