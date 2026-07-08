variable "admin_account_name" { type = string }
variable "reader_account_name" { type = string }


resource "google_service_account" "airflow" {
  account_id = "airflow"
  display_name = "Airflow Service Account"
}

resource "google_service_account" "admin" {
  account_id = var.admin_account_name 
  display_name = "Admin Service Account"
}

resource "google_service_account" "reader" {
  account_id = var.reader_account_name
  display_name = "Reader Service Account"
}


resource "google_service_account_key" "airflow_key" {
  service_account_id = google_service_account.airflow.name
}

resource "local_file" "airflow_key_file" {
  content = base64decode(google_service_account_key.airflow_key.private_key)
  filename = "${path.root}/airflow-key.json"
}
