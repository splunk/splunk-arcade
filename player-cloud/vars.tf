variable "signalfx_api_token" {
  description = "Your SignalFx API Token"
  type        = string
  sensitive   = true
}

variable "player_name" {
  description = "Splunk Arcade Player Name"
  type        = string
  sensitive   = false
}

variable "realm" {
  description = "Splunk Arcade Observability Realm"
  type        = string
  sensitive   = false
}

variable "namespace" {
  description = "The Kubernetes namespace"
  type        = string
  default     = "splunk-arcade"
}