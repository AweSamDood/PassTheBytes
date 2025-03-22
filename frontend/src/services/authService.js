import apiClient from './apiClient';
import axios from 'axios';

const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

const authService = {
    // Set tokens in localStorage
    setTokens: (accessToken, refreshToken) => {
        localStorage.setItem(TOKEN_KEY, accessToken);
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    },

    // Get tokens from localStorage
    getAccessToken: () => localStorage.getItem(TOKEN_KEY),
    getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),

    // Remove tokens from localStorage
    clearTokens: () => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
    },

    // Check if user is authenticated
    isAuthenticated: () => {
        return !!localStorage.getItem(TOKEN_KEY);
    },

    // Validate the token
    validateToken: async () => {
        try {
            const response = await apiClient.get('/jwt/validate');
            return response.data.isAuthenticated;
        } catch (error) {
            return false;
        }
    },

    // Refresh the access token
    refreshToken: async () => {
        const refreshToken = authService.getRefreshToken();
        if (!refreshToken) {
            return false;
        }

        try {
            const response = await apiClient.post('/jwt/refresh', {
                refresh_token: refreshToken
            });

            if (response.data.access_token) {
                localStorage.setItem(TOKEN_KEY, response.data.access_token);
                return true;
            }
            return false;
        } catch (error) {
            authService.clearTokens();
            return false;
        }
    },

    // Login
    login: async (signal) => {
        try {
            const response = await apiClient.get('/jwt/login', { signal });
            return response.data.authorization_url;
        } catch (error) {
            // Don't log aborted requests as errors
            if (!axios.isCancel(error)) {
                console.error('Login error:', error);
            }
            throw error;
        }
    },

    // Logout
    logout: () => {
        authService.clearTokens();
    }
};

export default authService;