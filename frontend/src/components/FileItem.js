import React, { useState } from 'react';
import { Button, Modal, message, Popconfirm, Input } from 'antd';
import { DownloadOutlined, DeleteOutlined, ShareAltOutlined, LinkOutlined } from '@ant-design/icons';
import apiClient from '../services/apiClient';
import '../css/FileItem.css';

const FileItem = ({ record, onDirectoryClick, onUpdate }) => {
    const [shareKey, setShareKey] = useState(record.share_key || null);
    const isShared = !!shareKey;
    const [shareModalVisible, setShareModalVisible] = useState(false);
    const [password, setPassword] = useState('');

    const downloadFile = (fileId) => {
        apiClient.get(`/download/${fileId}`, { responseType: 'blob' })
            .then((response) => {
                let filename = response.headers['x-filename'];
                if (!filename) {
                    const disposition = response.headers['content-disposition'];
                    if (disposition && disposition.indexOf('filename=') !== -1) {
                        filename = disposition.split('filename=')[1].replace(/"/g, '');
                    } else {
                        filename = 'downloaded_file';
                    }
                }

                const url = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', filename);
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
            })
            .catch((error) => {
                console.error('Error downloading file:', error);
                message.error('Failed to download the file.');
            });
    };

    const confirmDelete = (fileId) => {
        apiClient.delete(`/delete/${fileId}`)
            .then((response) => {
                message.success(response.data.message);
                onUpdate();
            })
            .catch((error) => {
                console.error('Error deleting file:', error);
                message.error('Failed to delete the file.');
            });
    };

    const showShareModal = () => {
        setShareModalVisible(true);
    };

    const handleShareOk = () => {
        apiClient.post(`/share/file/${record.id}`, { password })
            .then(res => {
                message.success(res.data.message);
                setShareKey(res.data.share_key);
                onUpdate();
            })
            .catch(err => {
                console.error(err);
                message.error(err.response?.data?.error || 'Failed to share file');
            })
            .finally(() => {
                setShareModalVisible(false);
                setPassword('');
            });
    };

    const handleShareCancel = () => {
        setShareModalVisible(false);
    };

    const revokeShare = () => {
        apiClient.post(`/share/file/${record.id}`, { revoke: true })
            .then((res) => {
                message.success(res.data.message);
                setShareKey(null);
                onUpdate();
            })
            .catch(err => {
                console.error(err);
                message.error(err.response?.data?.error || 'Failed to revoke share');
            });
    };

    const copyShareLink = () => {
        if (!shareKey) return;
        const linkToCopy = `${window.location.origin}/share/${shareKey}`;
        navigator.clipboard.writeText(linkToCopy)
            .then(() => {
                message.success('Link copied to clipboard!');
            })
            .catch(() => {
                message.error('Failed to copy link.');
            });
    };

    return (
        <div className="file-item">
            <div className="file-name-size">
                <div className="file-name">
                    {record.isDirectory ? (
                        <a onClick={() => onDirectoryClick(record.id)}>{record.name}</a>
                    ) : (
                        record.name
                    )}
                </div>
                <div className="file-size">
                    {record.size ? `${(record.size / 1024 / 1024).toFixed(2)} MB` : '-'}
                </div>
            </div>
            <div className="file-actions">
                {!record.isDirectory && (
                    <>
                        <Button
                            icon={<DownloadOutlined />}
                            onClick={() => downloadFile(record.id)}
                            style={{ marginRight: 8 }}
                        />
                        <Popconfirm
                            title="Are you sure you want to delete this file?"
                            onConfirm={() => confirmDelete(record.id)}
                            okText="Yes"
                            cancelText="No"
                        >
                            <Button icon={<DeleteOutlined />} danger style={{ marginRight: 8 }} />
                        </Popconfirm>
                        {!isShared ? (
                            <Button
                                icon={<ShareAltOutlined />}
                                onClick={showShareModal}
                            >
                                Share
                            </Button>
                        ) : (
                            <>
                                <Button
                                    icon={<LinkOutlined />}
                                    style={{ marginRight: 8 }}
                                    onClick={copyShareLink}
                                >
                                    Copy Link
                                </Button>
                                <Button
                                    icon={<ShareAltOutlined />}
                                    danger
                                    onClick={revokeShare}
                                >
                                    Revoke Share
                                </Button>
                            </>
                        )}
                    </>
                )}
            </div>
            <Modal
                title="Share File"
                open={shareModalVisible}
                onOk={handleShareOk}
                onCancel={handleShareCancel}
            >
                <p>Optionally set a password for this share link:</p>
                <Input.Password
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="Leave blank for no password"
                />
            </Modal>
        </div>
    );
};

export default FileItem;