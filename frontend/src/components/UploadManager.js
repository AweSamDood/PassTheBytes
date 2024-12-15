import React, { useState, useRef, useEffect } from 'react';
import { Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import axios from 'axios';
import apiClient from '../services/apiClient';

const { Dragger } = Upload;
const CHUNK_SIZE = 4 * 1024 * 1024; // 4 MB
const MAX_UPLOAD_FILES = 10;
const MAX_CONCURRENT_UPLOADS = 4;

const UploadManager = ({ currentDirId, onUploadComplete }) => {
    const [uploadingFiles, setUploadingFiles] = useState([]);
    const [uploadQueue, setUploadQueue] = useState([]);
    const [activeUploads, setActiveUploads] = useState(0);
    const cancelTokenMap = useRef(new Map());

    useEffect(() => {
        dequeueUpload();
    }, [activeUploads, uploadQueue]);

    const handleUpload = async ({file, onProgress, onError, onSuccess}) => {
        const startUpload = () => {
            setActiveUploads(prev => prev + 1);
            doUpload();
        };

        const doUpload = async () => {
            const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
            const uploadId = `upload-${Date.now()}-${file.uid}`;
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
                        headers: {'Content-Type': 'multipart/form-data'},
                        cancelToken: cancelSource.token,
                        onUploadProgress: (progressEvent) => {
                            const chunkProgress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
                            const overallProgress = Math.round(((chunkIndex + chunkProgress / 100) / totalChunks) * 100);
                            onProgress({percent: overallProgress});
                        },
                    });

                    if (!response.data.success) {
                        // Backend error (e.g., file already exists)
                        message.error(`Upload failed: ${response.data.error}`);
                        onError(new Error(response.data.error));
                        cancelTokenMap.current.delete(uploadId);
                        setActiveUploads(prev => prev - 1);
                        dequeueUpload();
                        return;
                    }

                    if (chunkIndex === totalChunks - 1 && response.data.message.includes('completed')) {
                        // Upload finished
                        message.success(`${file.name} uploaded successfully.`);
                        onSuccess("ok");
                        cancelTokenMap.current.delete(uploadId);
                        setActiveUploads(prev => prev - 1);

                        // Remove from uploading files since it's done
                        setUploadingFiles(prev =>
                            prev.filter(f => f.uid !== file.uid)
                        );

                        // Trigger update in parent
                        onUploadComplete();

                        dequeueUpload();
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
                    cancelTokenMap.current.delete(uploadId);
                    setActiveUploads(prev => prev - 1);
                    dequeueUpload();
                    return;
                }
            }
        };

        if (activeUploads < MAX_CONCURRENT_UPLOADS) {
            startUpload();
        } else {
            // Enqueue the upload
            setUploadQueue(prev => [...prev, {file, onProgress, onError, onSuccess}]);
        }
    };

    const dequeueUpload = () => {
        setUploadQueue(prevQueue => {
            const queue = [...prevQueue];
            if (queue.length > 0 && activeUploads < MAX_CONCURRENT_UPLOADS) {
                const next = queue.shift();
                handleUpload(next);
            }
            return queue;
        });
    };

    const uploadProps = {
        multiple: true,
        customRequest: (options) => {
            const { file } = options;
            const currentUploadCount = uploadingFiles.length + uploadQueue.length + activeUploads;
            if (currentUploadCount >= MAX_UPLOAD_FILES) {
                message.error('You cannot upload more than 10 files at once.');
                return;
            }
            handleUpload(options);
        },
        beforeUpload: (file, fileList) => {
            if (fileList.length > 10) {
                message.error('You cannot upload more than 10 files at once.');
                return Upload.LIST_IGNORE;
            }
            // We rely on backend to reject if file already exists
            return true;
        },
        onChange(info) {
            const { fileList: newFileList } = info;
            setUploadingFiles(newFileList.map(f => ({
                ...f,
                uploadId: f.uploadId || `upload-${Date.now()}-${f.uid}`,
                percent: f.percent || 0,
                status: f.status || 'uploading',
            })));
        },
        onRemove: async (file) => {
            try {
                if (file.status !== 'done') {
                    const uploadId = file.uploadId;
                    if (uploadId) {
                        const cancelSource = cancelTokenMap.current.get(uploadId);
                        if (cancelSource) {
                            cancelSource.cancel('Upload canceled by user.');
                            await apiClient.post('/cancel_upload', {upload_id: uploadId});
                            message.info(`Upload for "${file.name}" has been cancelled.`);
                        }
                    }
                    cancelTokenMap.current.delete(file.uploadId);
                }
                // Remove from uploading list
                setUploadingFiles(prev => prev.filter(f => f.uid !== file.uid));
                return true;
            } catch (error) {
                console.error('Error removing file:', error);
                message.error(`Failed to remove file "${file.name}".`);
                return false;
            }
        },
        fileList: uploadingFiles
    };

    return (
        <Dragger {...uploadProps} style={{ marginBottom: 20, marginTop: 20 }}>
            <p className="ant-upload-drag-icon">
                <InboxOutlined/>
            </p>
            <p className="ant-upload-text">Click or drag file to this area to upload</p>
            <p className="ant-upload-hint">
                Upload files directly to the current directory.
            </p>
        </Dragger>
    );
};

export default UploadManager;
