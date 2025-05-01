# utils/b2_upload.py
import os
from b2sdk.v2 import InMemoryAccountInfo, B2Api
from dotenv import load_dotenv

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



