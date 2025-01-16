import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Upload, message, Button, Space } from 'antd';
import { InboxOutlined, CloseCircleOutlined } from '@ant-design/icons';
import axios from 'axios';
import apiClient from '../services/apiClient';

const { Dragger } = Upload;

// Configuration
const CHUNK_SIZE = 4 * 1024 * 1024; // 4 MB
const MAX_UPLOAD_FILES = 200;       // Maximum files allowed in total

/**
 * Single-concurrency chunked-uploader:
 * - Only one file uploads at a time.
 * - We do NOT remove the file from the list upon success;
 *   instead we set `status: 'done'`.
 */
const UploadManager = ({ currentDirId, onUploadComplete }) => {
    const [fileList, setFileList] = useState([]);
    const [uploadQueue, setUploadQueue] = useState([]);
    const [isUploading, setIsUploading] = useState(false);

    // For cancel logic
    const cancelTokenMap = useRef(new Map());
    const currentUploadIdRef = useRef(null);

    // ------------------------------
    // 1) Actually upload the file (chunk by chunk)
    // ------------------------------
    const uploadFile = useCallback(async (uploadItem) => {
        const { file, onProgress, onError, onSuccess } = uploadItem;

        setIsUploading(true);

        // Prepare chunk info
        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
        const uploadId = file.uid;
        currentUploadIdRef.current = uploadId;

        // Create an axios CancelToken for this file
        const cancelSource = axios.CancelToken.source();
        cancelTokenMap.current.set(uploadId, cancelSource);

        let successful = false;

        try {
            // Loop through chunks
            for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
                // If canceled mid-way, stop
                if (!cancelTokenMap.current.has(uploadId)) {
                    throw new Error('Upload canceled');
                }

                // Create chunk
                const start = chunkIndex * CHUNK_SIZE;
                const end = Math.min(file.size, start + CHUNK_SIZE);
                const chunkBlob = file.slice(start, end);

                // FormData
                const formData = new FormData();
                formData.append('chunk', chunkBlob);
                formData.append('fileName', file.name);
                formData.append('chunkIndex', chunkIndex);
                formData.append('totalChunks', totalChunks);
                formData.append('uploadId', uploadId);
                formData.append('fileSize', file.size);
                formData.append('directoryId', currentDirId || '');

                // Send chunk
                const response = await apiClient.post('/upload_chunk', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                    cancelToken: cancelSource.token,
                    onUploadProgress: (progressEvent) => {
                        const chunkProgress = Math.round(
                            (progressEvent.loaded / progressEvent.total) * 100
                        );
                        const overallProgress = Math.round(
                            ((chunkIndex + chunkProgress / 100) / totalChunks) * 100
                        );

                        // Update antd's progress
                        onProgress({ percent: overallProgress });

                        // Update fileList's progress
                        setFileList((prev) =>
                            prev.map((f) =>
                                f.uid === file.uid
                                    ? { ...f, status: 'uploading', percent: overallProgress }
                                    : f
                            )
                        );
                    },
                });

                if (!response.data.success) {
                    // Could be 409 or something else
                    onError(new Error(response.data.error || 'Upload error'));
                    message.error(`Upload failed: ${response.data.error}`);
                    throw new Error(response.data.error);
                }

                // If last chunk => success
                if (
                    chunkIndex === totalChunks - 1 &&
                    response.data.message?.includes('completed')
                ) {
                    onSuccess('ok');
                    message.success(`${file.name} uploaded successfully.`);
                    successful = true;
                    onUploadComplete?.();
                }
            }
        } catch (err) {
            if (axios.isCancel(err) || err.message?.includes('canceled')) {
                console.log(`Canceled upload for ${file.name}`);
                message.info(`Upload canceled for ${file.name}`);
            } else {
                console.error('Chunk upload error:', err);
                onError(err);
                message.error(`Failed uploading ${file.name}`);
            }
        } finally {
            // Clean up
            cancelTokenMap.current.delete(uploadId);
            currentUploadIdRef.current = null;
            setIsUploading(false);

            // Mark the file as done or error, but do NOT remove it from the list
            setFileList((prev) =>
                prev.map((f) => {
                    if (f.uid !== file.uid) return f;
                    return successful
                        ? { ...f, status: 'done', percent: 100 }
                        : { ...f, status: 'error', percent: 0 };
                })
            );

            // Move on to next file
            startNextUpload();
        }
    }, [currentDirId, onUploadComplete]);

    // ------------------------------
    // 2) Start next file if not busy
    // ------------------------------
    const startNextUpload = useCallback(() => {
        if (isUploading) return;
        if (uploadQueue.length === 0) return;

        const [nextItem, ...rest] = uploadQueue;
        setUploadQueue(rest);
        uploadFile(nextItem);
    }, [isUploading, uploadQueue, uploadFile]);

    useEffect(() => {
        // Whenever queue changes or isUploading changes, try uploading
        if (!isUploading && uploadQueue.length > 0) {
            startNextUpload();
        }
    }, [uploadQueue, isUploading, startNextUpload]);

    // ------------------------------
    // 3) antd Upload props
    // ------------------------------
    const uploadProps = {
        multiple: true, // Let user select multiple files, but we'll do them one at a time
        customRequest: ({ file, onProgress, onError, onSuccess }) => {
            // Check if we're at the limit
            const totalCount = fileList.length + uploadQueue.length + (isUploading ? 1 : 0);
            if (totalCount >= MAX_UPLOAD_FILES) {
                message.error(`You cannot upload more than ${MAX_UPLOAD_FILES} files.`);
                return;
            }

            // Add to queue
            setUploadQueue((prev) => [
                ...prev,
                { file, onProgress, onError, onSuccess }
            ]);
        },

        onChange: (info) => {
            // Sync antd's fileList
            setFileList(info.fileList);
        },

        onRemove: async (file) => {
            try {
                if (file.status === 'uploading') {
                    // Cancel token
                    for (const [key, source] of cancelTokenMap.current.entries()) {
                        if (key.includes(file.uid)) {
                            source.cancel('Upload canceled by user.');
                            // Optionally tell backend
                            await apiClient.post('/cancel_upload', { upload_id: key }).catch(() => {});
                            break;
                        }
                    }
                }

                // Remove from queue if not started
                setUploadQueue((prev) => prev.filter((item) => item.file.uid !== file.uid));

                // antd will remove from `fileList` automatically if we return true
                return true;
            } catch (error) {
                console.error('Error removing file:', error);
                message.error(`Failed to remove ${file.name}`);
                return false;
            }
        },

        fileList
    };

    // ------------------------------
    // 4) Cancel/Remove All
    // ------------------------------
    const handleCancelAll = async () => {
        // If there's a current upload, cancel it
        const currentId = currentUploadIdRef.current;
        if (currentId && cancelTokenMap.current.has(currentId)) {
            cancelTokenMap.current.get(currentId).cancel('Canceled by user');
            cancelTokenMap.current.delete(currentId);
            await apiClient.post('/cancel_upload', { upload_id: currentId }).catch(() => {});
        }
        currentUploadIdRef.current = null;

        // Clear everything
        setFileList([]);
        setUploadQueue([]);
        setIsUploading(false);

        message.info('All uploads have been canceled and removed.');
    };

    // ------------------------------
    // 5) Render
    // ------------------------------
    return (
        <div style={{ margin: '20px 0' }}>
            <Dragger {...uploadProps}>
                <p className="ant-upload-drag-icon">
                    <InboxOutlined />
                </p>
                <p className="ant-upload-text">Click or drag files here to upload</p>
                <p className="ant-upload-hint">
                    Single file at a time (chunked). Max 15 total.
                </p>
            </Dragger>

            {fileList.length > 0 && (
                <Space style={{ marginTop: 16 }}>
                    <Button
                        onClick={handleCancelAll}
                        icon={<CloseCircleOutlined />}
                        danger
                    >
                        Cancel/Remove All
                    </Button>
                </Space>
            )}
        </div>
    );
};

export default UploadManager;
