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
variable "location" { type = string }
variable "zone_name" { type = string }
variable "notification_email" { type = string }
variable "admin_account_name" { type = string }
variable "reader_account_name" { type = string }
variable "gcs_bucket_name" { type = string }


provider "google" {
  project = var.project_id
  region = var.location
  zone = var.zone_name
}


module "iam" {
  source = "./modules/iam"

  admin_account_name = var.admin_account_name
  reader_account_name = var.reader_account_name
}

module "gcs" {
  source = "./modules/gcs"

  location = var.location
  gcs_bucket_name = var.gcs_bucket_name

  airflow_email = module.iam.airflow_email
  admin_email = module.iam.admin_email
  reader_email = module.iam.reader_email
}

module "bigquery" {
  source = "./modules/bigquery"

  project_id = var.project_id
  location = var.location
  notification_email = var.notification_email

  airflow_email = module.iam.airflow_email
  admin_email = module.iam.admin_email
  reader_email = module.iam.reader_email
}
