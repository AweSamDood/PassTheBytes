import React, { useEffect, useState, useRef } from 'react';
import { Table, Button, Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import axios from 'axios';
import apiClient from '../services/apiClient';
import Navbar from '../components/NavBar';

const { Dragger } = Upload;
const CHUNK_SIZE = 4 * 1024 * 1024; // 4 MB

const Files = () => {
    const [files, setFiles] = useState([]);
    const [directories, setDirectories] = useState([]);
    const [user, setUser] = useState(null);
    const [currentDirId, setCurrentDirId] = useState(null);
    const [uploadingFiles, setUploadingFiles] = useState([]);

    // Ref to store cancel tokens for each uploadId
    const cancelTokenMap = useRef(new Map());

    useEffect(() => {
        fetchFiles();
    }, []);

    const fetchFiles = (dirId = null) => {
        setCurrentDirId(dirId);
        const url = dirId ? `/files?dir_id=${dirId}` : '/files';
        apiClient.get(url)
            .then(response => {
                setFiles(response.data.files);
                setDirectories(response.data.directories);
                setUser(response.data.user);
            })
            .catch(err => console.error(err));
    };

    const deleteFile = (fileId) => {
        apiClient.delete(`/delete/${fileId}`)
            .then((response) => {
                message.success(response.data.message);
                setFiles(files.filter(file => file.id !== fileId));
            })
            .catch((error) => {
                console.error('Error deleting file:', error);
                message.error('Failed to delete the file.');
            });
    };

    const downloadFile = (fileId) => {
        apiClient.get(`/download/${fileId}`, { responseType: 'blob' })
            .then((response) => {
                let filename = response.headers['x-filename'] || 'downloaded_file';
                console.log('Filename:', filename);

                if (!filename) {
                    const disposition = response.headers['content-disposition'];
                    if (disposition && disposition.indexOf('filename=') !== -1) {
                        filename = disposition.split('filename=')[1].replace(/"/g, '');
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

    const handleUpload = async (file, onProgress, onError, onSuccess) => {
        // Check for duplicate file names, TODO - check backend for this
        const duplicate = files.find(f => f.filename === file.name);
        if (duplicate) {
            message.error(`A file named "${file.name}" already exists in this directory.`);
            onError(new Error('Duplicate file name'));
            return;
        }

        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
        const uploadId = `upload-${Date.now()}-${file.uid}`; // Unique per file

        // Create a CancelToken source and store it
        const cancelSource = axios.CancelToken.source();
        cancelTokenMap.current.set(uploadId, cancelSource);

        for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
            const start = chunkIndex * CHUNK_SIZE;
            const end = Math.min(file.size, start + CHUNK_SIZE);
            const chunk = file.slice(start, end);

            const formData = new FormData();
            formData.append('chunk', chunk);
            formData.append('fileName', file.name);
            formData.append('chunkIndex', chunkIndex);
            formData.append('totalChunks', totalChunks);
            formData.append('uploadId', uploadId);
            formData.append('fileSize', file.size);
            formData.append('directoryId', currentDirId || '');

            try {
                const response = await apiClient.post('/upload_chunk', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                    cancelToken: cancelSource.token, // Attach the cancel token
                    onUploadProgress: (progressEvent) => {
                        const chunkProgress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
                        const overallProgress = Math.round(((chunkIndex + chunkProgress / 100) / totalChunks) * 100);
                        onProgress({ percent: overallProgress });
                    },
                });

                if (!response.data.success) {
                    message.error(`Chunk ${chunkIndex + 1} failed to upload: ${response.data.error}`);
                    onError(new Error(response.data.error));
                    cancelTokenMap.current.delete(uploadId); // Clean up
                    return;
                }
            } catch (error) {
                if (axios.isCancel(error)) {
                    console.log(`Upload canceled for ${file.name}`);
                    onError(new Error('Upload canceled by user.'));
                } else {
                    console.error('Error uploading chunk:', error);
                    message.error(`Chunk ${chunkIndex + 1} upload failed.`);
                    onError(error);
                }
                cancelTokenMap.current.delete(uploadId); // Clean up
                return;
            }
        }

        // All chunks uploaded successfully
        message.success(`${file.name} uploaded successfully.`);
        onSuccess("ok");
        cancelTokenMap.current.delete(uploadId);
        // clean up uploadingFiles state
        setUploadingFiles(prev => prev.filter(f => f.uid !== file.uid));
        fetchFiles(currentDirId);
    };

    const uploadProps = {
        multiple: true,
        customRequest: ({ file, onProgress, onError, onSuccess }) => {
            // Assign a unique uploadId to each file
            file.uploadId = `upload-${Date.now()}-${file.uid}`;
            handleUpload(file, onProgress, onError, onSuccess);
        },
        beforeUpload: (file) => {
            // Prevent upload if file with same name exists
            const duplicate = files.find(f => f.filename === file.name);
            if (duplicate) {
                message.error(`A file named "${file.name}" already exists in this directory.`);
                return Upload.LIST_IGNORE;
            }
            return true;
        },
        onChange(info) {
            const { file, fileList: newFileList } = info;
            // Update uploadingFiles state
            setUploadingFiles(newFileList.map(f => ({
                ...f,
                uploadId: f.uploadId || `upload-${Date.now()}-${f.uid}`,
                percent: f.percent || 0,
                status: f.status || 'uploading',
            })));
        },
        onDrop(e) {
            console.log('Dropped files', e.dataTransfer.files);
        },
        fileList: uploadingFiles,
        onRemove: async (file) => {
            // Call the backend to cancel the upload
            try {
                const uploadId = file.uploadId;
                if (uploadId) {
                    // Cancel the Axios requests
                    const cancelSource = cancelTokenMap.current.get(uploadId);
                    if (cancelSource) {
                        cancelSource.cancel('Upload canceled by user.');
                    }

                    // Notify the backend to cancel
                    await apiClient.post('/cancel_upload', { upload_id: uploadId });

                    message.info(`Upload for "${file.name}" has been cancelled.`);
                }
                // Remove from uploadingFiles state
                setUploadingFiles(prev => prev.filter(f => f.uid !== file.uid));
                cancelTokenMap.current.delete(file.uploadId); // Clean up
                return true;
            } catch (error) {
                console.error('Error cancelling upload:', error);
                message.error(`Failed to cancel upload for "${file.name}".`);
                return false;
            }
        },
    };

    const columns = [
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            render: (text, record) => (
                record.isDirectory
                    ? <a onClick={() => fetchFiles(record.id)}>{record.name}</a>
                    : record.name
            ),
        },
        {
            title: 'Size',
            dataIndex: 'size',
            key: 'size',
            render: (size) => size ? `${(size / 1024 / 1024).toFixed(2)} MB` : '-',
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_, record) => (
                !record.isDirectory && (
                    <div>
                        <Button onClick={() => downloadFile(record.id)} style={{ marginRight: 8 }}>
                            Download
                        </Button>
                        <Button onClick={() => deleteFile(record.id)} danger>
                            Delete
                        </Button>
                    </div>
                )
            ),
        },
    ];

    const dataSource = [
        ...directories.map(dir => ({
            key: `dir-${dir.id}`,
            id: dir.id,
            name: dir.name,
            size: null,
            isDirectory: true,
        })),
        ...files.map(file => ({
            key: `file-${file.id}`,
            id: file.id,
            name: file.filename,
            size: file.filesize,
            isDirectory: false,
        })),
    ];

    return (
        <div>
            <Navbar />
            <h1>My Files</h1>
            {user && (
                <p>
                    <strong>Storage Used:</strong> {(user.used_space / 1024 / 1024).toFixed(2)} MB
                    / {(user.quota / 1024 / 1024).toFixed(2)} MB
                </p>
            )}
            <Dragger
                {...uploadProps}
                onChange={(info) => {
                    const { file, fileList: newFileList } = info;
                    setUploadingFiles(newFileList.map(f => ({
                        ...f,
                        uploadId: f.uploadId || `upload-${Date.now()}-${f.uid}`,
                        percent: f.percent || 0,
                        status: f.status || 'uploading',
                    })));
                }}
                onRemove={(file) => {
                    return uploadProps.onRemove(file);
                }}
            >
                <p className="ant-upload-drag-icon">
                    <InboxOutlined />
                </p>
                <p className="ant-upload-text">Click or drag file to this area to upload</p>
                <p className="ant-upload-hint">
                    Upload files directly to the current directory.
                </p>
            </Dragger>
            {currentDirId && (
                <Button style={{ marginTop: 20 }} onClick={() => fetchFiles(null)}>
                    Back to Root Directory
                </Button>
            )}
            <Table
                dataSource={dataSource} // Only directories and existing files
                columns={columns}
                pagination={false}
                bordered
                style={{ marginTop: 20 }}
            />
        </div>
    );
};

export default Files;
