from __future__ import absolute_import, print_function, unicode_literals

import gi
import signal

gi.require_version('AppIndicator3', '0.1')
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
from gi.repository import AppIndicator3, Gtk, Notify

from new_device_window import USBGuardNewDeviceApplication
from screensaver_dbus import ScreensaverDBUS
from usbguard_dbus import Rule, USBGuardDBUS
from usbguard_gnome_window import USBGuardGnomeApplication

# Gdk.threads_init()
APPINDICATOR_ID = 'USBGuardGnomeApplet'


class USBGuardAppIndicator(object):

    USBGUARD_ICON_PATH = '/home/chriz/repositories/usbguard/src/GUI.Qt/resources/usbguard-icon.svg'

    usbguard_app = None
    notifications = {}

    def __init__(self):
        Notify.init(APPINDICATOR_ID)
        self.indicator = AppIndicator3.Indicator.new(
            APPINDICATOR_ID,
            self.USBGUARD_ICON_PATH,
            AppIndicator3.IndicatorCategory.SYSTEM_SERVICES
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.update_menu()

        self.usbguard_dbus = USBGuardDBUS.get_instance()
        self.usbguard_dbus.register_device_policy_changed_callback(self.new_device_callback)

        self.screensaver_dbus = ScreensaverDBUS.get_instance()
        self.screensaver_dbus.register_screensaver_active_changed_callback(self.screensaver_active_changed_callback)

        self.device_policy_changed_ids = []

    def new_device_callback(self, device, rule_id):
        # user response to a previous notification will raise a new policy changed event, therefore ignore it
        if rule_id in self.device_policy_changed_ids:
            self.device_policy_changed_ids.remove(rule_id)
        else:
            description = device.get_class_description_string()
            notification = Notify.Notification.new("New USB device inserted", description, '/home/chriz/repositories/usbguard/src/GUI.Qt/resources/usbguard-icon.svg')
            notification.add_action('allow', 'Allow', self.on_allow_clicked, device)
            notification.add_action('block', 'Block', self.on_allow_clicked, device)
            notification.add_action('default', 'default', self.on_notification_clicked, device)
            notification.set_timeout(Notify.EXPIRES_NEVER) # TODO: maybe make configurable
            notification.connect('closed', self.on_notification_closed)
            notification.set_category("device.added")
            notification.show()
            self.notifications[notification.props.id] = notification

    def run(self):
        Gtk.main()
        print("Gtk.main() returned")

    def update_menu(self):
        menu = Gtk.Menu()
        open_text = 'Open' if self.usbguard_app is None else 'Close'
        item_open = Gtk.MenuItem(open_text)
        item_open.connect('activate', self.on_open)
        menu.append(item_open)
        item_quit = Gtk.MenuItem('Quit')
        item_quit.connect('activate', self.on_quit)
        menu.append(item_quit)
        menu.show_all()
        self.indicator.set_menu(menu)

    def open_window(self):
        self.execute_open_window()

    def quit(self):
        Notify.uninit()
        Gtk.main_quit()

    def execute_open_window(self):
        if self.usbguard_app is None:
            self.usbguard_app = USBGuardGnomeApplication()
            self.usbguard_app.run()
        else:
            self.usbguard_app.execute_quit()
            self.usbguard_app = None
        self.update_menu()

    def on_quit(self, _):
        if self.usbguard_app is not None:
            self.usbguard_app.execute_quit()
        self.quit()

    def on_open(self, _):
        self.open_window()

    def on_allow_clicked(self, notification, action_name, device):
        print("on_allow_clicked() for device {}".format(device))
        rule_id = self.usbguard_dbus.apply_device_policy(device.number, Rule.ALLOW, False)
        self.device_policy_changed_ids.append(rule_id)
        self.notifications[notification.props.id] = None

    def on_block_clicked(self, notification, action_name, device):
        print("on_block_clicked()")
        rule_id = self.usbguard_dbus.apply_device_policy(device.number, Rule.BLOCK, False)
        self.device_policy_changed_ids.append(rule_id)
        self.notifications[notification.props.id] = None

    def on_notification_clicked(self, notification, action_name, device):
        app = USBGuardNewDeviceApplication(device, self.usbguard_dbus)
        rule_id = app.run()
        self.notifications[notification.props.id] = None

    def on_notification_closed(self, notification):
        self.notifications[notification.props.id] = None


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    USBGuardAppIndicator().run()

if __name__ == "__main__":
    main()
