import React from 'react';
import { Button } from 'antd';

const FileItem = ({ record, onDirectoryClick, onDownload, onDelete }) => {
    const isDirectory = record.isDirectory;

    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
                        <Button onClick={() => onDownload(record.id)} style={{ marginRight: 8 }}>
                            Download
                        </Button>
                        <Button onClick={() => onDelete(record.id)} danger>
                            Delete
                        </Button>
                    </>
                )}
            </div>
        </div>
    );
};

export default FileItem;
