import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Input, Button, message } from 'antd';
import apiClient from '../services/apiClient';

const PublicSharePage = () => {
    const { shareKey } = useParams();
    const [filename, setFilename] = useState('');
    const [needsPassword, setNeedsPassword] = useState(false);
    const [password, setPassword] = useState('');

    useEffect(() => {
        apiClient.get(`/share/s/${shareKey}`)
            .then(res => {
                setFilename(res.data.filename);
                setNeedsPassword(res.data.needs_password);
            })
            .catch(err => {
                console.error(err);
                message.error(err.response?.data || 'Share not found or expired');
            });
    }, [shareKey]);

    const downloadFile = () => {
        apiClient.post(`/share/s/${shareKey}/download`, { password }, { responseType: 'blob' })
            .then(response => {
                let filenameHeader = response.headers['x-filename'];
                if (!filenameHeader) {
                    const disposition = response.headers['content-disposition'];
                    if (disposition && disposition.indexOf('filename=') !== -1) {
                        filenameHeader = disposition.split('filename=')[1].replace(/"/g, '');
                    } else {
                        filenameHeader = filename;
                    }
                }
                const url = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', filenameHeader);
                document.body.appendChild(link);
                link.click();
                link.remove();
            })
            .catch(err => {
                console.error(err);
                if (err.response?.status === 403) {
                    message.error('Invalid password!');
                } else {
                    message.error('Failed to download the file');
                }
            });
    };

    return (
        <div style={{ margin: 20 }}>
            <h2>File Share</h2>
            {filename ? <p>Filename: {filename}</p> : <p>No file info found.</p>}
            {needsPassword && (
                <div style={{ marginBottom: 16 }}>
                    <Input.Password
                        placeholder="Enter password"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        style={{ width: '300px' }}
                    />
                </div>
            )}
            <Button type="primary" onClick={downloadFile}>
                Download
            </Button>
        </div>
    );
};

export default PublicSharePage;
