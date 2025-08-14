from paramiko import SFTPClient

def mkdir_recursive(sftp_conn: SFTPClient, path: str) -> None:
    """
    Recursively create directories on an SFTP server.

    :param sftp_conn: The SFTP connection object.
    :param path: The directory path to create.
    """
    parts = path.split('/')
    current_path = ''

    for part in parts:
        if part:
            current_path = current_path + '/' + part
            try:
                sftp_conn.stat(current_path)
            except FileNotFoundError:
                # If the directory does not exist, create it
                sftp_conn.mkdir(current_path)