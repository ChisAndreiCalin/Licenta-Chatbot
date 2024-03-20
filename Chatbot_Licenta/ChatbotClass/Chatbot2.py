import pandas as pd
from fuzzywuzzy import process
import random
from datetime import datetime, timedelta
import hashlib


class Chatbot:
    def __init__(self, users_csv, diseases_csv, medicines_csv, responses_csv, mistakes_csv):
        self.users_csv = users_csv
        self.diseases_csv = diseases_csv
        self.medicines_csv = medicines_csv
        self.responses_csv = responses_csv
        self.mistakes_csv = mistakes_csv
        self.diseases_df = pd.read_csv(diseases_csv)

        self.users_df = self.load_csv(self.users_csv, ['Username', 'Password', 'Age', 'Weight', 'Height', 'LastLogin', 'CreationDate'])
        self.medicines_df = self.load_csv(self.medicines_csv, ['Denumirea comerciala','DCI','Forma','Conc','Firma / Tara detinatoare,Ambalaj','Pres.','ATC','Details'])
        self.responses_df = self.load_csv(self.responses_csv, ['Keywords', 'ResponseType', 'Response'])
        self.mistakes_df = self.load_csv(self.mistakes_csv, ['Original', 'Correction'])
        
        self.current_user = None

    def load_csv(self, file_path, columns):
        try:
            return pd.read_csv(file_path)
        except FileNotFoundError:
            return pd.DataFrame(columns=columns)

    def hash_password(self, password):
        """Hash a password for storing."""
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, hashed_password, user_password):
        """Verify a stored password against one provided by user."""
        return hashed_password == hashlib.sha256(user_password.encode()).hexdigest()

    def register_user(self):
        username = input("Choose a username: ")
        password = input("Choose a password: ")
        hashed_password = self.hash_password(password)  # Use the internal method
        age = input("Enter your age: ")
        weight = input("Enter your weight (kg): ")
        height = input("Enter your height (cm): ")
        creation_date = datetime.now()
        new_user = {
            'Username': username, 'Password': hashed_password, 'Age': age,
            'Weight': weight, 'Height': height, 'LastLogin': creation_date, 'CreationDate': creation_date
        }
        self.users_df = self.users_df._append(new_user, ignore_index=True)
        self.users_df.to_csv(self.users_csv, index=False)
        self.current_user = username
        print(f"Welcome, {username}! You have been registered.")

    def login_user(self):
        username = input("Username: ")
        password = input("Password: ")
        user = self.users_df[self.users_df['Username'] == username].iloc[0]
        if self.check_password(user['Password'], password):  # Use the internal method
            self.current_user = username
            print(f"Welcome back, {username}!")
            self.check_health_update_needed(user)
        else:
            print("Invalid username or password.")

    def check_health_update_needed(self, user):
        last_update = datetime.strptime(user['LastLogin'], '%Y-%m-%d %H:%M:%S.%f')
        if datetime.now() > last_update + timedelta(days=30):
            print("It's been a while since your last health profile update.")
            age = input("Please enter your age: ")
            weight = input("Please enter your weight (kg): ")
            height = input("Please enter your height (cm): ")
            user_index = self.users_df[self.users_df['Username'] == self.current_user].index[0]
            self.users_df.at[user_index, ['Age', 'Weight', 'Height']] = [age, weight, height]
            self.users_df.at[user_index, 'LastLogin'] = datetime.now()
            self.users_df.to_csv(self.users_csv, index=False)
            print("Health profile updated.")
        else:
            print("Your health profile is up to date.")

    def provide_medicine_info(self):
        medicine_name = input("Please enter (or re-enter) the medicine name you want to know more about: ").strip()
        # Find all matches for the medicine name
        matches = self.medicines_df[self.medicines_df['Denumirea comerciala'].str.lower() == medicine_name.lower()]

        if matches.empty:
            print(
                "Sorry, we couldn't find information on the requested medicine. Please check the spelling or try another medicine name.")
        else:
            print(f"Found {len(matches)} medicine(s) with the name '{medicine_name}':")
            for index, medicine_info in matches.iterrows():
                print("\nMedicine Information:")
                # Iterate over each column in the row and print the information
                for column in matches.columns:
                    print(f"{column}: {medicine_info[column]}")
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
            elif response_type == "mistake":
                self.record_feedback()
            elif any(phrase in user_input for phrase in ["thank you", "bye", "that will be all", "logout"]):
                print("You're welcome! I'm here whenever you need assistance. Goodbye for now.")
                break
            else:
                self.respond_dynamically(user_input)
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
            print("We couldn't identify your condition based on the symptoms provided. Consulting a doctor is recommended.")
            return

        print("Based on your symptoms, here are the possible conditions and their respective probabilities:")
        for disease, probability in sorted(disease_probabilities.items(), key=lambda x: x[1], reverse=True):
            print(f"- {disease}: {probability:.2f}% probability")
            urgency = self.diseases_df[self.diseases_df['boala_denumire'] == disease]['Urgency'].iloc[0]
            self.recommend_specialist_based_on_urgency(disease, urgency)
            self.suggest_medication(disease)
    def calculate_disease_probabilities(self, symptoms):
        # Example implementation - adjust based on your dataset structure
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

        # Filter out diseases with less than two matching symptoms
        filtered_diseases = {disease: count for disease, count in disease_symptom_count.items() if count >= 2}
        total_matching_symptoms = sum(filtered_diseases.values())
        disease_probabilities = {disease: (count / total_matching_symptoms) * 100 for disease, count in
                                 filtered_diseases.items()}
        return disease_probabilities

    def suggest_medication(self, disease):
        medication = self.diseases_df[self.diseases_df['boala_denumire'] == disease]['medicamentatie'].iloc[0]
        print(f"For {disease}, consider taking: {medication}")

    def record_feedback(self):
        print("You indicated that the information provided might be incorrect.")
        original_info = input("What was the incorrect information? ")
        correction = input("Please provide the correct information, if known: ")
        self.mistakes_df = self.mistakes_df.append({'Original': original_info, 'Correction': correction}, ignore_index=True)
        self.mistakes_df.to_csv('mistakes.csv', index=False)
        print("Thank you for your feedback. It has been recorded for review.")

    def respond_dynamically(self, message):
        intent, _ = process.extractOne(message, self.responses_df['Keywords'].unique())
        responses = self.responses_df[self.responses_df['Keywords'] == intent]['Response'].tolist()
        if responses:
            print(random.choice(responses))
        else:
            print("I'm not sure how to respond to that. Can you tell me more?")
