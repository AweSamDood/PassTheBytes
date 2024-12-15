import React from 'react';
import {Button, Modal, message, Popconfirm} from 'antd';
import {DownloadOutlined, DeleteOutlined} from '@ant-design/icons';
import apiClient from '../services/apiClient';

const FileItem = ({record, onDirectoryClick, onUpdate}) => {
    const isDirectory = record.isDirectory;

    const downloadFile = (fileId) => {
        apiClient.get(`/download/${fileId}`, {responseType: 'blob'})
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
    return (
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <div>
                {isDirectory ? (
                    <a onClick={() => onDirectoryClick(record.id)}>{record.name}</a>
                ) : (
                    record.name
                )}
            </div>
            <div>
                {record.size ? `${(record.size / 1024 / 1024).toFixed(2)} MB` : '-'}
            </div>
            <div>
                {!isDirectory && (
                    <>
                        <Button
                            icon={<DownloadOutlined/>}
                            onClick={() => downloadFile(record.id)}
                            style={{marginRight: 8}}
                        />
                        <Popconfirm
                            title="Are you sure you want to delete this file?"
                            onConfirm={() => confirmDelete(record.id)}
                            okText="Yes"
                            cancelText="No"
                        >
                            <Button
                                icon={<DeleteOutlined/>}
                                danger
                            />
                        </Popconfirm>
                    </>
                )}
            </div>
        </div>
    );
};

export default FileItem;
