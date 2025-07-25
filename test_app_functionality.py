import unittest
import sqlite3
from pathlib import Path

DB_PATH = "/mnt/data/product_metadata_app/app.db"

class TestProductMetadataApp(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cur = self.conn.cursor()
        self.cur.execute("DROP TABLE IF EXISTS products")
        self.cur.execute("DROP TABLE IF EXISTS requirements")
        self.cur.execute("DROP TABLE IF EXISTS requirement_assessments")

        self.cur.execute("CREATE TABLE products (ProductID INTEGER PRIMARY KEY, ProductName TEXT)")
        self.cur.execute("CREATE TABLE requirements (RequirementID INTEGER PRIMARY KEY, Framework TEXT, RequirementText TEXT)")
        self.cur.execute("CREATE TABLE requirement_assessments (ProductID INTEGER, RequirementID INTEGER, Status TEXT, StartDate TEXT, EndDate TEXT, CoveredByProductID INTEGER, PRIMARY KEY (ProductID, RequirementID))")

        self.cur.execute("INSERT INTO products (ProductID, ProductName) VALUES (1, 'Test Product')")
        self.cur.executemany("INSERT INTO requirements (RequirementID, Framework, RequirementText) VALUES (?, ?, ?)", [
            (1, 'CRA', 'Device must support secure boot.'),
            (2, 'RED', 'Maintain network integrity.'),
            (3, 'NIS2', 'Logging must be tamper-proof.')
        ])
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_products_exist(self):
        self.cur.execute("SELECT COUNT(*) FROM products")
        count = self.cur.fetchone()[0]
        self.assertGreater(count, 0, "No products found in database.")

    def test_requirements_exist(self):
        self.cur.execute("SELECT COUNT(*) FROM requirements")
        count = self.cur.fetchone()[0]
        self.assertGreater(count, 0, "No requirements found in database.")

    def test_requirement_assessment_insert_and_update(self):
        self.cur.execute("INSERT OR REPLACE INTO requirement_assessments (ProductID, RequirementID, Status, StartDate, EndDate, CoveredByProductID) VALUES (?, ?, ?, ?, ?, ?)", (
            1, 1, "Implemented", "2024-01-01", "2024-06-01", None
        ))
        self.conn.commit()

        self.cur.execute("SELECT Status FROM requirement_assessments WHERE ProductID = 1 AND RequirementID = 1")
        result = self.cur.fetchone()
        self.assertEqual(result[0], "Implemented")

    def test_indentation_and_spacing(self):
        app_path = Path("/mnt/data/product_metadata_app/app.py")
        self.assertTrue(app_path.exists(), "app.py file not found")
        with app_path.open("r") as f:
            lines = f.readlines()
        for line in lines:
            self.assertFalse("\t" in line, "Tab character found — use 4 spaces instead.")
            if line.strip():
                self.assertEqual((len(line) - len(line.lstrip())) % 4, 0, "Indentation not a multiple of 4.")

if __name__ == "__main__":
    unittest.main()