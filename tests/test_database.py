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

        # Check that the main CREATE TABLE queries were executed
        # and also the ALTER TABLE for backward compatibility.
        self.assertGreaterEqual(mock_cursor.execute.call_count, 10)
        
        executed_sql = " ".join([call[0][0] for call in mock_cursor.execute.call_args_list])
        self.assertIn("CREATE TABLE IF NOT EXISTS users", executed_sql)
        self.assertIn("default_wallet_id INTEGER REFERENCES wallets(id) ON DELETE SET NULL", executed_sql)
        self.assertIn("live_trading_enabled BOOLEAN DEFAULT FALSE", executed_sql)
        self.assertIn("ALTER TABLE users ADD COLUMN default_wallet_id", executed_sql)
        self.assertIn("ALTER TABLE users ADD COLUMN live_trading_enabled", executed_sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS wallets", executed_sql)
        self.assertIn("ALTER TABLE wallets ADD COLUMN chain_id", executed_sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS portfolio_history", executed_sql)
        
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('src.database.get_db_connection')
    def test_save_portfolio_snapshot(self, mock_get_conn):
        """Test saving a portfolio snapshot."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        database.save_portfolio_snapshot(1, 1234.56)

        mock_cursor.execute.assert_called_once_with(
            """
                INSERT INTO portfolio_history (user_id, total_value_usd, snapshot_date)
                VALUES (%s, %s, CURRENT_DATE)
                ON CONFLICT (user_id, snapshot_date) DO UPDATE SET total_value_usd = EXCLUDED.total_value_usd;
                """,
            (1, 1234.56)
        )
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
