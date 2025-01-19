import React, { useEffect, useState, useRef } from 'react';
import Navbar from '../components/NavBar';
import '../css/AdminDashboard.css';
import { Line } from '@ant-design/plots';
import apiClient from "../services/apiClient";
import { Helmet} from "react-helmet-async";

const AdminDashboard = ({ toggleTheme, isDarkMode, user }) => {
    const [performanceData, setPerformanceData] = useState([]);
    const intervalRef = useRef(null);

    const fetchPerformanceInfo = () => {
        const url = '/services/server_info';
        apiClient
            .get(url)
            .then((response) => {
                setPerformanceData((prevData) => {
                    const newData = [...prevData, response.data];
                    return newData.slice(-60); // Keep only the last 60 entries
                });
            })
            .catch((err) => console.error(err));
    };

    useEffect(() => {
        intervalRef.current = setInterval(fetchPerformanceInfo, 1000);

        return () => {
            clearInterval(intervalRef.current);
        };
    }, []);

    const renderThreadCharts = () => {
        if (performanceData.length === 0) return <p>Loading...</p>;

        const threadData = performanceData.flatMap((entry, index) =>
            entry.quicklook.percpu.map((thread, threadIndex) => ({
                time: index,
                cpu: thread.total,
                thread: `Thread ${threadIndex + 1}`,
                threadIndex: threadIndex
            }))
        );

        const threadCharts = Array.from({ length: 8 }, (_, threadIndex) => {
            const data = threadData.filter(d => d.threadIndex === threadIndex);
            const config = {
                data: data,
                xField: 'time',
                yField: 'cpu',
                seriesField: 'thread',
                smooth: true,
                height: 200,
                yAxis: {
                    min: 0,
                    max: 100,
                    label: {
                        formatter: (v) => `${v}%` // Optional: Appends '%' to the values
                    },
                },
                tooltip: {
                    showMarkers: false,
                },
                animation: {
                    appear: {
                        animation: 'path-in',
                        duration: 1000,
                    },
                },
            };

            return (
                <div className="thread-chart" key={threadIndex}>
                    <Line {...config} />
                </div>
            );
        });

        return <div className="thread-grid">{threadCharts}</div>;
    };


    return (
        <div>
            <Helmet>
                <title>Admin | PassTheBytes</title>
                <meta name="description" content="Monitor system performance, manage user activity, and ensure server readiness for maintenance on PassTheBytes." />
                <meta property="og:title" content="Admin | PassTheBytes" />
                <meta property="og:description" content="Monitor system performance, manage user activity, and ensure server readiness for maintenance on PassTheBytes." />
                {/* TODO <meta property="og:image" content="https://yourwebsite.com/placeholder-icon.png" />*/}
            </Helmet>
            <Navbar toggleTheme={toggleTheme} isDarkMode={isDarkMode} user={user} />
            <div className={`admin-dashboard-content ${isDarkMode ? 'dark-mode' : ''}`}>
                <h1>Admin Dashboard</h1>
                <div className="performance-section">
                    <h2>Thread Performance</h2>
                    {renderThreadCharts()}
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
