import datetime
import os
import uuid
from google.cloud import storage

BUCKET_NAME = "rpg-dm-images-qwiklabs-gcp-04-b94d5857ae5f"
GCP_PROJECT = "qwiklabs-gcp-04-b94d5857ae5f"


def upload_generated_image(image_bytes: bytes, category: str = "general", filename: str = "") -> str:
    """Uploads an image payload to GCS under an organized category path and returns the public HTTP URL.

    Args:
        image_bytes: Raw bytes of the image file.
        category: Image category ('portraits', 'encounters', 'locations', 'items', 'general').
        filename: Optional custom filename. Auto-generates timestamped UUID if omitted.

    Returns:
        Public HTTPS URL for embedding the image in UI cards or Markdown.
    """
    category_clean = category.lower().strip()
    valid_categories = {"portraits", "encounters", "locations", "items", "general"}
    if category_clean not in valid_categories:
        category_clean = "general"

    if not filename:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"img_{ts}_{unique_id}.png"

    blob_path = f"images/{category_clean}/{filename}"

    try:
        client = storage.Client(project=GCP_PROJECT)
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_path)
        blob.upload_from_string(image_bytes, content_type="image/png")
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"
        return public_url
    except Exception as e:
        return f"Error uploading image to GCS: {str(e)}"
