import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Find Settings text/button near the channel display
# Settings text appeared earlier at approximately (269, 288) area for channel 1
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm == 'Settings' and ct == 'Text':
        rect = c.rectangle()
        print(f"Settings text at: {rect}")
        # Find buttons overlapping this text
        for c2 in win.descendants():
            ct2 = c2.element_info.control_type
            if ct2 == 'Button':
                try:
                    r2 = c2.rectangle()
                    if r2.left <= rect.right and r2.right >= rect.left and r2.top <= rect.bottom + 20 and r2.bottom >= rect.top - 20:
                        print(f"  Nearby button: rect={r2}")
                        print(f"  Clicking button...")
                        c2.click_input()
                        time.sleep(4)
                        
                        # Check for settings dialog
                        for c3 in win.descendants():
                            ct3 = c3.element_info.control_type
                            nm3 = (c3.element_info.name or '')
                            if ct3 == 'Window' and ('Setting' in nm3 or 'Actuator' in nm3):
                                print(f"  SETTINGS DIALOG FOUND: {nm3}")
                                
                                # Now find Power tab/section
                                for c4 in c3.descendants():
                                    ct4 = c4.element_info.control_type
                                    nm4 = (c4.element_info.name or '')
                                    if any(kw in nm4 for kw in ['Power', 'power', 'Advanced', 'Persist', 'Rest']):
                                        print(f"    {ct4}: '{nm4}'")
                                break
                        break
                except:
                    pass
        break
