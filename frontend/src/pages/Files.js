import React, { useEffect, useState } from 'react';
import { Table, Button, message, Modal, Input, Breadcrumb } from 'antd';
import { HomeOutlined } from '@ant-design/icons';
import { Helmet } from 'react-helmet-async';
import apiClient from '../services/apiClient';
import Navbar from '../components/NavBar';
import FileItem from '../components/FileItem';
import StorageInfo from '../components/StorageInfo';
import UploadManager from '../components/UploadManager';

const Files = ({ toggleTheme, isDarkMode, userApp }) => {
    const [files, setFiles] = useState([]);
    const [directories, setDirectories] = useState([]);
    const [user, setUser] = useState(userApp);
    const [currentDirId, setCurrentDirId] = useState(null);
    const [currentDirectory, setCurrentDirectory] = useState(null);
    const [selectedRowKeys, setSelectedRowKeys] = useState([]);
    const [isCreateDirModalVisible, setIsCreateDirModalVisible] = useState(false);
    const [newDirName, setNewDirName] = useState('');
    const [breadcrumbs, setBreadcrumbs] = useState([]);

    useEffect(() => {
        fetchFiles();
    }, []);

    const fetchFiles = (dirId = null) => {
        setCurrentDirId(dirId);
        const url = dirId ? `/files?dir_id=${dirId}` : '/files';
        apiClient.get(url)
            .then(response => {
                console.log("response.data", response.data);
                setFiles(response.data.files);
                setDirectories(response.data.directories);
                setUser(response.data.user);
                setCurrentDirectory(response.data.current_directory || null);
                setSelectedRowKeys([]);
                if (response.data.breadcrumbs) {
                    setBreadcrumbs(response.data.breadcrumbs);
                } else {
                    setBreadcrumbs([{id:null, name:'Root'}]);
                    if (currentDirectory && currentDirectory.name) {
                        setBreadcrumbs([{id:null, name:'Root'},{id:currentDirectory.id, name:currentDirectory.name}]);
                    }
                }
            })
            .catch(err => console.error(err));
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

        Modal.confirm({
            title: 'Are you sure you want to delete the selected items?',
            onOk: () => {
                apiClient.delete('/delete_multiple_items', {
                    data: {
                        file_ids: fileIds,
                        dir_ids: dirIds
                    }
                })
                    .then(response => {
                        message.success(response.data.message);
                        fetchFiles(currentDirId);
                    })
                    .catch(error => {
                        console.error('Error deleting selected items:', error);
                        message.error('Failed to delete some items.');
                    })
                    .finally(() => {
                        setSelectedRowKeys([]);
                    });
            }
        });
    };

    const bulkDownload = () => {
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

        apiClient.post('/download_multiple_items', {
            file_ids: fileIds,
            dir_ids: dirIds
        }, {responseType: 'blob'})
            .then(response => {
                let filename = response.headers['x-filename'] || 'selected_items.zip';
                const url = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', filename);
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
            })
            .catch(error => {
                console.error('Error downloading selected items:', error);
                message.error('Failed to download selected items.');
            })
            .finally(() => {
                setSelectedRowKeys([]);
            });
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
                const errorMsg = err.response.data.error;
                console.error('Error creating directory:', err);
                message.error('Failed to create directory.' + (errorMsg ? ` Reason: ${errorMsg}` : ''));
            });
    };

    const onDirectoryClick = (dirId) => {
        fetchFiles(dirId);
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
                    onUpdate={() => {
                        fetchFiles(currentDirId);
                    }}
                />
            )
        }
    ];

    const rowSelection = {
        selectedRowKeys,
        onChange: (newSelectedRowKeys) => {
            setSelectedRowKeys(newSelectedRowKeys);
        },
    };

    return (
        <div>
            <Helmet>
                <title>Files | PassTheBytes</title>
                <meta name="description" content="Access and manage your files securely on PassTheBytes. Navigate directories, upload files, and organize your storage seamlessly." />
                <meta property="og:title" content="Files | PassTheBytes" />
                <meta property="og:description" content="Access and manage your files securely on PassTheBytes." />
                {/* TODO <meta property="og:image" content="https://yourwebsite.com/placeholder-icon.png" />*/}
            </Helmet>
            <Navbar toggleTheme={toggleTheme} isDarkMode={isDarkMode} user={user} />
            <h1>{user ? `${user.username}'s files` : ' '}</h1>
            <StorageInfo user={user}/>

            <UploadManager
                currentDirId={currentDirId}
                onUploadComplete={() => {
                    fetchFiles(currentDirId);
                }}
            />

            <div style={{marginBottom: 20, marginTop: 20}}>
                <Button onClick={() => setIsCreateDirModalVisible(true)} style={{marginRight: 8}}>
                    Create New Directory
                </Button>
                {selectedRowKeys.length === 0 ? (
                    <>
                        <Button disabled style={{marginRight: 8}}>
                            Delete Selected
                        </Button>
                        <Button disabled>
                            Download Selected
                        </Button>
                    </>
                ) : (
                    <>
                        <Button onClick={bulkDelete} danger style={{marginRight: 8}}>
                            Delete Selected
                        </Button>
                        <Button onClick={bulkDownload}>
                            Download Selected
                        </Button>
                    </>
                )}
            </div>
            <Breadcrumb style={{margin: '16px 0'}} separator=">">
                {breadcrumbs.map((bc, idx) => (
                    <Breadcrumb.Item key={idx}>
                        {bc.id !== currentDirId ? (
                            <a onClick={() => fetchFiles(bc.id)}>
                                {bc.name === 'Root' ? <HomeOutlined/> : bc.name}
                            </a>
                        ) : (
                            bc.name === 'Root' ? <HomeOutlined/> : bc.name
                        )}
                    </Breadcrumb.Item>
                ))}
            </Breadcrumb>

            <Table
                dataSource={[
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
                        size: file.size,
                        isDirectory: false,
                        share_key: file.share_key,
                    }))
                ]}
                columns={columns}
                pagination={false}
                bordered
                style={{marginTop: 20}}
                rowSelection={rowSelection}
                scroll={{ y: 'calc(100vh - 400px)' }}
            />

            <Modal
                title="Create New Directory"
                open={isCreateDirModalVisible}
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