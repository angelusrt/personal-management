variable "project_id" { type = string }
variable "notification_email" { type = string }
variable "location" { type = string }

variable "airflow_email" { type = string }
variable "admin_email" { type = string }
variable "reader_email" { type = string }

## Billing

resource "google_project_service" "billing_budgets" {
  service = "billingbudgets.googleapis.com"
}

resource "google_monitoring_notification_channel" "email" {
  display_name = "Billing Email"

  type = "email"

  labels = {
    email_address = var.notification_email
  }
}

## BigQuery

resource "google_project_service" "bigquery" {
  service = "bigquery.googleapis.com"

  disable_on_destroy = false
}

resource "google_bigquery_dataset" "gold_dataset" {
  dataset_id = "gold"
  location = var.location

  depends_on = [
    google_project_service.bigquery
  ]
}

resource "google_bigquery_dataset" "silver_dataset" {
  dataset_id = "silver"
  location = var.location

  depends_on = [
    google_project_service.bigquery
  ]
}

resource "google_bigquery_dataset" "bronze_dataset" {
  dataset_id = "bronze"
  location = var.location

  depends_on = [
    google_project_service.bigquery
  ]
}

## IAM

### Airflow User

resource "google_project_iam_member" "bigquery_airflow_user" {
  project = var.project_id
  role = "roles/bigquery.user"
  member = "serviceAccount:${var.airflow_email}"
}

resource "google_project_iam_member" "bigquery_airflow_editor" {
  project = var.project_id
  role = "roles/bigquery.dataEditor"
  member = "serviceAccount:${var.airflow_email}"
}

### Admin Account

resource "google_project_iam_member" "bigquery_admin_user" {
  project = var.project_id
  role = "roles/bigquery.dataEditor"
  member = "serviceAccount:${var.admin_email}"
}

### Normal User

resource "google_project_iam_member" "bigquery_reader_user" {
  project = var.project_id
  role = "roles/bigquery.dataViewer"
  member = "serviceAccount:${var.reader_email}"
}
