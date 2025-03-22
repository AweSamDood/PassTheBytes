import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import authService from '../services/authService';
import { Spin } from 'antd';

const AuthHandler = () => {
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const processAuth = async () => {
            const queryParams = new URLSearchParams(location.search);
            const accessToken = queryParams.get('access_token');
            const refreshToken = queryParams.get('refresh_token');

            if (accessToken && refreshToken) {
                // Save tokens
                authService.setTokens(accessToken, refreshToken);

                // Redirect to files page
                navigate('/files');
            } else {
                navigate('/');
            }
        };

        processAuth();
    }, [location, navigate]);

    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
            <Spin size="large" tip="Authenticating..." />
        </div>
    );
};

export default AuthHandler;