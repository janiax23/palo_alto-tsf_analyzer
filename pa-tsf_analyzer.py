import urllib3
import requests
import xml.etree.ElementTree as xml
import time
import subprocess
import tarfile
import os

urllib3.disable_warnings()

# ask the user to provide firewall IP address, firewall API key and the name of the TSF file 
fw_ip = input("Firewall MGMT IP Address: ")
fw_api_key = input ("Paste the firewall API key: ")
tsf_filename = input ("Proivde desired TSF file name: ")

# specify the first API request
generate_tsf_api_url = f"https://{fw_ip}/api/?key={fw_api_key}&type=export&category=tech-support"

# create the first API request to generate the TSF
api_request_generate_tsf = requests.get(url=generate_tsf_api_url,verify=False)
api_generate_tsf_response = api_request_generate_tsf.text
xml_response_generate_tsf = xml.fromstring(api_generate_tsf_response)

job_element = xml_response_generate_tsf.find('.//job')
job_value = job_element.text

if job_element is not None:
    print(f"The firewall is generating a TSF with job ID {job_value.strip()}")
else:
    print("<job> element not found in XML response.")

check_tsf_api_url = f"https://{fw_ip}/api/?key={fw_api_key}&type=export&category=tech-support&action=status&job-id={job_value}"

while True:
    api_request_check_tsf_status = requests.get(url=check_tsf_api_url, verify=False)
    api_check_tsf_response = api_request_check_tsf_status.text
    xml_response_tsf_status = xml.fromstring(api_check_tsf_response)
    

    status_element = xml_response_tsf_status.find('.//status')
    status_value = status_element.text
    progress_element = xml_response_tsf_status.find('.//progress')
    progress_value = progress_element.text


    if status_element is not None:
        if progress_value.strip() in ("1", "10", "40", "100"):
            print(f"The TSF file is being generated. The current status is: {progress_value.strip()}%")

        # Check if the job is finished
        if status_value == "FIN":
            print ("The TSF has been successfully generated!")
            break  # Exit the loop if the job is finished
   
    # Sleep for 20 seconds before checking again
    time.sleep(20)
						
# specify the third API request to export the TSF file
api_request_download_tsf = f"https://{fw_ip}/api/?key={fw_api_key}&type=export&category=tech-support&action=get&job-id={job_value}"

print("\n")

# create a curl command to download the TSF file from the firewall
curl_command = [
    "curl",
    "-o",
    f"/Users/j_nix23/Documents/tsf_files/{tsf_filename}.tgz",
    "-k",
    api_request_download_tsf
]

# run the curl command to download the TSF file 
try:
    subprocess.run(curl_command, check=True, shell=False)
    print("\nTSF file downloaded successfully.")
except subprocess.CalledProcessError as e:
    print(f"\nError downloading TSF file: {e}")

print ("\nExtracting the downloaded TSF file and creating an appended logfile")

tsf_file_path = f"/Users/j_nix23/Documents/tsf_files/{tsf_filename}.tgz"

# Path to the extracted directory
extracted_dir = "/Users/j_nix23/Documents/tsf_extracted/"

# Extract the contents of the .tgz file while preserving the directory structure
with tarfile.open(tsf_file_path, "r:gz") as tar:
    for tarinfo in tar:
        # Get the path to the extracted file while preserving the directory structure
        extracted_file_path = os.path.join(extracted_dir, tsf_filename, tarinfo.name)
        
        # Ensure the destination directory exists
        os.makedirs(os.path.dirname(extracted_file_path), exist_ok=True)
        
        # Extract the file to the specified destination
        tar.extract(tarinfo, path=os.path.join(extracted_dir, tsf_filename))


# Define the list of log files you want to append
log_files_to_append = [
    f"/Users/j_nix23/Documents/tsf_extracted/{tsf_filename}/var/log/pan/ms.log",
    f"/Users/j_nix23/Documents/tsf_extracted/{tsf_filename}/var/log/pan/mp-monitor.log"
]

# Initialize an empty string to store the appended content
appended_logs = ""

# Specify the merged log file path
merged_log_file_path = os.path.join(extracted_dir, f"{tsf_filename}_merged.log")

# Iterate through the list of log files and append their content
for log_file in log_files_to_append:
    # Check if the log file exists before attempting to read it
    if os.path.exists(log_file):
        with open(log_file, "r") as file:
            appended_logs += file.read()

# Write the appended content to the merged log file
with open(merged_log_file_path, "w") as merged_file:
    merged_file.write(appended_logs)


