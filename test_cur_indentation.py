import unittest

class TestIndentation(unittest.TestCase):
    def test_cur_cursor_indentation(self):
        with open("app.py", "r", encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if "cur = conn.cursor()" in line:
                self.assertTrue(line.startswith("            "), f"Line {i+1} is misindented: {line.strip()}")

if __name__ == "__main__":
    unittest.main()
