import sys
import os
import shutil
import csv
import time


def waiting_for_godot(time_start, time_end, time_min):
    time_duration = time_end - time_start
    time_waiting = time_min - time_duration
    while time_waiting > 1:
        time_waiting -= 1
        time.sleep(1)
        sys.stdout.write("\r")
        sys.stdout.write(f"waiting.... {round(time_waiting)}s")
        sys.stdout.flush()
    sys.stdout.write("\r")
    sys.stdout.flush()
    sys.stdout.write("                    ")
    sys.stdout.write("\r")
    sys.stdout.flush()


def move_and_rename_files(source_dir, xml_dest_dir, pdf_dest_dir, new_filename):
    try:
        # Find the first XML file in the source directory
        xml_file = next((file for file in os.listdir(source_dir) if file.endswith(".xml")), None)
        if not xml_file:
            return None, "No XML files found in the source directory."

        # Find the corresponding PDF file
        pdf_file = next((file for file in os.listdir(source_dir) if file.endswith(".pdf")), None)
        if not pdf_file:
            return None, "Corresponding PDF file not found."

        # Define the paths
        xml_source_path = os.path.join(source_dir, xml_file)
        pdf_source_path = os.path.join(source_dir, pdf_file)

        xml_dest_path = os.path.join(xml_dest_dir, f"{new_filename}.xml")
        pdf_dest_path = os.path.join(pdf_dest_dir, f"{new_filename}.pdf")

        # Move and rename the XML and PDF files
        shutil.move(xml_source_path, xml_dest_path)
        shutil.move(pdf_source_path, pdf_dest_path)

        return xml_dest_path, f"XML and PDF files moved and renamed to: {xml_dest_path} and {pdf_dest_path}"

    except Exception as e:
        return None, f"An error occurred: {e}"


def recreate_directory(dir_path):
    try:
        # Remove the directory if it exists
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        # Create a new directory
        os.makedirs(dir_path)
    except Exception as e:
        print(f"Failed to recreate directory {dir_path}. Reason: {e}")


def write_to_terminal(msg: str):
    sys.stdout.write("\r")
    sys.stdout.write(
        "                                                                                                  "
    )
    sys.stdout.flush()
    sys.stdout.write("\r")
    sys.stdout.write(msg)
    sys.stdout.flush()


def clean_list(data_list, forbidden_list):
    forbidden_list_lower = [item.lower() for item in forbidden_list]
    cleaned_list = [item for item in data_list if item.lower() not in forbidden_list_lower]
    return cleaned_list


def read_csv(file_path):
    with open(file_path, mode="r", newline="", encoding="utf-8") as file:
        # Creating a csv DictReader object
        reader = csv.DictReader(file, delimiter=";")

        # Reading CSV file and storing each row as a dictionary in a list
        data = [row for row in reader]

    return data


def initialize_csv(file_path, headers):
    """
    Initializes a csv file with specified headers.

    :param file_path: str, path to the csv file
    :param headers: list, headers to be written to the csv
    """
    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(headers)


def append_to_csv(file_path, data_dict):
    """
    Appends a dictionary of values to a csv file.

    :param file_path: str, path to the csv file
    :param data_dict: dict, values to be appended to the csv
    """
    with open(file_path, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=data_dict.keys(), delimiter=";")

        # If the file is empty, write the header
        if file.tell() == 0:
            writer.writeheader()

        writer.writerow(data_dict)
