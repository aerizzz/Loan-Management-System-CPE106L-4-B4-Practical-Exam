import tkinter as tk
from tkinter import ttk, messagebox
import uuid
import json
import os
from datetime import datetime


class Loan:
    def __init__(self, borrower_name, email, principal, interest_rate, months, loan_id=None, approval_date=None):
        self.borrower_name = borrower_name.strip()
        self.email = email.strip()
        self.principal = float(principal)
        self.interest_rate = float(interest_rate)
        self.months = int(months)
        
        self.loan_id = loan_id if loan_id else f"LN-{str(uuid.uuid4())[:6].upper()}"
        self.approval_date = approval_date if approval_date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.validate()

    def validate(self):
        if not self.borrower_name:
            raise ValueError("Borrower name cannot be empty.")
        if not self.email or "@" not in self.email or "." not in self.email:
            raise ValueError("A valid email address is required.")
        if self.principal <= 0:
            raise ValueError("Principal amount must be strictly positive.")
        if self.interest_rate < 0:
            raise ValueError("Interest rate cannot be negative.")
        if self.months <= 0:
            raise ValueError("Loan term must be at least 1 month.")

    @property
    def total_repayment(self):
        return self.principal + (self.principal * (self.interest_rate / 100) * (self.months / 12))

    def to_dict(self):
        return {
            "loan_id": self.loan_id,
            "borrower_name": self.borrower_name,
            "email": self.email,
            "principal": self.principal,
            "interest_rate": self.interest_rate,
            "months": self.months,
            "approval_date": self.approval_date
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            borrower_name=data["borrower_name"],
            email=data.get("email", "legacy-no-email@system.local"), 
            principal=data["principal"],
            interest_rate=data["interest_rate"],
            months=data["months"],
            loan_id=data["loan_id"],
            approval_date=data["approval_date"]
        )


class LoanDatabase:
    FILE_PATH = "loans_db.json"

    def __init__(self):
        self._loans = []
        self.load_data()

    def load_data(self):
        if os.path.exists(self.FILE_PATH):
            with open(self.FILE_PATH, "r") as file:
                data = json.load(file)
                self._loans = [Loan.from_dict(item) for item in data]
        else:
            self.generate_presets()

    def save_data(self):
        with open(self.FILE_PATH, "w") as file:
            json.dump([loan.to_dict() for loan in self._loans], file, indent=4)

    def generate_presets(self):
        self.add_loan(Loan("Aldwyn Umali", "umali@mapua.edu.ph", 50000, 5.0, 12))
        self.add_loan(Loan("Christian Yago", "yago@mapua.edu.ph", 150000, 4.5, 24))
        self.add_loan(Loan("Federico Tolentino III", "tolentino@mapua.edu.ph", 75000, 6.0, 36))

    def add_loan(self, loan):
        self._loans.append(loan)
        self.save_data()

    def get_all_loans(self):
        return self._loans

    def search_loans(self, query):
        query = query.lower().strip()
        return [
            loan for loan in self._loans 
            if query in loan.borrower_name.lower() or query in loan.loan_id.lower() or query in loan.email.lower()
        ]


# ==========================================
# 2. VIEW LAYER
# ==========================================
class LoanView:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.root.title("Loan Management System")
        self.root.geometry("1100x550") 
        
        self.bg_color = "#FFFDF9"      # Warm minimalist white
        self.primary = "#FF5722"       # Deep Orange
        self.secondary = "#E64A19"     # Darker Orange/Red for active states
        self.accent = "#FFCCBC"        # Light Orange for headers
        self.text_color = "#2C2C2C"

        self.root.configure(bg=self.bg_color)
        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        
        # Minimalist Flat Buttons
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background=self.primary, foreground="white", borderwidth=0, padding=6)
        style.map("Primary.TButton", background=[("active", self.secondary)])
        
        style.configure("Secondary.TButton", font=("Segoe UI", 9), background="#E0E0E0", foreground=self.text_color, borderwidth=0, padding=4)
        style.map("Secondary.TButton", background=[("active", "#D6D6D6")])

        # Clean Treeview
        style.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", foreground=self.text_color, borderwidth=0, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.accent, foreground=self.secondary, borderwidth=0)
        style.map("Treeview", background=[("selected", self.primary)], foreground=[("selected", "white")])

    def build_ui(self):
        # Left Panel: Data Entry Form
        form_frame = ttk.Frame(self.root, padding=25)
        form_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(form_frame, text="Loan Application", font=("Segoe UI", 16, "bold"), foreground=self.secondary).pack(pady=(0, 20))

        ttk.Label(form_frame, text="Borrower Name:").pack(anchor="w")
        self.entry_name = ttk.Entry(form_frame, width=32, font=("Segoe UI", 10))
        self.entry_name.pack(pady=(0, 12))

        ttk.Label(form_frame, text="Email Address:").pack(anchor="w")
        self.entry_email = ttk.Entry(form_frame, width=32, font=("Segoe UI", 10))
        self.entry_email.pack(pady=(0, 12))

        ttk.Label(form_frame, text="Principal Amount (₱):").pack(anchor="w")
        self.entry_principal = ttk.Entry(form_frame, width=32, font=("Segoe UI", 10))
        self.entry_principal.pack(pady=(0, 12))

        ttk.Label(form_frame, text="Annual Interest Rate (%):").pack(anchor="w")
        self.entry_interest = ttk.Entry(form_frame, width=32, font=("Segoe UI", 10))
        self.entry_interest.pack(pady=(0, 12))

        ttk.Label(form_frame, text="Term (Months):").pack(anchor="w")
        self.entry_term = ttk.Combobox(form_frame, values=[6, 12, 24, 36, 42, 54], state="readonly", width=30, font=("Segoe UI", 10))
        self.entry_term.current(1)
        self.entry_term.pack(pady=(0, 25))

        self.btn_submit = ttk.Button(form_frame, text="Process Loan", style="Primary.TButton", command=self.controller.handle_add_loan)
        self.btn_submit.pack(fill=tk.X)

        data_frame = ttk.Frame(self.root, padding=25)
        data_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        search_bar = ttk.Frame(data_frame)
        search_bar.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(search_bar, text="Search (Name, ID, Email):").pack(side=tk.LEFT, padx=(0, 10))
        self.entry_search = ttk.Entry(search_bar, width=35, font=("Segoe UI", 10))
        self.entry_search.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_search = ttk.Button(search_bar, text="Search", style="Primary.TButton", command=self.controller.handle_search)
        self.btn_search.pack(side=tk.LEFT)
        
        self.btn_reset = ttk.Button(search_bar, text="Show All", style="Secondary.TButton", command=self.controller.refresh_table)
        self.btn_reset.pack(side=tk.LEFT, padx=(10, 0))

        
        columns = ("id", "name", "email", "principal", "interest", "months", "total", "date")
        self.tree = ttk.Treeview(data_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Borrower")
        self.tree.heading("email", text="Email")
        self.tree.heading("principal", text="Principal (₱)")
        self.tree.heading("interest", text="Rate (%)")
        self.tree.heading("months", text="Term")
        self.tree.heading("total", text="Total Due (₱)")
        self.tree.heading("date", text="Date Approved")
        
        self.tree.column("id", width=70, anchor="center")
        self.tree.column("name", width=120)
        self.tree.column("email", width=140)
        self.tree.column("principal", width=90, anchor="e")
        self.tree.column("interest", width=60, anchor="center")
        self.tree.column("months", width=50, anchor="center")
        self.tree.column("total", width=90, anchor="e")
        self.tree.column("date", width=130, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True)

    def show_error(self, message):
        messagebox.showerror("Validation Error", message)

    def show_success(self, message):
        messagebox.showinfo("Success", message)

    def clear_form(self):
        self.entry_name.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)
        self.entry_principal.delete(0, tk.END)
        self.entry_interest.delete(0, tk.END)
        self.entry_term.current(1)


class LoanController:
    def __init__(self, root):
        self.db = LoanDatabase()
        self.view = LoanView(root, self)
        self.refresh_table()

    def handle_add_loan(self):
        name = self.view.entry_name.get()
        email = self.view.entry_email.get()
        principal = self.view.entry_principal.get()
        interest = self.view.entry_interest.get()
        months = self.view.entry_term.get()

        try:
            new_loan = Loan(name, email, principal, interest, months)
            self.db.add_loan(new_loan)
            
            self.view.show_success(f"Loan {new_loan.loan_id} approved for {new_loan.borrower_name}.")
            self.view.clear_form()
            self.refresh_table()
            
        except ValueError as e:
            if "could not convert string to float" in str(e):
                self.view.show_error("Financial values must be numeric.")
            else:
                self.view.show_error(str(e))

    def handle_search(self):
        query = self.view.entry_search.get()
        if not query:
            self.refresh_table()
            return
            
        results = self.db.search_loans(query)
        self._update_treeview(results)

    def refresh_table(self):
        self._update_treeview(self.db.get_all_loans())
        self.view.entry_search.delete(0, tk.END)

    def _update_treeview(self, loan_list):
        for row in self.view.tree.get_children():
            self.view.tree.delete(row)
            
        for loan in loan_list:
            self.view.tree.insert("", tk.END, values=(
                loan.loan_id,
                loan.borrower_name,
                loan.email,
                f"{loan.principal:,.2f}",
                f"{loan.interest_rate:.2f}",
                loan.months,
                f"{loan.total_repayment:,.2f}",
                loan.approval_date
            ))

if __name__ == "__main__":
    root = tk.Tk()
    app = LoanController(root)
    root.mainloop()