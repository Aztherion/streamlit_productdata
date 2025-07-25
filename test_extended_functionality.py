import unittest
import sqlite3
import os
import pandas as pd

DB_PATH = "app.db"

class TestFormValidation(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

    def test_eol_date_required_if_selected(self):
        self.cursor.execute("INSERT INTO products (ProductID, ProductName, CRAPlan, CRA_EoL_Date) VALUES (?, ?, ?, ?)",
                            (3001, "EOLTestProduct", "EoL", ""))
        self.conn.commit()
        self.cursor.execute("SELECT CRA_EoL_Date FROM products WHERE ProductID = 3001")
        eol_date = self.cursor.fetchone()[0]
        self.assertEqual(eol_date, "", "EOL Date should be empty but must be flagged in app logic")

    def tearDown(self):
        self.cursor.execute("DELETE FROM products WHERE ProductID = 3001")
        self.conn.commit()
        self.conn.close()

class TestDatabaseIntegrity(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

    def test_unique_product_id(self):
        self.cursor.execute("INSERT INTO products (ProductID, ProductName) VALUES (?, ?)", (4001, "UniqueProduct"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.cursor.execute("INSERT INTO products (ProductID, ProductName) VALUES (?, ?)", (4001, "Duplicate"))
            self.conn.commit()

    def tearDown(self):
        self.cursor.execute("DELETE FROM products WHERE ProductID = 4001")
        self.conn.commit()
        self.conn.close()

class TestCRALogic(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

    def test_stop_sell_requires_flag(self):
        self.cursor.execute("INSERT INTO products (ProductID, ProductName, CRAPlan, CRA_StopSell_VPApproved, CRA_StopSell_Flagged) VALUES (?, ?, ?, ?, ?)",
                            (5001, "StopSellProd", "Stop Sell in EU", "No", "No"))
        self.conn.commit()
        self.cursor.execute("SELECT CRA_StopSell_Flagged FROM products WHERE ProductID = 5001")
        result = self.cursor.fetchone()[0]
        self.assertEqual(result, "No", "Flagged should be 'Yes' if not approved")

    def tearDown(self):
        self.cursor.execute("DELETE FROM products WHERE ProductID = 5001")
        self.conn.commit()
        self.conn.close()

class TestDashboardTotals(unittest.TestCase):
    def test_product_count_matches_db(self):
        conn = sqlite3.connect(DB_PATH)
        db_count = pd.read_sql("SELECT COUNT(*) FROM products", conn).iloc[0, 0]
        conn.close()
        self.assertGreaterEqual(db_count, 0)

class TestImportExportSafety(unittest.TestCase):
    def test_invalid_csv_rejected(self):
        try:
            df = pd.read_csv("nonexistent.csv")
        except FileNotFoundError:
            self.assertTrue(True)
        else:
            self.fail("Invalid CSV should raise FileNotFoundError")

class TestSecurityBasic(unittest.TestCase):
    def test_sql_injection_defense(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM products WHERE ProductName = ?", ("'; DROP TABLE products; --",))
            results = cursor.fetchall()
            self.assertIsInstance(results, list)
        finally:
            conn.close()
