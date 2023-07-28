# Import Modules
import paramiko
import hashlib
import binascii

# Define the host key function
def get_host_key(host, port=22):
    transport = paramiko.Transport((host, port))
    transport.start_client()
    return transport.get_remote_server_key()

# Define the get fingerprint function
def get_fingerprint(host_key):
    fp_plain = hashlib.md5(host_key.asbytes()).digest()
    return ":".join("{:02x}".format(c) for c in fp_plain)

# Define the main function to get the MD5 Fingerprint
def main():
    host = 'blabla.sftp.example'  # replace with your hostname
    host_key = get_host_key(host)
    fingerprint = get_fingerprint(host_key)
    print(fingerprint)

if __name__ == "__main__":
    main()
