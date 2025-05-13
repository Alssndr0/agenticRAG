import os

from app.configs.minio_config import get_minio_settings
from minio import Minio, S3Error
from loguru import logger


class MinioClient:
    def __init__(self):
        """
        Initializes the MinioClient.
        """
        logger.info("Initializing MinioClient...")
        self.minio_client = Minio(
            get_minio_settings().ENDPOINT,
            get_minio_settings().ACCESS_KEY,
            get_minio_settings().SECRET_KEY,
            secure=False,  # Change to True if using HTTPS
            cert_check=False,
        )
        self.bucket_name = get_minio_settings().BUCKET

        self.model_name = get_minio_settings().MODEL
        # model details
        self.minio_model_dir = get_minio_settings().MINIO_MODEL_DIR
        self.local_model_dir = get_minio_settings().LOCAL_MODEL_DIR
        self.local_model_path = get_minio_settings().LOCAL_MODEL_PATH
        # bm25 details
        self.minio_bm25_dir = get_minio_settings().MINIO_BM25_DIR
        self.local_bm25_dir = get_minio_settings().LOCAL_BM25_DIR
        self.local_bm25_path = get_minio_settings().LOCAL_BM25_PATH
        # faiss details
        self.minio_faiss_dir = get_minio_settings().MINIO_FAISS_DIR
        self.local_faiss_dir = get_minio_settings().LOCAL_FAISS_DIR
        self.local_faiss_path = get_minio_settings().LOCAL_FAISS_PATH

        # Ensure bucket exists
        if not self.minio_client.bucket_exists(self.bucket_name):
            self.minio_client.make_bucket(self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' not found.")
        else:
            logger.info(f"Found bucket '{self.bucket_name}'")

    def upload_to_minio(self, file_path, object_name):
        """
        Uploads a file to MinIO.

        Args:
            file_path (str): Local path of the file to upload.
            object_name (str): Object name to be used in MinIO: FOLDER/filename.ext

        Usage: upload_to_minio('ai-re-lumera-assistant/README.md', 'AI-RE-LUMERA-ASSISTANT/test.txt')
        """
        logger.info(f"Uploading file from '{file_path}' as '{object_name}'...")
        try:
            self.minio_client.fput_object(self.bucket_name, object_name, file_path)
            logger.info(f"File uploaded successfully: {object_name}")
        except Exception as e:
            logger.error(f"Error uploading file: {e}")

    def download_from_minio(self, object_name, destination_path):
        """
        Downloads a file from MinIO.

        Args:
            object_name (str): Object name in MinIO: FOLDER/filename.ext
            destination_path (str): Local path to save the downloaded file.

        Usage: download_from_minio('AI-RE-LUMERA-ASSISTANT/test.txt', 'file.txt')
        """
        logger.info(f"Downloading file '{object_name}' to '{destination_path}'...")
        try:
            self.minio_client.fget_object(
                self.bucket_name, object_name, destination_path
            )
            logger.info(f"File downloaded successfully: {object_name}")
        except Exception as e:
            logger.error(f"Error downloading file: {e}")

    def list_files_in_folder(self, folder_name):
        """
        Lists all files in a folder in MinIO.

        Args:
            folder_name (str): Folder name in MinIO.

        Returns:
            List of object names within the folder.

        Usage: files_in_folder = list_files_in_folder('AI-RE-ID-CAPTURE')
        """
        logger.info(f"Listing files in folder '{folder_name}'...")
        try:
            objects = self.minio_client.list_objects(
                self.bucket_name, prefix=folder_name, recursive=True
            )
            object_names = [obj.object_name for obj in objects]
            logger.info(
                f"Found {len(object_names)} object(s) in folder '{folder_name}'."
            )
            return object_names
        except Exception as e:
            logger.error(f"Error listing objects in folder: {e}")
            return []

    def load_file_from_minio(self, object_name):
        """
        Loads a file from MinIO into a variable.

        Args:
            object_name (str): Object name in MinIO.

        Returns:
            str: Contents of the file as a string.

        Usage: file = load_file_from_minio('AI-RE-LUMERA-ASSISTANT/test.txt')
        """
        logger.info(f"Loading file '{object_name}' from MinIO...")
        try:
            temp_file_path = "/tmp/minio_temp_file"
            self.minio_client.fget_object(self.bucket_name, object_name, temp_file_path)
            with open(temp_file_path, "r") as file:
                file_contents = file.read()
            os.remove(temp_file_path)
            logger.info(f"File loaded successfully: {object_name}")
            return file_contents
        except Exception as e:
            logger.error(f"Error loading file from MinIO: {e}")
            return None

    def download_folder_from_minio(self, bucket, folder_prefix, local_dir):
        """
        Downloads all objects with the specified folder prefix from MinIO and
        saves them into the local directory, preserving the directory structure.

        If an object key ends with a '/', it is treated as a directory marker and
        the directory is created locally.
        """
        logger.info(
            f"Downloading folder '{folder_prefix}' from bucket '{bucket}' to '{local_dir}'..."
        )
        try:
            objects = self.minio_client.list_objects(
                bucket, prefix=folder_prefix, recursive=True
            )
            for obj in objects:
                object_name = obj.object_name
                # Compute the local relative path
                rel_path = os.path.relpath(object_name, folder_prefix)
                local_path = os.path.join(local_dir, rel_path)

                # Check if the object is a directory marker
                if object_name.endswith("/"):
                    os.makedirs(local_path, exist_ok=True)
                    logger.info(f"Created directory '{local_path}'")
                else:
                    # Ensure the parent directory exists
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    self.minio_client.fget_object(bucket, object_name, local_path)
                    logger.info(f"Downloaded file '{object_name}' to '{local_path}'")

            logger.info(
                f"Folder '{folder_prefix}' downloaded successfully to '{local_dir}'"
            )
        except S3Error as e:
            logger.error(f"Error downloading folder: {e}")
        except Exception as e:
            logger.error(f"Unexpected error downloading folder: {e}")

    def ensure_model_available(self):
        """Checks if the embeddings model is available locally; downloads if missing."""

        model_name = self.model_name
        minio_model_dir = self.minio_model_dir
        local_model_dir = self.local_model_dir
        local_model_path = self.local_model_path

        # Ensure the local directory exists
        if not os.path.exists(local_model_dir):
            os.makedirs(local_model_dir, exist_ok=True)
            logger.info(f"Created local directory: '{local_model_dir}'.")

        # Check if model exists
        if not os.path.exists(local_model_path):
            logger.info(
                f"Model '{model_name}' not found locally. Attempting to download from MinIO..."
            )
            self.download_folder_from_minio(
                get_minio_settings().BUCKET, minio_model_dir, local_model_dir
            )

            # Verify that it was downloaded
            if os.path.exists(local_model_path):
                logger.info(
                    f"Model '{model_name}' successfully downloaded to '{local_model_dir}'."
                )
            else:
                logger.error(
                    f"Download failed! Model '{model_name}' is still missing at '{local_model_path}'."
                )
        else:
            logger.info(f"Model '{model_name}' found locally. Skipping MinIO download.")

    def ensure_bm25index_available(self):
        """Checks if the BM25 index is available locally; downloads it if missing."""
        index_name = f"BM25 index {self.minio_bm25_dir}"
        minio_index_dir = self.minio_bm25_dir
        local_index_dir = (
            self.local_bm25_dir / get_minio_settings().BM25_INDEX_TIMESTAMP
        )  # Ensure timestamped folder
        local_index_file = (
            local_index_dir / "bm25.pkl"
        )  # Ensure we're checking the actual file

        # Ensure the local timestamped directory exists.
        if not os.path.exists(local_index_dir):
            os.makedirs(local_index_dir, exist_ok=True)
            logger.info(f"Created local BM25 directory: '{local_index_dir}'.")

        # Check if the BM25 index file exists locally.
        if not os.path.exists(local_index_file):
            logger.info(
                f"{index_name} not found locally. Attempting to download from MinIO..."
            )
            self.download_folder_from_minio(
                get_minio_settings().BUCKET, minio_index_dir, local_index_dir
            )

            # Verify that the BM25 index file exists after download.
            if os.path.exists(local_index_file):
                logger.info(
                    f"{index_name} successfully downloaded to '{local_index_file}'."
                )
            else:
                logger.error(
                    f"Download failed! {index_name} is still missing at '{local_index_file}'."
                )
        else:
            logger.info(f"{index_name} found locally. Skipping MinIO download.")

    def ensure_faissindex_available(self):
        """Checks if the FAISS index is available locally; downloads it if missing."""
        index_name = f"FAISS index {self.minio_faiss_dir}"
        minio_index_dir = self.minio_faiss_dir
        local_index_dir = (
            self.local_faiss_dir / get_minio_settings().FAISS_INDEX_TIMESTAMP
        )  # Ensure timestamped folder
        local_index_file_faiss = (
            local_index_dir / "index.faiss"
        )  # Ensure we're checking the actual FAISS file
        local_index_file_pkl = (
            local_index_dir / "index.pkl"
        )  # Ensure we're checking the metadata file

        # Ensure the local timestamped directory exists.
        if not os.path.exists(local_index_dir):
            os.makedirs(local_index_dir, exist_ok=True)
            logger.info(f"Created local FAISS directory: '{local_index_dir}'.")

        # Check if the FAISS index files exist locally.
        if not (
            os.path.exists(local_index_file_faiss)
            and os.path.exists(local_index_file_pkl)
        ):
            logger.info(
                f"{index_name} not found locally. Attempting to download from MinIO..."
            )
            self.download_folder_from_minio(
                get_minio_settings().BUCKET, minio_index_dir, local_index_dir
            )

            # Verify that the FAISS index files exist after download.
            if os.path.exists(local_index_file_faiss) and os.path.exists(
                local_index_file_pkl
            ):
                logger.info(
                    f"{index_name} successfully downloaded to '{local_index_dir}'."
                )
            else:
                logger.error(
                    f"Download failed! {index_name} is still missing at '{local_index_dir}'."
                )
        else:
            logger.info(f"{index_name} found locally. Skipping MinIO download.")
