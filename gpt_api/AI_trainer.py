import mysql.connector
import openai
import uuid

openai.api_key = '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'

def training_dataset_creation(prompt, answer, AI_name):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Q144bughL0?Y@JFYxPA0",
        database="externalmemorydb"
    )

    mycursor = mydb.cursor()

    id = str(uuid.uuid4())
    sql = "INSERT INTO AI_Responses (id, prompt, output, AI_name) VALUES (%s, %s, %s, %s)"
    val = (id, prompt, answer, AI_name)

    mycursor.execute(sql, val)

    mydb.commit()

    print(mycursor.rowcount, "record inserted.")