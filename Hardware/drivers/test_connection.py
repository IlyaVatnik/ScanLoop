"""Test PM100D connection via PyVISA-py + libusb."""
import sys
import os
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import libusb_package
    import usb.backend.libusb1
    import usb.core
    backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
    dev = usb.core.find(idVendor=0x1313, idProduct=0x8078, backend=backend)
    if dev:
        print(f"USB device found: VID={dev.idVendor:04x} PID={dev.idProduct:04x}")
    else:
        print("USB device NOT found via libusb")
except Exception as e:
    print(f"libusb error: {e}")

try:
    import pyvisa
    rm = pyvisa.ResourceManager('@py')
    resources = rm.list_resources()
    usb_res = [r for r in resources if 'USB' in r]
    print(f"PyVISA USB resources: {usb_res}")
    for res in usb_res:
        try:
            h = rm.open_resource(res)
            h.write("*IDN?")
            idn = h.read().strip()
            print(f"  {res}: {idn}")
            h.close()
        except Exception as e:
            print(f"  {res}: error - {e}")
except Exception as e:
    print(f"PyVISA error: {e}")

print("\nDone.")
