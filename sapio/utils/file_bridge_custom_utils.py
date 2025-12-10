import csv
from io import StringIO
from typing import List

from sapiopycommons.files.file_bridge import FileBridge
from sapiopylib.rest.DataRecordManagerService import DataRecordManager
from sapiopylib.rest.User import SapioUser

from sapio.utils.data_type_models import InstrumentModel, NotebookDirectoryModel
from sapio.utils.record_util import RecordUtil

# File Bridge Instrument Names
SAP_INTEGRATION = "SAP Integration"


def get_file_bridge_path(data_record_manager: DataRecordManager, instrument_name):
    network_path_list = []

    instrument_records = data_record_manager.query_data_records(InstrumentModel.DATA_TYPE_NAME.__str__(),
                                                                InstrumentModel.INSTRUMENTNAME__FIELD_NAME.field_name,
                                                                [instrument_name])
    for record in instrument_records:
        value = record.get_field_value(InstrumentModel.NETWORKFILEPATH__FIELD_NAME.field_name)
        if value:
            network_path_list.append(value)

    if not network_path_list:
        raise Exception("ERROR: 'SAP Integration' Instrument is not found or It's network path is empty")
    if len(network_path_list) > 1:
        raise Exception("ERROR: Multiple SAP Integration Instruments have been found")

    # Get bridge name and root folder path to process
    bridge_name, root_path = extract_folder_and_root_path(network_path_list[0])
    return bridge_name, root_path


def get_mirxes_dir(context):
    directories: List[NotebookDirectoryModel] = RecordUtil(context).query_models(
        NotebookDirectoryModel, NotebookDirectoryModel.DIRECTORYNAME__FIELD_NAME.field_name, ["MIRXES"])
    if directories:
        return directories[0]
    return None


def extract_folder_and_root_path(url):
    # Check if the URL starts with 'bridge://'
    if url.startswith("bridge://"):
        # Remove the 'bridge://' prefix
        url = url[len("bridge://"):]

    # Split the URL at the first '/' to separate the folder name from the remaining path
    parts = url.split('/', 1)
    # Folder name is the first part
    folder_name = parts[0]
    # Remaining path is the second part, if exists, otherwise empty string
    remaining_path = "/" + parts[1] if len(parts) > 1 else ''
    return folder_name, remaining_path


def get_csv_data_and_headers(file_bytes, filepath):
    if file_bytes:
        # Decode bytes to string
        csv_str = file_bytes.decode('utf-8')
        # Use StringIO to convert the string to a file-like object
        csv_file = StringIO(csv_str)
        # Read the CSV file
        reader = csv.DictReader(csv_file)
        # Extract headers
        headers = reader.fieldnames
        return headers, reader
    else:
        raise Exception(f"File {filepath} doesn't have proper data")


def write_processed_files_log(context, path, existing_log_content, log_file_name, processed_files):
    # Sort the file names
    sorted_processed_files = sorted(processed_files, reverse=True)
    # generate update log file content
    if len(sorted_processed_files) == 1:
        new_log_content = str(sorted_processed_files[0])
    elif len(sorted_processed_files) >= 1:
        new_log_content = "\n".join(sorted_processed_files)  # Join filenames with newline
    else:
        new_log_content = None
    if new_log_content:
        updated_log_content = new_log_content + "\n" + existing_log_content if existing_log_content else new_log_content
        updated_log_content.strip("\n")
        # Write the updated content back to the processed_files_log.txt
        FileBridge.write_file(context, path, log_file_name, updated_log_content.encode())


def move_file(context, bridge_name, source_folder, filebytes, destination_folder, filepath):
    FileBridge.write_file(context, bridge_name,
                          destination_folder + filepath,
                          filebytes)
    delete_file(context, bridge_name, source_folder + filepath)


def delete_file(context, bridge_name: str, file_path: str) -> None:
    """
    Delete an existing file in FileBridge.

    :param context: The current webhook context or a user object to send requests from.
    :param bridge_name: The name of the bridge to use.
    :param file_path: The path to the file to delete.
    """
    sub_path = '/ext/filebridge/deleteFile'
    params = {
        'Filepath': f"bridge://{bridge_name}/{file_path}"
    }
    user: SapioUser = context if isinstance(context, SapioUser) else context.user
    response = user.delete(sub_path, params=params)
    user.raise_for_status(response)
