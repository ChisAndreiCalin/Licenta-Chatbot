import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Chat.css';

function Chat({ currentUser, currentUserAge, currentUserType }) {
    const [message, setMessage] = useState('');
    const [conversation, setConversation] = useState([]);
    const [isTyping, setIsTyping] = useState(false);
    const [currentSymptoms, setCurrentSymptoms] = useState([]);
    const [diagnosisStep, setDiagnosisStep] = useState(false);
    const [awaitingAppointmentConfirmation, setAwaitingAppointmentConfirmation] = useState(false);
    const [awaitingDoctorSelection, setAwaitingDoctorSelection] = useState(false);
    const [awaitingAppointmentDetails, setAwaitingAppointmentDetails] = useState(false);
    const [awaitingMedicineName, setAwaitingMedicineName] = useState(false);
    const [awaitingMedicineSelection, setAwaitingMedicineSelection] = useState(false);
    const [awaitingSymptomMedicine, setAwaitingSymptomMedicine] = useState(false);
    const [awaitingMistakeType, setAwaitingMistakeType] = useState(false);
    const [awaitingMistakeDetails, setAwaitingMistakeDetails] = useState(false);
    const [currentDiagnoses, setCurrentDiagnoses] = useState([]);
    const [availableSpecialists, setAvailableSpecialists] = useState([]);
    const [currentSpecialist, setCurrentSpecialist] = useState('');
    const [medicineSuggestions, setMedicineSuggestions] = useState([]);
    const [mistakeDetails, setMistakeDetails] = useState({});

    useEffect(() => {
        // Greet user after login
        if (currentUser) {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Hello! How may I assist you today?' }
            ]);
        } else {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Please log in to continue.' }
            ]);
        }
    }, [currentUser]);

    const handleSendMessage = async () => {
        if (!message.trim()) return;

        // Add user's message to the conversation
        setConversation(prevConversation => [
            ...prevConversation,
            { sender: 'user', text: message }
        ]);

        setMessage('');  // Clear the input field
        setIsTyping(true); // Show typing indicator

        try {
            if (awaitingAppointmentConfirmation) {
                if (message.toLowerCase() === 'yes') {
                    await handleSpecialistSelection();
                } else {
                    setConversation(prevConversation => [
                        ...prevConversation,
                        { sender: 'bot', text: 'Thank you for using our service. Goodbye!' }
                    ]);
                }
                setAwaitingAppointmentConfirmation(false);
            } else if (awaitingDoctorSelection) {
                await handleDoctorSelection(message);
            } else if (awaitingAppointmentDetails) {
                await handleAppointmentDetails(message);
            } else if (awaitingMedicineName) {
                await handleMedicineSuggestions(message);
            } else if (awaitingMedicineSelection) {
                await handleMedicineInfo(message);
            } else if (awaitingSymptomMedicine) {
                await handleSymptomMedicineRequest(message);
            } else if (awaitingMistakeType) {
                await handleMistakeType(message);
            } else if (awaitingMistakeDetails) {
                if (mistakeDetails.original_mistake) {
                    await handleMistakeCorrection(message);
                } else {
                    await handleMistakeDetails(message);
                }
            } else if (diagnosisStep) {
                await handleSymptomSelection(message);
            } else {
                const response = await axios.post('http://127.0.0.1:5000/response_type', {
                    user_input: message
                }, {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const responseType = response.data.response_type;

                // Simulate typing delay
                setTimeout(async () => {
                    switch (responseType) {
                        case 'diagnostic':
                            await handleDiagnostic();
                            break;
                        case 'medicine':
                            await handleMedicineInfoRequest();
                            break;
                        case 'symptom_medicine':
                            await handleSymptomMedicine();
                            break;
                        case 'mistake':
                            await handleFeedback();
                            break;
                        default:
                            await handleDynamicResponse(message);
                            break;
                    }
                    setIsTyping(false); // Hide typing indicator
                }, 1000); // Adjust typing delay as needed
            }
        } catch (error) {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Error sending message' }
            ]);
            setIsTyping(false); // Hide typing indicator
        }
    };

    const handleKeyPress = (event) => {
        if (event.key === 'Enter') {
            handleSendMessage();
        }
    };

    const handleDiagnostic = async () => {
        try {
            const symptomsResponse = await axios.get('http://127.0.0.1:5000/symptoms');
            const symptoms = symptomsResponse.data;

            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Please describe your symptoms. Here are some possible symptoms you can choose from:' },
                { sender: 'bot', text: symptoms.join(', ') },
                { sender: 'bot', text: 'Pick at least two symptoms for a more accurate diagnosis.' }
            ]);

            setCurrentSymptoms(symptoms);
            setDiagnosisStep(true);
        } catch (error) {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Error retrieving symptoms' }
            ]);
        }
    };

    const handleMedicineInfoRequest = async () => {
        setConversation(prevConversation => [
            ...prevConversation,
            { sender: 'bot', text: 'Please provide the simple name of the medicine you want to learn about.' }
        ]);
        setAwaitingMedicineName(true);
    };

    const handleMedicineSuggestions = async (medicineInput) => {
        try {
            const response = await axios.post('http://127.0.0.1:5000/medicine_suggestions', {
                medicine_input: medicineInput.toUpperCase()
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const suggestions = response.data.suggestions;
            setMedicineSuggestions(suggestions);

            const suggestionMessages = suggestions.map(s => ({
                sender: 'bot',
                text: `${s.name} (Score: ${s.score})`
            }));

            setConversation(prevConversation => [
                ...prevConversation,
                ...suggestionMessages,
                { sender: 'bot', text: 'Please select a medicine from the list by typing its name exactly.' }
            ]);

            setAwaitingMedicineName(false);
            setAwaitingMedicineSelection(true);
        } catch (error) {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Error retrieving medicine suggestions' }
            ]);
        }
    };

    const handleMedicineInfo = async (medicineName) => {
        try {
            const response = await axios.post('http://127.0.0.1:5000/medicine_info', {
                medicine_name: medicineName
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const medicineData = response.data.data;

            const medicineInfoMessages = medicineData.map(m => ({
                sender: 'bot',
                text: `Medicine: ${m['Denumirea comerciala']}, ATC: ${m.ATC}, Form: ${m.Forma}, Dosage for Adults: ${m['Doza Adult']}, Dosage for Children: ${m['Doza Copil']}, Ambalaj: ${m.Ambalaj} , Concentratie: ${m.Conc} , Symptoms Treated: ${m['Simptome combatute']}`
            }));

            setConversation(prevConversation => [
                ...prevConversation,
                ...medicineInfoMessages
            ]);

            setAwaitingMedicineSelection(false);
        } catch (error) {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Error retrieving medicine information' }
            ]);
        }
    };

    const handleSymptomMedicine = async () => {
        setConversation(prevConversation => [
            ...prevConversation,
            { sender: 'bot', text: 'Please specify the symptom you\'re experiencing, and I\'ll help find suitable medicine.' }
        ]);
        setAwaitingSymptomMedicine(true);
    };

    const handleSymptomMedicineRequest = async (symptom) => {
        try {
            const response = await axios.post('http://127.0.0.1:5000/symptom_medicine', {
                symptom: symptom.toLowerCase()
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const medicines = response.data.medicines;

            const medicineMessages = medicines.map(m => ({
                sender: 'bot',
                text: `Medicine: ${m.medicine}, Dosage: ${m.dosage}`
            }));

            setConversation(prevConversation => [
                ...prevConversation,
                ...medicineMessages
            ]);

            setAwaitingSymptomMedicine(false);
        } catch (error) {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Error retrieving medicine information' }
            ]);
        }
    };

    const handleFeedback = async () => {
        if (currentUserType === 'Doctor' || currentUserType === 'Admin') {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Please provide the type of mistake (medicine or disease).' }
            ]);
            setAwaitingMistakeType(true);
        } else {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'You must be a Doctor or Admin to provide feedback.' }
            ]);
        }
    };

    const handleMistakeType = async (type) => {
        setMistakeDetails({ mistake_type: type });
        setConversation(prevConversation => [
            ...prevConversation,
            { sender: 'bot', text: 'Please specify the original mistake (e.g., disease/medicine name).' }
        ]);
        setAwaitingMistakeType(false);
        setAwaitingMistakeDetails(true);
    };

    const handleMistakeDetails = async (originalMistake) => {
        setMistakeDetails(prevDetails => ({ ...prevDetails, original_mistake: originalMistake }));
        setConversation(prevConversation => [
            ...prevConversation,
            { sender: 'bot', text: 'Please provide the correct information. Use ":" as a delimiter for the columns you want to specify.' }
        ]);
    };

    const handleMistakeCorrection = async (correctAnswer) => {
        const finalDetails = { ...mistakeDetails, correct_answer: correctAnswer };

        try {
            const response = await axios.post('http://127.0.0.1:5000/record_feedback', finalDetails, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: response.data.message }
            ]);
            setAwaitingMistakeDetails(false);
        } catch (error) {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Error recording feedback' }
            ]);
        }
    };

    const handleDynamicResponse = async (userInput) => {
        try {
            const response = await axios.post('http://127.0.0.1:5000/respond_dynamically', {
                message: userInput
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: response.data.response }
            ]);

        } catch (error) {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Error processing your request' }
            ]);
        }
    };

    const handleSymptomSelection = async (userInput) => {
        const selectedSymptoms = userInput.split(',').map(symptom => symptom.trim());
        if (selectedSymptoms.length < 2) {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Please select at least two symptoms.' }
            ]);
            return;
        }

        try {
            const response = await axios.post('http://127.0.0.1:5000/diagnose', {
                symptoms: selectedSymptoms
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.data.diagnoses) {
                const diagnoses = response.data.diagnoses;
                setCurrentDiagnoses(diagnoses);

                const diagnosisMessages = diagnoses.map(d => ({
                    sender: 'bot',
                    text: `${d.disease} (${d.probability}): ${d.medication}`
                }));

                setConversation(prevConversation => [
                    ...prevConversation,
                    ...diagnosisMessages,
                    { sender: 'bot', text: 'Would you like to make an appointment with a specialist?' }
                ]);
                setAwaitingAppointmentConfirmation(true);
            } else {
                setConversation(prevConversation => [
                    ...prevConversation,
                    { sender: 'bot', text: 'We couldn\'t identify your condition based on the symptoms provided. Consulting a doctor is recommended.' }
                ]);
            }

            setDiagnosisStep(false);
        } catch (error) {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Error diagnosing symptoms' }
            ]);
        }
    };

    const handleSpecialistSelection = async () => {
        if (currentDiagnoses.length > 0) {
            const disease = currentDiagnoses[0].disease; // Assuming the first diagnosis for simplicity

            try {
                const response = await axios.get(`http://127.0.0.1:5000/specialists_avaliable/${disease}`);
                const specialistsList = response.data.specialists;
                setAvailableSpecialists(specialistsList);

                const specialistMessages = specialistsList.map(s => ({
                    sender: 'bot',
                    text: `Doctor: ${s.Username}, Specialty: ${s.Specialty}`
                }));

                setConversation(prevConversation => [
                    ...prevConversation,
                    ...specialistMessages,
                    { sender: 'bot', text: 'Please select a doctor by entering the username.' }
                ]);

                setAwaitingDoctorSelection(true);
            } catch (error) {
                setConversation(prevConversation => [
                    ...prevConversation,
                    { sender: 'bot', text: 'Error retrieving specialists' }
                ]);
            }
        } else {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'No diagnoses available to find specialists.' }
            ]);
        }
    };

    const handleDoctorSelection = async (doctorUsername) => {
        const selectedSpecialist = availableSpecialists.find(s => s.Username.toLowerCase() === doctorUsername.toLowerCase());

        if (selectedSpecialist) {
            setCurrentSpecialist(selectedSpecialist.Username);
            setAwaitingDoctorSelection(false);

            try {
                const response = await axios.get(`http://127.0.0.1:5000/doctor_schedule/${selectedSpecialist.Username}`);

                const schedule = response.data.schedule;
                const scheduleMessages = Object.entries(schedule).map(([date, slots]) => ({
                    sender: 'bot',
                    text: `${date}: ${slots.join(', ')}`
                }));

                setConversation(prevConversation => [
                    ...prevConversation,
                    ...scheduleMessages,
                    { sender: 'bot', text: 'Please provide a date (YY/MM/DD) and hour (HH:MM) for the appointment.' }
                ]);

                setAwaitingAppointmentDetails(true);
            } catch (error) {
                setConversation(prevConversation => [
                    ...prevConversation,
                    { sender: 'bot', text: 'Error retrieving doctor schedule' }
                ]);
            }
        } else {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Doctor not found. Please select a doctor by entering the username from the list above.' }
            ]);
        }
    };

    const handleAppointmentDetails = async (userInput) => {
        const [date, hour] = userInput.split(',').map(detail => detail.trim());

        try {
            const result = await axios.post('http://127.0.0.1:5000/book_appointment', {
                doctor_username: currentSpecialist,
                date,
                hour
            });

            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: result.data.message }
            ]);

            setAwaitingAppointmentDetails(false);
        } catch (error) {
            setConversation(prevConversation => [
                ...prevConversation,
                { sender: 'bot', text: 'Error booking the appointment. Please try again.' }
            ]);
        }
    };

    return (
        <div className="chat-container">
            <div className="chat-box">
                {conversation.map((msg, index) => (
                    <div key={index} className={`chat-message ${msg.sender}`}>
                        {msg.text}
                    </div>
                ))}
                {isTyping && (
                    <div className="chat-message bot typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                )}
            </div>
            <div className="chat-input-container">
                <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type your message..."
                    className="chat-input"
                />
                <button onClick={handleSendMessage} className="chat-send-button">Send</button>
            </div>
        </div>
    );
}

export default Chat;
