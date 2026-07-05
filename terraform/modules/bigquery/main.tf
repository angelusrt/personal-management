terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "~> 7.0"
    }

    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 7.0"
    }
  }
}

variable "project_id" { type = string }
variable "region_name" { type = string }
variable "zone_name" { type = string }

variable "billing_account_id" { type = string }
variable "notification_email" { type = string }

variable "bigquery_dataset_name" { type = string }
variable "bigquery_raw_dataset_name" { type = string }
variable "bigquery_location" { type = string }
variable "bigquery_admin_account_name" { type = string }
variable "bigquery_reader_account_name" { type = string }
variable "bigquery_airflow_account_name" { type = string }

provider "google" {
  project = var.project_id
  region = var.region_name
  zone = var.zone_name
}

## Billing

resource "google_project_service" "billing_budgets" {
  project = var.project_id
  service = "billingbudgets.googleapis.com"
}

resource "google_monitoring_notification_channel" "email" {
  display_name = "Billing Email"

  type = "email"

  labels = {
    email_address = var.notification_email
  }
}

## BQ Configs

resource "google_project_service" "bigquery" {
  project = var.project_id
  service = "bigquery.googleapis.com"

  disable_on_destroy = false
}

resource "google_bigquery_dataset" "main_dataset" {
  dataset_id = var.bigquery_dataset_name
  location = var.bigquery_location

  depends_on = [
    google_project_service.bigquery
  ]
}

resource "google_bigquery_dataset" "raw_dataset" {
  dataset_id = var.bigquery_raw_dataset_name
  location = var.bigquery_location

  depends_on = [
    google_project_service.bigquery
  ]
}


## Admin Account

resource "google_service_account" "bigquery_admin_sa" {
  account_id = var.bigquery_admin_account_name 
  display_name = "BigQuery Admin Service Account"
}

resource "google_project_iam_member" "bigquery_admin_user" {
  project = var.project_id
  role = "roles/bigquery.dataEditor"
  member = "serviceAccount:${google_service_account.bigquery_admin_sa.email}"
}

## Normal User

resource "google_service_account" "bigquery_reader_sa" {
  account_id = var.bigquery_reader_account_name 
  display_name = "BigQuery Reader Service Account"
}

resource "google_project_iam_member" "bigquery_reader_user" {
  project = var.project_id
  role = "roles/bigquery.dataEditor"
  member = "serviceAccount:${google_service_account.bigquery_admin_sa.email}"
}

## Airflow's connection

resource "google_service_account" "bigquery_airflow_sa" {
  account_id = var.bigquery_airflow_account_name 
  display_name = "BigQuery Airflow's Service Account"
}

resource "google_project_iam_member" "bigquery_airflow_user" {
  project = var.project_id
  role = "roles/bigquery.user"
  member = "serviceAccount:${google_service_account.bigquery_airflow_sa.email}"
}

resource "google_project_iam_member" "bigquery_airflow_editor" {
  project = var.project_id
  role = "roles/bigquery.dataEditor"
  member = "serviceAccount:${google_service_account.bigquery_airflow_sa.email}"
}

resource "google_service_account_key" "bigquery_airflow_sa_key" {
  service_account_id = google_service_account.bigquery_airflow_sa.name
}

resource "local_file" "bigquery_airflow_sa_key_file" {
  content = base64decode(google_service_account_key.bigquery_airflow_sa_key.private_key)
  filename = "${path.module}/airflow-sa-key.json"
}
