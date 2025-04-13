# GoVroom - Car Rental Platform

GoVroom is a modern car rental platform that allows users to rent cars or share their own vehicles with others. Built with React, TypeScript, and Node.js.

## Features

- User authentication and authorization
- Car listing and searching
- Booking management
- Real-time availability tracking
- Secure payment processing
- User reviews and ratings

## Tech Stack

### Frontend
- React with TypeScript
- Chakra UI for styling
- React Router for navigation
- Formik for form management
- Yup for form validation
- Axios for API requests

### Backend
- Node.js with TypeScript
- Express.js
- MongoDB with Mongoose
- JWT for authentication
- bcrypt for password hashing

## Getting Started

### Prerequisites
- Node.js (v14 or higher)
- MongoDB
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/govroom.git
cd govroom
```

2. Install frontend dependencies:
```bash
npm install
```

3. Install backend dependencies:
```bash
cd backend
npm install
```

4. Create a `.env` file in the backend directory with the following variables:
```
PORT=5000
MONGODB_URI=mongodb://localhost:27017/govroom
JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRES_IN=7d
```

5. Start the development servers:

Frontend:
```bash
npm start
```

Backend:
```bash
cd backend
npm run dev
```

## Project Structure

```
govroom/
├── src/                    # Frontend source files
│   ├── components/        # Reusable React components
│   ├── pages/            # Page components
│   ├── theme/            # Chakra UI theme customization
│   └── App.tsx           # Main application component
├── backend/              # Backend source files
│   ├── src/             # Backend TypeScript source
│   ├── models/          # Mongoose models
│   └── routes/          # API routes
└── README.md            # Project documentation
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
