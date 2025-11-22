from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window
from allpy import faceid
from allpy import emodet
from allpy import aggression
from allpy import intruder
from allpy import loading
import requests
from bs4 import BeautifulSoup
import time

# Placeholder imports from allpy
# Import the necessary modules from allpy
# from allpy import faceid, emodet, aggression, intruder, tempctrl

# Dummy faceid and emodet functions (replace with your actual modules)
def run_faceid():
    print("Running faceid module...")

def run_emodet():
    print("Running emodet module...")

# Temperature Control Unit class (for demonstration)
class TemperatureControlUnit:
    def __init__(self, city, target_temp=25.0):
        self.city = city
        self.target_temp = target_temp
        self.current_temp = 0.0
        self.status = ""

    def fetch_temperature(self):
        """Fetch the current temperature from a weather website."""
        try:
            url = f"https://www.timeanddate.com/weather/india/{self.city.lower().replace(' ', '-')}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            temp_div = soup.find("div", {"id": "qlook"})
            temp_string = temp_div.find("div", {"class": "h2"}).text.strip()
            self.current_temp = float(temp_string.split("°")[0])  # Extract temperature
            self.status = f"Current temperature: {self.current_temp}°C"
        except Exception as e:
            self.status = f"Error fetching temperature: {e}"
            self.current_temp = self.target_temp  # Fallback

    def adjust_temperature(self):
        """Adjust the temperature to the target temperature."""
        error = self.target_temp - self.current_temp
        if error > 0:
            appliance = "HEATER"
        elif error < 0:
            appliance = "AC"
        else:
            self.status = "Temperature is already at target. No adjustment needed."
            return

        runtime = abs(error)
        print(f"{appliance} running for {runtime:.2f} seconds...")
        time.sleep(runtime)
        self.current_temp += error
        self.status = f"Adjusted temperature: {self.current_temp:.2f}°C || {appliance} WAS ACTIVATED"

# Temperature Control Screen
class TemperatureControlScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.city = "Sehore"
        self.target_temp = 22.0

        # Layout for the screen
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)

        # Title Label
        title_label = Label(text="Temperature Control", font_size="24sp", size_hint=(1, 0.1))
        layout.add_widget(title_label)

        # Target Temperature Label
        self.target_temp_label = Label(
            text=f"Target Temperature: {self.target_temp}°C", font_size="18sp", size_hint=(1, 0.1)
        )
        layout.add_widget(self.target_temp_label)

        # Temperature Slider
        temp_slider = Slider(min=16, max=30, value=self.target_temp, size_hint=(1, 0.2))
        temp_slider.bind(value=self.on_slider_value_change)
        layout.add_widget(temp_slider)

        # Fetch and Adjust Button
        fetch_button = Button(
            text="Fetch & Adjust Temperature", size_hint=(1, 0.2), background_color=(0.2, 0.8, 0.4, 1)
        )
        fetch_button.bind(on_press=self.on_fetch_button_press)
        layout.add_widget(fetch_button)

        # Status Label
        self.status_label = Label(text="", font_size="16sp", size_hint=(1, 0.3), color=(0.5, 0.5, 0.5, 1))
        layout.add_widget(self.status_label)

        # Close Button (Back to Main Menu)
        close_button = Button(
            text="Back to Main Menu", size_hint=(1, 0.2), background_color=(0.8, 0.2, 0.2, 1)
        )
        close_button.bind(on_press=self.close_window)
        layout.add_widget(close_button)

        self.add_widget(layout)

    def on_slider_value_change(self, instance, value):
        """Update target temperature based on slider value."""
        self.target_temp = float(value)
        self.target_temp_label.text = f"Target Temperature: {self.target_temp:.1f}°C"

    def on_fetch_button_press(self, instance):
        """Fetch and adjust temperature."""
        tcu = TemperatureControlUnit(city=self.city, target_temp=self.target_temp)
        tcu.fetch_temperature()  # Fetch current temperature
        self.status_label.text = tcu.status  # Display current temperature
        Clock.schedule_once(lambda dt: self.update_status(tcu), 1)

    def update_status(self, tcu):
        tcu.adjust_temperature()
        self.status_label.text = tcu.status

    def close_window(self, instance):
        """Go back to Main Menu."""
        self.manager.current = "main_menu"

# Main Menu Screen
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)

        title_label = Label(text="Main Menu", font_size="32sp", size_hint=(1, 0.2))
        layout.add_widget(title_label)

        # Add buttons to menu
        self.add_menu_button(layout, "Indoor Cam (Aggression)", self.run_aggression)
        self.add_menu_button(layout, "Backdoor Cam (Intruder)", self.run_intruder)
        self.add_menu_button(layout, "Temperature Control", self.open_tempctrl_window)
        self.add_menu_button(layout, "Exit App", self.shrink_window)

        self.add_widget(layout)

    def add_menu_button(self, layout, text, callback):
        btn = Button(text=text, size_hint=(1, 0.2), font_size=24)
        btn.bind(on_press=callback)
        layout.add_widget(btn)

    def run_aggression(self, instance):
        # Placeholder for aggression module
        aggression.run()
        print("Running aggression module...")

    def run_intruder(self, instance):
        # Placeholder for intruder module
        intruder.run()
        print("Running intruder module...")

    def open_tempctrl_window(self, instance):
        """Navigate to the Temperature Control screen."""
        self.manager.current = "temp_control_screen"

    def shrink_window(self, instance):
        # Get the current center of the window
        center_x, center_y = Window.left + Window.width / 2, Window.top + Window.height / 2

        target_width = 100
        target_height = 100

        # Calculate the new top-left corner to keep the window centered
        new_left = center_x - target_width / 2
        new_top = center_y - target_height / 2 

        # Define the shrinking animation
        animation = Animation(
            size=(100, 100),  # Shrink the window to target size
            left=new_left,  # Adjust the top-left position
            top=new_top,
            duration=0.5,
        )
        animation.bind(on_complete=self.exit_app)
        animation.start(Window)

    def exit_app(self, instance, *args):
        exit()


# Main Application class
class MyKivyApp(App):
    
    

    def build(self):
        loading.run()
        # Run the faceid and emodet modules initially
        faceid.run()
        emodet.run()

        # Create the ScreenManager
        sm = ScreenManager(transition=SlideTransition())

        # Add the screens
        sm.add_widget(MainMenuScreen(name="main_menu"))
        sm.add_widget(TemperatureControlScreen(name="temp_control_screen"))

        return sm

# Run the app
if __name__ == "__main__":
    MyKivyApp().run()
