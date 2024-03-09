import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

# Load the environment variables
load_dotenv()
# Set the OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the Flask application
app = Flask(__name__)

# Initialize the database connection
db_uri = "mysql+mysqlconnector://root:19991998aA@localhost:3306/Chinook"
db = SQLDatabase.from_uri(db_uri)

def get_schema(_):
    return db.get_table_info()

# Initialize the language model
llm = ChatOpenAI()

# Define the chains and templates
template = """
Based on the table schema below, write a sql query that would answer the user's question:
{schema}

Question: {question}

SQL Query:

"""
prompt = ChatPromptTemplate.from_template(template)

sql_chain = (
    RunnablePassthrough.assign(schema=get_schema) 
    | prompt
    | llm.bind(stop="\nSQL Result:")
    | StrOutputParser()
)

template = """
Based on the table schema below, write a sql query that would answer the user's question:
{schema}

Question: {question}

SQL Query: {query}

SQL Response: {response}

"""
prompt = ChatPromptTemplate.from_template(template)
def run_query(query):
    return db.run(query)
full_chain = (
    RunnablePassthrough.assign(query=sql_chain).assign( 
    schema=get_schema,
    response= lambda vars: run_query(vars["query"])

    )
    | prompt
    | llm
    | StrOutputParser()


)

@app.route('/query', methods=['POST'])
def query():
    try:

        question = request.json['question']
        sql_query = sql_chain.invoke({"question": question})
        # Invoke the chain
        result = full_chain.invoke({"question": question})
        print("sql_query:", sql_query)
        print("Result:", result)
        return jsonify({"result": result}, {"sql_query": sql_query})
    except Exception as e:
        return jsonify({"error": str(e)})
if __name__ == "__main__":
    app.run(debug=True)
