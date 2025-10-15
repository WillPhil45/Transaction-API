import sqlite3
import pandas as pd
from fastapi import UploadFile
import time
from .models import UploadResponse, SummaryResponse, ClearResponse

class Database:
    ''' This class contains the database logic that the fastAPI endpoints 
        utilise to complete tasks such as upload or statistics summary. 
        
        Uploading is done in chunks to ensure consistent memory usage,
        protecting against any unwanted side effects of attempting huge
        file uploads whilst maintaining performance.'''
    CHUNK_SIZE=10000 # This constant determines the amount of rows processed within a single chunk when uploading a new CSV file

    def __init__(self):
        # Call database setup method
        self._init_db()
    
    def _init_db(self):
        # Establish database connection 
        connection = sqlite3.connect('transactions.db')

        # Initialise cursor object to use for statement execution
        cursor = connection.cursor()

        # Create main table
        cursor.execute("""CREATE TABLE IF NOT EXISTS 
                            transactions(transaction_id TEXT PRIMARY KEY,
                                        user_id INTEGER, 
                                        product_id INTEGER, 
                                        timestamp TEXT, 
                                        transaction_amount REAL)""")

        # Commit database changes
        connection.commit()
        # Close connection
        connection.close()

        print("Database Initialised")

    async def upload_csv(self, file: UploadFile) -> UploadResponse:
        # Take note of start time
        start=time.time()
        connection = sqlite3.connect('transactions.db')
        cursor = connection.cursor()
    
        # Count rows before upload for later comparison to ascertain how many rows were added
        cursor.execute("SELECT COUNT(*) FROM transactions")
        rows_before = cursor.fetchone()[0]

        try:
            # Use pandas to produce an iterator where each object contains CHUNK_SIZE lines from the input file
            chunks = pd.read_csv(
                    file.file,
                    chunksize=self.CHUNK_SIZE,
                    dtype={
                        'transaction_id': str,
                        'user_id': 'int32',
                        'product_id': 'int32',
                        'transaction_amount': 'float32'
                    },
                    parse_dates=['timestamp']
                )
            
            first_chunk = True
            # Iterate over each chunk, performing validation checks before converting the chunk to SQL and appending it to transactions table
            for chunk in chunks:
                # Check whether this is the first chunk to perform column validation
                if first_chunk:
                    expected_columns=['transaction_id', 'user_id', 'product_id', 
                               'timestamp', 'transaction_amount']
                    if list(chunk.columns) != expected_columns:
                        raise ValueError(
                            f"Invalid columns. Expected: {expected_columns}, "
                            f"Got: {list(chunk.columns)}"
                        )
                    # Make sure first chunk flag is now false
                    first_chunk=False

                # Check whether the current chunk contains any null or empty values (ensures data integrity)
                if chunk.isnull().any().any():
                    raise ValueError("CSV contains null/empty values")
            
                # Check that no values for 'transaction_amount' in the current chunk are negative
                if (chunk['transaction_amount'] <= 0).any():
                    raise ValueError("Transaction amounts must be positive")
                
                # Check that all user and product IDs are positive integers
                if (chunk['user_id'] <= 0).any() or (chunk['product_id'] <= 0).any():
                    raise ValueError("User ID and Product ID must be positive")

                chunk.to_sql(
                            'transactions',
                            connection,
                            if_exists='append',
                            index=False
                        ) 
            
            # Check how many rows are now in the transactions table after the upload is complete
            cursor.execute("SELECT COUNT(*) FROM transactions")
            rows_after = cursor.fetchone()[0]

            # Compare this to rows before to ascertain how many rows were successfully appended to the transactions table
            rows_inserted = rows_after - rows_before
            # Commit the changes
            connection.commit()
        
        # Catch pandas exception for empty files
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty")
        
        # Catch pandas exception for invalid file formatting
        except pd.errors.ParserError as e:
            raise ValueError(f"Invalid CSV format: {str(e)}")
        
        # Catch any other exceptions
        except Exception as e:
            # Make sure any changes that have been made are reverted
            connection.rollback()
            raise ValueError(f"ERROR: {str(e)}")

        finally:
            # Make sure the database connection is closed
            connection.close()
            # take note of the end time to calculate the total time of the upload later
            end=time.time()

        # return a dict that follows the predefined UploadResponse pydantic model
        return {
                "success": True,
                "message": "Transactions uploaded successfully",
                "rows_processed": rows_inserted,
                "processing_time_seconds": round(end-start, 2)  
        }


    def get_summary(self, user_id: int, start_date: str, end_date: str) -> SummaryResponse:
        # Open database connection and initialise cursor
        connection = sqlite3.connect('transactions.db')
        cursor = connection.cursor()

        # Define SQL query to extract the statistics we want from the transactions table for an unspecified user ID and date range
        query = """
            SELECT 
                COUNT(*) as transaction_count,
                MAX(transaction_amount) as max_amount,
                MIN(transaction_amount) as min_amount,
                AVG(transaction_amount) as mean_amount
            FROM transactions
            WHERE user_id = ?
            AND timestamp >= ?
            AND timestamp <= ?
        """
        
        # Pass the user_id, start_date, and end_date variables to the query and execute
        cursor.execute(query, (user_id, start_date, end_date))
        # Fetch the result
        result = cursor.fetchone()
        connection.close()

        # Ensure that at least one transaction was found. If not, raise an error.
        if result[0] == 0:
            raise ValueError(
                f"No transactions found for user_id {user_id} "
                f"between {start_date} and {end_date}"
            )
        
        # Return the result in the SummaryResponse model format
        return {
            "user_id": user_id,
            "transaction_count": result[0],
            "max_amount": result[1],
            "min_amount": result[2],
            "mean_amount": round(result[3], 2), # Round mean average to 2 dp
            "start_date": start_date,
            "end_date": end_date
        }
    
    # This function was made for testing purposes as I encountered some issues during testing where simply deleting the transactions.db file was not sufficient to ensure values had not been cached
    def clear(self) -> ClearResponse:
        # Establish database connection and initialise cursor
        connection = sqlite3.connect('transactions.db')
        cursor = connection.cursor()

        # Delete transactions table contents
        cursor.execute("DELETE FROM transactions")
        # Commit the deletion
        connection.commit()
        
        # Check how many rows were deleted
        rows_deleted = cursor.rowcount
        connection.close()
        
        # Return relevent details in the ClearResponse model format
        return { "success":True,
                "message": f"{rows_deleted} Transactions deleted"}



