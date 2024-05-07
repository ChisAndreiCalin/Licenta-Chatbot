from ChatbotClass.Chatbot2 import Chatbot
from constants import *
if __name__ == '__main__':
    csvmedicamente = DATASET_FOLDER + SEPARATOR + "Medicamente_Csv.csv"
    csvboli = DATASET_FOLDER + SEPARATOR + "CSVBoli.csv"
    csvuser = DATASET_FOLDER + SEPARATOR + "userCsv.csv"
    csvraspunsuri = DATASET_FOLDER + SEPARATOR + "responce.csv"
    csvmistakes = DATASET_FOLDER + SEPARATOR + "mistakes.csv"
    csvschedule = DATASET_FOLDER + SEPARATOR + "Schedule.csv"
    chatbot = Chatbot(csvuser, csvboli, csvmedicamente, csvraspunsuri, csvmistakes, csvschedule)
    chatbot.start()