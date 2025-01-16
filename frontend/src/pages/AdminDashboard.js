import React, { useEffect, useState } from 'react';
import Navbar from '../components/NavBar';
import '../css/AdminDashboard.css';
import apiClient from "../services/apiClient";

const AdminDashboard = ({ toggleTheme, isDarkMode, user }) => {
    const [performanceInfo, setPerformanceInfo] = useState(null);

    const fetchPerformanceInfo = () => {
        const url = '/services/server_info';
        apiClient.get(url).then((response) => {
            console.log("response.data", response.data);
            setPerformanceInfo(response.data);
        }).catch(err => console.error(err));
    }

    useEffect(() => {
        fetchPerformanceInfo();
    }, []);

    return (
        <div>
            <Navbar toggleTheme={toggleTheme} isDarkMode={isDarkMode} user={user} />
            <div className={`admin-dashboard-content ${isDarkMode ? 'dark-mode' : ''}`}>
                <h1>Admin Dashboard</h1>
                <div className="performance-info">
                    <h2>Performance Info</h2>
                    {performanceInfo && (
                        <pre>
                            {JSON.stringify(performanceInfo, null, 2)}
                        </pre>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;