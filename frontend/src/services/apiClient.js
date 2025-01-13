import axios from 'axios';

const apiClient = axios.create({
    baseURL: process.env.REACT_APP_API_BASE_URL || 'https://localhost:5000/api',
    withCredentials: true,
});


export default apiClient;
