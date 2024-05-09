import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './Register.css';

function Register({ setCurrentUser, setCurrentUserAge, setCurrentUserType }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [age, setAge] = useState('');
    const [weight, setWeight] = useState('');
    const [height, setHeight] = useState('');
    const [specialPassword, setSpecialPassword] = useState('');
    const [specialty, setSpecialty] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const [showSpecialtyInput, setShowSpecialtyInput] = useState(false);
    const navigate = useNavigate();

    const handleRegister = async (e) => {
        e.preventDefault();

        try {
            const response = await axios.post('http://127.0.0.1:5000/register', {
                username,
                password,
                age: parseInt(age),
                weight: parseFloat(weight),
                height: parseFloat(height),
                special_password: specialPassword
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.data.message.startsWith('Welcome')) {
                const userResponse = await axios.get(`http://127.0.0.1:5000/users/${username}`);
                const user = userResponse.data;

                setCurrentUser(username);
                setCurrentUserAge(user.Age);
                setCurrentUserType(user.Type);

                if (user.Type === 'Doctor') {
                    setShowSpecialtyInput(true);
                } else if (user.Type === 'Admin') {
                    await handleAdminFlow();
                } else {
                    navigate('/chat');
                }
            } else {
                setErrorMessage(response.data.message);
            }
        } catch (error) {
            setErrorMessage('Error registering');
        }
    };

    const handleSpecialtyUpdate = async () => {
        try {
            const response = await axios.post('http://127.0.0.1:5000/update_doctor_specialty', {
                specialty
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.data.message.includes("Specialty updated")) {
                navigate('/chat');
            } else {
                setErrorMessage(response.data.message);
            }
        } catch (error) {
            setErrorMessage('Error updating specialty');
        }
    };

    const handleAdminFlow = async () => {
        try {
            const mistakesResponse = await axios.get('http://127.0.0.1:5000/mistakes');
            if (mistakesResponse.data.message === "No new mistakes to review.") {
                navigate('/chat');
            } else {
                navigate('/mistakes');
            }
        } catch (error) {
            setErrorMessage('Error checking for mistakes');
            navigate('/chat');
        }
    };

    return (
        <div className="register-container">
            <h2>Register</h2>
            <form onSubmit={handleRegister}>
                <input
                    type="text"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
                <input
                    type="number"
                    placeholder="Age"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    required
                />
                <input
                    type="number"
                    placeholder="Weight"
                    value={weight}
                    onChange={(e) => setWeight(e.target.value)}
                    required
                />
                <input
                    type="number"
                    placeholder="Height"
                    value={height}
                    onChange={(e) => setHeight(e.target.value)}
                    required
                />
                <input
                    type="text"
                    placeholder="Special Password (if any)"
                    value={specialPassword}
                    onChange={(e) => setSpecialPassword(e.target.value)}
                />
                <button type="submit">Register</button>
            </form>
            {showSpecialtyInput && (
                <div className="specialty-container">
                    <input
                        type="text"
                        placeholder="Enter your specialty"
                        value={specialty}
                        onChange={(e) => setSpecialty(e.target.value)}
                        required
                    />
                    <button onClick={handleSpecialtyUpdate}>Update Specialty</button>
                </div>
            )}
            {errorMessage && <p className="error-message">{errorMessage}</p>}
        </div>
    );
}

export default Register;
