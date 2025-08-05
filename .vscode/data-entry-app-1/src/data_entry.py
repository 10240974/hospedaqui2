class DataEntry:
    def __init__(self):
        self.entries = []

    def add_entry(self, entry):
        self.entries.append(entry)

    def update_entry(self, index, updated_entry):
        if 0 <= index < len(self.entries):
            self.entries[index] = updated_entry
        else:
            raise IndexError("Entry index out of range.")

    def delete_entry(self, index):
        if 0 <= index < len(self.entries):
            del self.entries[index]
        else:
            raise IndexError("Entry index out of range.")