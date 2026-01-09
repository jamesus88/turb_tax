#!/usr/bin/env python3

from book import Book
from datetime import datetime
from argparse import ArgumentParser

def today():
    return datetime.today().strftime("%Y-%m-%d")

def main():

    parser = ArgumentParser(prog="turb tax CLI", description="easy finance tracker")

    parser.add_argument("ledger_name")
    subparsers = parser.add_subparsers(title="Actions", dest="command")

    view_parser = subparsers.add_parser("view", help="view all entries")
    view_parser.add_argument("-m", "--max", type=int)
    view_parser.add_argument("-d", "--details", action="store_true")
    view_parser.set_defaults(max = 200)

    edit_parser = subparsers.add_parser("edit", help="edit book or entry")
    edit_parser.add_argument("--index", "-i", type=int, help="Do not include index to edit book")
    edit_parser.add_argument("--date", "-d")
    edit_parser.add_argument("--amount", "-a", type=float)
    edit_parser.add_argument("--desc", "-p")
    edit_parser.add_argument("--apr", help="apr as a decimal")
    edit_parser.set_defaults(desc = None, apr = None, index=None, date=today())

    add_parser = subparsers.add_parser("add", help="add entry")
    add_parser.add_argument("amount", type=float)
    add_parser.add_argument("--date", "-d", help="date (yyyy-mm-dd)")
    add_parser.add_argument("--desc", "-p")
    add_parser.set_defaults(date = today(), desc = None)

    interest_parser = subparsers.add_parser("interest", help="add interest")
    interest_parser.add_argument("--date", "-d", help="date (yyyy-mm-dd)")
    interest_parser.add_argument("--compound", "-c", help="compound freq (e.g. 12)")
    interest_parser.set_defaults(date = today(), compound = 12)

    delete_parser = subparsers.add_parser("delete", help="delete entry")
    delete_parser.add_argument("index", type=int, help="id of the entry to delete")

    clear_parser = subparsers.add_parser("clear", help="clear all entries")
    clear_parser.add_argument("--confirm", action="store_true")

    args = parser.parse_args()
    
    book = Book(args.ledger_name)
    print()
    
    match args.command:
        case 'view':
            if args.details:
                book.info()
            
            book.read(max_row=args.max, skip_header=True)
        case 'edit':
            if args.index:
                book.edit_entry(args.index, args.date, args.desc, args.amount)
            else:
                if args.desc:
                    book.edit_desc(args.desc)

            if args.apr:
                book.edit_apr(args.apr)
        case 'interest':
            book.interest(args.date, args.compound)
        case 'add':
            book.add_entry(args.amount, args.date, args.desc)
        case 'delete':
            book.delete_entry(args.index)
        case 'clear':
            if args.confirm:
                book.clear()
            else:
                print("Failure: did not --confirm.")
        case _:
            book.info()
            print("Commands: view, add, delete, clear. Call --help for more.")

    return 0


if __name__ == "__main__":
    main()