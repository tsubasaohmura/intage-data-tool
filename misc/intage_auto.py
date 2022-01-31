import os
import pywinauto
import re
import sys
import time
from pywinauto.timings import TimeoutError
from pywinauto.findwindows import ElementNotFoundError

# TODO: this info must be moved to environs
EMAIL = ""
PASSWORD = ""

# Make the script work slightly slower for better robustness
pywinauto.timings.Timings.slow()

# TODO: kill any iexplore.exe processes
os.system("TASKKILL /F /IM iexplore.exe")

# Create app
app = pywinauto.Application(backend='uia').start(
    'C:\Program Files\Internet Explorer\iexplore.exe "https://i-canvas.intage.co.jp/v0150/client/15.0.28/"')
app = pywinauto.Application(backend='uia').start(
    'C:\Program Files (x86)\Microsoft\Edge\Application\_msedge.exe "https://i-canvas.intage.co.jp/v0150/client/15.0.28/"')

# Grab correct window dialog and confirm the window is open
try:
    dlg = app.window(title_re=".*INTAGE iCanvas.*")
    dlg.wait('ready')
except:
    print("Dialog not found!")
    sys.exit(1)

# Choose English language and click "Sign in"
dlg.child_window(title="English", auto_id="lang_en", control_type="Hyperlink").click_input()

# Log in
dlg.child_window(title="E-mail", auto_id="email", control_type="Edit").set_edit_text(EMAIL)
dlg.child_window(title="Password", auto_id="user_pw", control_type="Edit").set_edit_text(PASSWORD)
dlg.child_window(title="Sign in ログイン", auto_id="signin_button", control_type="Hyperlink").click_input()

# Open order
dlg.child_window(title="Open order list", control_type="Text").wait('ready').click_input()

# This is very cumbersome approach, but somehow we can't select the list item directly.
# ListBox4 = list with all saved INTAGE reports
# TODO: Refactor this approach.
dlg['ListBox4'].wait('ready')
item = dlg['ListBox4'].child_window(best_match='All Regions CSV Last Week Auto').wait('ready').parent()
item.click_input()
dlg['ListBox4'].child_window(title='Edit', parent=item).click_input()

# Change week duration - will always reset previous state to the latest 1 week
dlg.child_window(title_re='.*Total.*week.*', control_type='Text').click_input()
# TODO: this is completely unreliable, but there's no way to get control of the slider. Need to try different browsers.
# Maybe headless browser? Or image recognition?
r = dlg['Same Sample Period'].rectangle()
pywinauto.mouse.double_click(coords=(r.right - 5, r.bottom + 50))
dlg['Set'].click_input()

# Get week number and save new report
week = dlg.child_window(title_re='.*Total.*week.*', control_type='Text').texts()[0][:10]  # Get first 10 symbols YYYY/MM/DD
assert re.fullmatch("\d{4}/\d{2}\/\d{2}", week) is not None
dlg['Order'].click_input()
dlg['Order3'].click_input()

# Wait for the report generation and download the file
# We need to reassign item because previous reference gets invalidated by this time
exists = False
while not exists:
    try:
        item = dlg['ListBox4'].child_window(best_match='All Regions CSV Last Week Auto').wait('ready').parent()
        dlg['ListBox4'].child_window(title='Download', parent=item).wait('ready', timeout=15).click_input()
        exists = True
    except TimeoutError:
        print("TimeoutError")
        continue
    except ElementNotFoundError:
        print("ElementNotFoundError")
        continue

# Code below is specifically for Internet Explorer
dlg.child_window(title="OK", control_type="Button", parent=dlg).click_input()
dlg['SplitButton2'].click_input()
pywinauto.keyboard.send_keys("{DOWN}{ENTER}")

filename = week.replace("/", "-") + ".zip"

time.sleep(5)
handle = pywinauto.findwindows.find_window(title='Save As')
saveas = pywinauto.Application().connect(handle=handle)['Save As']
saveas.wait('ready')
saveas.set_focus()
pywinauto.keyboard.send_keys("%{n}")
pywinauto.keyboard.send_keys(filename + "{ENTER}")

# Wait until download is completed
dlg.child_window(title="Open", control_type="SplitButton").wait('ready')

os.system("start C:\\Users\\kirill.denisenko\\Downloads\\" + filename)
