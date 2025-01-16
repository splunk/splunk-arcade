from kubernetes import client, config

APP_NAME = "splunk-arcade"
NAMESPACE = "splunk-arcade"
IMAGE_PLAYER_CABINET = "splunk-arcade/cabinet:latest"
IMAGE_PULL_POLICY = "IfNotPresent"


class _Config:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(_Config, cls).__new__(cls)

        return cls._instance

    def __init__(self):
        self.config = config.load_incluster_config()


def player_deployment_create(player_id: str) -> None:
    # ensure config is loaded
    _ = _Config()

    dep = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(
            name=f"{APP_NAME}-player-{player_id}",
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            strategy=client.V1DeploymentStrategy(
                rolling_update=client.V1RollingUpdateDeployment(
                    max_surge=1,
                    max_unavailable=0,
                ),
                type="RollingUpdate",
            ),
            selector=client.V1LabelSelector(
                match_labels={
                    "app.kubernetes.io/name": f"{APP_NAME}-cabinet",
                    "app.kubernetes.io/instance": f"{APP_NAME}-cabinet-{player_id}",
                }
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={
                        "app.kubernetes.io/name": f"{APP_NAME}-cabinet",
                        "app.kubernetes.io/instance": f"{APP_NAME}-cabinet-{player_id}",
                    },
                ),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="player",
                            image=IMAGE_PLAYER_CABINET,
                            image_pull_policy=IMAGE_PULL_POLICY,
                            resources=client.V1ResourceRequirements(
                                requests={
                                    "cpu": "250m",
                                    "memory": "128Mi",
                                },
                                limits={
                                    "cpu": "500m",
                                    "memory": "512Mi",
                                },
                            ),
                            env=[
                                client.V1EnvVar(
                                    name="NODE_IP",
                                    value_from=client.V1EnvVarSource(
                                        field_ref=client.V1ObjectFieldSelector(
                                            field_path="status.hostIP"
                                        )
                                    ),
                                ),
                                client.V1EnvVar(
                                    name="OTEL_EXPORTER_OTLP_ENDPOINT",
                                    value="http://$(NODE_IP):4317",
                                ),
                                client.V1EnvVar(
                                    name="OTEL_EXPORTER_HEALTH_ENDPOINT",
                                    value="http://$(NODE_IP):13133",
                                ),
                                client.V1EnvVar(
                                    name="PLAYER_NAME",
                                    value=player_id,
                                ),
                                client.V1EnvVar(
                                    name="DATABASE_URL",
                                    value=f"postgresql://postgres:password@{APP_NAME}-postgresql/myapp",
                                ),
                                client.V1EnvVar(
                                    name="REDIS_HOST",
                                    value=f"{APP_NAME}-redis-master",
                                ),
                                client.V1EnvVar(
                                    name="SCOREBOARD_HOST", value=f"{APP_NAME}-scoreboard"
                                ),
                                client.V1EnvVar(
                                    name="OTEL_SERVICE_NAME", value="splunk-arcade-player"
                                ),
                                client.V1EnvVar(
                                    name="OTEL_RESOURCE_ATTRIBUTES",
                                    value="service.name=$(OTEL_SERVICE_NAME),service.namespace=splunk-arcade,deployment.environment=gameify",
                                ),
                            ],
                            ports=[
                                client.V1ContainerPort(
                                    name="http",
                                    container_port=5_000,
                                ),
                            ],
                            liveness_probe=client.V1Probe(
                                http_get=client.V1HTTPGetAction(
                                    path="/alive", port="http", scheme="HTTP"
                                ),
                                success_threshold=1,
                                failure_threshold=2,
                                period_seconds=30,
                                timeout_seconds=5,
                            ),
                        )
                    ],
                    service_account_name="default",
                ),
            ),
        ),
    )

    apps_v1 = client.AppsV1Api()
    resp = apps_v1.create_namespaced_deployment(namespace=NAMESPACE, body=dep)
    print(f"create player deployment resp {resp}")


def player_deployment_ready(player_id: str) -> bool:
    # ensure config is loaded
    _ = _Config()

    apps_v1 = client.AppsV1Api()
    resp = apps_v1.read_namespaced_deployment_status(
        namespace=NAMESPACE, name=f"player-{player_id}"
    )
    print(f"check player deployment resp {resp}")

    return True
