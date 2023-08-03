#This Python script is designed to automatically upload files to a remote server via SFTP (SSH File Transfer Protocol).
#The script uses the `paramiko` module for SSH and SFTP operations, `tkinter` for a simple file or directory selection GUI, 
#and `tqdm` for displaying progress bars during file upload. Logging operations are performed using the `logging` module, 
#and threading is accomplished with `concurrent.futures`. The `retrying` module is used to implement retrying of failed uploads.
#The script first reads in the server and user credentials from a config.ini file. The user's private key is used for 
#authentication, and the server hostname and the remote directory are specified in this config file.
#Upon running the script, a GUI prompts the user to select either individual files or a directory for upload. 
#When the user confirms the selection, the script establishes an SFTP session to the specified server using the provided 
#credentials, and navigates to the remote directory.
#The script then begins uploading the selected files or directories. Each file upload is accompanied by a progress bar which 
#displays the file name and the upload progress in gigabytes. The script can upload multiple files simultaneously 
#due to threading.
#If an upload fails, the script will attempt to retry the upload a specified number of times with a specified delay between 
#retries. 
#The script also logs its activities, which include upload start, completion, success, failure, and connection errors.
#At the end of the script, the SFTP session is closed. The script does not terminate until all selected files and directories 
#have been processed.

import paramiko
import os
import configparser
import tkinter as tk
from tkinter import filedialog
from tqdm import tqdm
import logging
from datetime import datetime
from retrying import retry
from concurrent.futures import ThreadPoolExecutor
import time
from threading import Lock

# Set up logging to create a log file in the directory where the script is running from
log_filename = "upload_log.log"
MAX_RETRIES = 3
RETRY_DELAY = 10000  # delay in milliseconds
MAX_THREADS = 5

def configure_logger(log_level=logging.INFO):
    handlers = [
        logging.FileHandler(log_filename),
    ]

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )

    logger = logging.getLogger()
    return logger

def bytes_to_gigabytes(bytes):
    return bytes / 1024 / 1024 / 1024

# Create a new tqdm object
progress_bar = None
# Create a lock for progress bar updates
progress_bar_lock = Lock()

def print_progress(transferred, to_be_transferred):
    transferred_gigabytes = bytes_to_gigabytes(transferred)
    with progress_bar_lock:
        progress_bar.update(transferred_gigabytes - progress_bar.n)

@retry(stop_max_attempt_number=MAX_RETRIES, wait_fixed=RETRY_DELAY)
def upload_file(sftp, local_file, remote_file, logger):
    global progress_bar
    logger.info('Uploading file: %s', local_file)

    # Get the size of the local file in GB
    local_file_size = bytes_to_gigabytes(os.path.getsize(local_file))

    try:
        # Create a new progress bar for each file
        # Extract file name from the local_file path
        file_name = os.path.basename(local_file)
        
        progress_bar = tqdm(total=local_file_size, unit='GB', unit_scale=True, desc=file_name, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} ({percentage:3.0f}%)')
        
        sftp.put(local_file, remote_file, callback=print_progress)
    except Exception as e:
        logger.error("Upload failed: %s", str(e))
        return False
    finally:
        # Close the progress bar
        if progress_bar is not None:
            progress_bar.close()

        # Introduce a delay
        time.sleep(1)

    return True

def upload_dir(sftp, local_dir, remote_dir, logger):
    for root, dirs, files in os.walk(local_dir):
        for file in files:
            local_file = os.path.join(root, file)
            remote_file = remote_dir + '/' + os.path.relpath(local_file, local_dir).replace('\\', '/')
            upload_file(sftp, local_file, remote_file, logger)

def select_files_or_dir():
    root = tk.Tk()
    root.withdraw()
    file_or_dir = tk.messagebox.askquestion("Choose Files or Folder", "Choose Yes if you want to upload files", default='yes')
    if file_or_dir == 'yes':
        files = filedialog.askopenfilenames()
        dirs = []
    else:
        dirs = [filedialog.askdirectory()]
        files = []

    return root, files, dirs

def main():
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')
        logger = configure_logger(log_level=logging.INFO)
        private_key_path = config.get('Credentials', 'private_key_path')
        if not os.path.exists(private_key_path):
            logger.error("Private key file not found at the specified path")
            exit(1)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        hostname = config.get('Server', 'hostname')
        username = config.get('Credentials', 'username')
        private_key = paramiko.RSAKey(filename=private_key_path)

        logger.info("Connecting to %s@%s", username, hostname)
        ssh.connect(hostname, username=username, pkey=private_key)
        logger.info("Connected successfully")

        sftp = ssh.open_sftp()
        remote_dir = config.get('Server', 'remote_dir')
        try:
            sftp.chdir(remote_dir)
        except IOError:
            logger.error(f"Remote directory {remote_dir} doesn't exist")
            exit(1)

        root, files, dirs = select_files_or_dir()
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            for file in files:
                remote_file = remote_dir + os.path.basename(file)
                executor.submit(upload_file, sftp, file, remote_file, logger)
            for dir in dirs:
                executor.submit(upload_dir, sftp, dir, remote_dir, logger)
        root.destroy()

        sftp.close()

        logger.info("Upload succeeded")

    except paramiko.AuthenticationException:
        logger.error("Authentication failed, please verify your credentials")
    except paramiko.SSHException as e:
        logger.error("Could not establish SSH connection: %s", str(e))
    except Exception as e:
        logger.error("Error occurred during file transfer: %s", str(e))
    finally:
        if 'ssh' in locals():  # Check if 'ssh' variable is defined before closing
            ssh.close()

if __name__ == "__main__":
    main()
