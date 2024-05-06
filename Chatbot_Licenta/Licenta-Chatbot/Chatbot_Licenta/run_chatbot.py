from ChatbotClass.Chatbot2 import Chatbot
from constants import *

if __name__ == "__main__":
    csvmedicamente = DATASET_FOLDER + SEPARATOR + "MedicamenteCsv2.csv"
    csvboli = DATASET_FOLDER + SEPARATOR + "CSVBoli.csv"
    csvuser = DATASET_FOLDER + SEPARATOR + "userCsv.csv"
    csvraspunsuri = DATASET_FOLDER + SEPARATOR + "responce.csv"
    csvmistakes = DATASET_FOLDER + SEPARATOR + "mistakes.csv"
    chatbot = Chatbot(csvuser, csvboli, csvmedicamente, csvraspunsuri, csvuser)
    chatbot.start()