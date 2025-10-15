Transaction API:

The transaction API service I built was created using python 3.13.
All dependencies are listed in the requirements.txt file found within the code repository.

The design of my API takes into account requirements for large dataset handling (1 Million rows+),
Comprehensive error checking and validation, and type safety/ data validation using pydantic validation models.

The API provides endpoints for uploading CSV files and querying for statistics summaries within date ranges.

Installation:

First, Clone the repository using this command.

git clone https://github.com/WillPhil45/Transaction-API.git

Change directory to the repository then continue by creating a new virtual environment as show below.

python -m venv venv

# Activate on macOS/Linux
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate

Now, Install the dependencies from the requirements.txt.

pip install -r requirements.txt
 
The 'data' folder already contains test datasets ranging in size from 1,000 transactions to 1,000,000 but if you
want to create new data sets, edit the 'TRANSACTIONS' variable in the 'generate_test_data' script to match the
amount of rows you want and run the script to generate a new test dataset.

Running the API:

To start the FastAPI development server, change directory to the app folder and run the following command.

fastapi dev main.py

You will see the terminal output some information and provide links to the API and it's SwaggerUI interactive documentation 
running on your host machine at http://127.0.0.1:8000/docs.

There is alternative interactive API documentation available at http://127.0.0.1:8000/redocs.

Design:

My approach to designing the API was to seperate the architecture into two main scripts, main.py and storage.py.

main.py is essentially the API layer, handling http request and response and linking the endpoints to backend database functionality.

storage.py is the database layer, responsible to performing operations that require database interactions or data processing.

I chose to use sqlite3 as a lightweight database alternative for this project because it strikes a nice balance between storing
1 million rows of data in memory which would be extremely inefficient and too simple and linking the API to an actual database like 
postgres which would be cumbersome to set up and port for submission. When the database first intialises, sqlite creates a file in the
directory you are running the dev server from called 'transactions.db' which contains any data you upload meaning you have a database that
is stored on disk instead of memory without dealing with a full database management system. This choice would allow you to easily upgrade the
database capabilities without needing the change the API layer/ main.py script.

Performance:

The API service can complete (On my machine) a 1 million row csv upload in about 60 seconds on average and query time is fast enough to not be noticeable,
Probably ~200ms.

Testing:

I have included a test script powered by the pytest library which tests a variety of scenarios for the upload and summary endpoints.

These test cases could be extended to cover more edge cases but I believe that I covered the most important edge and error cases as well as simple valid input tests.

To run the test suite yourself, change directory to the 'tests' folder then run the following command.

pytest -v test_api.py

Everything should pass.

