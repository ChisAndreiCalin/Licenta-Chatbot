import pandas as pd
from fuzzywuzzy import process
import random
from datetime import datetime, timedelta
import hashlib
import ast



class Chatbot:
    def __init__(self, users_csv, diseases_csv, medicines_csv, responses_csv, mistakes_csv):
        self.users_csv = users_csv
        self.diseases_csv = diseases_csv
        self.medicines_csv = medicines_csv
        self.responses_csv = responses_csv
        self.mistakes_csv = mistakes_csv
        self.diseases_df = pd.read_csv(diseases_csv)

        self.users_df = self.load_csv(self.users_csv, ['Username', 'Password', 'Age', 'Weight', 'Height', 'Type', 'LastLogin', 'CreationDate'])
        self.medicines_df = self.load_csv(self.medicines_csv, ['Denumirea comerciala', 'DCI', 'Forma', 'Conc', 'Firma / Tara detinatoare,Ambalaj', 'Pres.', 'ATC', 'Details'])
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
            return pd.DataFrame(columns=columns)

    def hash_password(self, password):
        """Hash a password for storing."""
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, hashed_password, user_password):
        """Verify a stored password against one provided by user."""
        return hashed_password == hashlib.sha256(user_password.encode()).hexdigest()

    def register_user(self):
        username = input("Choose a username: ")
        # Check if username is unique
        if (username==self.users_df['Username']).any():
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

        hashed_password = self.hash_password(password)  # Use the internal method to hash the password
        creation_date = datetime.now()
        new_user = {
            'Username': username, 'Password': hashed_password, 'Age': age,
            'Weight': weight, 'Height': height, 'Type': user_type,
            'LastLogin': creation_date, 'CreationDate': creation_date
        }
        self.users_df = self.users_df._append(new_user, ignore_index=True)
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
        # Ensure the DataFrame is correctly handling lists
        for column in ['reporters', 'admin_reviews']:
            if column in self.mistakes_df.columns:
                self.mistakes_df[column] = self.mistakes_df[column].apply(
                    lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
            else:
                # Initialize column with empty lists if it doesn't exist
                self.mistakes_df[column] = [[] for _ in range(len(self.mistakes_df))]
        to_review = self.mistakes_df[(self.mistakes_df['reporters'].apply(lambda x: len(x) >= 2)) & (
            ~self.mistakes_df['admin_reviews'].apply(lambda x: self.current_user in x))]

        if to_review.empty:
            print("No new mistakes to review.")
            return

        for index, mistake in to_review.iterrows():
            print(
                f"Mistake ID: {index}, Type: {mistake['mistake_type']}, Original: {mistake['original_mistake']}, Correction: {mistake['correct_answer']}")
            action = input("Approve correction? (yes/no): ").lower()
            if action == 'yes':
                # Process correction...
                print("Correction approved and processed.")
            else:
                print("Correction rejected.")

            # Update the admin_reviews list
            admin_reviews = self.mistakes_df.at[index, 'admin_reviews']
            admin_reviews.append(self.current_user)
            self.mistakes_df.at[index, 'admin_reviews'] = admin_reviews

        self.mistakes_df.to_csv(self.mistakes_csv, index=False)

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
        if self.current_user is None or self.users_df[self.users_df['Username'] == self.current_user]['Type'].iloc[0] not in ['Doctor', 'Admin']:
            print("You must be a Doctor or Admin to provide feedback.")
            return

        mistake_type = input("Is this mistake related to a 'medicine' or a 'disease'? ")
        original_mistake = input("Please specify the original information (e.g., row name or disease/medicine name): ")
        correct_answer = input("Please provide the full correct row or information: ")

        # Check if a similar mistake has already been reported
        existing_mistake = self.mistakes_df[(self.mistakes_df['mistake_type'] == mistake_type) & (
                    self.mistakes_df['original_mistake'] == original_mistake)]

        if not existing_mistake.empty:
            # If similar mistake exists, append the current user to the reporters list (if they haven't already reported it)
            if self.current_user not in existing_mistake['reporters'].iloc[0]:
                existing_mistake['reporters'].iloc[0].append(self.current_user)
                print("Your report has been added to an existing mistake report.")
        else:
            # If it's a new mistake, create a new record
            self.mistakes_df = self.mistakes_df.append({
                'mistake_type': mistake_type,
                'original_mistake': original_mistake,
                'correct_answer': correct_answer,
                'reporters': [self.current_user],
                'admin_reviews': []
            }, ignore_index=True)
            print("Your feedback has been recorded for review.")

        self.mistakes_df.to_csv(self.mistakes_csv, index=False)

    def respond_dynamically(self, message):
        intent, _ = process.extractOne(message, self.responses_df['Keywords'].unique())
        responses = self.responses_df[self.responses_df['Keywords'] == intent]['Response'].tolist()
        if responses:
            print(random.choice(responses))
        else:
            print("I'm not sure how to respond to that. Can you tell me more?")
