import os

from kubernetes import client, config

APP_NAME = os.getenv("APP_NAME") or "splunk-arcade"
IMAGE_PLAYER_CLOUD = os.getenv("PLAYER_CLOUD_IMAGE") or "splunk-arcade/player-cloud:latest"
IMAGE_PULL_POLICY = os.getenv("IMAGE_PULL_POLICY") or "IfNotPresent"
NAMESPACE = os.getenv("NAMEPSACE") or "splunk-arcade"
SPLUNK_OBSERVABILITY_REALM = os.getenv("SPLUNK_OBSERVABILITY_REALM", "")
SPLUNK_OBSERVABILITY_API_ACCESS_TOKEN = os.getenv("SPLUNK_OBSERVABILITY_API_ACCESS_TOKEN", "")


def main():
    config.load_kube_config()

    core_v1 = client.CoreV1Api()
    batch_v1 = client.BatchV1Api()

    secrets = core_v1.list_namespaced_secret(
        namespace=NAMESPACE,
        label_selector="app.kubernetes.io/name=splunk-arcade-player-cloud-state",
    )

    for secret in secrets.items:
        player_id = secret.metadata.name.removeprefix("tfstate-default-")

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                name=f"{APP_NAME}-player-{player_id}-cloud-cleanup",
                labels={
                    "app.kubernetes.io/name": f"{APP_NAME}-player-cloud-cleanup",
                    "app.kubernetes.io/instance": f"{APP_NAME}-player-cloud-cleanup-{player_id}",
                },
            ),
            spec=client.V1JobSpec(
                ttl_seconds_after_finished=60,
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={
                            "app.kubernetes.io/name": f"{APP_NAME}-player-cloud-cleanup",
                            "app.kubernetes.io/instance": f"{APP_NAME}-player-cloud-cleanup-{player_id}",
                        },
                    ),
                    spec=client.V1PodSpec(
                        restart_policy="Never",
                        containers=[
                            client.V1Container(
                                name="player-cloud",
                                image=IMAGE_PLAYER_CLOUD,
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
                                        name=f"TF_VAR_signalfx_api_token",
                                        value=SPLUNK_OBSERVABILITY_API_ACCESS_TOKEN,
                                    ),
                                    client.V1EnvVar(
                                        name=f"KUBE_NAMESPACE",
                                        value=NAMESPACE,
                                    ),
                                    client.V1EnvVar(
                                        name=f"TF_VAR_player_name",
                                        value=player_id,
                                    ),
                                    client.V1EnvVar(
                                        name=f"TF_VAR_realm",
                                        value=SPLUNK_OBSERVABILITY_REALM,
                                    ),
                                ],
                                command=["/entrypoint.destroy.sh"],
                            ),
                        ],
                        # so it can get secrets for tfstate
                        service_account_name=f"{APP_NAME}-service-account",
                    ),
                )
            ),
        )

        try:
            batch_v1.create_namespaced_job(namespace=NAMESPACE, body=job)
        except Exception as exc:
            print(f"failed creating cleanup job for player {player_id} -- *not* removing secret. exception: {exc}")

            # continue so we leave the state secret
            continue

        core_v1.delete_namespaced_secret(namespace=NAMESPACE, name=secret.metadata.name)



if __name__ == "__main__":
    main()
