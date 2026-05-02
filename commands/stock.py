import gspread
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
STOCK_COL = 2

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("Pickguard Stock").sheet1

def generate_code(variant_arr):
    for i in range(len(variant_arr)):
        if variant_arr[i] in ("Glossy", "Standard", "Standard (Bent Ear)"):
            variant_arr[i] = ""
        if variant_arr[i] == "With Holes":
            variant_arr[i] = "Holes"
        if variant_arr[i] == "Without Holes":
            variant_arr[i] = "No Holes"
    code = " - ".join([v for v in variant_arr if v])
    return code

def get_row(design):
    cell = sheet.find(design)
    if not cell:
        sheet.append_row([design, 0])
        cell = sheet.find(design)
    row = cell.row
    return row

def check_stock(design, quantity=1):
    row = get_row(design)
    stock = int(sheet.cell(row, STOCK_COL).value)
    if stock - quantity >= 0:
        return True, row, stock
    return False, row, stock

def update_stock(design, quantity=1):
    stock_available, row, stock = check_stock(design, quantity)
    if stock_available:
        new_stock = stock - quantity
        sheet.update_cell(row, STOCK_COL, new_stock)