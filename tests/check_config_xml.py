import xml.etree.ElementTree as ET
import re

tree = ET.parse(r'C:\ProgramData\Thorlabs\MotionControl\ThorlabsDeviceConfiguration.xml')
root = tree.getroot()

# Print all DeviceType entries
for elem in root.iter('DeviceType'):
    did = elem.get('ID')
    name = elem.get('Name', '')
    if did == '70' or 'BSC' in name.upper() or '202' in name:
        print(f"ID={did} Name={name}")
        for child in elem:
            print(f"  {child.tag}: {child.attrib}")

print("\n--- All DeviceType IDs ---")
for elem in root.iter('DeviceType'):
    print(f"  {elem.get('ID')}: {elem.get('Name', '?')}")
