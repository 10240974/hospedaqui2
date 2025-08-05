import streamlit as st
from data_entry import DataEntry

def main():
    st.title("Data Entry Application")

    data_entry = DataEntry()

    menu = ["Add Entry", "Update Entry", "Delete Entry"]
    choice = st.sidebar.selectbox("Select an option", menu)

    if choice == "Add Entry":
        st.subheader("Add New Entry")
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=0)
        if st.button("Add"):
            data_entry.add_entry(name, age)
            st.success("Entry added successfully!")

    elif choice == "Update Entry":
        st.subheader("Update Existing Entry")
        entry_id = st.number_input("Entry ID", min_value=1)
        name = st.text_input("New Name")
        age = st.number_input("New Age", min_value=0)
        if st.button("Update"):
            data_entry.update_entry(entry_id, name, age)
            st.success("Entry updated successfully!")

    elif choice == "Delete Entry":
        st.subheader("Delete Entry")
        entry_id = st.number_input("Entry ID", min_value=1)
        if st.button("Delete"):
            data_entry.delete_entry(entry_id)
            st.success("Entry deleted successfully!")

if __name__ == "__main__":
    main()