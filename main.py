import tkinter as tk
from tkinter import ttk, messagebox
import uuid
import json
import os
import re
from datetime import datetime

class Loan:
    EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

    def __init__(self, borrower_name, email, principal, interest_rate, months, 
                 payment_method="Bank Transfer", comakers="None", loan_id=None, 
                 approval_date=None, balance=None, status="Active", months_paid=0):
        self.borrower_name = borrower_name.strip()
        self.email = email.strip()
        self.principal = float(principal)
        self.interest_rate = float(interest_rate)
        self.months = int(months)
        self.payment_method = payment_method.strip() or "Bank Transfer"
        self.comakers = comakers.strip() or "None"
        self.months_paid = int(months_paid)
        
        self.loan_id = loan_id or f"LN-{uuid.uuid4().hex[:6].upper()}"
        self.approval_date = approval_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.validate()
        
        self.balance = float(balance) if balance is not None else self.total_repayment
        self.status = status
        self.due_date = self._calculate_due_date()

    def validate(self):
        if not self.borrower_name:
            raise ValueError("Borrower name cannot be empty.")
        if not self.EMAIL_REGEX.match(self.email):
            raise ValueError("A valid email address is required (e.g., name@domain.com).")
        if self.principal <= 0:
            raise ValueError("Principal amount must be strictly positive.")
        if self.interest_rate < 0:
            raise ValueError("Interest rate cannot be negative.")
        if self.months <= 0:
            raise ValueError("Loan term must be at least 1 month.")

    def _calculate_due_date(self):
        dt = datetime.strptime(self.approval_date, "%Y-%m-%d %H:%M:%S")
        year = dt.year + (dt.month // 12)
        month = (dt.month % 12) + 1
        leap = 1 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 0
        days_in_month = [0, 31, 28 + leap, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        day = min(dt.day, days_in_month[month])
        return f"{year:04d}-{month:02d}-{day:02d}"

    @property
    def total_repayment(self):
        return round(self.principal + (self.principal * (self.interest_rate / 100) * (self.months / 12)), 2)

    @property
    def monthly_installment(self):
        return round(self.total_repayment / self.months, 2)

    def to_dict(self):
        return {
            "loan_id": self.loan_id,
            "borrower_name": self.borrower_name,
            "email": self.email,
            "principal": self.principal,
            "interest_rate": self.interest_rate,
            "months": self.months,
            "payment_method": self.payment_method,
            "comakers": self.comakers,
            "approval_date": self.approval_date,
            "balance": self.balance,
            "status": self.status,
            "months_paid": self.months_paid
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            borrower_name=data["borrower_name"],
            email=data.get("email", "legacy-no-email@system.local"),
            principal=data["principal"],
            interest_rate=data["interest_rate"],
            months=data["months"],
            payment_method=data.get("payment_method", "Bank Transfer"),
            comakers=data.get("comakers", "None"),
            loan_id=data["loan_id"],
            approval_date=data["approval_date"],
            balance=data.get("balance"),
            status=data.get("status", "Active"),
            months_paid=data.get("months_paid", 0)
        )


class LoanDatabase:
    FILE_PATH = "loans_db.json"

    def __init__(self):
        self._loans = []
        self._loan_map = {}  
        self.load_data()

    def load_data(self):
        if os.path.exists(self.FILE_PATH):
            try:
                with open(self.FILE_PATH, "r", encoding="utf-8") as f:
                    self._loans = [Loan.from_dict(item) for item in json.load(f)]
            except (json.JSONDecodeError, KeyError):
                self.generate_presets()
        else:
            self.generate_presets()
        self._rebuild_index()

    def _rebuild_index(self):
        self._loan_map = {loan.loan_id: loan for loan in self._loans}

    def save_data(self):
        with open(self.FILE_PATH, "w", encoding="utf-8") as f:
            json.dump([l.to_dict() for l in self._loans], f, indent=4)

    def generate_presets(self):
        self._loans = [
            Loan("Aldwyn Umali", "umali@mapua.edu.ph", 50000, 5.0, 12),
            Loan("Christian Yago", "yago@mapua.edu.ph", 150000, 4.5, 24),
            Loan("Federico Tolentino III", "tolentino@mapua.edu.ph", 75000, 6.0, 36)
        ]
        self.save_data()

    def add_loan(self, loan):
        self._loans.append(loan)
        self._loan_map[loan.loan_id] = loan
        self.save_data()

    def update_loan_details(self, loan_id, new_term, new_payment, new_comaker):
        loan = self._loan_map.get(loan_id)
        if not loan:
            return False
        loan.months = int(new_term)
        loan.payment_method = new_payment
        loan.comakers = new_comaker
        self.save_data()
        return True

    def process_monthly_payment(self, loan_id):
        loan = self._loan_map.get(loan_id)
        if loan and loan.months_paid < loan.months:
            loan.months_paid += 1
            loan.balance = max(0.0, round(loan.balance - loan.monthly_installment, 2))
            loan.status = "Cleared" if (loan.months_paid >= loan.months or loan.balance == 0.0) else "Paid (This Month)"
            self.save_data()
            return True, loan
        return False, None

    def get_all_loans(self):
        return self._loans

    def get_loan_by_id(self, loan_id):
        return self._loan_map.get(loan_id)

    def search_loans(self, query):
        q = query.lower().strip()
        if not q:
            return self._loans
        return [
            l for l in self._loans 
            if q in l.borrower_name.lower() or q in l.loan_id.lower() or q in l.email.lower()
        ]

class LoanView:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.root.title("Loan Management System")
        self.root.geometry("1420x680")

        self.bg_color = "#FFFDF9"
        self.primary = "#FF5722"
        self.secondary = "#E64A19"
        self.accent = "#FFCCBC"
        self.card_bg = "#FFFFFF"
        self.text_color = "#2C2C2C"

        self.root.configure(bg=self.bg_color)
        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background=self.primary, foreground="white", borderwidth=0, padding=6)
        style.map("Primary.TButton", background=[("active", self.secondary)])
        
        style.configure("Secondary.TButton", font=("Segoe UI", 9), background="#E0E0E0", foreground=self.text_color, borderwidth=0, padding=4)
        style.map("Secondary.TButton", background=[("active", "#D6D6D6")])

        style.configure("Success.TButton", font=("Segoe UI", 10, "bold"), background="#4CAF50", foreground="white", borderwidth=0, padding=6)
        style.map("Success.TButton", background=[("active", "#388E3C")])
        
        style.configure("Info.TButton", font=("Segoe UI", 10, "bold"), background="#2196F3", foreground="white", borderwidth=0, padding=6)
        style.map("Info.TButton", background=[("active", "#1976D2")])

        style.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", foreground=self.text_color, borderwidth=0, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.accent, foreground=self.secondary, borderwidth=0)
        style.map("Treeview", background=[("selected", self.primary)], foreground=[("selected", "white")])

    def build_ui(self):
        left_panel = ttk.Frame(self.root, padding=20)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left_panel, text="CardiLoan", font=("Segoe UI", 15, "bold"), foreground=self.secondary).pack(pady=(0, 10))

        fields = [
            ("Borrower Name:", "entry_name", ttk.Entry),
            ("Email Address:", "entry_email", ttk.Entry),
            ("Principal Amount (₱):", "entry_principal", ttk.Entry),
            ("Annual Interest Rate (%):", "entry_interest", ttk.Entry),
        ]
        
        for label_text, attr, widget_cls in fields:
            ttk.Label(left_panel, text=label_text).pack(anchor="w")
            widget = widget_cls(left_panel, width=32, font=("Segoe UI", 9))
            widget.pack(pady=(0, 6))
            setattr(self, attr, widget)

        ttk.Label(left_panel, text="Term (Months):").pack(anchor="w")
        self.entry_term = ttk.Combobox(left_panel, values=[6, 12, 24, 36, 42, 54], state="readonly", width=30, font=("Segoe UI", 9))
        self.entry_term.current(1)
        self.entry_term.pack(pady=(0, 12))

        self.btn_submit = ttk.Button(left_panel, text="Process Loan", style="Primary.TButton", command=self.controller.handle_add_loan)
        self.btn_submit.pack(fill=tk.X, pady=(0, 15))

        card_border = tk.LabelFrame(
            left_panel, text=" Selected Loan Overview ", font=("Segoe UI", 9, "bold"),
            fg=self.secondary, bg=self.card_bg, bd=1, relief="solid", padx=10, pady=8
        )
        card_border.pack(fill=tk.BOTH, expand=True)

        self.detail_vars = {k: tk.StringVar(value=f"{k.capitalize()}: -") for k in [
            "id", "status", "borrower", "email", "principal", "due_total", "balance", "progress", "payment", "comaker"
        ]}
        self.detail_vars["borrower"].set("Borrower: Select a loan")

        card_layout = [
            ("id", 0, 0, 1), ("status", 0, 1, 1),
            ("borrower", 1, 0, 2), ("email", 2, 0, 2),
            ("principal", 3, 0, 1), ("due_total", 3, 1, 1),
            ("balance", 4, 0, 1), ("progress", 4, 1, 1),
            ("payment", 5, 0, 2), ("comaker", 6, 0, 2)
        ]
        for key, r, c, span in card_layout:
            tk.Label(
                card_border, textvariable=self.detail_vars[key], font=("Segoe UI", 8),
                bg=self.card_bg, fg=self.text_color, anchor="w"
            ).grid(row=r, column=c, sticky="w", padx=2, pady=2, columnspan=span)

        data_frame = ttk.Frame(self.root, padding=20)
        data_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        search_bar = ttk.Frame(data_frame)
        search_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 15))
        ttk.Label(search_bar, text="Search (Name, ID, Email):").pack(side=tk.LEFT, padx=(0, 10))
        self.entry_search = ttk.Entry(search_bar, width=35, font=("Segoe UI", 10))
        self.entry_search.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_search.bind("<Return>", lambda e: self.controller.handle_search())

        ttk.Button(search_bar, text="Search", style="Primary.TButton", command=self.controller.handle_search).pack(side=tk.LEFT)
        ttk.Button(search_bar, text="Show All", style="Secondary.TButton", command=self.controller.refresh_table).pack(side=tk.LEFT, padx=(10, 0))

        action_bar = ttk.Frame(data_frame)
        action_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(15, 0))
        ttk.Button(action_bar, text="Edit Selected Loan", style="Secondary.TButton", command=self.controller.handle_edit_request).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_bar, text="Log Monthly Payment", style="Success.TButton", command=self.controller.handle_payment).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_bar, text="View Progress", style="Info.TButton", command=self.controller.handle_view_progress).pack(side=tk.LEFT)

        columns = ("id", "name", "total", "balance", "progress", "due", "status", "payment")
        self.tree = ttk.Treeview(data_frame, columns=columns, show="headings", height=15)
        
        headers = [
            ("id", "ID", 75, "center"), ("name", "Borrower", 140, "w"),
            ("total", "Total Due (₱)", 95, "e"), ("balance", "Balance (₱)", 95, "e"),
            ("progress", "Progress", 70, "center"), ("due", "Next Due Date", 90, "center"),
            ("status", "Status", 110, "center"), ("payment", "Payment Method", 100, "center")
        ]
        for cid, text, w, anc in headers:
            self.tree.heading(cid, text=text)
            self.tree.column(cid, width=w, anchor=anc)

        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.controller.handle_tree_selection)

    def display_loan_details(self, loan):
        if not loan:
            return
        mapping = {
            "id": f"ID: {loan.loan_id}",
            "status": f"Status: {loan.status}",
            "borrower": f"Borrower: {loan.borrower_name}",
            "email": f"Email: {loan.email}",
            "principal": f"Principal: ₱{loan.principal:,.2f}",
            "due_total": f"Total: ₱{loan.total_repayment:,.2f}",
            "balance": f"Balance: ₱{loan.balance:,.2f}",
            "progress": f"Paid: {loan.months_paid}/{loan.months} mos",
            "payment": f"Payment: {loan.payment_method}",
            "comaker": f"Co-maker: {loan.comakers or 'None'}"
        }
        for k, v in mapping.items():
            self.detail_vars[k].set(v)

    def open_edit_dialog(self, loan):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Loan - {loan.loan_id}")
        dialog.geometry("400x350")
        dialog.configure(bg=self.bg_color)
        dialog.grab_set()

        form = ttk.Frame(dialog, padding=20)
        form.pack(fill=tk.BOTH, expand=True)

        ttk.Label(form, text=f"Modifying: {loan.borrower_name}", font=("Segoe UI", 12, "bold"), foreground=self.secondary).pack(pady=(0, 15))

        ttk.Label(form, text="Stretch Term Period (Months):").pack(anchor="w")
        term_combo = ttk.Combobox(form, values=[6, 12, 24, 36, 42, 54, 60, 72], state="readonly", width=35, font=("Segoe UI", 10))
        term_combo.set(loan.months)
        term_combo.pack(pady=(0, 10))

        ttk.Label(form, text="Payment Method:").pack(anchor="w")
        pay_combo = ttk.Combobox(form, values=["Bank Transfer", "Post-Dated Check", "Salary Deduction", "Cash"], state="readonly", width=35, font=("Segoe UI", 10))
        pay_combo.set(loan.payment_method)
        pay_combo.pack(pady=(0, 10))

        ttk.Label(form, text="Add Co-maker(s):").pack(anchor="w")
        comaker_entry = ttk.Entry(form, width=37, font=("Segoe UI", 10))
        comaker_entry.insert(0, loan.comakers)
        comaker_entry.pack(pady=(0, 20))

        ttk.Button(
            form, text="Save Changes", style="Primary.TButton",
            command=lambda: self.controller.handle_save_edit(loan.loan_id, term_combo.get(), pay_combo.get(), comaker_entry.get(), dialog)
        ).pack(fill=tk.X)

    def open_progress_dialog(self, loan):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Payment Progress - {loan.loan_id}")
        dialog.geometry("350x400")
        dialog.configure(bg=self.bg_color)
        dialog.grab_set()

        form = ttk.Frame(dialog, padding=20)
        form.pack(fill=tk.BOTH, expand=True)
        ttk.Label(form, text=f"Schedule: {loan.borrower_name}", font=("Segoe UI", 12, "bold"), foreground=self.secondary).pack(pady=(0, 10))

        progress_bar = ttk.Progressbar(form, orient="horizontal", length=300, mode="determinate")
        progress_bar["value"] = (loan.months_paid / loan.months) * 100
        progress_bar.pack(pady=(0, 15))

        list_frame = tk.Frame(form, bg=self.bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        schedule_list = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Segoe UI", 10), borderwidth=0, highlightthickness=1, highlightcolor=self.accent)
        for i in range(1, loan.months + 1):
            if i <= loan.months_paid:
                schedule_list.insert(tk.END, f"Month {i}: PAID ✓")
                schedule_list.itemconfig(tk.END, {'fg': 'green'})
            else:
                schedule_list.insert(tk.END, f"Month {i}: PENDING - ₱{loan.monthly_installment:,.2f}")
                schedule_list.itemconfig(tk.END, {'fg': 'red'})

        schedule_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=schedule_list.yview)

    def show_error(self, message):
        messagebox.showerror("Error", message)

    def show_success(self, message):
        messagebox.showinfo("Success", message)

    def clear_form(self):
        for entry in [self.entry_name, self.entry_email, self.entry_principal, self.entry_interest]:
            entry.delete(0, tk.END)
        self.entry_term.current(1)


class LoanController:
    def __init__(self, root):
        self.db = LoanDatabase()
        self.view = LoanView(root, self)
        self.refresh_table()

    def _format_loan_row(self, loan):
        return (
            loan.loan_id,
            loan.borrower_name,
            f"{loan.total_repayment:,.2f}",
            f"{loan.balance:,.2f}",
            f"{loan.months_paid}/{loan.months}",
            loan.due_date,
            loan.status,
            loan.payment_method
        )

    def handle_tree_selection(self, event=None):
        selection = self.view.tree.selection()
        if selection:
            loan_id = self.view.tree.item(selection[0])['values'][0]
            loan = self.db.get_loan_by_id(loan_id)
            if loan:
                self.view.display_loan_details(loan)

    def handle_add_loan(self):
        try:
            new_loan = Loan(
                self.view.entry_name.get(),
                self.view.entry_email.get(),
                self.view.entry_principal.get(),
                self.view.entry_interest.get(),
                self.view.entry_term.get()
            )
            self.db.add_loan(new_loan)
            self.view.show_success(f"Loan {new_loan.loan_id} approved for {new_loan.borrower_name}.")
            self.view.clear_form()
            
            item_id = self.view.tree.insert("", tk.END, values=self._format_loan_row(new_loan))
            self.view.tree.selection_set(item_id)
            self.view.tree.see(item_id)
            self.view.display_loan_details(new_loan)
        except ValueError as e:
            msg = "Financial values must be numeric." if "could not convert string to float" in str(e) else str(e)
            self.view.show_error(msg)

    def handle_search(self):
        results = self.db.search_loans(self.view.entry_search.get())
        self._render_tree(results)

    def handle_edit_request(self):
        selection = self.view.tree.selection()
        if not selection:
            self.view.show_error("Please select a loan record from the table to edit.")
            return
        loan = self.db.get_loan_by_id(self.view.tree.item(selection[0])['values'][0])
        if loan:
            self.view.open_edit_dialog(loan)

    def handle_save_edit(self, loan_id, term, payment, comaker, dialog):
        if self.db.update_loan_details(loan_id, term, payment, comaker):
            dialog.destroy()
            loan = self.db.get_loan_by_id(loan_id)
            self._update_selected_tree_row(loan)
            self.view.display_loan_details(loan)
            self.view.show_success(f"Loan {loan_id} updated successfully.")
        else:
            self.view.show_error("Failed to update loan. Record not found.")

    def handle_payment(self):
        selection = self.view.tree.selection()
        if not selection:
            self.view.show_error("Please select a loan record to process a payment.")
            return

        loan_id = self.view.tree.item(selection[0])['values'][0]
        success, loan = self.db.process_monthly_payment(loan_id)
        if success:
            self._update_selected_tree_row(loan)
            self.view.display_loan_details(loan)
            self.view.show_success(f"Payment logged! Remaining balance for {loan.borrower_name} is ₱{loan.balance:,.2f}.")
        else:
            self.view.show_error("Cannot process payment. Loan is already fully cleared.")

    def handle_view_progress(self):
        selection = self.view.tree.selection()
        if not selection:
            self.view.show_error("Please select a loan record to view progress.")
            return
        loan = self.db.get_loan_by_id(self.view.tree.item(selection[0])['values'][0])
        if loan:
            self.view.open_progress_dialog(loan)

    def _update_selected_tree_row(self, loan):
        selection = self.view.tree.selection()
        if selection:
            self.view.tree.item(selection[0], values=self._format_loan_row(loan))

    def refresh_table(self):
        self._render_tree(self.db.get_all_loans())
        self.view.entry_search.delete(0, tk.END)

    def _render_tree(self, loan_list):
        self.view.tree.delete(*self.view.tree.get_children())
        for loan in loan_list:
            self.view.tree.insert("", tk.END, values=self._format_loan_row(loan))


if __name__ == "__main__":
    app_root = tk.Tk()
    app = LoanController(app_root)
    app_root.mainloop()