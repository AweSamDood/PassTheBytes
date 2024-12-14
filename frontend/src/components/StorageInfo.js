import React from 'react';

const StorageInfo = ({user}) => {
    if (!user) return null;
    const usedMB = (user.used_space / 1024 / 1024)
    const usedGB = (user.used_space / 1024 / 1024 / 1024)
    const quotaMB = (user.quota / 1024 / 1024)
    const quotaGB = (user.quota / 1024 / 1024 / 1024)
    const used = usedGB >= 1 ? `${usedGB.toFixed(2)} GB` : `${usedMB.toFixed(2)} MB`
    const quota = quotaGB >= 1 ? `${quotaGB.toFixed(2)} GB` : `${quotaMB.toFixed(2)} MB`
    return (
        <p>
            <strong>Storage Used:</strong> {used} / {quota}
        </p>
    );


}

export default StorageInfo;
