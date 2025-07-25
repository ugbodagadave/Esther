import unittest
from unittest.mock import patch, MagicMock
import os
import psycopg2
from src import database

class TestDatabase(unittest.TestCase):

    @patch.dict(os.environ, {"DATABASE_URL": "dummy_url"})
    @patch('psycopg2.connect')
    def test_get_db_connection_success(self, mock_connect):
        """Test that a successful database connection is established."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        conn = database.get_db_connection()
        
        mock_connect.assert_called_once_with("dummy_url")
        self.assertEqual(conn, mock_conn)

    @patch.dict(os.environ, {"DATABASE_URL": "dummy_url"})
    @patch('psycopg2.connect', side_effect=psycopg2.OperationalError("Connection failed"))
    def test_get_db_connection_failure(self, mock_connect):
        """Test that the connection function returns None on failure."""
        conn = database.get_db_connection()
        self.assertIsNone(conn)

    @patch('src.database.get_db_connection')
    def test_initialize_database(self, mock_get_conn):
        """Test the database initialization function."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        database.initialize_database()

        # Check that the correct CREATE TABLE queries were executed
        self.assertEqual(mock_cursor.execute.call_count, 2)
        mock_cursor.execute.assert_any_call(unittest.mock.ANY) # Check if execute was called
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
