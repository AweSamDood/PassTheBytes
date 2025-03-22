# PassTheBytes

**PassTheBytes** is a modern file-sharing and personal storage solution designed for individuals. Initially aimed at personal use, PassTheBytes will evolve to an invite-only platform, allowing users to share files securely with friends and approved members.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Development](#development)
- [Roadmap](#roadmap)

## Features

### Current Features

- **Authentication:**
  - **Discord Login:** Secure authentication via Discord OAuth2
  - **JWT Support:** Stateless authentication with access and refresh tokens

- **File Management:**
  - **File Upload and Download:** Chunked file uploads for better reliability and large file support
  - **Directory Organization:** Create, navigate, and manage directories
  - **Bulk Operations:** Select and download/delete multiple files and directories at once

- **File Sharing:**
  - **Public Share Links:** Generate shareable links for files
  - **Password Protection:** Optional password protection for shared files

- **UI Features:**
  - **Dark/Light Mode:** Toggle between dark and light themes
  - **Responsive Design:** Works on both desktop and mobile devices
  - **Breadcrumb Navigation:** Easy navigation between directories

- **System Features:**
  - **Admin Dashboard:** Performance monitoring for administrators
  - **Storage Quotas:** User-specific storage quotas
  - **Automatic Cleanup:** Background service to clean up stale temporary files
  - **Robust Error Handling:** Comprehensive logging and error management

## Technology Stack

### Backend
- **Framework:** Flask with Blueprints for modular code structure
- **Database:** SQLite (default), with PostgreSQL support
- **Authentication:** Discord OAuth2 and JWT
- **Security:** Rate limiting, secure cookie configuration, content security policy

### Frontend
- **Framework:** React.js with Ant Design
- **State Management:** React Hooks
- **HTTP Client:** Axios with interceptors for token refresh
- **Build Tool:** Create React App

### Infrastructure
- **Development:** HTTPS with self-signed certificates
- **Storage:** Local file system with organization by user ID and directories
- **Logging:** Rotating file logs

## Installation

### Prerequisites
- Python 3.10 or higher
- Node.js and npm
- Discord Developer Account (for OAuth2 credentials)

### Backend Setup
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
  - Windows: `venv\Scripts\activate`
  - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file in the backend directory with the following variables:
   ```
   CLIENT_ID=your_discord_client_id
   CLIENT_SECRET=your_discord_client_secret
   REDIRECT_URI=https://localhost:5000/api/jwt/callback
   FRONTEND_URI=https://localhost:3000
   SECRET_KEY=your_secret_key
   JWT_SECRET_KEY=your_jwt_secret_key
   ADMIN_DISCORD_USER_ID=your_discord_user_id
   ```
6. Run the backend: `flask run`

### Frontend Setup
1. Navigate to the frontend directory
2. Install dependencies: `npm install`
3. Create a `.env` file with:
   ```
   REACT_APP_API_BASE_URL=https://localhost:5000/api
   ```
4. Start the frontend development server: `npm start`

## Development

### Folder Structure
- **backend/**: Flask backend API
  - **auth/**: Authentication modules
  - **core/**: Core file operations
  - **share/**: File sharing functionality
  - **user/**: User management
  - **services/**: Background services

- **frontend/**: React frontend
  - **src/components/**: Reusable React components
  - **src/pages/**: Page components
  - **src/services/**: API and authentication services
  - **src/css/**: Stylesheets

## Roadmap

### Priority Features
- **Additional OAuth Methods:** Implement additional authentication providers beyond Discord
  - Google OAuth
  - GitHub OAuth
- **Directory Sharing:** Extend sharing capabilities to entire directories
- **Expiring Share Links:** Add automatic expiration dates for shared files and directories
- **Search Functionality:** Implement search within the current directory/folder
- **File Preview:** Preview images and GIFs after successful password verification for password-protected shares
- **Shared File Management:** User interface to view and manage all currently active shared files
- **Download Experience:** Fix download timeout issues and improve download feedback