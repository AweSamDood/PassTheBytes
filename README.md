# PassTheBytes

**PassTheBytes** is a modern file-sharing and personal storage solution designed for individuals. Initially aimed at personal use, PassTheBytes will evolve to an invite-only platform, allowing users to share files securely with friends and approved members.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Development](#development)
- [Roadmap](#roadmap)

### Project Status

**Note:** This is one of my earlier projects. It includes a variety of features like Discord authentication, file sharing, and a responsive UI. However, it does not have a formal CI/CD pipeline, automated testing, or security audits.

For a more recent and mature example of my work, please see my **[passthebytes-tools](https://github.com/your-github/passthebytes-tools)** project, which features a full CI/CD pipeline with automated security scanning and deployment.

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
- **Framework:** Flask (Python) with Blueprints for modular code structure
- **Database:** SQLite (default), with PostgreSQL support possible
- **Authentication:** Discord OAuth2 and JWT
- **Security:** Rate limiting, secure cookie configuration, content security policy
- **Modules:**
  - **auth/**: Authentication (OAuth, JWT)
  - **core/**: File and directory operations
  - **share/**: File sharing logic
  - **user/**: User management
  - **servicies/**: Background services (e.g., cleanup, server info)
  - **uploads/**: User file storage
  - **logs/**: Rotating file logs

### Frontend
- **Framework:** React.js (JavaScript)
- **UI Library:** Ant Design
- **State Management:** React Hooks
- **HTTP Client:** Axios (with token refresh interceptors)
- **Build Tool:** Create React App
- **Structure:**
  - **src/components/**: Reusable components
  - **src/pages/**: Page-level components
  - **src/services/**: API/auth logic
  - **src/css/**: Styles

### Infrastructure & Deployment
- **Development:** HTTPS with self-signed certificates
- **Deployment:** Docker and docker-compose files included for both backend and frontend
- **Storage:** Local file system, organized by user ID and directories
- **Logging:** Rotating file logs

## Installation

### Prerequisites
- Python 3.10 or higher
- Node.js and npm
- Discord Developer Account (for OAuth2 credentials)
- (Optional) Docker & Docker Compose for containerized deployment

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

### Docker Deployment (Optional)
- Use the provided `docker-compose.yml` files in the root and passthebytes-tools/ for production or development deployment.

## Development

### Folder Structure (Key Directories)
- **backend/**: Flask backend API
  - **auth/**: Authentication modules
  - **core/**: File and directory operations
  - **share/**: File sharing
  - **user/**: User management
  - **servicies/**: Background/utility services
  - **uploads/**: User file storage
  - **logs/**: Log files
- **frontend/**: React frontend
  - **src/components/**: Reusable React components
  - **src/pages/**: Page components
  - **src/services/**: API/authentication services
  - **src/css/**: Stylesheets

## Roadmap

### Priority Features
- **Additional OAuth Methods:** Google, GitHub, etc.
- **Directory Sharing:** Share entire directories
- **Expiring Share Links:** Automatic expiration for shared files/directories
- **Search Functionality:** Search within directories
- **File Preview:** Preview images/GIFs for password-protected shares
- **Shared File Management:** UI for managing active shares
- **Download Experience:** Improve download reliability and feedback
