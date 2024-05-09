from ChatbotClass.Chatbotapi import ChatbotAPI
from constants import *
from flask import Flask, request, jsonify
from flask_cors import CORS


import json
app = Flask(__name__)
CORS(app)

csvmedicamente = DATASET_FOLDER + SEPARATOR + "Medicamente_Csv.csv"
csvboli = DATASET_FOLDER + SEPARATOR + "CSVBoli.csv"
csvuser = DATASET_FOLDER + SEPARATOR + "userCsv.csv"
csvraspunsuri = DATASET_FOLDER + SEPARATOR + "responce.csv"
csvmistakes = DATASET_FOLDER + SEPARATOR + "mistakes.csv"
csvschedule = DATASET_FOLDER + SEPARATOR + "Scheduleapi.csv"
chatbot = ChatbotAPI(csvuser, csvboli, csvmedicamente, csvraspunsuri, csvmistakes, csvschedule)
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    age = data.get('age')
    weight = data.get('weight')
    height = data.get('height')
    special_password = data.get('special_password', '')
    result = chatbot.register_user(username, password, age, weight, height, special_password)
    return jsonify({'message': result})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    result = chatbot.login_user(username, password)
    return jsonify({'message': result})
@app.route('/users/<username>', methods=['GET'])
def get_user(username):
    user = chatbot.get_user(username)
    if user:
        return jsonify(user)
    else:
        return jsonify({'message': 'User not found'}), 404
@app.route('/check_update_health', methods=['POST'])
def check_update_health():
    data = request.get_json()
    username = data.get('username')
    result = chatbot.check_health_update_needed(username)
    return jsonify({'message': result})

@app.route('/update_health', methods=['POST'])
def update_health():
    data = request.get_json()
    username = data.get('username')
    age = data.get('age')
    weight = data.get('weight')
    height = data.get('height')
    result = chatbot.update_user_health(username, age, weight, height)
    return jsonify({'message': result})


# Initialize your Chatbot class here, make sure to provide the correct CSV paths

@app.route('/mistakes', methods=['GET'])
def show_mistakes():
    result = chatbot.review_mistakes()
    if isinstance(result, str):
        return jsonify({'message': result})
    else:
        return jsonify({'mistakes': result})

@app.route('/process_mistake', methods=['POST'])
def process_mistake():
    data = request.get_json()
    mistake_id = data.get('mistake_id')
    approve_correction = data.get('approve_correction', False)  # Default to False if not specified

    result = chatbot.process_mistake_review(int(mistake_id), approve_correction)
    return jsonify({'message': result})


@app.route('/update_doctor_specialty', methods=['POST'])
def update_doctor_specialty():
    data = request.get_json()
    new_specialty = data.get('specialty')
    result = chatbot.update_doctor_specialty(new_specialty)
    return jsonify({'message': result})
@app.route('/symptoms', methods=['GET'])
def get_symptoms():
    symptoms = chatbot.list_possible_symptoms()
    return jsonify(symptoms)
@app.route('/diagnose', methods=['POST'])
def diagnose():
    symptoms = request.json.get('symptoms', [])
    if len(symptoms) < 2:
        return jsonify({'message': "At least two symptoms are needed for a more accurate diagnosis."}), 400

    diagnoses = chatbot.diagnose_symptoms(symptoms)
    if not diagnoses:
        return jsonify({'message': "We couldn't identify your condition based on the symptoms provided. Consulting a doctor is recommended."}), 404

    diagnosis_info = []
    for diagnosis in diagnoses:
        disease = diagnosis['disease']
        medication_suggestion = chatbot.suggest_medication(disease)
        diagnosis.update({'medication': medication_suggestion})
        diagnosis_info.append(diagnosis)

    return jsonify({'diagnoses': diagnosis_info})

@app.route('/specialists', methods=['POST'])
def get_specialists():
    disease = request.json.get('disease')
    specialists = chatbot.get_specialists(disease)
    if not specialists:
        return jsonify({'message': 'No specialists found for the given disease.'}), 404
    return jsonify({'specialists': specialists})
@app.route('/doctor_schedule/<username>', methods=['GET'])
def doctor_schedule(username):
    schedule = chatbot.get_doctor_schedule(username)
    return jsonify({'schedule': schedule})
@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    doctor_username = request.json.get('doctor_username')
    date = request.json.get('date')  # Expect date in YY/MM/DD format
    hour = request.json.get('hour')
    result = chatbot.book_appointment(doctor_username, date, hour)
    return jsonify({'message': result})
@app.route('/specialists_avaliable/<disease>', methods=['GET'])
def get_specialists_avaliable(disease):
    specialists = chatbot.find_specialists_by_disease(disease)
    if not specialists:
        return jsonify({'message': 'No specialists available for this disease.'}), 404
    return jsonify({'specialists': specialists})

@app.route('/medicine_info', methods=['POST'])
def medicine_info():
    data = request.json
    medicine_name = data.get('medicine_name')
    result = chatbot.provide_medicine_info(medicine_name)
    return jsonify(result)

@app.route('/medicine_suggestions', methods=['POST'])
def medicine_suggestions():
    data = request.json
    medicine_input = data.get('medicine_input')
    result = chatbot.get_user_medicine(medicine_input)
    return jsonify(result)

@app.route('/symptom_medicine', methods=['POST'])
def symptom_medicine():
    data = request.json
    symptom = data.get('symptom')
    result = chatbot.handle_symptom_medicine_request(symptom)
    return jsonify(result)

@app.route('/record_feedback', methods=['POST'])
def record_feedback():
    data = request.json
    mistake_type = data.get('mistake_type')
    original_mistake = data.get('original_mistake')
    correct_answer = data.get('correct_answer')
    result = chatbot.record_feedback(mistake_type, original_mistake, correct_answer)
    return jsonify(result)

@app.route('/response_type', methods=['POST'])
def response_type():
    data = request.json
    user_input = data.get('user_input')
    response_type = chatbot.get_response_type(user_input)
    return jsonify({'response_type': response_type})


@app.route('/respond_dynamically', methods=['POST'])
def respond_dynamically():
    data = request.json
    message = data.get('message')
    response = chatbot.respond_dynamically(message)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)