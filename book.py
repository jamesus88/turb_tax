import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

import pathlib
DIR = str(pathlib.Path(__file__).parent.resolve())

class Book:
    def __init__(self, name):
        self.name = name
        self.db = sqlite3.connect(DIR + "/files/turb_tax.db")
        self.cursor = self.db.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book TEXT NOT NULL,
                date TEXT NOT NULL,
                desc TEXT,
                amount REAL NOT NULL
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Books (
                name TEXT PRIMARY KEY,
                desc TEXT,
                apr REAL
            );    
        """)

        self.cursor.execute("""
            INSERT OR IGNORE INTO Books (name)
            VALUES (?)
        """, (self.name,))

        self.db.commit()
        pd.options.display.float_format = '{:,.2f}'.format

    def info(self):
        name, desc, apr = self.cursor.execute("SELECT * FROM Books WHERE name = ?", (self.name,)).fetchone()
        bal = self.balance()
        print("---------------")
        print("turb tax:", self.name)
        if desc is not None: print(desc)
        if apr is not None: print("apr:", apr)
        print("Balance:", bal)
        print("---------------\n")
        return (name, desc, apr)
    
    def get_entry(self, index):
        i, book, date, desc, amount = self.cursor.execute("SELECT * FROM Entries WHERE id = ?", (index,)).fetchone()
        return (i, book, date, desc, amount)

    def read(self, calc_balance = True, max_row = 2000, skip_header=False):
        s = "SELECT * FROM Entries WHERE book = ?;"
        df = pd.read_sql_query(s, self.db, params=[self.name])
        df.set_index("id", inplace=True)

        df.sort_values("date", inplace=True)

        if calc_balance: df["balance"] = self.cumsum()

        if not skip_header:
            print("---------------")
            print("turb tax:", self.name)
            print("---------------")

        print(df.tail(max_row).to_string())
        print()
        return df
    
    def edit_entry(self, index, date, desc, amount):
        _, _, old_date, old_desc, old_amount = self.get_entry(index)
        self.cursor.execute("""
            UPDATE Entries
            SET date = ?,
                desc = ?,
                amount = ?
            WHERE id = ?
        """, (date or old_date, desc or old_desc, amount or old_amount, index))
        self.db.commit()

        self.read()

    def edit_desc(self, desc):
        self.cursor.execute("""
            UPDATE Books
            SET desc = ?
            WHERE name = ?;
        """, (desc, self.name))
        self.db.commit()

        self.info()

    def edit_apr(self, apr):
        self.cursor.execute("""
            UPDATE Books
            SET apr = ?
            WHERE name = ?;
        """, (apr, self.name))
        self.db.commit()

        self.info()


    def balance(self):
        self.cursor.execute("SELECT SUM(amount) FROM Entries WHERE book = ?;", (self.name,))
        bal = self.cursor.fetchone()
        return bal[0]

    def cumsum(self):
        self.cursor.execute("SELECT amount FROM Entries WHERE book = ?;", (self.name,))
        amts = np.array(self.cursor.fetchall()).flatten()
        return np.cumsum(amts)
    
    def interest(self, date, compound = 12):
        bal = self.balance()
        if not bal: raise ValueError("Must make an initial deposit first!")

        _, _, apr = self.info()
        i = bal * (apr / compound)
        self.add_entry(i, date, "interest earned")
        return i

    def add_entry(self, amount, date = datetime.now().strftime("%Y-%m-%d"), desc = ""):
        self.cursor.execute("""
            INSERT INTO Entries (book, date, desc, amount)
            VALUES (?, ?, ?, ?);
        """, (self.name, date, desc, amount))
        self.db.commit()

        bal = self.balance()
        print(f"Line added. New balance: ${bal}")

        self.read(max_row=5)

    def delete_entry(self, index):
        self.cursor.execute(f"DELETE FROM Entries WHERE id = {index};")
        self.db.commit()

        if self.cursor.rowcount > 0:
            bal = self.balance()
            print(f"Line removed. New balance: ${bal}")
            self.read(max_row=5)
        else:
            print(f"Failed to delete line {index}: id not found.\n")

    def clear(self):
        if input("Clear Book? Enter to continue: ") == "":
            self.cursor.execute("DELETE FROM Entries WHERE book = ?;", (self.name,))
            self.cursor.execute("DELETE FROM Books WHERE name = ?;", (self.name,))
            self.cursor.execute("DELETE FROM sqlite_sequence WHERE name='Entries';")
            self.db.commit()
            print("All lines cleared.")
        else:
            print("Deletion canceled.")