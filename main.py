from src.utils import setup_logger
import logging
from flask import Flask, request, jsonify
from pydantic import BaseModel, ValidationError
from agent.LLM import LLM

app = Flask(__name__)
agent = LLM('gpt-4o')

setup_logger()
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

class QueryResponse(BaseModel):
    query: str
    answer: str

@app.route('/query', methods=['POST'])
def create_query():
    try:
        # Extract the question from the request data
        request_data = request.json
        query = request_data.get('query')

        answer = agent.call(query)

        response = QueryResponse(query=query, answer=answer)
        
        return jsonify(response.dict())
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="localhost", port=8000, debug=True)