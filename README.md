# QR Code Event Management App

A FastAPI application for event registration, QR code generation, and check-in management.

## Features

- Event creation and management
- Custom registration forms
- QR code generation for attendees
- Check-in functionality
- Admin authentication

## Authentication System

The application includes a basic authentication system that restricts admin features to authenticated users while keeping registration forms publicly accessible.

### Admin Features (Protected)

- Event creation and management
- Form field configuration
- Submissions viewing
- QR code scanning and check-in

### Public Features

- Event registration forms
- Form submission
- QR code receipt

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create an admin user:
   ```
   python create_admin.py <username> <email> <password>
   ```

3. Run the application:
   ```
   uvicorn main:app --reload
   ```

## Usage

1. Login as an admin:
   - Access `/auth/login` or `/admin` to log in
   - Use the credentials created with the admin script

2. Create events and forms:
   - Create a new event form through the admin interface
   - Configure fields as needed

3. Share registration links:
   - Share the public registration URL with attendees:
   ```
   /submission/create/{form_id}
   ```

4. Manage registrations:
   - View and track submissions
   - Scan QR codes for check-in

## User Management

Admins can manage users through the admin interface:
- Create new users (regular or admin)
- Delete existing users

## Authentication Details

- HTTP Basic Authentication is used for simplicity
- Admin users can access all features
- Regular users have limited access (if implemented)
- Public access is available only to registration forms 