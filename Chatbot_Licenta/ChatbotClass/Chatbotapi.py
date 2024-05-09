import pandas as pd
import hashlib
from datetime import datetime, timedelta
import ast
from fuzzywuzzy import process, fuzz
import random


class ChatbotAPI:
    def __init__(self, users_csv, diseases_csv, medicines_csv, responses_csv, mistakes_csv, doctor_schedule_csv):
        self.users_csv = users_csv
        self.diseases_csv = diseases_csv
        self.medicines_csv = medicines_csv
        self.responses_csv = responses_csv
        self.mistakes_csv = mistakes_csv
        self.doctor_schedule_csv = doctor_schedule_csv

        self.users_df = self.load_csv(self.users_csv,['Username', 'Password', 'Age', 'Weight', 'Height', 'Type', 'LastLogin','CreationDate', 'Specialty', 'LastUpdate'])
        self.medicines_df = self.load_csv(self.medicines_csv,['Denumirea comerciala', 'DCI', 'Forma', 'Conc', 'Firma / Tara detinatoare','Ambalaj', 'Pres.', 'ATC', 'Doza_Adult', 'Doza_Copil', 'Simptome_combatute'])
        self.responses_df = self.load_csv(self.responses_csv, ['Keywords', 'ResponseType', 'Response'])
        self.mistakes_df = self.load_csv(self.mistakes_csv,['mistake_type', 'original_mistake', 'correct_answer', 'reporters', 'admin_reviews'])
        self.diseases_df = self.load_csv(self.diseases_csv, ['cod_999','boala_denumire','simptome','medicamentatie','medic_specialist','Urgency','probabilitate'])
        self.doctor_schedule_df = self.load_csv(self.doctor_schedule_csv, ['Username','Date','AppointmentHour','PatientUsername', 'Status'])
        self.mistakes_df = pd.read_csv(self.mistakes_csv)
        if 'admin_reviews' in self.mistakes_df.columns:
            self.mistakes_df['admin_reviews'] = self.mistakes_df['admin_reviews'].apply(ast.literal_eval)
        else:
            self.mistakes_df['admin_reviews'] = [[] for _ in range(len(self.mistakes_df))]

        self.current_user = None
        self.current_user_type = None
        self.current_user_age = None  # Add an attribute to store the current user's age
        self.preprocess_medicine_names()
        self.load_response_mapping()

    def get_user(self, username):
        user_df = self.users_df[self.users_df['Username'] == username]
        if not user_df.empty:
            user = user_df.iloc[0].to_dict()
            return user
        return None
    def load_response_mapping(self):
        self.response_mapping = {}
        for _, row in self.responses_df.iterrows():
            keywords = row['Keywords'].split('.')  # Assuming keywords are period-separated
            for keyword in keywords:
                self.response_mapping[keyword.strip().lower()] = row['ResponseType']

    def get_response_type(self, user_input):
        user_input = user_input.lower()
        for keyword, response_type in self.response_mapping.items():
            if keyword in user_input:
                return response_type
        return "unknown"

    def respond_dynamically(self, message):
        intent, _ = process.extractOne(message, self.responses_df['Keywords'].unique())
        responses = self.responses_df[self.responses_df['Keywords'] == intent]['Response'].tolist()
        if responses:
            return random.choice(responses)
        else:
            return "I'm not sure how to respond to that. Can you tell me more?"

    def load_csv(self, file_path, columns):
        try:
            return pd.read_csv(file_path)
        except FileNotFoundError:
            print(f"File {file_path} not found. Using empty DataFrame with columns {columns}.")
            return pd.DataFrame(columns=columns)
        except pd.errors.ParserError:
            print(f"Error parsing {file_path}. Check if the CSV format is correct.")
            return pd.DataFrame(columns=columns)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, hashed_password, user_password):
        return hashed_password == hashlib.sha256(user_password.encode()).hexdigest()

    def register_user(self, username, password, age, weight, height, special_password):
        if username in self.users_df['Username'].values:
            return "This username is already taken. Please choose a different one."

        hashed_password = self.hash_password(password)
        user_type = "Customer"
        specialty = None
        if special_password == "12345678":
            user_type = "Admin"
        elif special_password == "87654321":
            user_type = "Doctor"
            specialty = "General"  # Assuming a default speciality, modify as needed

        new_user = {
            'Username': username, 'Password': hashed_password, 'Age': age, 'Weight': weight,
            'Height': height, 'Type': user_type, 'LastLogin': datetime.now(), 'CreationDate': datetime.now(),
            'Specialty': specialty, 'LastUpdate': datetime.now()
        }
        self.users_df = pd.concat([self.users_df, pd.DataFrame([new_user])], ignore_index=True)
        self.users_df.to_csv(self.users_csv, index=False)
        self.current_user= username
        self.current_user_type=user_type
        self.current_user_age = age
        return f"Welcome, {username}! You have been registered as a {user_type}."

    def login_user(self, username, password):
        user_df = self.users_df[self.users_df['Username'] == username]
        if user_df.empty:
            return "Invalid username or password."

        user = user_df.iloc[0]
        if self.check_password(user['Password'], password):
            self.current_user = username
            self.current_user_type = user['Type']
            self.current_user_age = user['Age']  # Set the current user's age

            return f"Welcome back, {username}!"
        else:
            return "Invalid username or password."

    def review_mistakes(self):
        if self.current_user_type != 'Admin':
            return "Only admins can review mistakes."

        to_review = self.mistakes_df[(self.mistakes_df['reporters'].apply(lambda x: len(x) >= 1)) &
                                     (~self.mistakes_df['admin_reviews'].apply(lambda x: self.current_user in x))]
        if to_review.empty:
            return "No new mistakes to review."

        reviews = []
        for index, mistake in to_review.iterrows():
            reviews.append({
                "Mistake ID": index,
                "Type": mistake['mistake_type'],
                "Original": mistake['original_mistake'],
                "Proposed Correction": mistake['correct_answer'],
                "Affected Fields": self.determine_fields_affected(mistake['mistake_type'])
            })
        return reviews

    def process_mistake_review(self, mistake_id, approve_correction):
        if self.current_user_type != 'Admin':
            return "Unauthorized action. Only admins can process mistakes."

        try:
            mistake = self.mistakes_df.loc[mistake_id]
        except KeyError:
            return "Mistake not found."

        admin_reviews = mistake.get('admin_reviews', [])
        if isinstance(admin_reviews, str):
            admin_reviews = ast.literal_eval(admin_reviews)

        admin_reviews.append(self.current_user)
        self.mistakes_df.at[mistake_id, 'admin_reviews'] = admin_reviews

        if approve_correction:
            # Correctly specify CSV paths based on mistake type
            if mistake['mistake_type'] == 'medicine':
                csv_path = self.medicines_csv
                columns = ["Denumirea comerciala", "DCI", "Forma", "Conc", "Firma / Tara detinatoare", "Ambalaj",
                           "Pres.", "ATC", "Doza_Adult", "Doza_Copil", "Simptome_combatute"]
                match_index = 0  # Assuming 'Denumirea comerciala' is the key field for matching
            elif mistake['mistake_type'] == 'disease':
                csv_path = self.diseases_csv
                columns = ["cod_999", "boala_denumire", "simptome", "medicamentatie", "medic_specialist", "Urgency",
                           "probabilitate"]
                match_index = 1  # Assuming 'boala_denumire' is the key field for matching
            else:
                return "Unknown mistake type."

            # Call update_csv with the correct parameters and file path
            result = self.update_csv(mistake, csv_path, columns, match_index)
            if result:
                self.mistakes_df = self.mistakes_df.drop(mistake_id)
                self.mistakes_df.to_csv(self.mistakes_csv, index=False)
                return "Correction approved and processed, mistake removed from review list."
            else:
                return "Failed to apply correction."
        else:
            self.mistakes_df = self.mistakes_df.drop(mistake_id)
            self.mistakes_df.to_csv(self.mistakes_csv, index=False)
            return "Correction rejected, mistake removed from review list."

    def determine_fields_affected(self, mistake_type):
        if mistake_type == 'medicine':
            return ["Denumirea comerciala", "DCI", "Forma", "Conc", "Firma / Tara detinatoare", "Ambalaj", "Pres.",
                    "ATC", "Doza_Adult", "Doza_Copil", "Simptome_combatute"]
        elif mistake_type == 'disease':
            return ["cod_999", "boala_denumire", "simptome", "medicamentatie", "medic_specialist", "Urgency",
                    "probabilitate"]
        return []

    def update_doctor_specialty(self, new_specialty):
        if self.current_user_type != 'Doctor':
            return "Only doctors can update their specialty."

        self.users_df.loc[self.users_df['Username'] == self.current_user, 'Specialty'] = new_specialty
        self.users_df.to_csv(self.users_csv, index=False)
        return f"Specialty updated to {new_specialty}."

    def check_health_update_needed(self, username):
        user_df = self.users_df[self.users_df['Username'] == username]
        if user_df.empty:
            return "User not found."

        user = user_df.iloc[0]
        creation_date = datetime.strptime(user['CreationDate'], '%Y-%m-%d %H:%M:%S.%f')
        last_update_str = user.get('LastUpdate')

        current_date = datetime.now()
        last_update = None if pd.isna(last_update_str) else datetime.strptime(last_update_str, '%Y-%m-%d %H:%M:%S.%f')

        # Check if today is the creation day of the month
        if current_date.day == creation_date.day:
            return "Health profile needs update to health parameters."

        # Check if last update is missing or more than a month ago
        if last_update is None or current_date - last_update > timedelta(days=30):
            return "Health profile needs update to health parameters."

        return "Your health profile is up to date."

    def update_user_health(self, username, age, weight, height):
        try:
            # Ensure username exists
            if username not in self.users_df['Username'].values:
                return "Username not found."

            user_index = self.users_df[self.users_df['Username'] == username].index[0]
            self.users_df.at[user_index, 'Age'] = age
            self.users_df.at[user_index, 'Weight'] = weight
            self.users_df.at[user_index, 'Height'] = height
            self.users_df.at[user_index, 'LastUpdate'] = datetime.now()
            self.users_df.to_csv(self.users_csv, index=False)
            return "Your health profile is up to date."
        except Exception as e:
            return f"An error occurred: {str(e)}"
    def update_csv(self, mistake, csv_path, columns, match_column_index):
        data_df = pd.read_csv(csv_path)
        correct_info = mistake['correct_answer'].split(':')  # Assuming ':' as the delimiter

        if len(correct_info) != len(columns):
            return "Error: Correction information does not match the expected number of columns."

        row_indices = data_df[data_df[columns[match_column_index]] == mistake['original_mistake']].index
        if row_indices.empty:
            return "No matching record found to update."

        for idx in row_indices:
            for col, info in zip(columns, correct_info):
                try:
                    data_df.at[idx, col] = self.cast_value(info, data_df[col].dtype)
                except ValueError as e:
                    return f"Error converting {info} to {data_df[col].dtype}: {e}"

        data_df.to_csv(csv_path, index=False)
        return f"Updated {csv_path} successfully."

    def cast_value(self, value, dtype):
        if pd.api.types.is_integer_dtype(dtype):
            return int(value)
        elif pd.api.types.is_float_dtype(dtype):
            return float(value)
        elif pd.api.types.is_string_dtype(dtype):
            return str(value)
        else:
            return value

    def list_possible_symptoms(self):
        # Collect unique symptoms from the diseases dataframe
        unique_symptoms = set()
        for symptoms_list in self.diseases_df['simptome'].dropna():
            [unique_symptoms.add(symptom.strip().lower()) for symptom in symptoms_list.split('.')]
        return list(unique_symptoms)

    def diagnose_symptoms(self, user_symptoms):
        # Calculates disease probabilities based on symptoms
        disease_symptom_count = {}
        total_symptoms_per_disease = {}
        for user_symptom in user_symptoms:
            for index, row in self.diseases_df.iterrows():
                disease_symptoms = row['simptome'].split('.')
                total_symptoms_per_disease[row['boala_denumire']] = len(disease_symptoms)
                for disease_symptom in disease_symptoms:
                    if user_symptom.strip().lower() in disease_symptom.strip().lower():
                        if row['boala_denumire'] not in disease_symptom_count:
                            disease_symptom_count[row['boala_denumire']] = 0
                        disease_symptom_count[row['boala_denumire']] += 1

        # Compute probabilities by averaging symptom match ratio and base disease probability
        diseases = []
        for disease, match_count in disease_symptom_count.items():
            if match_count >= 2:
                symptom_match_ratio = match_count / total_symptoms_per_disease[disease]
                base_probability = self.calculate_probability(disease)
                final_probability = (
                                                symptom_match_ratio + base_probability / 100) / 2  # Averaging match ratio and base probability
                final_probability *= 100  # Convert to percentage
                specialist = self.get_specialists(disease)
                diseases.append({
                    'disease': disease,
                    'probability': f"{final_probability:.2f}%",
                    'specialist': specialist
                })

        return diseases

    def suggest_medication(self, disease):
        # Retrieves medication information based on the diagnosed disease
        medication = self.diseases_df[self.diseases_df['boala_denumire'] == disease]['medicamentatie'].iloc[0]
        if pd.isna(medication):
            return f"No specific medication recommended for {disease}. Please consult a healthcare provider."
        return f"For {disease}, consider taking: {medication}"
    def calculate_probability(self, disease):
        probability_str = self.diseases_df[self.diseases_df['boala_denumire'] == disease]['probabilitate'].iloc[0]
        numerator, denominator = map(float, probability_str.split('/'))
        return (numerator / denominator) * 100  # Convert to percentage

    def get_specialists(self, disease):
        # Retrieve the specialist based on the disease diagnosed
        specialist = self.diseases_df[self.diseases_df['boala_denumire'] == disease].iloc[0]['medic_specialist']
        return specialist

    def get_doctor_schedule(self, username):
        # Get the schedule for the next three days for the specified doctor
        current_date = datetime.now().date()
        doctor_schedule = {}
        for i in range(3):
            day = current_date + timedelta(days=i)
            day_schedule = self.doctor_schedule_df[
                (self.doctor_schedule_df['Username'] == username) &
                (self.doctor_schedule_df['Date'] == day.strftime('%Y-%m-%d'))
                ]
            if not day_schedule.empty:
                doctor_schedule[day.strftime('%Y-%m-%d')] = day_schedule['AvailableSlots'].tolist()
            else:
                doctor_schedule[day.strftime('%Y-%m-%d')] = ['Open']
        return doctor_schedule

    def book_appointment(self, doctor_username, date, hour):
        if not self.current_user:
            return "No user is currently logged in."

        date = datetime.strptime(date, '%y/%m/%d').date()  # Ensure date is in the correct format

        if self.is_slot_available(doctor_username, date, hour):
            new_entry = pd.DataFrame({
                'Username': [doctor_username],
                'Date': [date.strftime('%y/%m/%d')],
                'AppointmentHour': [hour],
                'PatientUsername': [self.current_user]  # Use the currently logged-in user
            })

            # Update the schedule DataFrame
            self.doctor_schedule_df = pd.concat([self.doctor_schedule_df, new_entry], ignore_index=True)
            self.doctor_schedule_df.to_csv(self.doctor_schedule_csv, index=False)
            return f"Appointment booked with Dr. {doctor_username} for {self.current_user} on {date.strftime('%y/%m/%d')} at {hour}."
        else:
            return "This slot is already booked. Please choose another slot."

    def is_slot_available(self, username, date, hour):
        # Check availability of the slot
        matches = self.doctor_schedule_df[
            (self.doctor_schedule_df['Username'] == username) &
            (self.doctor_schedule_df['Date'] == date.strftime('%y/%m/%d')) &
            (self.doctor_schedule_df['AppointmentHour'] == hour)
]
        return matches.empty
    def find_specialists_by_disease(self, disease):
        # Fetch the required specialty for the given disease
        try:
            required_specialty = self.diseases_df[self.diseases_df['boala_denumire'].str.lower() == disease.lower()]['medic_specialist'].iloc[0]
        except IndexError:
            return []  # No disease found with that name, or no specialist defined

        # Filter doctors who specialize in the required specialty
        matching_doctors = self.users_df[self.users_df['Specialty'].str.lower() == required_specialty.lower()]
        if matching_doctors.empty:
            return []

        # Format the list of specialists to return
        specialists_list = matching_doctors[['Username', 'Specialty']].to_dict(orient='records')
        return specialists_list

    def preprocess_medicine_names(self):
        # Extract base name by selecting the first part before any dosage or unit information
        self.medicines_df['Simple Name'] = self.medicines_df['Denumirea comerciala'].apply(
            lambda x: x.split()[0].upper())
        # Create a dictionary mapping simple names to their respective full commercial names
        self.simple_to_full_name = \
        self.medicines_df[['Simple Name', 'Denumirea comerciala']].drop_duplicates().set_index('Simple Name')[
                'Denumirea comerciala'].to_dict()
    def provide_medicine_info(self, medicine_name):
        if not medicine_name:
            return {"message": "No medicine name provided. Exiting the medicine info request."}

        # Case-insensitive exact match from user-confirmed or directly provided input
        medicine_name = medicine_name.lower()
        matches = self.medicines_df[self.medicines_df['Denumirea comerciala'].str.lower() == medicine_name]

        if matches.empty:
            return {
                "message": "Sorry, we couldn't find any information on the requested medicine. Please check the spelling or try another name."
            }
        else:
            medicine_info_list = []
            for index, medicine_info in matches.iterrows():
                info = {column.replace('_', ' '): medicine_info[column] for column in matches.columns if
                        pd.notna(medicine_info[column]) and medicine_info[column] != ''}
                medicine_info_list.append(info)
            return {"message": f"Found {len(matches)} medicine(s) with the name '{medicine_name}':",
                    "data": medicine_info_list}

    def get_user_medicine(self, medicine_input):
        if 'Simple Name' not in self.medicines_df.columns:
            self.preprocess_medicine_names()
        unique_medicines = list(self.medicines_df['Simple Name'].str.upper().unique())

        possible_matches = process.extractBests(medicine_input.upper(), unique_medicines, scorer=fuzz.token_sort_ratio,
                                                limit=5)

        if possible_matches:
            suggestions = []
            for match, score in possible_matches:
                full_medicine_name = self.simple_to_full_name.get(match, match)
                suggestions.append({"name": full_medicine_name, "score": score})
            return {"suggestions": suggestions}
        else:
            return {"message": "No close matches found. Please try again."}

    def handle_symptom_medicine_request(self, symptom):
        if not self.current_user:
            return {"message": "No user is currently logged in."}

        # Ensure symptom is in lower case for matching
        symptom = symptom.lower().strip()

        # Filter medicines based on the provided symptom
        matched_medicines = self.medicines_df[self.medicines_df['Simptome_combatute'].str.lower().str.contains(symptom)]

        if matched_medicines.empty:
            return {"message": "No medicines found for the provided symptom."}
        else:
            medicines_info = []
            unique_simple_names = set()
            for index, medicine_info in matched_medicines.iterrows():
                # Get the simple name of the medicine
                simple_name = medicine_info['Denumirea comerciala'].split()[0].upper()
                unique_simple_names.add(simple_name)

            for simple_name in unique_simple_names:
                # Get the full name of the medicine from the dataframe
                full_name = matched_medicines[matched_medicines['Denumirea comerciala'].str.startswith(simple_name)][
                    'Denumirea comerciala'].iloc[0]
                # Get the appropriate dosage based on age
                dosage_column = 'Doza_Adult' if self.current_user_age > 16 else 'Doza_Copil'
                dosage = matched_medicines[matched_medicines['Denumirea comerciala'].str.startswith(simple_name)][
                    dosage_column].iloc[0]
                medicines_info.append({"medicine": full_name, "dosage": dosage})

            return {"medicines": medicines_info}

    def record_feedback(self, mistake_type, original_mistake, correct_answer):
        if self.current_user is None or self.current_user_type not in ['Doctor', 'Admin']:
            return {"message": "You must be a Doctor or Admin to provide feedback."}

        required_columns = {'mistake_type', 'original_mistake', 'correct_answer', 'reporters', 'admin_reviews'}
        missing_columns = required_columns - set(self.mistakes_df.columns)
        for column in missing_columns:
            if column in ['reporters', 'admin_reviews']:
                self.mistakes_df[column] = self.mistakes_df.apply(lambda x: [], axis=1)
            else:
                self.mistakes_df[column] = pd.NA

        new_record = pd.DataFrame([{
            'mistake_type': mistake_type,
            'original_mistake': original_mistake,
            'correct_answer': correct_answer,
            'reporters': [self.current_user],
            'admin_reviews': []
        }])

        self.mistakes_df = pd.concat([self.mistakes_df, new_record], ignore_index=True)

        try:
            self.mistakes_df.to_csv(self.mistakes_csv, index=False)
            return {"message": f"Data successfully written to {self.mistakes_csv}."}
        except Exception as e:
            return {"message": f"Failed to write data to CSV: {e}"}