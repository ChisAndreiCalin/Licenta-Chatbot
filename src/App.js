import React, { useState } from 'react';
import { Route, Routes } from 'react-router-dom';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Chat from './pages/Chat';
import './App.css';

function App() {
    const [currentUser, setCurrentUser] = useState(null);
    const [currentUserAge, setCurrentUserAge] = useState(null);
    const [currentUserType, setCurrentUserType] = useState(null);

    return (
        <div className="App">
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login setCurrentUser={setCurrentUser} setCurrentUserAge={setCurrentUserAge} setCurrentUserType={setCurrentUserType} />} />
                <Route path="/register" element={<Register />} />
                <Route path="/chat" element={<Chat currentUser={currentUser} currentUserAge={currentUserAge} currentUserType={currentUserType}/>} />
            </Routes>
        </div>
    );
}

export default App;
