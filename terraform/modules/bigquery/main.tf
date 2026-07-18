variable "project_id" { type = string }
variable "notification_email" { type = string }
variable "location" { type = string }

variable "airflow_email" { type = string }
variable "admin_email" { type = string }
variable "reader_email" { type = string }

variable "gcs_bucket_name" { type = string }

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

## External Tables with GCS

variable "ingestion_sources" {
  type = set(string)
  default = [
    "notas_nutricao", 
    "notas_tarefas", 
    "notas_introspeccao", 
    "notas_atributos",
    "notas_nutricao_enriquecida", 
    "notas_atributos_enriquecido", 
  ]
}

resource "google_bigquery_table" "ingestion_external" {
  for_each = var.ingestion_sources

  dataset_id = google_bigquery_dataset.bronze_dataset.dataset_id
  table_id = "raw_${each.value}"
  project = var.project_id

  external_data_configuration {
    autodetect = true
    source_format = "PARQUET"
    source_uris = ["gs://${var.gcs_bucket_name}/${each.value}/*.parquet"]
  }

  deletion_protection = false
}

## Dataplex

resource "google_project_service" "dataplex" {
  project = var.project_id
  service = "dataplex.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "lineage" {
  project = var.project_id
  service = "datalineage.googleapis.com"

  disable_on_destroy = false
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

resource "google_project_iam_member" "lineage_airflow_viewer" {
  project = var.project_id
  role = "roles/datalineage.viewer"
  member  = "serviceAccount:${var.airflow_email}"
}

### Admin Account

resource "google_project_iam_member" "bigquery_admin_user" {
  project = var.project_id
  role = "roles/bigquery.dataEditor"
  member = "serviceAccount:${var.admin_email}"
}

resource "google_project_iam_member" "lineage_admin_viewer" {
  project = var.project_id
  role = "roles/datalineage.viewer"
  member  = "serviceAccount:${var.admin_email}"
}

### Normal User

resource "google_project_iam_member" "bigquery_reader_user" {
  project = var.project_id
  role = "roles/bigquery.dataViewer"
  member = "serviceAccount:${var.reader_email}"
}

resource "google_project_iam_member" "lineage_reader_viewer" {
  project = var.project_id
  role = "roles/datalineage.viewer"
  member  = "serviceAccount:${var.reader_email}"
}
