import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime
import csv

# ───────────────────────────────
# Database Setup
# ───────────────────────────────
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    description TEXT,
    amount REAL
)
""")
conn.commit()

# ───────────────────────────────
# Core Functions
# ───────────────────────────────

def add_expense():
    date = date_entry.get_date().strftime("%Y-%m-%d")
    category = category_entry.get()
    description = desc_entry.get()
    amount = amount_entry.get()

    if not (date and category and description and amount):
        messagebox.showerror("Error", "All fields are required!")
        return

    try:
        amount = float(amount)
    except ValueError:
        messagebox.showerror("Error", "Amount must be a number.")
        return

    cursor.execute(
        "INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
        (date, category, description, amount)
    )
    conn.commit()
    clear_fields()
    show_expenses()
    calculate_total()
    messagebox.showinfo("Success", "Expense added successfully!")


def show_expenses():
    for row in tree.get_children():
        tree.delete(row)

    cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
    rows = cursor.fetchall()

    for i, row in enumerate(rows, start=1):
        tree.insert("", "end", values=(i, row[1], row[2], row[3], row[4]))


def clear_fields():
    date_entry.set_date(datetime.today())
    category_entry.set("")
    desc_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)


def delete_expense():
    selected = tree.selection()
    if not selected:
        messagebox.showerror("Error", "Please select an expense to delete.")
        return

    confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this expense?")
    if not confirm:
        return

    item = tree.item(selected[0])
    values = item["values"]

    cursor.execute("""
        SELECT id FROM expenses
        WHERE date=? AND category=? AND description=? AND amount=?
        ORDER BY id DESC LIMIT 1
    """, (values[1], values[2], values[3], values[4]))
    record = cursor.fetchone()
    if record:
        cursor.execute("DELETE FROM expenses WHERE id=?", (record[0],))
        conn.commit()

    show_expenses()
    calculate_total()
    messagebox.showinfo("Deleted", "Expense deleted successfully!")


def calculate_total():
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]
    total_label.config(text=f"Total: ₹{total:.2f}" if total else "Total: ₹0.00")


def export_to_csv():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["S.No", "Date", "Category", "Description", "Amount"])
        cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
        rows = cursor.fetchall()
        for i, row in enumerate(rows, start=1):
            writer.writerow([i, row[1], row[2], row[3], row[4]])
    messagebox.showinfo("Exported", f"Expenses exported to {file_path}")


def category_summary():
    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    summary_data = cursor.fetchall()

    if not summary_data:
        messagebox.showinfo("No Data", "No expenses to summarize.")
        return

    summary_text = "\n".join([f"{cat}: ₹{amt:.2f}" for cat, amt in summary_data])
    messagebox.showinfo("Category Summary", summary_text)


def edit_expense():
    selected = tree.selection()
    if not selected:
        messagebox.showerror("Error", "Please select an expense to edit.")
        return

    item = tree.item(selected[0])
    _, date, category, desc, amount = item["values"]

    cursor.execute("""
        SELECT id FROM expenses
        WHERE date=? AND category=? AND description=? AND amount=?
        ORDER BY id DESC LIMIT 1
    """, (date, category, desc, amount))
    record = cursor.fetchone()
    if not record:
        messagebox.showerror("Error", "Expense not found in database.")
        return
    expense_id = record[0]

    edit_window = tk.Toplevel(root)
    edit_window.title("Edit Expense")
    edit_window.geometry("350x300")
    edit_window.resizable(False, False)

    tk.Label(edit_window, text="Date:").pack(pady=5)
    edit_date = DateEntry(edit_window, date_pattern='yyyy-mm-dd')
    edit_date.set_date(datetime.strptime(date, "%Y-%m-%d"))
    edit_date.pack()

    tk.Label(edit_window, text="Category:").pack(pady=5)
    edit_category = ttk.Combobox(edit_window, values=categories, state="readonly")
    edit_category.set(category)
    edit_category.pack()

    tk.Label(edit_window, text="Description:").pack(pady=5)
    edit_desc = tk.Entry(edit_window)
    edit_desc.insert(0, desc)
    edit_desc.pack()

    tk.Label(edit_window, text="Amount:").pack(pady=5)
    edit_amount = tk.Entry(edit_window)
    edit_amount.insert(0, amount)
    edit_amount.pack()

    def save_edit():
        new_date = edit_date.get_date().strftime("%Y-%m-%d")
        new_category = edit_category.get()
        new_desc = edit_desc.get()
        new_amount = edit_amount.get()

        try:
            new_amount = float(new_amount)
        except ValueError:
            messagebox.showerror("Error", "Amount must be numeric.")
            return

        cursor.execute("""
            UPDATE expenses
            SET date=?, category=?, description=?, amount=?
            WHERE id=?
        """, (new_date, new_category, new_desc, new_amount, expense_id))
        conn.commit()
        edit_window.destroy()
        show_expenses()
        calculate_total()
        messagebox.showinfo("Updated", "Expense updated successfully!")

    tk.Button(edit_window, text="Save Changes", command=save_edit, bg="#4CAF50", fg="white").pack(pady=15)


def on_closing():
    conn.close()
    root.destroy()


# ───────────────────────────────
# UI Setup
# ───────────────────────────────

root = tk.Tk()
root.title("Expense Tracker")
root.geometry("1000x600")
root.config(padx=10, pady=10)
root.eval('tk::PlaceWindow . center')
root.protocol("WM_DELETE_WINDOW", on_closing)

# Labels
tk.Label(root, text="Date:").grid(row=0, column=0, sticky="e")
tk.Label(root, text="Category:").grid(row=1, column=0, sticky="e")
tk.Label(root, text="Description:").grid(row=2, column=0, sticky="e")
tk.Label(root, text="Amount:").grid(row=3, column=0, sticky="e")

# Inputs
date_entry = DateEntry(root, width=18, date_pattern='yyyy-mm-dd', background='darkblue', foreground='white')
date_entry.grid(row=0, column=1, padx=5, pady=2)

categories = ["Food", "Transport", "Bills", "Entertainment", "Shopping", "Other"]
category_entry = ttk.Combobox(root, values=categories, state="readonly")
category_entry.grid(row=1, column=1, padx=5, pady=2)

desc_entry = tk.Entry(root)
amount_entry = tk.Entry(root)
desc_entry.grid(row=2, column=1, padx=5, pady=2)
amount_entry.grid(row=3, column=1, padx=5, pady=2)

# Buttons
tk.Button(root, text="Add Expense", command=add_expense, bg="#4CAF50", fg="white", width=15).grid(row=4, column=0, pady=10)
tk.Button(root, text="Edit Expense", command=edit_expense, bg="#9C27B0", fg="white", width=15).grid(row=4, column=1)
tk.Button(root, text="Delete Expense", command=delete_expense, bg="#f44336", fg="white", width=15).grid(row=4, column=2)
tk.Button(root, text="Export CSV", command=export_to_csv, bg="#607D8B", fg="white", width=15).grid(row=4, column=3)

# Table
columns = ("S.No", "Date", "Category", "Description", "Amount")
tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

tree.column("S.No", width=60)
tree.column("Date", width=100)
tree.column("Category", width=150)
tree.column("Description", width=300)
tree.column("Amount", width=120)

tree.grid(row=5, column=0, columnspan=6, pady=15, sticky="nsew")

# Scrollbar
scrollbar = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
tree.configure(yscroll=scrollbar.set)
scrollbar.grid(row=5, column=6, sticky="ns")

# Summary Buttons
tk.Button(root, text="Total", command=calculate_total, bg="#FF9800", fg="white", width=12).grid(row=6, column=0, pady=10)
tk.Button(root, text="Category Summary", command=category_summary, bg="#3F51B5", fg="white", width=18).grid(row=6, column=1)

# Total Label
total_label = tk.Label(root, text="Total: ₹0.00", font=("Arial", 12, "bold"))
total_label.grid(row=7, column=0, columnspan=4, pady=10)

root.grid_rowconfigure(5, weight=1)
root.grid_columnconfigure(3, weight=1)

show_expenses()
calculate_total()

root.bind('<Return>', lambda e: add_expense())

root.mainloop()





