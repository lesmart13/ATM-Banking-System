import datetime
import json
import os
from getpass import getpass
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import random
import string

class BankAccount:
    def __init__(self, account_number, pin, balance=0, transaction_history=None, is_active=True):
        self.account_number = account_number
        self.pin = pin
        self.balance = balance
        self.transaction_history = transaction_history if transaction_history else []
        self.is_active = is_active
        self.pin_attempts = 0
        self.locked = False
    
    def deposit(self, amount):
        if amount > 0 and self.is_active and not self.locked:
            self.balance += amount
            transaction = {
                'type': 'deposit',
                'amount': amount,
                'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'balance_after': self.balance,
                'to_account': self.account_number
            }
            self.transaction_history.append(transaction)
            return True, "Deposit successful"
        return False, "Invalid deposit amount or account locked/inactive"
    
    def withdraw(self, amount):
        if self.locked:
            return False, "Account is locked. Please contact admin."
        if not self.is_active:
            return False, "Account is inactive."
        if amount > 0 and self.balance >= amount:
            self.balance -= amount
            transaction = {
                'type': 'withdrawal',
                'amount': amount,
                'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'balance_after': self.balance,
                'from_account': self.account_number
            }
            self.transaction_history.append(transaction)
            return True, "Withdrawal successful"
        return False, "Invalid withdrawal amount or insufficient funds"
    
    def transfer(self, amount, recipient_account):
        if self.locked:
            return False, "Account is locked. Please contact admin."
        if not self.is_active:
            return False, "Account is inactive."
        if amount > 0 and self.balance >= amount:
            self.balance -= amount
            recipient_account.balance += amount
            
            # Create transaction for sender
            sender_transaction = {
                'type': 'transfer_out',
                'amount': amount,
                'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'balance_after': self.balance,
                'from_account': self.account_number,
                'to_account': recipient_account.account_number
            }
            self.transaction_history.append(sender_transaction)
            
            # Create transaction for recipient
            recipient_transaction = {
                'type': 'transfer_in',
                'amount': amount,
                'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'balance_after': recipient_account.balance,
                'from_account': self.account_number,
                'to_account': recipient_account.account_number
            }
            recipient_account.transaction_history.append(recipient_transaction)
            
            return True, "Transfer successful"
        return False, "Invalid transfer amount or insufficient funds"
    
    def get_balance(self):
        return self.balance if not self.locked and self.is_active else 0
    
    def get_transaction_history(self):
        return self.transaction_history if not self.locked else []
    
    def change_pin(self, old_pin, new_pin):
        if self.locked:
            return False, "Account is locked. Please contact admin."
        if old_pin == self.pin:
            if len(new_pin) == 4 and new_pin.isdigit():
                self.pin = new_pin
                self.pin_attempts = 0
                return True, "PIN changed successfully"
            return False, "PIN must be 4 digits"
        self.pin_attempts += 1
        if self.pin_attempts >= 3:
            self.locked = True
            return False, "Too many incorrect attempts. Account locked."
        return False, "Incorrect current PIN"
    
    def generate_receipt(self, transaction_type, amount, other_account=None):
        receipt = f"""
        {'='*40}
        ATM TRANSACTION RECEIPT
        {'='*40}
        Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        Account: {self.account_number}
        Transaction Type: {transaction_type.upper()}
        Amount: ${amount:.2f}
        """
        
        if other_account:
            if transaction_type == 'transfer_out':
                receipt += f"Recipient Account: {other_account}\n"
            elif transaction_type == 'transfer_in':
                receipt += f"Sender Account: {other_account}\n"
        
        receipt += f"""
        Available Balance: ${self.balance:.2f}
        {'='*40}
        Thank you for banking with us!
        """
        return receipt

class ATM:
    def __init__(self):
        self.accounts = {}
        self.admin_users = {'admin': 'admin123'}  # In real system, use secure hashing
        self.load_accounts()
        self.current_account = None
        self.current_admin = None
    
    def load_accounts(self):
        if os.path.exists('accounts.json'):
            with open('accounts.json', 'r') as f:
                accounts_data = json.load(f)
                for acc_num, acc_data in accounts_data.items():
                    self.accounts[acc_num] = BankAccount(
                        acc_num,
                        acc_data['pin'],
                        acc_data['balance'],
                        acc_data['transaction_history'],
                        acc_data.get('is_active', True)
                    )
                    self.accounts[acc_num].pin_attempts = acc_data.get('pin_attempts', 0)
                    self.accounts[acc_num].locked = acc_data.get('locked', False)
    
    def save_accounts(self):
        accounts_data = {}
        for acc_num, account in self.accounts.items():
            accounts_data[acc_num] = {
                'pin': account.pin,
                'balance': account.balance,
                'transaction_history': account.transaction_history,
                'is_active': account.is_active,
                'pin_attempts': account.pin_attempts,
                'locked': account.locked
            }
        with open('accounts.json', 'w') as f:
            json.dump(accounts_data, f, indent=2)
    
    def authenticate(self, account_number, pin):
        if account_number in self.accounts and not self.accounts[account_number].locked:
            account = self.accounts[account_number]
            if account.pin == pin:
                account.pin_attempts = 0
                self.current_account = account
                return True, "Authentication successful"
            else:
                account.pin_attempts += 1
                if account.pin_attempts >= 3:
                    account.locked = True
                    self.save_accounts()
                    return False, "Too many incorrect attempts. Account locked."
                return False, f"Incorrect PIN. {3 - account.pin_attempts} attempts remaining"
        return False, "Invalid account number or account is locked"
    
    def authenticate_admin(self, username, password):
        if username in self.admin_users and self.admin_users[username] == password:
            self.current_admin = username
            return True
        return False
    
    def generate_account_number(self):
        while True:
            acc_num = ''.join(random.choices(string.digits, k=8))
            if acc_num not in self.accounts:
                return acc_num
    
    def create_account(self, name, pin, initial_deposit=0):
        account_number = self.generate_account_number()
        self.accounts[account_number] = BankAccount(account_number, pin, initial_deposit)
        if initial_deposit > 0:
            self.accounts[account_number].deposit(initial_deposit)
        self.save_accounts()
        return account_number
    
    def close_account(self, account_number, admin_username):
        if account_number in self.accounts and admin_username in self.admin_users:
            if self.accounts[account_number].balance == 0:
                del self.accounts[account_number]
                self.save_accounts()
                return True, "Account closed successfully"
            return False, "Cannot close account with non-zero balance"
        return False, "Invalid account number or admin credentials"
    
    def unlock_account(self, account_number, admin_username):
        if account_number in self.accounts and admin_username in self.admin_users:
            self.accounts[account_number].locked = False
            self.accounts[account_number].pin_attempts = 0
            self.save_accounts()
            return True, "Account unlocked successfully"
        return False, "Invalid account number or admin credentials"

class ATMGUI:
    def __init__(self, atm):
        self.atm = atm
        self.root = tk.Tk()
        self.root.title("ATM Banking System")
        self.root.geometry("600x500")
        
        self.create_main_menu()
    
    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def create_main_menu(self):
        self.clear_frame()
        
        tk.Label(self.root, text="Welcome to ATM Banking System", font=("Arial", 16)).pack(pady=20)
        
        tk.Button(self.root, text="Customer Login", command=self.create_customer_login, width=20).pack(pady=10)
        tk.Button(self.root, text="Admin Login", command=self.create_admin_login, width=20).pack(pady=10)
        tk.Button(self.root, text="Create New Account", command=self.create_new_account, width=20).pack(pady=10)
        tk.Button(self.root, text="Exit", command=self.root.quit, width=20).pack(pady=10)
    
    def create_customer_login(self):
        self.clear_frame()
        
        tk.Label(self.root, text="Customer Login", font=("Arial", 14)).pack(pady=10)
        
        tk.Label(self.root, text="Account Number:").pack()
        self.acc_num_entry = tk.Entry(self.root)
        self.acc_num_entry.pack()
        
        tk.Label(self.root, text="PIN:").pack()
        self.pin_entry = tk.Entry(self.root, show="*")
        self.pin_entry.pack()
        
        tk.Button(self.root, text="Login", command=self.handle_customer_login).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.create_main_menu).pack(pady=5)
    
    def handle_customer_login(self):
        account_number = self.acc_num_entry.get()
        pin = self.pin_entry.get()
        
        success, message = self.atm.authenticate(account_number, pin)
        if success:
            self.create_customer_menu()
        else:
            messagebox.showerror("Login Failed", message)
    
    def create_admin_login(self):
        self.clear_frame()
        
        tk.Label(self.root, text="Admin Login", font=("Arial", 14)).pack(pady=10)
        
        tk.Label(self.root, text="Username:").pack()
        self.admin_user_entry = tk.Entry(self.root)
        self.admin_user_entry.pack()
        
        tk.Label(self.root, text="Password:").pack()
        self.admin_pass_entry = tk.Entry(self.root, show="*")
        self.admin_pass_entry.pack()
        
        tk.Button(self.root, text="Login", command=self.handle_admin_login).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.create_main_menu).pack(pady=5)
    
    def handle_admin_login(self):
        username = self.admin_user_entry.get()
        password = self.admin_pass_entry.get()
        
        if self.atm.authenticate_admin(username, password):
            self.create_admin_menu()
        else:
            messagebox.showerror("Login Failed", "Invalid admin credentials")
    
    def create_new_account(self):
        self.clear_frame()
        
        tk.Label(self.root, text="Create New Account", font=("Arial", 14)).pack(pady=10)
        
        tk.Label(self.root, text="Full Name:").pack()
        self.name_entry = tk.Entry(self.root)
        self.name_entry.pack()
        
        tk.Label(self.root, text="PIN (4 digits):").pack()
        self.new_pin_entry = tk.Entry(self.root, show="*")
        self.new_pin_entry.pack()
        
        tk.Label(self.root, text="Confirm PIN:").pack()
        self.confirm_pin_entry = tk.Entry(self.root, show="*")
        self.confirm_pin_entry.pack()
        
        tk.Label(self.root, text="Initial Deposit (optional):").pack()
        self.deposit_entry = tk.Entry(self.root)
        self.deposit_entry.pack()
        
        tk.Button(self.root, text="Create Account", command=self.handle_create_account).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.create_main_menu).pack(pady=5)
    
    def handle_create_account(self):
        name = self.name_entry.get()
        pin = self.new_pin_entry.get()
        confirm_pin = self.confirm_pin_entry.get()
        deposit = self.deposit_entry.get()
        
        if not name:
            messagebox.showerror("Error", "Name is required")
            return
        
        if len(pin) != 4 or not pin.isdigit():
            messagebox.showerror("Error", "PIN must be 4 digits")
            return
        
        if pin != confirm_pin:
            messagebox.showerror("Error", "PINs do not match")
            return
        
        try:
            initial_deposit = float(deposit) if deposit else 0
            if initial_deposit < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid deposit amount")
            return
        
        account_number = self.atm.create_account(name, pin, initial_deposit)
        messagebox.showinfo("Success", f"Account created successfully!\nYour account number is: {account_number}")
        self.create_main_menu()
    
    def create_customer_menu(self):
        self.clear_frame()
        
        tk.Label(self.root, text=f"Welcome, Account {self.atm.current_account.account_number}", font=("Arial", 14)).pack(pady=10)
        
        buttons = [
            ("Check Balance", self.show_balance),
            ("Deposit Money", self.create_deposit),
            ("Withdraw Money", self.create_withdraw),
            ("Transfer Money", self.create_transfer),
            ("Transaction History", self.show_transaction_history),
            ("Change PIN", self.create_change_pin),
            ("Print Receipt", self.print_receipt),
            ("Logout", self.logout)
        ]
        
        for text, command in buttons:
            tk.Button(self.root, text=text, command=command, width=20).pack(pady=5)
    
    def show_balance(self):
        balance = self.atm.current_account.get_balance()
        messagebox.showinfo("Account Balance", f"Your current balance is: ${balance:.2f}")
    
    def create_deposit(self):
        amount = simpledialog.askfloat("Deposit", "Enter amount to deposit:")
        if amount is not None:
            success, message = self.atm.current_account.deposit(amount)
            if success:
                self.atm.save_accounts()
                receipt = self.atm.current_account.generate_receipt('deposit', amount)
                messagebox.showinfo("Success", f"{message}\n\n{receipt}")
            else:
                messagebox.showerror("Error", message)
    
    def create_withdraw(self):
        amount = simpledialog.askfloat("Withdraw", "Enter amount to withdraw:")
        if amount is not None:
            success, message = self.atm.current_account.withdraw(amount)
            if success:
                self.atm.save_accounts()
                receipt = self.atm.current_account.generate_receipt('withdrawal', amount)
                messagebox.showinfo("Success", f"{message}\n\n{receipt}")
            else:
                messagebox.showerror("Error", message)
    
    def create_transfer(self):
        self.clear_frame()
        
        tk.Label(self.root, text="Transfer Money", font=("Arial", 14)).pack(pady=10)
        
        tk.Label(self.root, text="Recipient Account Number:").pack()
        self.recipient_entry = tk.Entry(self.root)
        self.recipient_entry.pack()
        
        tk.Label(self.root, text="Amount:").pack()
        self.transfer_amount_entry = tk.Entry(self.root)
        self.transfer_amount_entry.pack()
        
        tk.Button(self.root, text="Transfer", command=self.handle_transfer).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.create_customer_menu).pack(pady=5)
    
    def handle_transfer(self):
        recipient_number = self.recipient_entry.get()
        amount_str = self.transfer_amount_entry.get()
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid amount")
            return
        
        if recipient_number not in self.atm.accounts:
            messagebox.showerror("Error", "Recipient account not found")
            return
        
        if recipient_number == self.atm.current_account.account_number:
            messagebox.showerror("Error", "Cannot transfer to yourself")
            return
        
        recipient_account = self.atm.accounts[recipient_number]
        success, message = self.atm.current_account.transfer(amount, recipient_account)
        if success:
            self.atm.save_accounts()
            receipt = self.atm.current_account.generate_receipt('transfer_out', amount, recipient_number)
            messagebox.showinfo("Success", f"{message}\n\n{receipt}")
            self.create_customer_menu()
        else:
            messagebox.showerror("Error", message)
    
    def show_transaction_history(self):
        history = self.atm.current_account.get_transaction_history()
        self.clear_frame()
        
        tk.Label(self.root, text="Transaction History", font=("Arial", 14)).pack(pady=10)
        
        text_area = scrolledtext.ScrolledText(self.root, width=70, height=20)
        text_area.pack(pady=10)
        
        if not history:
            text_area.insert(tk.END, "No transactions yet.")
        else:
            for t in history:
                text_area.insert(tk.END, 
                    f"{t['date']} - {t['type'].upper()}: ${t['amount']:.2f}\n"
                    f"Balance: ${t['balance_after']:.2f}\n")
                if 'to_account' in t:
                    text_area.insert(tk.END, f"To: {t['to_account']}\n")
                if 'from_account' in t:
                    text_area.insert(tk.END, f"From: {t['from_account']}\n")
                text_area.insert(tk.END, "-"*50 + "\n")
        
        text_area.config(state=tk.DISABLED)
        tk.Button(self.root, text="Back", command=self.create_customer_menu).pack(pady=5)
    
    def create_change_pin(self):
        old_pin = simpledialog.askstring("Change PIN", "Enter current PIN:", show='*')
        if old_pin is None:
            return
        
        new_pin = simpledialog.askstring("Change PIN", "Enter new PIN (4 digits):", show='*')
        if new_pin is None:
            return
        
        confirm_pin = simpledialog.askstring("Change PIN", "Confirm new PIN:", show='*')
        if confirm_pin is None:
            return
        
        if new_pin != confirm_pin:
            messagebox.showerror("Error", "PINs do not match")
            return
        
        success, message = self.atm.current_account.change_pin(old_pin, new_pin)
        if success:
            self.atm.save_accounts()
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)
    
    def print_receipt(self):
        # In a real system, this would connect to a receipt printer
        # For this demo, we'll just show the last transaction
        history = self.atm.current_account.get_transaction_history()
        if not history:
            messagebox.showinfo("Receipt", "No transactions to print")
            return
        
        last_trans = history[-1]
        receipt = self.atm.current_account.generate_receipt(
            last_trans['type'],
            last_trans['amount'],
            last_trans.get('to_account', last_trans.get('from_account', None))
        )
        messagebox.showinfo("Receipt", receipt)
    
    def create_admin_menu(self):
        self.clear_frame()
        
        tk.Label(self.root, text=f"Admin Panel - Logged in as {self.atm.current_admin}", font=("Arial", 14)).pack(pady=10)
        
        buttons = [
            ("View All Accounts", self.show_all_accounts),
            ("Unlock Account", self.unlock_account),
            ("Close Account", self.close_account),
            ("View Account Details", self.view_account_details),
            ("Logout", self.admin_logout)
        ]
        
        for text, command in buttons:
            tk.Button(self.root, text=text, command=command, width=20).pack(pady=5)
    
    def show_all_accounts(self):
        accounts = self.atm.accounts
        self.clear_frame()
        
        tk.Label(self.root, text="All Accounts", font=("Arial", 14)).pack(pady=10)
        
        text_area = scrolledtext.ScrolledText(self.root, width=70, height=20)
        text_area.pack(pady=10)
        
        if not accounts:
            text_area.insert(tk.END, "No accounts found.")
        else:
            for acc_num, account in accounts.items():
                status = "Active" if account.is_active else "Inactive"
                locked = " (Locked)" if account.locked else ""
                text_area.insert(tk.END, 
                    f"Account: {acc_num}\n"
                    f"Balance: ${account.balance:.2f}\n"
                    f"Status: {status}{locked}\n"
                    f"Transactions: {len(account.transaction_history)}\n"
                    f"{'-'*50}\n")
        
        text_area.config(state=tk.DISABLED)
        tk.Button(self.root, text="Back", command=self.create_admin_menu).pack(pady=5)
    
    def unlock_account(self):
        account_number = simpledialog.askstring("Unlock Account", "Enter account number to unlock:")
        if account_number:
            success, message = self.atm.unlock_account(account_number, self.atm.current_admin)
            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
    
    def close_account(self):
        account_number = simpledialog.askstring("Close Account", "Enter account number to close:")
        if account_number:
            success, message = self.atm.close_account(account_number, self.atm.current_admin)
            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
    
    def view_account_details(self):
        account_number = simpledialog.askstring("Account Details", "Enter account number:")
        if account_number and account_number in self.atm.accounts:
            account = self.atm.accounts[account_number]
            self.clear_frame()
            
            tk.Label(self.root, text=f"Account Details: {account_number}", font=("Arial", 14)).pack(pady=10)
            
            status = "Active" if account.is_active else "Inactive"
            locked = " (Locked)" if account.locked else ""
            
            info = f"""
            Account Number: {account_number}
            Balance: ${account.balance:.2f}
            Status: {status}{locked}
            PIN Attempts: {account.pin_attempts}
            Transaction Count: {len(account.transaction_history)}
            """
            
            tk.Label(self.root, text=info).pack(pady=10)
            
            tk.Button(self.root, text="View Transactions", 
                     command=lambda: self.show_account_transactions(account_number)).pack(pady=5)
            tk.Button(self.root, text="Back", command=self.create_admin_menu).pack(pady=5)
        elif account_number:
            messagebox.showerror("Error", "Account not found")
    
    def show_account_transactions(self, account_number):
        account = self.atm.accounts[account_number]
        history = account.get_transaction_history()
        
        self.clear_frame()
        
        tk.Label(self.root, text=f"Transactions for Account {account_number}", font=("Arial", 14)).pack(pady=10)
        
        text_area = scrolledtext.ScrolledText(self.root, width=70, height=20)
        text_area.pack(pady=10)
        
        if not history:
            text_area.insert(tk.END, "No transactions yet.")
        else:
            for t in history:
                text_area.insert(tk.END, 
                    f"{t['date']} - {t['type'].upper()}: ${t['amount']:.2f}\n"
                    f"Balance: ${t['balance_after']:.2f}\n")
                if 'to_account' in t:
                    text_area.insert(tk.END, f"To: {t['to_account']}\n")
                if 'from_account' in t:
                    text_area.insert(tk.END, f"From: {t['from_account']}\n")
                text_area.insert(tk.END, "-"*50 + "\n")
        
        text_area.config(state=tk.DISABLED)
        tk.Button(self.root, text="Back", command=self.create_admin_menu).pack(pady=5)
    
    def logout(self):
        self.atm.current_account = None
        self.create_main_menu()
    
    def admin_logout(self):
        self.atm.current_admin = None
        self.create_main_menu()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    atm_system = ATM()
    app = ATMGUI(atm_system)
    app.run()