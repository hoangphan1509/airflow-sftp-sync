from airflow.sdk import dag, task, Variable
from airflow.providers.sftp.hooks.sftp import SFTPHook

from datetime import datetime
from pathlib import Path
import logging
import stat
from sftp_utils import mkdir_recursive

logger = logging.getLogger(__name__)


@task
def get_new_file_list(sftp_conn_id: str) -> list[str]:
    """
    List all new files in the SFTP server

    This task connects to the SFTP server, and lists all files in the remote
    directory. It assumes that the SFTP server is properly configured in
    Airflow's ``sftp_default`` connection.

    The list of files is returned as a list of strings, where each string is the
    remote path of a file.
    """
    # retrieve last run timestamp from variables
    last_runtime = int(Variable.get("SOURCE_SFPT_LAST_RUNTIME", 0))

    sftp_hook = SFTPHook.get_hook(sftp_conn_id)
    conn = sftp_hook.get_conn()

    recent_files = []

    q = ["~/"]

    lastest_runtime = last_runtime

    while len(q) > 0:
        current_path = q.pop(0)
        logger.info(f"Listing files in {current_path}")
        files_attr_sftp = conn.listdir_attr(current_path)

        for f in files_attr_sftp:
            if stat.S_ISDIR(f.st_mode):
                # If it's a directory, add it to the queue for further exploration
                q.append(str(Path(current_path) / f.filename))
            else:
                # If it's a file, check if it is newer than the last runtime
                if f.st_mtime > last_runtime:
                    logger.info(f"Found new file: {f.filename} at {current_path}")
                    recent_files.append(str(Path(current_path) / f.filename))

                    if f.st_mtime > lastest_runtime:
                        lastest_runtime = f.st_mtime

    logger.info(f"Found {len(recent_files)} new files in SFTP server \n {recent_files}")

    # Update the last runtime variable to the current time
    Variable.set("SOURCE_SFPT_LAST_RUNTIME", str(lastest_runtime))

    # Return the list of new files
    return recent_files


@task
def sync_file(source_conn_id: str, target_conn_id: str, file_path: str) -> None:
    logger.info(f"Syncing {file_path} from {source_conn_id} to {target_conn_id}")
    source_hook = SFTPHook(source_conn_id)
    target_hook = SFTPHook(target_conn_id)

    with source_hook.get_conn() as source_conn, target_hook.get_conn() as target_conn:
        parent_dir = str(Path(file_path).parent)
        try:
            sftp_stat = target_conn.stat(parent_dir)

            # If it exists, check if it's a directory
            if not stat.S_ISDIR(sftp_stat.st_mode):
                raise ValueError(f"Path {parent_dir} exists but is not a directory.")
        except FileNotFoundError:
            # The path doesn't exist, so create it
            mkdir_recursive(target_conn, parent_dir)
            print(f"Created directory: {parent_dir}")

        with source_conn.file(file_path, "r") as source_file:
            with target_conn.file(file_path, "w") as target_file:
                chunk_size = 1024 * 1024  # 1 MB
                while True:
                    chunk = source_file.read(chunk_size)
                    if not chunk:
                        break
                    target_file.write(chunk)

    logger.info(
        f"Successfully synced {file_path} from {source_conn_id} to {target_conn_id}"
    )


@task
def quality_check(source_conn_id: str, target_conn_id: str, file: str) -> None:
    logger.info(
        f"Performing quality check for {file} between {source_conn_id} and {target_conn_id}"
    )
    source_hook = SFTPHook(source_conn_id)
    target_hook = SFTPHook(target_conn_id)

    with source_hook.get_conn() as source_conn, target_hook.get_conn() as target_conn:
        with source_conn.file(file, "r") as source_file:
            with target_conn.file(file, "r") as target_file:
                try:
                    source_hash = source_file.check("md5")
                    target_content = target_file.check("md5")

                    if source_hash != target_content:
                        raise ValueError(
                            f"Quality check failed for {file}: source hash {source_hash} does not match target hash {target_content}"
                        )
                    else:
                        logger.info(f"Quality check passed for {file}")
                except OSError as e:
                    logger.error(f"the server doesn’t support the “check-file” extension, or possibly doesn’t support the hash algorithm requested: {e}")
                    if source_conn.stat(file).st_size == target_conn.stat(file).st_size:
                        logger.info(f"File size matches for {file}, quality check passed")
                    else:
                        raise ValueError(
                            f"Quality check failed for {file}: file sizes do not match"
                        )


@dag(
    schedule=None,
    start_date=datetime(2022, 1, 1),
    catchup=False,
    tags=["sftp"],
)
def sftp_sync():
    new_files = get_new_file_list("source-sftp")
    sync_task = sync_file.expand(
        source_conn_id=["source-sftp"],
        target_conn_id=["target-sftp"],
        file_path=new_files,
    )

    quality_check_task = quality_check.expand(
        source_conn_id=["source-sftp"], target_conn_id=["target-sftp"], file=new_files
    )
    new_files >> sync_task >> quality_check_task


sftp_sync_dag = sftp_sync()
