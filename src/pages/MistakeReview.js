import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './MistakeReview.css';

function MistakeReview({ currentUser }) {
    const [mistakes, setMistakes] = useState([]);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchMistakes = async () => {
            try {
                const response = await axios.get('http://127.0.0.1:5000/mistakes');
                if (response.data.mistakes && response.data.mistakes.length > 0) {
                    setMistakes(response.data.mistakes);
                } else {
                    navigate('/chat');
                }
            } catch (error) {
                setError('Error retrieving mistakes');
            }
        };

        fetchMistakes();
    }, [navigate]);

    const handleMistakeReview = async (mistakeId, approve) => {
        try {
            await axios.post('http://127.0.0.1:5000/process_mistake', {
                mistake_id: mistakeId,
                approve_correction: approve
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            setMistakes(prevMistakes => prevMistakes.filter(mistake => mistake['Mistake ID'] !== mistakeId));

            if (mistakes.length === 1) {
                navigate('/chat');
            }
        } catch (error) {
            setError('Error processing mistake review');
        }
    };

    return (
        <div className="mistake-review-container">
            <h2>Mistake Review</h2>
            {error && <p className="error-message">{error}</p>}
            {mistakes.length === 0 ? (
                <p>No mistakes to review.</p>
            ) : (
                mistakes.map(mistake => (
                    <div key={mistake['Mistake ID']} className="mistake">
                        <p><strong>Type:</strong> {mistake.Type}</p>
                        <p><strong>Original:</strong> {mistake.Original}</p>
                        <p><strong>Proposed Correction:</strong> {mistake['Proposed Correction']}</p>
                        <p><strong>Affected Fields:</strong> {mistake['Affected Fields'].join(', ')}</p>
                        <button onClick={() => handleMistakeReview(mistake['Mistake ID'], true)}>Approve</button>
                        <button onClick={() => handleMistakeReview(mistake['Mistake ID'], false)}>Reject</button>
                    </div>
                ))
            )}
        </div>
    );
}

export default MistakeReview;
