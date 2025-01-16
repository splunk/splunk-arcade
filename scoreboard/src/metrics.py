from opentelemetry import metrics


class ArcadeMetrics:
    meter = metrics.get_meter(__name__)

    imvaders_projectile_metric = meter.create_counter(
        name="arcade.imvaders.projectiles.count",
        unit="1",
        description="The number of projectiles fired",
    )

    imvaders_level_metric = meter.create_counter(
        name="arcade.imvaders.level",
        unit="1",
        description="The Game Level",
    )
    imvaders_score_metric = meter.create_counter(
        name="arcade.imvaders.score",
        unit="1",
        description="The number of projectiles fired",
    )
    imvaders_duration_metric = meter.create_counter(
        name="arcade.imvaders.game.duration",
        unit="1",
        description="The Game Duration",
    )

    @staticmethod
    def scoreboard_metric_processor(attr):
        final_sb_metric_dict = {}
        final_sb_metric_dict["projectiles"] = attr.get("projectiles")
        final_sb_metric_dict["level"] = attr.get("level")
        final_sb_metric_dict["current_score"] = attr.get("current_score")
        final_sb_metric_dict["duration"] = attr.get("duration")

        ### Drop Ephemeral Dimensions ###
        drop = (
            "duration",
            "position",
            "lives_remaining",
            "level",
            "active",
            "projectiles",
            "current_score",
        )
        for key in drop:
            attr.pop(key, None)
        ArcadeMetrics.imvaders_projectile_metric.add(
            final_sb_metric_dict.get("projectiles"), attributes=attr
        )
        ArcadeMetrics.imvaders_duration_metric.add(
            final_sb_metric_dict.get("duration"), attributes=attr
        )
        ArcadeMetrics.imvaders_level_metric.add(final_sb_metric_dict.get("level"), attributes=attr)
        ArcadeMetrics.imvaders_score_metric.add(
            final_sb_metric_dict.get("current_score"), attributes=attr
        )
        return final_sb_metric_dict

    @staticmethod
    def ship_imvader_proj_count(attr):
        value = attr.get("projectiles")
        drop = (
            "duration",
            "position",
            "lives_remaining",
            "level",
            "active",
            "projectiles",
            "current_score",
        )
        for key in drop:
            attr.pop(key, None)

        if value:
            return ArcadeMetrics.imvaders_projectile_metric.add(value, attributes=attr)

    @staticmethod
    def ship_imvader_duration(attr):
        value = attr.get("duration")
        drop = (
            "duration",
            "position",
            "lives_remaining",
            "level",
            "active",
            "projectiles",
            "current_score",
        )
        for key in drop:
            attr.pop(key, None)

        if value:
            return ArcadeMetrics.imvaders_duration_metric.add(int(value), attributes=attr)

    @staticmethod
    def ship_imvader_level(attr):
        value = attr.get("level")
        drop = (
            "duration",
            "position",
            "lives_remaining",
            "level",
            "active",
            "projectiles",
            "current_score",
        )
        for key in drop:
            attr.pop(key, None)

        if value:
            return ArcadeMetrics.imvaders_level_metric.add(int(value), attributes=attr)

    @staticmethod
    def ship_imvader_score(attr):
        value = attr.get("current_score")
        drop = (
            "duration",
            "position",
            "lives_remaining",
            "level",
            "active",
            "projectiles",
            "current_score",
        )
        for key in drop:
            attr.pop(key, None)

        if value:
            return ArcadeMetrics.imvaders_score_metric.add(int(value), attributes=attr)
