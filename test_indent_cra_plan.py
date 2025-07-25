import unittest

class TestIndentationCRA(unittest.TestCase):
    def test_indentation_of_cra_plan_block(self):
        with open("app.py", "r", encoding="utf-8") as f:
            lines = f.readlines()

        inside_block = False
        for idx, line in enumerate(lines):
            if 'if plan_option == "Stop Sell in EU":' in line:
                inside_block = True
                continue
            if inside_block:
                if line.strip() == "":
                    continue
                if line.strip().startswith("else:"):
                    break
                # Ensure the line is indented at least 12 spaces (3 levels)
                self.assertTrue(line.startswith(" " * 12), f"Line {idx+1} not properly indented: {line.strip()}")

if __name__ == "__main__":
    unittest.main()
