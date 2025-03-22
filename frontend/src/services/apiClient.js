import axios from 'axios';
import authService from './authService';

const apiClient = axios.create({
    baseURL: process.env.REACT_APP_API_BASE_URL || 'https://localhost:5000/api',
    withCredentials: true,
});

// Request interceptor to add Authorization header with JWT token
apiClient.interceptors.request.use(
    (config) => {
        const token = authService.getAccessToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor to handle token refresh on 401 errors
apiClient.interceptors.response.use(
    (response) => {
        return response;
    },
    async (error) => {
        const originalRequest = error.config;

        // If the error is 401 and we haven't tried to refresh the token yet
        if (error.response.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshed = await authService.refreshToken();
                if (refreshed) {
                    // Retry the original request with the new token
                    const token = authService.getAccessToken();
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                    return apiClient(originalRequest);
                }
            } catch (refreshError) {
                // If refresh token is also expired, redirect to login
                authService.clearTokens();
                window.location.href = '/';
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

export default apiClient;