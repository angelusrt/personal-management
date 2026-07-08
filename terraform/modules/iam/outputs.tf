output "airflow_email" { value = google_service_account.airflow.email }
output "admin_email"   { value = google_service_account.admin.email }
output "reader_email"  { value = google_service_account.reader.email }

output "airflow_key" {
  value = google_service_account_key.airflow_key.private_key
  sensitive = true
}
