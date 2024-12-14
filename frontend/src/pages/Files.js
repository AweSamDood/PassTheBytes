import React, {useEffect, useState, useRef} from 'react';
import {Table, Button, Upload, message, Modal, Input} from 'antd';
import {InboxOutlined} from '@ant-design/icons';
import axios from 'axios';
import apiClient from '../services/apiClient';
import Navbar from '../components/NavBar';
import FileItem from '../components/FileItem';
import StorageInfo from '../components/StorageInfo';

const {Dragger} = Upload;
const CHUNK_SIZE = 4 * 1024 * 1024; // 4 MB

const Files = () => {
    const [files, setFiles] = useState([]);
    const [directories, setDirectories] = useState([]);
    const [user, setUser] = useState(null);
    const [currentDirId, setCurrentDirId] = useState(null);
    const [uploadingFiles, setUploadingFiles] = useState([]);
    const [selectedRowKeys, setSelectedRowKeys] = useState([]);
    const [isCreateDirModalVisible, setIsCreateDirModalVisible] = useState(false);
    const [newDirName, setNewDirName] = useState('');

    const cancelTokenMap = useRef(new Map());

    useEffect(() => {
        fetchFiles();
        fetchUserInfo();
    }, []);

    const fetchFiles = (dirId = null) => {
        setCurrentDirId(dirId);
        const url = dirId ? `/files?dir_id=${dirId}` : '/files';
        apiClient.get(url)
            .then(response => {
                setFiles(response.data.files);
                setDirectories(response.data.directories);
                setSelectedRowKeys([]);
            })
            .catch(err => console.error(err));
    };

    const fetchUserInfo = () => {
        const userUrl = `/user`
        apiClient.get(userUrl)
            .then(response => {
                setUser(response.data.user);
            }).catch(err => console.error(err));
    };

    const deleteFile = (fileId) => {
        apiClient.delete(`/delete/${fileId}`)
            .then((response) => {
                message.success(response.data.message);
                setFiles(files.filter(file => file.id !== fileId));
                fetchUserInfo();
            })
            .catch((error) => {
                console.error('Error deleting file:', error);
                message.error('Failed to delete the file.');
            });
    };

    const bulkDelete = () => {
        const fileIds = [];
        const dirIds = [];
        selectedRowKeys.forEach(key => {
            const [type, idStr] = key.split('-');
            const id = parseInt(idStr, 10);
            if (type === 'file') {
                fileIds.push(id);
            } else if (type === 'dir') {
                dirIds.push(id);
            }
        });

        // Send a single request to delete all selected files and directories
        apiClient.delete('/delete_multiple_items', {
            data: {
                file_ids: fileIds,
                dir_ids: dirIds
            }
        })
            .then(response => {
                message.success(response.data.message);
                fetchUserInfo();
                fetchFiles(currentDirId);
            })
            .catch(error => {
                console.error('Error deleting selected items:', error);
                message.error('Failed to delete some items.');
            })
            .finally(() => {
                setSelectedRowKeys([]);
            });
    };


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

    const handleUpload = async (file, onProgress, onError, onSuccess) => {
        const duplicate = files.find(f => f.filename === file.name);
        if (duplicate) {
            message.error(`A file named "${file.name}" already exists in this directory.`);
            onError(new Error('Duplicate file name'));
            return;
        }

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
                    message.error(`Chunk ${chunkIndex + 1} failed to upload: ${response.data.error}`);
                    onError(new Error(response.data.error));
                    cancelTokenMap.current.delete(uploadId);
                    return;
                }

                if (chunkIndex === totalChunks - 1 && response.data.message.includes('completed')) {
                    fetchUserInfo();
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
                return;
            }
        }

        message.success(`${file.name} uploaded successfully.`);
        onSuccess("ok");
        cancelTokenMap.current.delete(uploadId);
        setUploadingFiles(prev => prev.filter(f => f.uid !== file.uid));
        fetchFiles(currentDirId);
    };

    const uploadProps = {
        multiple: true,
        customRequest: ({file, onProgress, onError, onSuccess}) => {
            file.uploadId = `upload-${Date.now()}-${file.uid}`;
            handleUpload(file, onProgress, onError, onSuccess);
        },
        beforeUpload: (file) => {
            const duplicate = files.find(f => f.filename === file.name);
            if (duplicate) {
                message.error(`A file named "${file.name}" already exists in this directory.`);
                return Upload.LIST_IGNORE;
            }
            return true;
        },
        onChange(info) {
            const {fileList: newFileList} = info;
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
            try {
                const uploadId = file.uploadId;
                if (uploadId) {
                    const cancelSource = cancelTokenMap.current.get(uploadId);
                    if (cancelSource) {
                        cancelSource.cancel('Upload canceled by user.');
                    }

                    await apiClient.post('/cancel_upload', {upload_id: uploadId});
                    message.info(`Upload for "${file.name}" has been cancelled.`);
                }
                setUploadingFiles(prev => prev.filter(f => f.uid !== file.uid));
                cancelTokenMap.current.delete(file.uploadId);
                return true;
            } catch (error) {
                console.error('Error cancelling upload:', error);
                message.error(`Failed to cancel upload for "${file.name}".`);
                return false;
            }
        },
    };

    const onDirectoryClick = (dirId) => {
        fetchFiles(dirId);
    };

    const onDelete = (fileId) => {
        deleteFile(fileId);
    };

    const onDownload = (fileId) => {
        downloadFile(fileId);
    };

    const createDirectory = () => {
        if (!newDirName.trim()) {
            message.error('Directory name cannot be empty.');
            return;
        }
        apiClient.post('/create_directory', {
            name: newDirName,
            parent_id: currentDirId || null
        })
            .then(() => {
                message.success('Directory created.');
                setIsCreateDirModalVisible(false);
                setNewDirName('');
                fetchFiles(currentDirId);
            })
            .catch((err) => {
                console.error('Error creating directory:', err);
                message.error('Failed to create directory.');
            });
    };

    const columns = [
        {
            title: 'Item',
            dataIndex: 'item',
            key: 'item',
            render: (_, record) => (
                <FileItem
                    record={record}
                    onDirectoryClick={onDirectoryClick}
                    onDownload={onDownload}
                    onDelete={onDelete}
                />
            )
        }
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

    const rowSelection = {
        selectedRowKeys,
        onChange: (newSelectedRowKeys) => {
            setSelectedRowKeys(newSelectedRowKeys);
        },
    };

    return (
        <div>
            <Navbar/>
            <h1>{user ? `${user.username}'s files` : '   '}</h1>
            <StorageInfo user={user}/>

            <Dragger
                {...uploadProps}
                onChange={(info) => {
                    const {file, fileList: newFileList} = info;
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
                    <InboxOutlined/>
                </p>
                <p className="ant-upload-text">Click or drag file to this area to upload</p>
                <p className="ant-upload-hint">
                    Upload files directly to the current directory.
                </p>
            </Dragger>
            <div style={{marginBottom: 20, marginTop: 20}}>
                <Button onClick={() => setIsCreateDirModalVisible(true)} style={{marginRight: 8,}}>
                    Create New Directory
                </Button>
                {selectedRowKeys.length === 0 ? (
                    <Button disabled>
                        Delete Selected
                    </Button>
                ) : (
                    <Button onClick={bulkDelete} danger>
                        Delete Selected
                    </Button>)}
            </div>
            {currentDirId && (
                <Button style={{}} onClick={() => fetchFiles(null)}>
                    Back to Root Directory
                </Button>
            )}
            <Table
                dataSource={dataSource}
                columns={columns}
                pagination={false}
                bordered
                style={{marginTop: 20}}
                rowSelection={rowSelection}
            />

            <Modal
                title="Create New Directory"
                visible={isCreateDirModalVisible}
                onOk={createDirectory}
                onCancel={() => setIsCreateDirModalVisible(false)}
            >
                <Input
                    placeholder="Directory Name"
                    value={newDirName}
                    onChange={(e) => setNewDirName(e.target.value)}
                />
            </Modal>
        </div>
    );
};

export default Files;
