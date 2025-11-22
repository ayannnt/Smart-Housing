from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window

# Set app window size
#Window.size = (600, 400)

class LoadingScreen(BoxLayout):
    #Window.size = (600, 400)
    def __init__(self, **kwargs):
        super(LoadingScreen, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 20
        self.padding = 50

        # Big "Loading..." Label
        self.loading_label = Label(
            text="Loading...",
            font_size="50sp",
            color=(0.2, 0.7, 1, 1),  # Bright blue
            opacity=0  # Start with opacity 0
        )
        self.add_widget(self.loading_label)

        # Start the animation for 3 cycles
        self.animation_count = 0
        self.animate_loading()

    def animate_loading(self):
        anim = Animation(opacity=1, duration=1, t="in_out_quart") + \
               Animation(opacity=0, duration=1, t="in_out_quart")
        anim.bind(on_complete=self.on_animation_complete)  # Bind to handle animation end
        anim.start(self.loading_label)

    def on_animation_complete(self, *args):
        self.animation_count += 1
        if self.animation_count < 3:  # Repeat for 3 cycles
            self.animate_loading()
        else:
            self.stop_loading()

    def stop_loading(self):
        # After 3 animations, stop and display a final message (optional)
        self.loading_label.text = "Done"
        self.loading_label.opacity = 1


# Main App Class
class MyApp(App):
    def build(self):
        return LoadingScreen()


def run():
    MyApp().run()
