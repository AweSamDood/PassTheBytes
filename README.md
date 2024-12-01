# PassTheBytes

**PassTheBytes** is a simple file-sharing and personal storage solution designed for individuals. Initially aimed at personal use, PassTheBytes will evolve to an invite-only platform, allowing users to share files securely with friends and approved members.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [TODO](#todo)


## Features

- **File Upload and Download:** Easily upload and download files.
- **File Sharing:** Share files publicly or keep them private.
- **Authentication:**
  - **Discord Login:** Currently supports login via Discord.
  - **Email Login:** Planned addition for broader authentication options.
- **User-Friendly Interface:** Built with HTML and Bootstrap for a clean and responsive design.
- **Logging and Error Handling:** Comprehensive logging for monitoring and debugging.
- **Flash Messages:** Informative flash messages for user actions and notifications.

## Technology Stack

- **Backend:**
  - Flask
  - Flask-Migrate
  - SQLAlchemy (SQLite as the default database)
  
- **Frontend:**
  - HTML
  - Bootstrap 4.5.2
  - JavaScript (Vanilla JS with plans to migrate to Vue or React)
  
- **Database:**
  - SQLite (default setup for simplicity)
  
- **Authentication:**
  - Discord OAuth2
  - Planned addition of Email Authentication

- **Other Tools:**
  - Python 3.10
  - Flask Blueprints for modular code structure

## TODO

### Authentication:
- Add Email Login alongside Discord Login.
- Implement invite-only registration requiring approval.

### Frontend Enhancements:
- Migrate from pure HTML and Bootstrap to a modern JavaScript framework like Vue.js or React.

### Additional Features:
- Implement file versioning.
- Add search functionality for files.
- Enhance user profiles.
