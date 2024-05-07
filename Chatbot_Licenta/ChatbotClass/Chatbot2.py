import pandas as pd
from fuzzywuzzy import process, fuzz
import random
from datetime import datetime, timedelta
import hashlib
import ast


class Chatbot:
    def __init__(self, users_csv, diseases_csv, medicines_csv, responses_csv, mistakes_csv, doctor_schedule_csv):
        self.users_csv = users_csv
        self.diseases_csv = diseases_csv
        self.medicines_csv = medicines_csv
        self.responses_csv = responses_csv
        self.mistakes_csv = mistakes_csv
        self.diseases_df = pd.read_csv(diseases_csv)
        self.doctor_schedule_csv = doctor_schedule_csv
        self.doctor_schedule_df = self.load_csv(doctor_schedule_csv, ['Username', 'Date', 'AvailableSlots'])

        self.users_df = self.load_csv(self.users_csv, ['Username', 'Password', 'Age', 'Weight', 'Height', 'Type', 'LastLogin', 'CreationDate' 'Specialty'])
        self.medicines_df = self.load_csv(self.medicines_csv, ['Denumirea comerciala', 'DCI', 'Forma', 'Conc', 'Firma / Tara detinatoare,Ambalaj', 'Pres.', 'ATC', 'Doza_Adult','Doza_Copil','Simptome_combatute'])
        self.responses_df = self.load_csv(self.responses_csv, ['Keywords', 'ResponseType', 'Response'])
        self.mistakes_df = self.load_csv(self.mistakes_csv, ['mistake_type', 'original_mistake', 'correct_answer', 'reporters', 'admin_reviews'])
        # Assuming mistakes_df is your DataFrame
        if 'reporters' not in self.mistakes_df.columns:
            self.mistakes_df['reporters'] = [[] for _ in range(len(self.mistakes_df))]
        if 'admin_reviews' not in self.mistakes_df.columns:
            self.mistakes_df['admin_reviews'] = [[] for _ in range(len(self.mistakes_df))]

        self.current_user = None




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
        """Hash a password for storing."""
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, hashed_password, user_password):
        """Verify a stored password against one provided by user."""
        return hashed_password == hashlib.sha256(user_password.encode()).hexdigest()

    def login_or_register(self):
        user_action = input("Do you want to (login) or (register)? ").lower().strip()
        while user_action not in ["login", "register"]:
            print("Please type 'login' or 'register'.")
            user_action = input("Do you want to (login) or (register)? ").lower().strip()

        if user_action == "login":
            self.login_user()
        elif user_action == "register":
            self.register_user()
        else:
            print("Invalid action. Please type 'login' or 'register'.")


    def register_user(self):
        username = input("Choose a username: ")
        # Check if username is unique
        if (username == self.users_df['Username']).any():
            print("This username is already taken. Please choose a different one.")
            return

        password = input("Choose a password: ")
        age = input("Enter your age: ")
        weight = input("Enter your weight (kg): ")
        height = input("Enter your height (cm): ")
        # Special password prompt
        special_password = input("Enter the special password (leave blank if you are a customer): ")

        user_type = "Customer"  # Default user type
        if special_password == "12345678":
            user_type = "Admin"
        elif special_password == "87654321":
            user_type = "Doctor"
            # Ask for doctor's speciality
            speciality = input("Enter your speciality: ").strip().upper()
            while not speciality:
                print("Speciality cannot be empty.")
                speciality = input("Enter your speciality: ").strip().upper()

        hashed_password = self.hash_password(password)  # Use the internal method to hash the password
        creation_date = datetime.now()
        new_user = {
            'Username': username, 'Password': hashed_password, 'Age': age,
            'Weight': weight, 'Height': height, 'Type': user_type,
            'LastLogin': creation_date, 'CreationDate': creation_date
        }
        if user_type == "Doctor":
            new_user['Speciality'] = speciality
        self.users_df = pd.concat([self.users_df, pd.DataFrame([new_user])], ignore_index=True)
        self.users_df.to_csv(self.users_csv, index=False)
        self.current_user = username
        print(f"Welcome, {username}! You have been registered as a {user_type}.")
    def login_user(self):
        username = input("Username: ")
        password = input("Password: ")

        user = self.users_df[self.users_df['Username'] == username].iloc[0]
        if self.check_password(user['Password'], password):  # Use the internal method
            self.current_user = username
            print(f"Welcome back, {username}!")
            self.check_health_update_needed(user)

            # If the user is an Admin, prompt for mistake review
            if user['Type'] == 'Admin':
                self.review_mistakes()
        else:
            print("Invalid username or password.")

    def review_mistakes(self):
        # Correct handling of lists stored in CSV
        for column in ['reporters', 'admin_reviews']:
            if column in self.mistakes_df.columns:
                self.mistakes_df[column] = self.mistakes_df[column].apply(
                    lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

        to_review = self.mistakes_df[(self.mistakes_df['reporters'].apply(lambda x: len(x) >= 1)) & (
            ~self.mistakes_df['admin_reviews'].apply(lambda x: self.current_user in x))]

        if to_review.empty:
            print("No new mistakes to review.")
            return

        for index, mistake in to_review.iterrows():
            print(
                f"Mistake ID: {index}, Type: {mistake['mistake_type']}, Original: {mistake['original_mistake']}, Correction: {mistake['correct_answer']}")
            action = input("Approve correction? (yes/no): ").lower()

            if action == 'yes':
                print("Correction approved and processed.")
                if mistake['mistake_type'] == 'medicine':
                    self.update_csv(mistake, self.medicines_csv, [
                        "Denumirea comerciala", "DCI", "Forma", "Conc", "Firma / Tara detinatoare", "Ambalaj", "Pres.",
                        "ATC", "Doza_Adult", "Doza_Copil", "Simptome_combatute"
                    ], 0)  # 0 is the index for "Denumirea comerciala"
                elif mistake['mistake_type'] == 'disease':
                    self.update_csv(mistake, self.diseases_csv, [
                        "cod_999", "boala_denumire", "simptome", "medicamentatie", "medic_specialist", "Urgency",
                        "probabilitate"
                    ], 1)  # 1 is the index for "boala_denumire"
            else:
                print("Correction rejected.")

            admin_reviews = self.mistakes_df.at[index, 'admin_reviews']
            admin_reviews.append(self.current_user)
            self.mistakes_df.at[index, 'admin_reviews'] = admin_reviews

        self.mistakes_df.to_csv(self.mistakes_csv, index=False)

    def update_csv(self, mistake, csv_path, columns, match_column_index):
        data_df = pd.read_csv(csv_path)
        correct_info = mistake['correct_answer'].split(':')  # Using ':' based on your example

        # Check that correction info matches expected columns
        if len(correct_info) != len(columns):
            print("Error: Correction information does not match the expected number of columns.")
            return

        # Attempt to locate the record
        row_indices = data_df[data_df[columns[match_column_index]] == mistake['original_mistake']].index
        if not row_indices.empty:
            for idx in row_indices:  # This handles multiple or single index cases
                for col, value in zip(columns, correct_info):
                    # Check the data type of the column and cast value accordingly
                    col_dtype = data_df[col].dtype
                    try:
                        if pd.api.types.is_integer_dtype(col_dtype):
                            value = int(value)  # Convert value to integer if column is integer type
                        elif pd.api.types.is_float_dtype(col_dtype):
                            value = float(value)  # Convert value to float if column is float type
                        elif pd.api.types.is_string_dtype(col_dtype):
                            value = str(value)  # Keep value as string if column is string type
                        data_df.at[idx, col] = value
                    except ValueError as e:
                        print(f"Error converting {value} to {col_dtype}: {e}")

            data_df.to_csv(csv_path, index=False)
            print(f"Updated {csv_path} successfully.")
        else:
            print("No matching record found to update.")
    def check_health_update_needed(self, user):
        last_update = datetime.strptime(user['LastLogin'], '%Y-%m-%d %H:%M:%S.%f')
        if datetime.now() > last_update + timedelta(days=30):
            print("It's been a while since your last health profile update.")

            # Convert input values to integers before assigning them to DataFrame
            age = int(input("Please enter your age: "))
            weight = int(input("Please enter your weight (kg): "))
            height = int(input("Please enter your height (cm): "))

            user_index = self.users_df[self.users_df['Username'] == self.current_user].index[0]

            # Update the user's information with correctly typed values
            self.users_df.loc[user_index, 'Age'] = age
            self.users_df.loc[user_index, 'Weight'] = weight
            self.users_df.loc[user_index, 'Height'] = height
            self.users_df.loc[user_index, 'LastLogin'] = datetime.now()

            self.users_df.to_csv(self.users_csv, index=False)
            print("Health profile updated.")
        else:
            print("Your health profile is up to date.")

    def provide_medicine_info(self):
        print("Please provide the name of the medicine you want to learn about.")
        medicine_name = self.get_user_medicine()

        if not medicine_name:
            print("No medicine name provided. Exiting the medicine info request.")
            return

        # Case-insensitive exact match from user-confirmed or directly provided input
        medicine_name = medicine_name.lower()
        matches = self.medicines_df[self.medicines_df['Denumirea comerciala'].str.lower() == medicine_name]

        if matches.empty:
            print(
                "Sorry, we couldn't find any information on the requested medicine. Please check the spelling or try another name.")
        else:
            print(f"Found {len(matches)} medicine(s) with the name '{medicine_name}':")
            for index, medicine_info in matches.iterrows():
                print("\nMedicine Information:")
                for column in matches.columns:
                    if pd.notna(medicine_info[column]) and medicine_info[column] != '':
                        print(f"{column.replace('_', ' ')}: {medicine_info[column]}")

    def preprocess_medicine_names(self):
        # Extract base name by selecting the first part before any dosage or unit information
        self.medicines_df['Simple Name'] = self.medicines_df['Denumirea comerciala'].apply(
            lambda x: x.split()[0].upper())
        # Create a dictionary mapping simple names to their respective full commercial names
        self.simple_to_full_name = \
        self.medicines_df[['Simple Name', 'Denumirea comerciala']].drop_duplicates().set_index('Simple Name')[
            'Denumirea comerciala'].to_dict()

    def get_user_medicine(self):
        if 'Simple Name' not in self.medicines_df.columns:
            self.preprocess_medicine_names()
        unique_medicines = list(self.medicines_df['Simple Name'].str.upper().unique())

        while True:
            medicine_input = input(
                "Enter the medicine name you're looking for (or 'done' if you're finished): ").strip().upper()
            if medicine_input == 'done':
                return None

            possible_matches = process.extractBests(medicine_input, unique_medicines, scorer=fuzz.token_sort_ratio,
                                                    limit=5)

            if possible_matches:
                print("Did you mean one of these?")
                for i, (match, score) in enumerate(possible_matches):
                    full_medicine_name = self.simple_to_full_name.get(match, match)
                    print(f"{i + 1}. {full_medicine_name} ({score}%)")

                choice = input(
                    "Please enter the number or name of the correct medicine from the list above, or type 'retry' to try again: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(possible_matches):
                    selected_medicine = possible_matches[int(choice) - 1][0]  # Get simple name from matches
                    full_medicine_name = self.simple_to_full_name[
                        selected_medicine]  # Map simple name to full name correctly
                    return full_medicine_name
                elif any(choice.lower() == match[0].lower() for match in possible_matches):
                    return self.simple_to_full_name[choice.upper()]
                elif choice.lower() == 'retry':
                    continue
                else:
                    print("Invalid selection, please try again.")
            else:
                print("No close matches found. Please try again.")


    def load_response_mapping(self):
        # Maps keywords to response types for dynamic lookup
        self.response_mapping = {}
        for _, row in self.responses_df.iterrows():
            keywords = row['Keywords'].split('.')  # Assuming keywords are comma-separated
            for keyword in keywords:
                self.response_mapping[keyword.strip().lower()] = row['ResponseType']

    def get_response_type(self, user_input):
        # Determine the response type based on keywords in the user input
        for keyword, response_type in self.response_mapping.items():
            if keyword in user_input:
                return response_type
        return "unknown"  # Default if no keywords match

    def start(self):
        self.login_or_register()
        print("Hello! How may I assist you today?")

        self.load_response_mapping()  # Load the response mapping

        while self.current_user:
            user_input = input("\nYou: ").strip().lower()
            response_type = self.get_response_type(user_input)

            if response_type == "diagnostic":
                self.diagnose_symptom()
            elif response_type == "medicine":
                self.provide_medicine_info()
            elif response_type == "symptom_medicine":
                user_age = int(self.users_df[self.users_df['Username'] == self.current_user]['Age'].iloc[0])

                self.handle_symptom_medicine_request(user_age)
            elif response_type == "mistake":
                self.record_feedback()
            if any(phrase in user_input for phrase in ["thank you", "bye", "that will be all", "logout"]):
                print("You're welcome! I'm here whenever you need assistance. Goodbye for now.")
                break
            else:
                self.respond_dynamically(user_input)

    def handle_symptom_medicine_request(self, user_age):
        print("Please specify the symptom you're experiencing, and I'll help find suitable medicine.")
        symptom = input("Symptom: ").lower().strip()

        # Filter medicines based on the provided symptom
        matched_medicines = self.medicines_df[self.medicines_df['Simptome_combatute'].str.lower().str.contains(symptom)]

        if matched_medicines.empty:
            print("No medicines found for the provided symptom.")
        else:
            print("Medicines for the provided symptom:")
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
                dosage_column = 'Doza_Adult' if user_age > 16 else 'Doza_Copil'
                dosage = matched_medicines[matched_medicines['Denumirea comerciala'].str.startswith(simple_name)][
                    dosage_column].iloc[0]
                print(f"Medicine: {full_name}, Dosage: {dosage}")
    def get_user_symptom(self):
            unique_symptoms = set()
            # Split symptoms in the DataFrame and create a unique list
            for symptoms_list in self.diseases_df['simptome']:
                for symptom in symptoms_list.split('.'):
                    unique_symptoms.add(symptom.strip().lower())

            while True:
                symptom_input = input("Enter your symptom (or 'done' if no more symptoms): ").strip().lower()
                if symptom_input == 'done':
                    break

                # Directly return the symptom if it exactly matches a known symptom (ignoring case)
                if symptom_input in unique_symptoms:
                    return symptom_input

                # Use fuzzy matching to find the closest symptom if there is no exact match
                matched_symptom, score = process.extractOne(symptom_input, list(unique_symptoms))

                # Only ask for confirmation if the match score is below a certain threshold to handle potential misspellings
                if score < 100:
                    confirmation = input(f"Did you mean {matched_symptom}? (Y/n): ").strip().lower()
                    if confirmation == 'y' or confirmation == '':
                        return matched_symptom  # Return the corrected symptom upon confirmation
                    else:
                        print("Symptom not recognized. Please try again.")
                else:
                    # If the score is 100, it means the match is exact or very close, so return it without asking
                    return matched_symptom
    def recommend_specialist_based_on_urgency(self, disease, urgency):
        # Fetch the medical specialist for the given disease
        specialist = self.diseases_df[self.diseases_df['boala_denumire'] == disease]['medic_specialist'].iloc[0]

        if urgency == "Urgent":
            print(
                f"This condition may require urgent attention. Please consider visiting a {specialist} as soon as possible.")
        elif urgency == "Semi-urgent":
            print(f"It's advisable to see a {specialist} soon. Your condition appears to be semi-urgent.")
        else:  # Not really urgent
            print(f"Your condition doesn't seem to be urgent, but if symptoms persist, consider seeing a {specialist}.")

    def diagnose_symptom(self):
        print("Let's identify your condition based on the symptoms you describe.")
        symptoms = []
        while True:
            symptom = self.get_user_symptom()
            if not symptom:
                break
            symptoms.append(symptom)

        if len(symptoms) < 2:
            print("At least two symptoms are needed for a more accurate diagnosis.")
            return

        disease_probabilities = self.calculate_disease_probabilities(symptoms)
        if not disease_probabilities:
            print(
                "We couldn't identify your condition based on the symptoms provided. Consulting a doctor is recommended.")
            return

        print("Based on your symptoms, here are the possible conditions and their respective probabilities:")
        for disease, probability in sorted(disease_probabilities.items(), key=lambda x: x[1], reverse=True):
            print(f"- {disease}: {probability:.2f}% probability")
            urgency = self.diseases_df[self.diseases_df['boala_denumire'] == disease]['Urgency'].iloc[0]
            self.recommend_specialist_based_on_urgency(disease, urgency)
            self.suggest_medication(disease)
        appointment_choice = input(
            "Would you like to make an appointment with a specialist? (yes/no): ").lower().strip()
        if appointment_choice == "yes":
            self.make_specialist_appointment(disease)
    def make_specialist_appointment(self, disease):
        specialist_type = self.diseases_df[self.diseases_df['boala_denumire'] == disease]['medic_specialist'].iloc[0]
        print(f"We need to find a {specialist_type} specialist for your condition.")

        # Find users who are doctors and specialize in the required field
        matching_doctors = self.users_df[
            (self.users_df['Type'] == 'Doctor') & (self.users_df['Specialty'] == specialist_type)]

        if matching_doctors.empty:
            print("Sorry, no specialist available for this condition.")
            return

        print("Available specialists:")
        for idx, doctor in matching_doctors.iterrows():
            print(f"{idx}: {doctor['Username']}")

        doctor_choice = input("Please select a doctor by entering the corresponding index: ").strip()

        # Check if the input is a valid index
        if not doctor_choice.isdigit() or int(doctor_choice) not in matching_doctors.index:
            print("Invalid selection. Please select a valid index.")
            return

        doctor_index = int(doctor_choice)
        doctor_username = matching_doctors.loc[doctor_index, 'Username']
        print(f"Appointment will be made with Dr. {doctor_username}.")

        # Proceed to make the appointment
        self.schedule_doctor_appointment(doctor_username)

    def get_doctor_schedule(self, doctor_username):
        # Get the schedule for the next 3 days for the specified doctor
        current_date = datetime.now().date()
        doctor_schedule = []

        for _ in range(3):
            # Check if there is an entry for the current date in the schedule CSV
            schedule_entry = self.doctor_schedule_df[
                (self.doctor_schedule_df['Username'] == doctor_username) &
                (self.doctor_schedule_df['Date'] == current_date)
            ]

            if not schedule_entry.empty:
                # Doctor's schedule for the current date is not empty
                available_slots = schedule_entry['AvailableSlots'].iloc[0]
                doctor_schedule.append(f"{current_date.strftime('%A')}, {available_slots}")
            else:
                # Doctor's schedule for the current date is open
                doctor_schedule.append(f"{current_date.strftime('%A')}, Open")

            # Move to the next day
            current_date += timedelta(days=1)

        return doctor_schedule

    def schedule_doctor_appointment(self, doctor_username):
        # Get doctor's availability and schedule appointment
        doctor_schedule = self.get_doctor_schedule(doctor_username)
        if not doctor_schedule:
            print("Failed to schedule appointment. Please try again later.")
            return

        # Print doctor's available slots
        print(f"Available slots for Dr. {doctor_username}:")
        for idx, slot in enumerate(doctor_schedule, start=1):
            print(f"{idx}: {slot}")

        slot_choice = input("Please select a slot by entering the corresponding index: ").strip()

        # Check if the input is a valid index
        if not slot_choice.isdigit() or int(slot_choice) < 1 or int(slot_choice) > len(doctor_schedule):
            print("Invalid selection. Please select a valid index.")
            return

        selected_slot = doctor_schedule[int(slot_choice) - 1]
        if "Open" in selected_slot:
            # Slot is open, schedule the appointment
            print(f"Appointment with Dr. {doctor_username} scheduled for {selected_slot}.")
            appointment_date = selected_slot.split(',')[0]
            appointment_hour = input("Please enter the appointment hour: ").strip()
            self.update_doctor_schedule(doctor_username, appointment_date, appointment_hour)
        else:
            print("Selected slot is not available. Please choose another slot.")
    def update_doctor_schedule(self, doctor_username, date, appointment_hour):
        # Update the doctor's schedule CSV to mark the selected hour as booked
        new_entry = pd.DataFrame({
            'Username': [doctor_username],
            'Date': [date],
            'AppointmentHour': [appointment_hour]
        })
        self.doctor_schedule_df = pd.concat([self.doctor_schedule_df, new_entry], ignore_index=True)
        self.doctor_schedule_df.to_csv(self.doctor_schedule_csv, index=False)

    def calculate_disease_probabilities(self, symptoms):
        disease_symptom_count = {}
        for symptom in symptoms:
            for _, disease_row in self.diseases_df.iterrows():
                disease_symptoms = disease_row['simptome'].split('.')
                match_count = sum(1 for disease_symptom in disease_symptoms if
                                  symptom.strip().lower() == disease_symptom.strip().lower())
                if match_count > 0:
                    if disease_row['boala_denumire'] in disease_symptom_count:
                        disease_symptom_count[disease_row['boala_denumire']] += match_count
                    else:
                        disease_symptom_count[disease_row['boala_denumire']] = match_count

        # Filter out diseases with less than two matching symptoms and parse fractional probabilities
        disease_probabilities = {}
        for disease, count in disease_symptom_count.items():
            if count >= 2:
                probability_str = self.diseases_df[self.diseases_df['boala_denumire'] == disease]['probabilitate'].iloc[
                    0]
                numerator, denominator = probability_str.split('/')
                probability = (float(numerator) / float(denominator)) * 100  # Convert to percentage
                disease_probabilities[disease] = probability

        return disease_probabilities

    def suggest_medication(self, disease):
        medication = self.diseases_df[self.diseases_df['boala_denumire'] == disease]['medicamentatie'].iloc[0]
        print(f"For {disease}, consider taking: {medication}")

    import pandas as pd

    def record_feedback(self):
        if self.current_user is None or self.users_df[self.users_df['Username'] == self.current_user]['Type'].iloc[0] not in ['Doctor', 'Admin']:
            print("You must be a Doctor or Admin to provide feedback.")
            return

        mistake_type = input("Is this mistake related to a 'medicine' or a 'disease'? ")
        original_mistake = input("Please specify the original information (e.g., row name or disease/medicine name): ")
        correct_answer = input("Please provide the full correct row or information: make sure you use : as delimiterfor the collumns you want also please write all information  ")

        # Ensure all required columns exist and are initialized correctly
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

        # Add new record to DataFrame
        self.mistakes_df = pd.concat([self.mistakes_df, new_record], ignore_index=True)

        print("Current DataFrame state before saving:")
        print(self.mistakes_df)

        try:
            self.mistakes_df.to_csv(self.mistakes_csv, index=False)
            print(f"Data successfully written to {self.mistakes_csv}.")
        except Exception as e:
            print("Failed to write data to CSV:", e)

    def respond_dynamically(self, message):
        intent, _ = process.extractOne(message, self.responses_df['Keywords'].unique())
        responses = self.responses_df[self.responses_df['Keywords'] == intent]['Response'].tolist()
        if responses:
            print(random.choice(responses))
        else:
            print("I'm not sure how to respond to that. Can you tell me more?")
