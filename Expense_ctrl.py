import os
import json
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.storage.jsonstore import JsonStore
from plyer import notification

# File to store stock and budget data
STOCK_FILE = "stock.json"
BUDGET_FILE = "budget.json"

# Initial Data
TOTAL_BUDGET = 10000
THRESHOLD = 3
DEFAULT_STOCK = {
    "Rice": 10, "Wheat": 8, "Milk": 5, "Eggs": 12, "Bread": 6,
    "Butter": 4, "Cheese": 3, "Chicken": 7, "Fruits": 9, "Vegetables": 10
}
DEFAULT_PRICES = {"Rice": 500, "Milk": 200, "Eggs": 250, "Bread": 150, "Cheese": 450, "Chicken": 700, "Fruits": 400, "Vegetables": 300}

class StockScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = JsonStore(STOCK_FILE)
        self.load_stock()
        self.create_ui()
    
    def load_stock(self):
        if not os.path.exists(STOCK_FILE):
            for item, qty in DEFAULT_STOCK.items():
                self.store.put(item, quantity=qty)
    
    def update_stock(self, item):
        qty = self.store.get(item)["quantity"]
        new_qty = max(0, qty - 1)
        self.store.put(item, quantity=new_qty)
        
        if new_qty <= THRESHOLD:
            self.manager.get_screen("expense").add_to_shopping_list(item)
            self.manager.current = "expense"
        
        self.refresh_display()
    
    def increase_stock(self, item, qty):
        """Increase stock in real-time when an item is bought."""
        current_qty = self.store.get(item)["quantity"]
        new_qty = current_qty + qty
        self.store.put(item, quantity=new_qty)
        self.store.store_load()
        self.refresh_display()  # Refresh UI to show updated stock

    def refresh_display(self):
        self.clear_widgets()
        self.create_ui()
    
    def create_ui(self):
        layout = GridLayout(cols=2, padding=10, spacing=10)
        
        for item in self.store.keys():
            qty = self.store.get(item)["quantity"]
            btn = Button(
                text=f"{item}\nQty: {qty}",
                font_size=20,
                on_press=lambda instance, i=item: self.update_stock(i)
            )
            layout.add_widget(btn)
        
        self.add_widget(layout)

class ExpenseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.budget_store = JsonStore(BUDGET_FILE)
        self.stock_screen = None  # Reference to StockScreen
        
        if not self.budget_store.exists("remaining_budget"):
            self.budget_store.put("remaining_budget", amount=TOTAL_BUDGET)
        
        self.shopping_list = {}
        self.quantity_inputs = {}  # Stores TextInput for quantities
        self.create_ui()
    
    def create_ui(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.budget_label = Label(text=f"Budget: ₹{self.get_budget()}", font_size=28)
        self.layout.add_widget(self.budget_label)

        self.item_layout = GridLayout(cols=3, padding=10, spacing=10)
        self.layout.add_widget(self.item_layout)

        self.purchase_button = Button(text="Purchase Items", font_size=24, on_press=self.purchase_items)
        self.layout.add_widget(self.purchase_button)
        
         # Input for adding money
        self.money_input = TextInput(hint_text="Enter amount to add", font_size=20, multiline=False)
        self.layout.add_widget(self.money_input)

        # Button to add money
        self.add_money_button = Button(text="Add Money", font_size=24, on_press=self.add_money)
        self.layout.add_widget(self.add_money_button)
        
        self.back_button = Button(text="Back to Stock", font_size=24, on_press=self.go_back)
        self.layout.add_widget(self.back_button)

        self.add_widget(self.layout)
    
    def add_to_shopping_list(self, item):
        """Add item to shopping list and allow user to select quantity."""
        if item not in self.shopping_list:
            self.shopping_list[item] = 1
        
        self.refresh_display()

    def add_money(self, instance):
        """Increase budget manually and save to budget.json."""
        try:
            amount = int(self.money_input.text)
            if amount > 0:
                new_budget = self.get_budget() + amount
                self.budget_store.put("remaining_budget", amount=new_budget)  # ✅ Save updated budget
                self.budget_store.store_load()  # ✅ Ensure immediate save
                self.refresh_display()  # ✅ Update UI

                # 📢 Show Notification
                os.system(f'''osascript -e 'display notification "New Budget: ₹{new_budget}" with title "Budget Updated"' ''')

        except ValueError:
            pass  # Ignore invalid input

    
    def refresh_display(self):
        self.item_layout.clear_widgets()
        self.quantity_inputs.clear()  # Reset inputs

        total_cost = 0
        
        for item, qty in self.shopping_list.items():
            price_per_unit = DEFAULT_PRICES.get(item, 100)
            price = price_per_unit * qty
            total_cost += price
            
            label = Label(text=f"{item} (₹{price_per_unit} each)", font_size=20)
            self.item_layout.add_widget(label)
            
            qty_input = TextInput(text=str(qty), font_size=20, multiline=False, size_hint_x=0.4)
            self.quantity_inputs[item] = qty_input
            self.item_layout.add_widget(qty_input)

            increase_btn = Button(text="+", size_hint_x=0.2, on_press=lambda instance, i=item: self.increase_quantity(i))
            self.item_layout.add_widget(increase_btn)
        
        remaining_budget = self.get_budget() - total_cost
        self.budget_label.text = f"Budget: ₹{remaining_budget}"

        if remaining_budget < 2000:
            os.system(f'''osascript -e 'display notification "Low Budget: ₹{remaining_budget}" with title "Warning!"' ''')
    
    def increase_quantity(self, item):
        """Increase the quantity of a selected item."""
        if item in self.shopping_list:
            self.shopping_list[item] += 1
            self.quantity_inputs[item].text = str(self.shopping_list[item])  # Update input field
        self.refresh_display()

    def get_budget(self):
        return self.budget_store.get("remaining_budget")["amount"]
    
    def purchase_items(self, instance):
        """Deducts cost from budget and adds purchased items back to stock."""
        total_cost = 0
        purchases = {}

        # Read input values
        for item, qty_input in self.quantity_inputs.items():
            try:
                qty = int(qty_input.text)
                if qty <= 0:
                    continue
                purchases[item] = qty
                total_cost += DEFAULT_PRICES.get(item, 100) * qty
            except ValueError:
                continue

        remaining_budget = max(0, self.get_budget() - total_cost)
        self.budget_store.put("remaining_budget", amount=remaining_budget)  # Save new budget
        self.budget_store.store_load()
        
        # Update stock with purchased items
        if self.stock_screen is None:
            self.stock_screen = self.manager.get_screen("stock")
        
        for item, qty in purchases.items():
            self.stock_screen.increase_stock(item, qty)  # Increase stock
        
        self.shopping_list.clear()  # Clear shopping list
        self.refresh_display()
        self.stock_screen.refresh_display()  # Force stock screen to refresh immediately
    
    def go_back(self, instance):
        self.manager.current = "stock"

class StockExpenseApp(App):
    def build(self):
        sm = ScreenManager()
        stock_screen = StockScreen(name="stock")
        expense_screen = ExpenseScreen(name="expense")
        
        sm.add_widget(stock_screen)
        sm.add_widget(expense_screen)

        # Reference ExpenseScreen to StockScreen
        expense_screen.stock_screen = stock_screen

        return sm

if __name__ == "__main__":
    StockExpenseApp().run()
