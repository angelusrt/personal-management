variable "location" { type = string }
variable "gcs_bucket_name" { type = string }

variable "airflow_email" { type = string }
variable "admin_email" { type = string }
variable "reader_email" { type = string }


resource "google_storage_bucket" "default" {
  name = var.gcs_bucket_name
  location = var.location
  storage_class = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy = false

  versioning {
    enabled = true
  }

  public_access_prevention = "enforced"
}


## IAM

### Airflow Account

resource "google_storage_bucket_iam_member" "airflow_user" {
  bucket = google_storage_bucket.default.name
  role = "roles/storage.objectUser"
  member = "serviceAccount:${var.airflow_email}"
}

### Admin Account

resource "google_storage_bucket_iam_member" "admin_user" {
  bucket = google_storage_bucket.default.name
  role = "roles/storage.admin"
  member = "serviceAccount:${var.admin_email}"
}

### Normal User

resource "google_storage_bucket_iam_member" "reader_user" {
  bucket = google_storage_bucket.default.name
  role = "roles/storage.objectViewer"
  member = "serviceAccount:${var.reader_email}"
}
