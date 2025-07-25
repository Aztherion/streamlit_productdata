import unittest
import sqlite3
import os
from datetime import datetime

DB_PATH = "app.db"

class TestProductMetadataApp(unittest.TestCase):
    def setUp(self):
        # Ensure test DB is in a known state
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

    def test_database_connection(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in self.cursor.fetchall()]
        self.assertIn("products", tables)

    def test_insert_new_product(self):
        self.cursor.execute("INSERT INTO products (ProductID, ProductName, LeagueID) VALUES (?, ?, ?)", (9999, "TestProduct", 1))
        self.conn.commit()
        self.cursor.execute("SELECT * FROM products WHERE ProductID = 9999")
        product = self.cursor.fetchone()
        self.assertIsNotNone(product)
        self.assertEqual(product[1], "TestProduct")

    def test_update_cra_plan_to_eol(self):
        self.cursor.execute("UPDATE products SET CRAPlan = ?, CRA_EoL_Date = ? WHERE ProductID = 9999", ("EoL", "2030-12-31"))
        self.conn.commit()
        self.cursor.execute("SELECT CRAPlan, CRA_EoL_Date FROM products WHERE ProductID = 9999")
        result = self.cursor.fetchone()
        self.assertEqual(result[0], "EoL")
        self.assertEqual(result[1], "2030-12-31")

    def test_set_stop_sell_and_flag(self):
        self.cursor.execute("UPDATE products SET CRAPlan = ?, CRA_StopSell_VPApproved = ?, CRA_StopSell_Flagged = ? WHERE ProductID = 9999", 
                            ("Stop Sell in EU", "No", "Yes"))
        self.conn.commit()
        self.cursor.execute("SELECT CRA_StopSell_VPApproved, CRA_StopSell_Flagged FROM products WHERE ProductID = 9999")
        result = self.cursor.fetchone()
        self.assertEqual(result, ("No", "Yes"))

    def test_delete_test_product(self):
        self.cursor.execute("DELETE FROM products WHERE ProductID = 9999")
        self.conn.commit()
        self.cursor.execute("SELECT * FROM products WHERE ProductID = 9999")
        self.assertIsNone(self.cursor.fetchone())

    def tearDown(self):
        self.conn.close()

if __name__ == "__main__":
    unittest.main()
