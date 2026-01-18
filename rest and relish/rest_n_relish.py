import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from mysql.connector import Error
from datetime import date, timedelta, datetime # Import datetime for date parsing

# --- (Main App Class) ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rest & Relish System")
        self.geometry("900x700")
        
        # Configure styles for a more modern look
        self.style = ttk.Style(self)
        self.style.theme_use('clam') # 'clam', 'alt', 'default', 'classic'
        self.style.configure('TNotebook.Tab', font=('Helvetica', 12, 'bold'), padding=[10, 5])
        self.style.configure('TButton', font=('Helvetica', 10), padding=5)
        self.style.configure('TLabel', font=('Helvetica', 10))
        self.style.configure('TEntry', font=('Helvetica', 10))
        self.style.configure('Treeview.Heading', font=('Helvetica', 10, 'bold'))
        self.style.configure('Selected.TButton', font=('Helvetica', 10), padding=5, background='#0078d4', foreground='white')

        self.db_conn = None
        
        # --- Direct Database Connection ---
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Your_Mysql_Password",  # <-- YOUR MYSQL PASSWORD
                database="rest_relish_db",
                autocommit=True  # <-- This fixes the transaction error
            )
            
            if conn.is_connected():
                self.db_conn = conn
                self.create_main_widgets()
                # Load initial data
                self.refresh_room_dashboard()
                self.refresh_table_dashboard()
            
        except Error as e:
            messagebox.showerror("Database Connection Failed", f"Error connecting to database:\n{e}\n\nPlease ensure MySQL is running and credentials in the code are correct.")
            self.destroy() # Close app if connection fails

    def create_main_widgets(self):
        # Create the main Tab controller (Notebook)
        self.notebook = ttk.Notebook(self)
        
        # Create the two main frames for our tabs
        self.hotel_frame = ttk.Frame(self.notebook, padding="10")
        self.restaurant_frame = ttk.Frame(self.notebook, padding="10")
        
        # Add the frames as tabs
        self.notebook.add(self.hotel_frame, text='REST (Hotel)')
        self.notebook.add(self.restaurant_frame, text='RELISH (Restaurant)')
        
        self.notebook.pack(expand=True, fill='both')
        
        # --- Build the content for each tab ---
        self.setup_hotel_tab()
        self.setup_restaurant_tab()
        
        # --- Class variables for Restaurant ---
        self.current_table_info = None
        self.current_order_items = []

    def setup_hotel_tab(self):
        # --- Left Side: Controls ---
        hotel_controls = ttk.Frame(self.hotel_frame, padding="10")
        hotel_controls.pack(side="left", fill="y", padx=5)

        ttk.Button(hotel_controls, text="Guest Check-In", command=self.open_check_in).pack(fill='x', pady=5)
        ttk.Button(hotel_controls, text="Guest Check-Out", command=self.open_check_out).pack(fill='x', pady=5)
        ttk.Button(hotel_controls, text="View Booking Folio", command=self.open_view_folio).pack(fill='x', pady=5)
        
        # --- Right Side: Dashboard ---
        hotel_dashboard = ttk.Frame(self.hotel_frame, padding="10")
        hotel_dashboard.pack(side="right", expand=True, fill="both")

        ttk.Label(hotel_dashboard, text="Room Dashboard", font=("Helvetica", 14, "bold")).pack(pady=10)

        cols = ("room_number", "room_type", "price", "status")
        self.room_tree = ttk.Treeview(hotel_dashboard, columns=cols, show='headings')
        for col in cols:
            self.room_tree.heading(col, text=col.replace('_', ' ').title())
        self.room_tree.pack(expand=True, fill="both", pady=5)
        
        # Add color tags
        self.room_tree.tag_configure('Available', background='#d9f0d9')
        self.room_tree.tag_configure('Occupied', background='#f0d9d9')

        ttk.Button(hotel_dashboard, text="Refresh Dashboard", command=self.refresh_room_dashboard).pack(pady=10)

    def setup_restaurant_tab(self):
        # --- Left Side: Table Dashboard ---
        table_dashboard = ttk.Frame(self.restaurant_frame, padding="10")
        table_dashboard.pack(side="left", fill="y", padx=5)
        
        ttk.Label(table_dashboard, text="Table Dashboard", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        self.table_grid_frame = ttk.Frame(table_dashboard)
        self.table_grid_frame.pack(expand=True, fill='both')
        
        ttk.Button(table_dashboard, text="Refresh Tables", command=self.refresh_table_dashboard).pack(pady=10)

        # --- Right Side: Order Management ---
        order_frame = ttk.Frame(self.restaurant_frame, padding="10")
        order_frame.pack(side="right", expand=True, fill="both")

        self.selected_table_label = ttk.Label(order_frame, text="Selected Table: [None]", font=("Helvetica", 14, "bold"))
        self.selected_table_label.pack(pady=10)
        
        # --- Menu Frame ---
        menu_frame = ttk.Frame(order_frame)
        menu_frame.pack(fill='both', expand=True, pady=5)
        
        ttk.Label(menu_frame, text="Menu", font=("Helvetica", 12, "bold")).pack()
        
        menu_cols = ("item_id", "name", "price", "category")
        self.menu_tree = ttk.Treeview(menu_frame, columns=menu_cols, show='headings', height=10)
        for col in menu_cols:
            self.menu_tree.heading(col, text=col.replace('_', ' ').title())
        self.menu_tree.column("item_id", width=50, anchor='center')
        self.menu_tree.column("price", width=80, anchor='e')
        self.menu_tree.pack(fill='both', expand=True, side='left')
        
        menu_scroll = ttk.Scrollbar(menu_frame, orient="vertical", command=self.menu_tree.yview)
        menu_scroll.pack(side='right', fill='y')
        self.menu_tree.configure(yscrollcommand=menu_scroll.set)

        ttk.Button(order_frame, text="Add Selected Item to Order >>", command=self.add_item_to_order).pack(pady=5)

        # --- Current Order Frame ---
        current_order_frame = ttk.Frame(order_frame)
        current_order_frame.pack(fill='both', expand=True, pady=10)
        
        ttk.Label(current_order_frame, text="Current Order", font=("Helvetica", 12, "bold")).pack()
        
        order_cols = ("item_id", "name", "qty", "sub_total")
        self.current_order_tree = ttk.Treeview(current_order_frame, columns=order_cols, show='headings', height=5)
        for col in order_cols:
            self.current_order_tree.heading(col, text=col.replace('_', ' ').title())
        self.current_order_tree.column("item_id", width=50, anchor='center')
        self.current_order_tree.column("qty", width=50, anchor='center')
        self.current_order_tree.column("sub_total", width=80, anchor='e')
        self.current_order_tree.pack(fill='both', expand=True)

        # --- Payment Frame ---
        payment_frame = ttk.Frame(order_frame)
        payment_frame.pack(fill='x', pady=10)
        
        self.pay_walk_in_btn = ttk.Button(payment_frame, text="Pay (Walk-In)", state="disabled", command=self.process_walk_in_payment)
        self.pay_walk_in_btn.pack(side='left', expand=True, fill='x', padx=5)
        
        self.charge_to_room_btn = ttk.Button(payment_frame, text="Charge to Room", state="disabled", command=self.process_charge_to_room)
        self.charge_to_room_btn.pack(side='right', expand=True, fill='x', padx=5)
        

    # --- HOTEL (REST) FUNCTIONS ---
    
    def refresh_room_dashboard(self):
        # Clear existing items
        for item in self.room_tree.get_children():
            self.room_tree.delete(item)
        
        cursor = None # Define cursor outside try
        try:
            cursor = self.db_conn.cursor(dictionary=True)
            cursor.execute("SELECT room_number, room_type, price_per_night, is_occupied FROM rooms ORDER BY room_number")
            rooms = cursor.fetchall()
            for room in rooms:
                status = "Occupied" if room['is_occupied'] else "Available"
                self.room_tree.insert("", "end", values=(
                    room['room_number'],
                    room['room_type'],
                    f"₹{room['price_per_night']:.2f}", 
                    status
                ), tags=(status,))
        except Error as e:
            messagebox.showerror("Error", f"Failed to fetch room status:\n{e}")
        finally:
            if cursor: cursor.close()
            # No commit needed because of autocommit=True

    def open_check_in(self):
        CheckInWindow(self, self.db_conn)
        
    def open_check_out(self):
        CheckOutWindow(self, self.db_conn)
        
    def open_view_folio(self):
        booking_id = simpledialog.askinteger("View Folio", "Enter Booking ID:", parent=self)
        if not booking_id:
            return
            
        folio_details, total = self._get_booking_folio(booking_id)
        
        if folio_details is None:
            messagebox.showerror("Error", f"Could not find folio for Booking ID {booking_id}.", parent=self)
            return
            
        messagebox.showinfo(f"Folio for Booking {booking_id}", f"{folio_details}\n----------------\nGRAND TOTAL: ₹{total:.2f}")

    def _get_booking_folio(self, booking_id):
        cursor = None
        try:
            cursor = self.db_conn.cursor(dictionary=True)
            
            # 1. Get room cost from bookings
            cursor.execute("SELECT total_room_cost FROM bookings WHERE booking_id = %s", (booking_id,))
            booking_result = cursor.fetchone()
            
            if not booking_result:
                return None, None
                
            room_cost = booking_result['total_room_cost']
            grand_total = room_cost
            folio_details = f"Room Charges: ₹{room_cost:.2f}\n\nRestaurant Charges:\n"
            
            # 2. Get all 'charged_to_room' orders
            cursor.execute("""
                SELECT order_timestamp, order_total 
                FROM orders 
                WHERE booking_id = %s AND order_status = 'charged_to_room'
            """, (booking_id,))
            
            orders = cursor.fetchall()
            
            if not orders:
                folio_details += "  (None)\n"
            else:
                for order in orders:
                    folio_details += f"  - {order['order_timestamp'].strftime('%Y-%m-%d %H:%M')}: ₹{order['order_total']:.2f}\n"
                    grand_total += order['order_total']
                    
            return folio_details, grand_total
            
        except Error as e:
            messagebox.showerror("Database Error", f"Error fetching folio:\n{e}")
            return None, None
        finally:
            if cursor: cursor.close()
            # No commit needed because of autocommit=True


    # --- RESTAURANT (RELISH) FUNCTIONS ---
    
    def refresh_table_dashboard(self, selected_table_number=None):
        for widget in self.table_grid_frame.winfo_children():
            widget.destroy()
            
        cursor = None
        try:
            cursor = self.db_conn.cursor(dictionary=True)
            cursor.execute("SELECT table_id, table_number, status FROM tables ORDER BY table_number")
            tables = cursor.fetchall()
            
            row, col = 0, 0
            for table in tables:
                btn_text = f"{table['table_number']}\n({table['status']})"
                
                style_name = 'TButton'
                if table['table_number'] == selected_table_number:
                    style_name = 'Selected.TButton'
                
                btn = ttk.Button(self.table_grid_frame, text=btn_text, style=style_name, command=lambda t=table: self.select_table(t))
                btn.grid(row=row, column=col, padx=5, pady=5, ipadx=10, ipady=10)
                
                col += 1
                if col > 2: # 3 buttons per row
                    col = 0
                    row += 1
                    
        except Error as e:
            messagebox.showerror("Error", f"Failed to fetch table status:\n{e}")
        finally:
            if cursor: cursor.close()
            # No commit needed because of autocommit=True
            
    def select_table(self, table_info):
        self.current_table_info = table_info
        self.selected_table_label.config(text=f"Selected Table: {table_info['table_number']} ({table_info['status']})")
        
        self.clear_current_order()
        
        # --- Back to the original single function call ---
        self.load_menu()
        
        self.pay_walk_in_btn.config(state="normal")
        self.charge_to_room_btn.config(state="normal")
        
        self.refresh_table_dashboard(selected_table_number=table_info['table_number'])
            
    def load_menu(self):
        """
        Loads all menu items from the database into the menu_tree.
        """
        for item in self.menu_tree.get_children():
            self.menu_tree.delete(item)
            
        cursor = None
        try:
            cursor = self.db_conn.cursor(dictionary=True)
            
            query = "SELECT item_id, name, price, category FROM menu_items ORDER BY category, name"
            
            cursor.execute(query)
            menu_items = cursor.fetchall()
            
            for item in menu_items:
                self.menu_tree.insert("", "end", values=(
                    item['item_id'],
                    item['name'],
                    f"₹{item['price']:.2f}",
                    item['category']
                ))
        except Error as e:
            messagebox.showerror("Error", f"Failed to load menu:\n{e}")
        finally:
            if cursor: cursor.close()
            # No commit needed because of autocommit=True

    def add_item_to_order(self):
        selected_item_iid = self.menu_tree.focus()
        if not selected_item_iid:
            messagebox.showwarning("No Selection", "Please select a menu item to add.")
            return
            
        if not self.current_table_info:
            messagebox.showwarning("No Table", "Please select a table before adding items.")
            return

        item_data = self.menu_tree.item(selected_item_iid)['values']
        item_id = item_data[0]
        name = item_data[1]
        price = float(item_data[2].replace('₹', ''))
        
        for order_item_iid in self.current_order_tree.get_children():
            values = self.current_order_tree.item(order_item_iid)['values']
            if values[0] == item_id:
                qty = values[2] + 1
                new_sub_total = qty * price
                self.current_order_tree.item(order_item_iid, values=(item_id, name, qty, f"₹{new_sub_total:.2f}"))
                return
                
        self.current_order_tree.insert("", "end", values=(item_id, name, 1, f"₹{price:.2f}"))

    def clear_current_order(self):
        for item in self.current_order_tree.get_children():
            self.current_order_tree.delete(item)

    def process_walk_in_payment(self):
        order_details = self._get_order_details_from_tree()
        if not order_details:
            messagebox.showwarning("Empty Order", "Cannot process an empty order.", parent=self)
            return

        if not messagebox.askyesno("Confirm Payment", f"Total bill is ₹{order_details['total']:.2f}. Confirm payment?"):
            return

        success = self._create_order_in_db(
            table_id=self.current_table_info['table_id'],
            booking_id=None,
            order_status='paid',
            order_total=order_details['total'],
            items=order_details['items']
        )
        
        if success:
            messagebox.showinfo("Success", f"Payment of ₹{order_details['total']:.2f} recorded.")
            self._reset_restaurant_ui()

    def process_charge_to_room(self):
        order_details = self._get_order_details_from_tree()
        if not order_details:
            messagebox.showwarning("Empty Order", "Cannot process an empty order.", parent=self)
            return

        room_number = simpledialog.askstring("Charge to Room", "Enter guest's room number:", parent=self)
        if not room_number:
            return

        booking_id = self._get_booking_id_from_room(room_number)
        if not booking_id:
            messagebox.showerror("Error", f"Could not find an active booking for Room {room_number}.", parent=self)
            return

        if not messagebox.askyesno("Confirm Charge", f"Charge ₹{order_details['total']:.2f} to Room {room_number}?"):
            return

        success = self._create_order_in_db(
            table_id=self.current_table_info['table_id'],
            booking_id=booking_id,
            order_status='charged_to_room',
            order_total=order_details['total'],
            items=order_details['items']
        )

        if success:
            messagebox.showinfo("Success", f"Charge of ₹{order_details['total']:.2f} posted to Room {room_number}.")
            self._reset_restaurant_ui()

    # --- RESTAURANT HELPER FUNCTIONS ---

    def _get_order_details_from_tree(self):
        items_list = []
        total_price = 0.0

        for item_iid in self.current_order_tree.get_children():
            values = self.current_order_tree.item(item_iid)['values']
            item_id = int(values[0])
            qty = int(values[2])
            sub_total = float(values[3].replace('₹', ''))
            
            items_list.append({
                "item_id": item_id,
                "quantity": qty,
                "sub_total": sub_total
            })
            total_price += sub_total
        
        if not items_list:
            return None
            
        return {"items": items_list, "total": total_price}

    def _get_booking_id_from_room(self, room_number):
        query = """
        SELECT b.booking_id 
        FROM bookings b
        JOIN rooms r ON b.room_id = r.room_id
        WHERE r.room_number = %s AND b.is_active = 1
        """
        cursor = None
        try:
            cursor = self.db_conn.cursor(dictionary=True)
            cursor.execute(query, (room_number,))
            result = cursor.fetchone()
            if result:
                return result['booking_id']
            else:
                return None
        except Error as e:
            messagebox.showerror("Database Error", f"Error finding booking:\n{e}")
            return None
        finally:
            if cursor: cursor.close()
            # No commit needed because of autocommit=True

    def _create_order_in_db(self, table_id, booking_id, order_status, order_total, items):
        cursor = None
        try:
            cursor = self.db_conn.cursor()
            
            # This function needs a transaction, so we start one.
            # This temporarily overrides autocommit=True
            self.db_conn.start_transaction()
            
            order_query = """
            INSERT INTO orders (table_id, booking_id, order_status, order_total, order_timestamp)
            VALUES (%s, %s, %s, %s, NOW())
            """
            order_data = (table_id, booking_id, order_status, order_total)
            cursor.execute(order_query, order_data)
            
            order_id = cursor.lastrowid
            
            item_query = """
            INSERT INTO order_items (order_id, item_id, quantity, sub_total)
            VALUES (%s, %s, %s, %s)
            """
            item_data = [
                (order_id, item['item_id'], item['quantity'], item['sub_total'])
                for item in items
            ]
            cursor.executemany(item_query, item_data)
            
            table_query = "UPDATE tables SET status = 'available' WHERE table_id = %s"
            cursor.execute(table_query, (table_id,))
            
            self.db_conn.commit() # We must manually commit this transaction
            return True
            
        except Error as e:
            if self.db_conn:
                self.db_conn.rollback() # We must manually roll back on error
            messagebox.showerror("Transaction Failed", f"Could not save order. Changes were rolled back.\nError: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def _reset_restaurant_ui(self):
        self.clear_current_order()
        self.selected_table_label.config(text="Selected Table: [None]")
        self.pay_walk_in_btn.config(state="disabled")
        self.charge_to_room_btn.config(state="disabled")
        self.current_table_info = None
        self.refresh_table_dashboard()


    # --- APP LIFECYCLE ---
    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.db_conn and self.db_conn.is_connected():
                self.db_conn.close()
                print("MySQL connection closed.")
            self.destroy()

# --- (End of Main App Class) ---


# --- NEW Toplevel Window for CHECK-IN ---
class CheckInWindow(tk.Toplevel):
    def __init__(self, parent, db_conn):
        super().__init__(parent)
        self.parent_app = parent 
        self.db_conn = db_conn
        
        self.title("Guest Check-In")
        self.geometry("700x500")
        self.transient(parent)
        self.grab_set()

        # --- Guest Details Frame ---
        guest_frame = ttk.LabelFrame(self, text="Guest Details", padding=10)
        guest_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(guest_frame, text="First Name:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.first_name_entry = ttk.Entry(guest_frame)
        self.first_name_entry.grid(row=0, column=1, sticky='ew', padx=5)
        
        ttk.Label(guest_frame, text="Last Name:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.last_name_entry = ttk.Entry(guest_frame)
        self.last_name_entry.grid(row=1, column=1, sticky='ew', padx=5)
        
        ttk.Label(guest_frame, text="Email:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.email_entry = ttk.Entry(guest_frame)
        self.email_entry.grid(row=0, column=3, sticky='ew', padx=5)
        
        ttk.Label(guest_frame, text="Phone:").grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.phone_entry = ttk.Entry(guest_frame)
        self.phone_entry.grid(row=1, column=3, sticky='ew', padx=5)
        
        guest_frame.columnconfigure(1, weight=1)
        guest_frame.columnconfigure(3, weight=1)
        
        # --- Booking Details Frame ---
        booking_frame = ttk.LabelFrame(self, text="Booking Details", padding=10)
        booking_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(booking_frame, text="Check-In (YYYY-MM-DD):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.check_in_entry = ttk.Entry(booking_frame)
        self.check_in_entry.insert(0, date.today().isoformat()) # Default to today
        self.check_in_entry.grid(row=0, column=1, sticky='ew', padx=5)
        
        ttk.Label(booking_frame, text="Check-Out (YYYY-MM-DD):").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.check_out_entry = ttk.Entry(booking_frame)
        self.check_out_entry.insert(0, (date.today() + timedelta(days=1)).isoformat()) # Default to tomorrow
        self.check_out_entry.grid(row=0, column=3, sticky='ew', padx=5)

        booking_frame.columnconfigure(1, weight=1)
        booking_frame.columnconfigure(3, weight=1)

        # --- Available Rooms Frame ---
        rooms_frame = ttk.LabelFrame(self, text="Select an Available Room", padding=10)
        rooms_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        cols = ("room_id", "room_number", "room_type", "price")
        self.rooms_tree = ttk.Treeview(rooms_frame, columns=cols, show='headings', height=5)
        self.rooms_tree.heading("room_id", text="ID")
        self.rooms_tree.heading("room_number", text="Room No.")
        self.rooms_tree.heading("room_type", text="Type")
        self.rooms_tree.heading("price", text="Price/Night")
        self.rooms_tree.column("room_id", width=30, anchor='center')
        self.rooms_tree.pack(fill="both", expand=True)
        
        self.load_available_rooms()

        # --- Confirmation Button ---
        confirm_btn = ttk.Button(self, text="Confirm Check-In", command=self.process_check_in)
        confirm_btn.pack(pady=10)

    def load_available_rooms(self):
        for item in self.rooms_tree.get_children():
            self.rooms_tree.delete(item)
            
        cursor = None
        try:
            cursor = self.db_conn.cursor(dictionary=True)
            cursor.execute("SELECT room_id, room_number, room_type, price_per_night FROM rooms WHERE is_occupied = 0")
            rooms = cursor.fetchall()
            for room in rooms:
                self.rooms_tree.insert("", "end", values=(
                    room['room_id'],
                    room['room_number'],
                    room['room_type'],
                    room['price_per_night'] 
                ))
        except Error as e:
            messagebox.showerror("Error", f"Failed to fetch available rooms:\n{e}", parent=self)
        finally:
            if cursor: cursor.close()
            # No commit needed because of autocommit=True
            
    def process_check_in(self):
        first_name = self.first_name_entry.get()
        last_name = self.last_name_entry.get()
        email = self.email_entry.get()
        phone = self.phone_entry.get()
        check_in_str = self.check_in_entry.get()
        check_out_str = self.check_out_entry.get()
        
        selected_item = self.rooms_tree.focus()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a room.", parent=self)
            return
            
        if not (first_name and last_name and check_in_str and check_out_str):
            messagebox.showwarning("Warning", "Please fill in all guest and date fields.", parent=self)
            return

        room_data = self.rooms_tree.item(selected_item)['values']
        room_id = room_data[0]
        price_per_night = float(room_data[3])
        
        try:
            check_in_date = date.fromisoformat(check_in_str)
            check_out_date = date.fromisoformat(check_out_str)
            if check_in_date >= check_out_date:
                raise ValueError("Check-out date must be after check-in date.")
            
            num_nights = (check_out_date - check_in_date).days
            total_room_cost = num_nights * price_per_night
            
        except ValueError as e:
            messagebox.showwarning("Invalid Date", f"Error in dates: {e}", parent=self)
            return

        cursor = None
        try:
            cursor = self.db_conn.cursor()
            # This function needs a transaction, so we start one.
            self.db_conn.start_transaction()
            
            guest_query = "INSERT INTO guests (first_name, last_name, email, phone) VALUES (%s, %s, %s, %s)"
            cursor.execute(guest_query, (first_name, last_name, email, phone))
            guest_id = cursor.lastrowid
            
            booking_query = """
            INSERT INTO bookings (guest_id, room_id, check_in_date, check_out_date, total_room_cost, is_active)
            VALUES (%s, %s, %s, %s, %s, 1)
            """
            cursor.execute(booking_query, (guest_id, room_id, check_in_str, check_out_str, total_room_cost))
            
            room_query = "UPDATE rooms SET is_occupied = 1 WHERE room_id = %s"
            cursor.execute(room_query, (room_id,))
            
            self.db_conn.commit() # Manually commit this transaction
            
            messagebox.showinfo("Success", f"Guest {first_name} {last_name} checked into Room {room_data[1]}.", parent=self)
            
            self.parent_app.refresh_room_dashboard() 
            self.destroy() 
            
        except Error as e:
            if self.db_conn: self.db_conn.rollback() # Manually roll back
            messagebox.showerror("Transaction Failed", f"Could not complete check-in.\nError: {e}", parent=self)
        finally:
            if cursor: cursor.close()


# --- NEW Toplevel Window for CHECK-OUT ---
# --- (This class includes the button-disabling fix, which is still good) ---
class CheckOutWindow(tk.Toplevel):
    def __init__(self, parent, db_conn):
        super().__init__(parent)
        self.parent_app = parent 
        self.db_conn = db_conn
        
        self.title("Guest Check-Out")
        self.geometry("800x400")
        self.transient(parent)
        self.grab_set()
        
        bookings_frame = ttk.LabelFrame(self, text="Select an Active Booking to Check-Out", padding=10)
        bookings_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        cols = ("booking_id", "room_number", "guest_name", "check_in_date", "check_out_date")
        self.bookings_tree = ttk.Treeview(bookings_frame, columns=cols, show='headings', height=10)
        for col in cols:
            self.bookings_tree.heading(col, text=col.replace('_', ' ').title())
            
        self.bookings_tree.column("booking_id", width=50, anchor='center')
        self.bookings_tree.pack(fill="both", expand=True)
        
        self.load_active_bookings()
        
        # Save the button as a class variable so we can disable it
        self.confirm_btn = ttk.Button(self, text="View Folio & Process Check-Out", command=self.process_check_out)
        self.confirm_btn.pack(pady=10)
        
    def load_active_bookings(self):
        for item in self.bookings_tree.get_children():
            self.bookings_tree.delete(item)
            
        cursor = None
        try:
            cursor = self.db_conn.cursor(dictionary=True)
            query = """
            SELECT b.booking_id, r.room_number, CONCAT(g.first_name, ' ', g.last_name) AS guest_name, b.check_in_date, b.check_out_date
            FROM bookings b
            JOIN guests g ON b.guest_id = g.guest_id
            JOIN rooms r ON b.room_id = r.room_id
            WHERE b.is_active = 1
            ORDER BY r.room_number
            """
            cursor.execute(query)
            bookings = cursor.fetchall()
            for b in bookings:
                self.bookings_tree.insert("", "end", values=(
                    b['booking_id'],
                    b['room_number'],
                    b['guest_name'],
                    b['check_in_date'],
                    b['check_out_date']
                ))
        except Error as e:
            messagebox.showerror("Error", f"Failed to fetch active bookings:\n{e}", parent=self)
        finally:
            if cursor: cursor.close()
            # No commit needed because of autocommit=True

    def process_check_out(self):
        selected_item = self.bookings_tree.focus()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a booking to check-out.", parent=self)
            return
            
        booking_data = self.bookings_tree.item(selected_item)['values']
        booking_id = booking_data[0]
        guest_name = booking_data[2]
        
        # This function is now safe because _get_booking_folio will not leave an open transaction
        folio_details, total = self.parent_app._get_booking_folio(booking_id)
        if folio_details is None:
            messagebox.showerror("Error", f"Could not calculate folio for Booking {booking_id}.", parent=self)
            return
            
        confirm_msg = f"--- FINAL FOLIO for {guest_name} ---\n\n"
        confirm_msg += f"{folio_details}\n----------------\nGRAND TOTAL: ₹{total:.2f}"
        confirm_msg += "\n\nProcess payment and check-out this guest?"
        
        if not messagebox.askyesno("Confirm Check-Out & Payment", confirm_msg, parent=self):
            return
            
        # Disable button to prevent double-clicks
        self.confirm_btn.config(state="disabled")
        
        cursor = None
        try: 
            cursor = self.db_conn.cursor()
            # This function needs a transaction, so we start one.
            self.db_conn.start_transaction()
            
            cursor.execute("SELECT room_id FROM bookings WHERE booking_id = %s", (booking_id,))
            result = cursor.fetchone()
            if not result:
                raise Error("Booking ID not found during check-out.")
            
            room_id = result[0]
            
            cursor.execute("UPDATE bookings SET is_active = 0 WHERE booking_id = %s", (booking_id,))
            
            cursor.execute("UPDATE rooms SET is_occupied = 0 WHERE room_id = %s", (room_id,))
            
            self.db_conn.commit() # Manually commit this transaction
            
            messagebox.showinfo("Success", f"Guest {guest_name} has been checked out.", parent=self)
            
            # --- THIS IS THE FIXED LINE ---
            self.parent_app.refresh_room_dashboard() 
            self.destroy() # Window closes on success
            
        except Error as e:
            if self.db_conn: self.db_conn.rollback() # Manually roll back
            messagebox.showerror("Transaction Failed", f"Could not complete check-out.\nError: {e}", parent=self)
            
            # Re-enable button ONLY if it failed
            try:
                self.confirm_btn.config(state="normal")
            except tk.TclError:
                pass # Ignore if window is already closing
        finally:
            if cursor: cursor.close()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing) # Handle window close
    app.mainloop()