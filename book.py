import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

class Book:
    def __init__(self, name):
        self.name = name
        self.db = sqlite3.connect(f"./files/turb_tax.db")
        self.cursor = self.db.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ledger TEXT NOT NULL,
                date TEXT NOT NULL,
                desc TEXT,
                amount REAL NOT NULL
            );
        """)
        self.db.commit()
        pd.options.display.float_format = '{:,.2f}'.format

    def read(self, calc_balance = True, max_row = 2000):
        s = "SELECT * FROM Ledger WHERE ledger = ?;"
        df = pd.read_sql_query(s, self.db, params=[self.name])
        df.set_index("id", inplace=True)

        if calc_balance: df["balance"] = self.cumsum()
        print("---------------")
        print("turb tax:", self.name)
        print("---------------")

        print(df.tail(max_row).to_string())
        print()
        return df

    def balance(self):
        self.cursor.execute("SELECT SUM(amount) FROM Ledger WHERE ledger = ?;", (self.name,))
        bal = self.cursor.fetchone()
        return bal[0]

    def cumsum(self):
        self.cursor.execute("SELECT amount FROM Ledger WHERE ledger = ?;", (self.name,))
        amts = np.array(self.cursor.fetchall()).flatten()
        return np.cumsum(amts)

    def add_entry(self, amount, date = datetime.now().strftime("%Y-%m-%d"), desc = ""):
        self.cursor.execute("""
            INSERT INTO Ledger (ledger, date, desc, amount)
            VALUES (?, ?, ?, ?);
        """, (self.name, date, desc, amount))
        self.db.commit()

        bal = self.balance()
        print(f"Line added. New balance: ${bal}")

        self.read(max_row=5)

    def delete_entry(self, index):
        self.cursor.execute(f"DELETE FROM Ledger WHERE id = {index};")
        self.db.commit()

        if self.cursor.rowcount > 0:
            bal = self.balance()
            print(f"Line removed. New balance: ${bal}")
            self.read(max_row=5)
        else:
            print(f"Failed to delete line {index}: id not found.\n")

    def clear(self):
        if input("Clear Ledger? Enter to continue: ") == "":
            self.cursor.execute("DELETE FROM Ledger WHERE ledger = ?;", (self.name,))
            self.cursor.execute("DELETE FROM sqlite_sequence WHERE name='Ledger';")
            self.db.commit()
            print("All lines cleared.")
        else:
            print("Deletion canceled.")