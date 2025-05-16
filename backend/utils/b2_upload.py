# utils/b2_upload.py
import os
from b2sdk.v2 import InMemoryAccountInfo, B2Api
from dotenv import load_dotenv
from io import BytesIO



load_dotenv()

info = InMemoryAccountInfo()
b2_api = B2Api(info)
b2_api.authorize_account("production", os.getenv("B2_APPLICATION_KEY_ID"), os.getenv("B2_APPLICATION_KEY"))
bucket = b2_api.get_bucket_by_name(os.getenv("B2_BUCKET_NAME"))

print(f"B2_APPLICATION_KEY_ID: {os.getenv('B2_APPLICATION_KEY_ID')}")
print(f"B2_BUCKET_NAME: {os.getenv('B2_BUCKET_NAME')}")


def upload_file_to_b2(file_obj, filename):
    file_obj.seek(0)
    b2_file = bucket.upload_bytes(file_obj.read(), filename)

    # Correct the file ID attribute to 'id_'
    file_id = b2_file.id_  # 'id_' is the correct attribute for the file ID

    return b2_file.file_name, file_id

from io import BytesIO

# def download_file_from_b2(s3_key):
#     try:
#         byte_stream = BytesIO()
#         print("s3", s3_key)
#         bucket.download_file_by_name(s3_key, byte_stream)
#         byte_stream.seek(0)
#         return byte_stream.read()
#     except Exception as e:
#         print("Error downloading file from B2:", e)
#         return None

def download_file_from_b2(s3_key):
    try:
        byte_stream = BytesIO()
        downloaded_file = bucket.download_file_by_name(s3_key)
        downloaded_file.save(byte_stream)
        byte_stream.seek(0)
        return byte_stream.read()
    except Exception as e:
        print(f"Error downloading file from B2: {e}")
        return None





