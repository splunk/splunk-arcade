terraform {
  required_version = ">= 1.0"

  required_providers {
    signalfx = {
      source  = "splunk-terraform/signalfx"
      version = "~> 9.7.1"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35.1"
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


// imvaders dashboard + charts
resource "signalfx_dashboard" "splunk_arcade_dashboard" {
  name            = "Splunk Arcade Dashboard - ${var.player_name}"
  description     = "Splunk Arcade Player Dashboard for ${var.player_name}"
  dashboard_group = signalfx_dashboard_group.observability_group.id
  time_range      = "-15m"

  chart {
    chart_id = signalfx_time_chart.imvaders_score.id
    column   = 0
    row      = 0
    height   = 1
    width    = 6
  }
  chart {
    chart_id = signalfx_time_chart.imvaders_mean_score_by_player.id
    column   = 6
    row      = 0
    height   = 1
    width    = 6
  }
  chart {
    chart_id = signalfx_time_chart.imvaders_score_all_players.id
    column   = 0
    row      = 1
    height   = 1
    width    = 6
  }
  chart {
    chart_id = signalfx_time_chart.imvaders_mean_score_by_version.id
    column   = 6
    row      = 0
    height   = 1
    width    = 6
  }
  chart {
    chart_id = signalfx_time_chart.logger_score.id
    column   = 0
    row      = 2
    height   = 1
    width    = 6
  }
  chart {
    chart_id = signalfx_time_chart.logger_mean_score_by_player.id
    column   = 6
    row      = 2
    height   = 1
    width    = 6
  }
  chart {
    chart_id = signalfx_time_chart.logger_score_all_players.id
    column   = 0
    row      = 3
    height   = 1
    width    = 6
  }
  chart {
    chart_id = signalfx_time_chart.bughunt_score.id
    column   = 0
    row      = 4
    height   = 1
    width    = 6
  }
  chart {
    chart_id = signalfx_time_chart.bughunt_mean_score_by_player.id
    column   = 6
    row      = 4
    height   = 1
    width    = 6
  }
  chart {
    chart_id = signalfx_time_chart.bughunt_score_all_players.id
    column   = 0
    row      = 5
    height   = 1
    width    = 6
  }
}

resource "signalfx_time_chart" "imvaders_score" {
  name = "IMvaders Scores - ${var.player_name}"

  program_text = <<-EOF
    A = data('arcade.imvaders.score').publish(label='A')
  EOF
}

resource "signalfx_time_chart" "imvaders_score_all_players" {
  name         = "IMvaders Scores - All Players"
  plot_type    = "ColumnChart"
  stacked      = true
  program_text = <<-EOF
    A = data('arcade.imvaders.score').publish(label='A')
  EOF
}

resource "signalfx_time_chart" "imvaders_mean_score_by_player" {
  name      = "IMvaders Avg Game Score - ${var.player_name}"
  plot_type = "AreaChart"


  program_text = <<-EOF
    A = data('arcade.imvaders.score', filter=filter('player_name', '${var.player_name}')).mean(by=['player_name']).publish(label='A')
  EOF
}

resource "signalfx_time_chart" "imvaders_mean_score_by_version" {
  name      = "IMvaders Score Avg by Version - All Players"
  plot_type = "AreaChart"


  program_text = <<-EOF
    A = data('arcade.imvaders.score', filter=filter('player_name', '${var.player_name}')).mean(by=['player_name']).publish(label='A')
  EOF
}

// logger charts
resource "signalfx_time_chart" "logger_score" {
  name = "Logger Scores - ${var.player_name}"

  program_text = <<-EOF
    A = data('arcade.logger.score').publish(label='A')
  EOF
}

resource "signalfx_time_chart" "logger_score_all_players" {
  name         = "Logger Scores - All Players"
  plot_type    = "ColumnChart"
  stacked      = true
  program_text = <<-EOF
    A = data('arcade.logger.score').publish(label='A')
  EOF
}

resource "signalfx_time_chart" "logger_mean_score_by_player" {
  name      = "Logger Avg Game Score - ${var.player_name}"
  plot_type = "AreaChart"


  program_text = <<-EOF
    A = data('arcade.logger.score', filter=filter('player_name', '${var.player_name}')).mean(by=['player_name']).publish(label='A')
  EOF
}

// bughunt charts
resource "signalfx_time_chart" "bughunt_score" {
  name = "Bug Hunt Scores - ${var.player_name}"

  program_text = <<-EOF
    A = data('arcade.bughunt.score').publish(label='A')
  EOF
}

resource "signalfx_time_chart" "bughunt_score_all_players" {
  name         = "Bug Hunt Scores - All Players"
  plot_type    = "ColumnChart"
  stacked      = true
  program_text = <<-EOF
    A = data('arcade.bughunt.score').publish(label='A')
  EOF
}

resource "signalfx_time_chart" "bughunt_mean_score_by_player" {
  name      = "Bug Hunt Avg Game Score - ${var.player_name}"
  plot_type = "AreaChart"


  program_text = <<-EOF
    A = data('arcade.bughunt.score', filter=filter('player_name', '${var.player_name}')).mean(by=['player_name']).publish(label='A')
  EOF
}

resource "kubernetes_config_map" "tf_outputs" {
  metadata {
    name      = "tf-outputs-${var.player_name}"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/name" = "splunk-arcade-player-cloud-outputs"
    }
  }

  data = {
    dashboard_url = signalfx_dashboard.splunk_arcade_dashboard.url
  }
}