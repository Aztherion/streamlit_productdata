import unittest
import sqlite3
import pandas as pd

DB_PATH = "app.db"

class TestDashboardAnalytics(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

    def test_cra_compliance_aggregation(self):
        df = pd.read_sql_query("""
            SELECT 
                COUNT(*) AS Total,
                SUM(CASE WHEN AwareOfCRA = 'Yes' THEN 1 ELSE 0 END) AS CRA_Aware,
                SUM(CASE WHEN CRACompliant = 'Yes' THEN 1 ELSE 0 END) AS CRA_Compliant,
                SUM(CASE WHEN KEVProcessExists = 'Yes' THEN 1 ELSE 0 END) AS KEV_OK,
                SUM(CASE WHEN DisclosureProcessSE = 'Yes' THEN 1 ELSE 0 END) AS Disclosure_OK
            FROM vulnerability_compliance
        """, self.conn)

        total = int(df['Total'][0])
        aware = int(df['CRA_Aware'][0])
        compliant = int(df['CRA_Compliant'][0])
        kev = int(df['KEV_OK'][0])
        disclosure = int(df['Disclosure_OK'][0])

        self.assertGreaterEqual(total, 0)
        self.assertLessEqual(aware, total)
        self.assertLessEqual(compliant, total)
        self.assertLessEqual(kev, total)
        self.assertLessEqual(disclosure, total)

    def test_flagged_stop_sell_display(self):
        df = pd.read_sql_query("""
            SELECT * FROM products
            WHERE CRAPlan = 'Stop Sell in EU' AND CRA_StopSell_Flagged = 'Yes'
        """, self.conn)
        for _, row in df.iterrows():
            self.assertEqual(row['CRAPlan'], 'Stop Sell in EU')
            self.assertEqual(row['CRA_StopSell_Flagged'], 'Yes')

    def tearDown(self):
        self.conn.close()

if __name__ == "__main__":
    unittest.main()
