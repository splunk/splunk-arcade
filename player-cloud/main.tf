terraform {
  required_version = ">= 1.0"

  required_providers {
    signalfx = {
      source  = "splunk-terraform/signalfx"
      version = "~> 9.7.1"
    }
  }

  backend "kubernetes" {
    in_cluster_config = true
    labels = {
      "app.kubernetes.io/name" = "splunk-arcade-player-cloud-state"
    }
  }
}

provider "signalfx" {
  auth_token = var.signalfx_api_token
  api_url    = "https://api.${var.realm}.signalfx.com"
}

resource "signalfx_dashboard_group" "observability_group" {
  name        = "splunk-arcade-${var.player_name}"
  description = "Group containing dashboards for key observability metrics"
}

resource "signalfx_dashboard" "splunk_arcade_dashboard" {
  name            = "Splunk Arcade Dashboard - ${var.player_name}"
  description     = "Splunk Arcade Player Dashboard for ${var.player_name}"
  dashboard_group = signalfx_dashboard_group.observability_group.id
  time_range      = "-1d"

  chart {
    chart_id = signalfx_time_chart.imvaders_score.id
    column   = 0
    height   = 1
    width    = 6
  }

  chart {
    chart_id = signalfx_time_chart.imvaders_mean_score_by_player.id
    column   = 6
    height   = 1
    width    = 6
  }

  chart {
    chart_id = signalfx_time_chart.logger_player_score.id
    column   = 6
    height   = 1
    width    = 6
  }
}

resource "signalfx_time_chart" "imvaders_score" {
  name         = "IMvaders Scores - ${var.player_name}"
  program_text = <<-EOF
    A = data('arcade.imvaders.score').publish(label='A')
  EOF
}

resource "signalfx_time_chart" "imvaders_mean_score_by_player" {
  name         = "IMvaders Avg Game Score - ${var.player_name}"
  plot_type    = "AreaChart"
  program_text = <<-EOF
    A = data('arcade.imvaders.score', filter=filter('player_name', '${var.player_name}')).mean(by=['player_name']).publish(label='A')
  EOF
}

resource "signalfx_time_chart" "logger_player_score" {
  name         = "Logger Scores - ${var.player_name}"
  program_text = <<-EOF
    A = data('arcade.logger.score', filter=filter('player_name', '${var.player_name}')).publish(label='A')
  EOF
}