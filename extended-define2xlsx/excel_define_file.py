import csv
import xlsxwriter as XLS
import os


class ExcelDefineFile:
    def __init__(self, files, tabs, data_path, excel_filename):
        self.xlsx_file = os.path.join(data_path, excel_filename)
        self.files = files
        self.tabs = tabs

    def create_excel(self):
        workbook = XLS.Workbook(self.xlsx_file, {"strings_to_numbers": False})
        header_format = workbook.add_format({"bold": True, "bg_color": "#CCFFFF", "border": True, "border_color": "black"})
        for index, csv_file in enumerate(self.files):
            worksheet = workbook.add_worksheet(self.tabs[index])
            is_header_row = True
            try:
                with open(csv_file, 'rt', encoding='utf8') as f:
                    reader = csv.reader(f)
                    for r, row in enumerate(reader):
                        for c, col in enumerate(row):
                            if is_header_row:
                                worksheet.write(r, c, col, header_format)
                                worksheet.set_column(r, c, 30)
                            else:
                                worksheet.write(r, c, col)
                        is_header_row = False
            except UnicodeDecodeError as ue:
                print(f"Encoding error writing load file for row {row} and col {col}: {ue}")
        workbook.close()
        return len(workbook.sheetnames)
