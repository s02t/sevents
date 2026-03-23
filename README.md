# sevents
## QR Event Management System

This is an event management system with QR code generation and check-in functionality.

## Screenshots & Demo
![image alt](https://github.com/s02t/sevents/blob/25c9d85d1438085a956fa598d7e81907c6e3d34a/screenshots/Screenshot%202026-03-23%20at%2011-04-28%20sevents.png)
![image alt](https://raw.githubusercontent.com/s02t/sevents/25c9d85d1438085a956fa598d7e81907c6e3d34a/screenshots/Screenshot%202026-03-23%20at%2011-04-38%20sevents.png)
![image alt](https://raw.githubusercontent.com/s02t/sevents/25c9d85d1438085a956fa598d7e81907c6e3d34a/screenshots/Screenshot%202026-03-23%20at%2011-04-46%20sevents.png)

![image alt](https://raw.githubusercontent.com/s02t/sevents/25c9d85d1438085a956fa598d7e81907c6e3d34a/screenshots/Screenshot%202026-03-23%20at%2011-05-08%20sevents.png)
![image alt](https://raw.githubusercontent.com/s02t/sevents/25c9d85d1438085a956fa598d7e81907c6e3d34a/screenshots/Screenshot%202026-03-23%20at%2011-06-24%20sevents.png)
![image alt](https://raw.githubusercontent.com/s02t/sevents/25c9d85d1438085a956fa598d7e81907c6e3d34a/screenshots/Screenshot%202026-03-23%20at%2011-04-17%20sevents.png)
![image alt](https://raw.githubusercontent.com/s02t/sevents/25c9d85d1438085a956fa598d7e81907c6e3d34a/screenshots/Screenshot%202026-03-23%20at%2011-18-06%20sevents.png)
![image alt](https://raw.githubusercontent.com/s02t/sevents/25c9d85d1438085a956fa598d7e81907c6e3d34a/screenshots/Screenshot%202026-03-23%20at%2011-18-21%20sevents.png)

### Link to Video Demo

https://youtu.be/ye8QURvuo6k?si=XjXXQfQOxpGTIob7

Features

- Create and manage events
- Generate customizable registration forms
- Set event capacity with unlimited or limited seats
- Generate QR codes for attendees
- Send automatic email confirmations with QR codes
- Check in attendees by scanning QR codes
- View event statistics and reports

## Setup Email with Mailtrap

To enable email functionality (registration confirmations and notifications):

1. Sign up for a free [Mailtrap](https://mailtrap.io/) account
2. Create a new inbox in Mailtrap
3. Go to the SMTP settings section to get your credentials
4. Create a `.env` file in the root directory with the following:

```
# Mailtrap SMTP settings
MAIL_USERNAME=your_mailtrap_username
MAIL_PASSWORD=your_mailtrap_password
MAIL_FROM=noreply@example.com
MAIL_PORT=2525
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_FROM_NAME=QR Event System

# Other settings
MAIL_TLS=True
MAIL_SSL=False
USE_CREDENTIALS=True
VALIDATE_CERTS=True
```

5. Replace `your_mailtrap_username` and `your_mailtrap_password` with your actual credentials

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up the database: `python init_db.py`
4. Create an admin user: `python create_admin.py`
5. Start the server: `uvicorn main:app --reload`

## Usage

1. Access the admin dashboard at: http://localhost:8000/
2. Login with your admin credentials
3. Create new events and registration forms
4. Share registration links with potential attendees
5. Monitor registrations and check-ins via the dashboard 
