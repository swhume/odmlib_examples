from abc import ABC


class DefineObject(ABC):
    def __init__(self):
        self.sheet = None
        self.lang = "en"

    def load_row(self, row_values, header):
        row = {}
        for cell in zip(header, row_values):
            row[cell[0]] = cell[1]
        return row

    def load_header(self, num_cols):
        header = []
        for row in self.sheet.iter_rows(min_row=1, max_row=1, min_col=1, max_col=num_cols, values_only=True):
            header = list(row)
        return header

    def generate_oid(self, descriptors):
        # ensure the element type prefix is not already pre-pended to the OID
        if len(descriptors) > 1 and descriptors[1].startswith(descriptors[0] + "."):
            oid = ".".join(descriptors[1:]).upper()
        else:
            oid = ".".join(descriptors).upper()
        return oid

    def find_object(self, objects, oid):
        for o in objects:
            if oid == o.OID:
                return o
        return None
