from __future__ import absolute_import, print_function, unicode_literals

from src.rule_parser import RULE


class Device(object):

    # TODO: Create more specific lookup also including sub-class and protocol
    # (c.f. http://www.usb.org/developers/defined_class)
    DEVICE_CLASSES = {
        0x00: "Device Unspecified",
        0x01: "Audio (Speaker, microphone, sound card, MIDI)",
        0x02: "Communications and CDC Control (Modem, Ethernet adapter, Wi-Fi adapter, RS232 serial adapter)",
        0x03: "Human Interface Device (HID)",
        0x05: "Physical Interface Device (PID)",
        0x06: "Image(PTP / MTP) (Webcam, scanner)",
        0x07: "Printer",
        0x08: "Mass storage",
        0x09: "USB hub",
        0x0A: "CDC - Data",
        0x0B: "Smart Card",
        0x0D: "Content Security (e.g. Fingerprint reader)",
        0x0E: "Video (e.g. Webcam)",
        0x0F: "Personal healthcare device class (PHDC) (e.g. Pulse monitor (watch))",
        0x10: "Audio / Video (AV)",
        0x11: "Billboard (Describes USB-C alternate modes supported by device)",
        0x12: "USB Type-C Bridge Class",
        0xDC: "Diagnostic Device (USB compliance testing device)",
        0xE0: "Wireless Controller",
        0xEF: "Miscellaneous (ActiveSync device)",
        0xFE: "Application-specific (IrDA Bridge, Test & Measurement Class (USBTMC), USB DFU (Device Firmware Upgrade))",
        0xFF: "Vendor-specific",
    }

    def __init__(self, number, rule, id, serial, name, hash, parent_hash, via_port, with_interface):
        self.number = number
        self.rule = rule
        self.id = id
        self.serial = serial
        self.name = name
        self.hash = hash
        self.parent_hash = parent_hash
        self.via_port = via_port
        self.with_interface = with_interface
        if not isinstance(self.with_interface, list):
            self.with_interface = [self.with_interface]

    def get_class_description_set(self):
        descriptions = set()
        for interface in self.with_interface:
            base_class_bytes = int(interface[:2], 16)
            descriptions.add(self.DEVICE_CLASSES[base_class_bytes])
        return descriptions

    def get_class_description_string(self):
        return "\n".join(self.get_class_description_set())

    def is_allowed(self):
        return self.rule.lower() == "allow"

    def __str__(self):
        return "<{} ({}) '{}' {} '{}'>".format(self.number, self.id, self.name, self.rule, self.get_class_description_string())

    def __repr__(self):
        return self.__str__()

    def as_list(self):
        return [
            self.number,
            self.rule,
            self.id,
            self.name,
            self.via_port,
            "\n".join(self.with_interface),
            self.get_class_description_string(),
        ]

    @staticmethod
    def generate_device(device_dbus_struct):
        number = int(device_dbus_struct[0])
        info = parse_rule(str(device_dbus_struct[1]))
        return Device(number=number, **info)


def parse_rule(rule_string):
    result_dict = {}
    parsed_rule = RULE.parseString(rule_string).asList()
    result_dict['rule'] = parsed_rule[0]
    for key, value in parsed_rule[1]:
        result_dict[key.replace('-', '_')] = value
    return result_dict

if __name__ == "__main__":
    print(parse_rule('allow id 1d6b:0002 serial "0000:00:14.0" name "xHCI Host Controller" hash "Miigb8mx72Z0q6L+YMai0mDZSlYC8qiSMctoUjByF2o=" parent-hash "G1ehGQdrl3dJ9HvW9w2HdC//pk87pKzFE1WY25bq8k4=" with-interface 09:00:00'))