import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Login.css';

function Login({ setCurrentUser, setCurrentUserAge, setCurrentUserType }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [age, setAge] = useState('');
    const [weight, setWeight] = useState('');
    const [height, setHeight] = useState('');
    const [error, setError] = useState('');
    const [updateHealth, setUpdateHealth] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('http://127.0.0.1:5000/login', {
                username,
                password
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.data.message.startsWith('Welcome back')) {
                const userResponse = await axios.get(`http://127.0.0.1:5000/users/${username}`);
                const user = userResponse.data;

                setCurrentUser(username);
                setCurrentUserAge(user.Age);
                setCurrentUserType(user.Type);

                const checkHealthResponse = await axios.post('http://127.0.0.1:5000/check_update_health', {
                    username
                }, {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (checkHealthResponse.data.message === 'Health profile needs update to health parameters.') {
                    setUpdateHealth(true);
                } else {
                    if (user.Type === 'Admin') {
                        const mistakesResponse = await axios.get('http://127.0.0.1:5000/mistakes');
                        if (mistakesResponse.data.mistakes && mistakesResponse.data.mistakes.length > 0) {
                            navigate('/mistake-review');
                        } else {
                            navigate('/chat');
                        }
                    } else {
                        navigate('/chat');
                    }
                }
            } else {
                setError('Invalid username or password');
            }
        } catch (error) {
            setError('Error logging in');
        }
    };

    const handleUpdateHealth = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post('http://127.0.0.1:5000/update_health', {
                username,
                age: parseFloat(age),
                weight: parseFloat(weight),
                height: parseFloat(height)
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.data.message === 'Your health profile is up to date.') {
                const userResponse = await axios.get(`http://127.0.0.1:5000/users/${username}`);
                const user = userResponse.data;

                if (user.Type === 'Admin') {
                    const mistakesResponse = await axios.get('http://127.0.0.1:5000/mistakes');
                    if (mistakesResponse.data.mistakes && mistakesResponse.data.mistakes.length > 0) {
                        navigate('/mistake-review');
                    } else {
                        navigate('/chat');
                    }
                } else {
                    navigate('/chat');
                }
            } else {
                setError('Error updating health profile');
            }
        } catch (error) {
            setError('Error updating health profile');
        }
    };

    return (
        <div className="login-container">
            {!updateHealth ? (
                <form onSubmit={handleLogin} className="login-form">
                    <h2>Login</h2>
                    <input
                        type="text"
                        placeholder="Username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                    />
                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                    {error && <p className="error-message">{error}</p>}
                    <button type="submit">Login</button>
                </form>
            ) : (
                <form onSubmit={handleUpdateHealth} className="login-form">
                    <h2>Update Health Profile</h2>
                    <input
                        type="number"
                        placeholder="Age"
                        value={age}
                        onChange={(e) => setAge(e.target.value)}
                    />
                    <input
                        type="number"
                        placeholder="Weight (kg)"
                        value={weight}
                        onChange={(e) => setWeight(e.target.value)}
                    />
                    <input
                        type="number"
                        placeholder="Height (cm)"
                        value={height}
                        onChange={(e) => setHeight(e.target.value)}
                    />
                    {error && <p className="error-message">{error}</p>}
                    <button type="submit">Update Health</button>
                </form>
            )}
        </div>
    );
}

export default Login;
