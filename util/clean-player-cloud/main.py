import os
import time

from kubernetes import client, config

# this whole thing is terribad. but... should work

# will slurp these up from explicitly having pipeline pass them in or being set anyway
APP_NAME = os.getenv("APP_NAME") or "splunk-arcade"
IMAGE_PULL_POLICY = os.getenv("IMAGE_PULL_POLICY") or "IfNotPresent"
NAMESPACE = os.getenv("NAMEPSACE") or "splunk-arcade"
SPLUNK_OBSERVABILITY_REALM = os.getenv("SPLUNK_OBSERVABILITY_REALM", "")
SPLUNK_OBSERVABILITY_API_ACCESS_TOKEN = os.getenv("SPLUNK_OBSERVABILITY_API_ACCESS_TOKEN", "")


def wait_cleanup_job_complete(job_name: str) -> bool:
    timeout = 300
    interval = 5
    batch_v1 = client.BatchV1Api()
    start_time = time.time()

    while time.time() - start_time < timeout:
        resp = batch_v1.read_namespaced_job(
            name=job_name,
            namespace=NAMESPACE,
        )

        if resp.status.succeeded:
            return True

        time.sleep(interval)

    return False


def main():
    config.load_kube_config()

    core_v1 = client.CoreV1Api()
    batch_v1 = client.BatchV1Api()

    # we fetch portal so we can get the same tag since all images should be using same tag
    # and we dont know if we are using "latest" (dev) or some commit hash (prod)
    apps_v1 = client.AppsV1Api()
    resp = apps_v1.list_namespaced_deployment(
        namespace=NAMESPACE,
        label_selector=f"app.kubernetes.io/name={APP_NAME}-portal",
    )
    if not resp.items:
        raise Exception("couldn't glean tag from portal deployment")

    # i hate this but using devspace local reg this should be fine... for now
    registry = "/".join(resp.items[0].spec.template.spec.containers[0].image.split("/")[0:2])
    tag = resp.items[0].spec.template.spec.containers[0].image.split(":")[-1]

    image_player_cloud = f"{registry}/player-cloud:{tag}"

    secrets = core_v1.list_namespaced_secret(
        namespace=NAMESPACE,
        label_selector="app.kubernetes.io/name=splunk-arcade-player-cloud-state",
    )

    job_names = []
    secret_names = []

    for secret in secrets.items:
        player_id = secret.metadata.name.removeprefix("tfstate-default-")
        job_name = f"{APP_NAME}-player-{player_id}-cloud-cleanup"

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                name=job_name,
                labels={
                    "app.kubernetes.io/name": f"{APP_NAME}-player-cloud-cleanup",
                    "app.kubernetes.io/instance": f"{APP_NAME}-player-cloud-cleanup-{player_id}",
                },
            ),
            spec=client.V1JobSpec(
                ttl_seconds_after_finished=360,
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
                                image=image_player_cloud,
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
                                    client.V1EnvVar(
                                        name=f"TF_VAR_namespace",
                                        value=NAMESPACE,
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
            print(f"failed creating cleanup job for player {player_id}")

            if "AlreadyExists" in exc.body:
                print(" error a conflict, we'll remove secret assuming that a job pod already "
                      "ran for this user...")
                pass
            else:
                print(f"    error *not* a conflict, will not remove secret..., exception: {exc}")
                # continue so we leave the state secret; but if "conflict" its because there was
                # already a pod that ran for this
                continue

        job_names.append(job_name)
        secret_names.append(secret.metadata.name)


    for job_name in job_names:
        print(f"waiting on job {job_name}...")

        if not wait_cleanup_job_complete(job_name=job_name):
            print(f"job  {job_name} did not complete in time... there is prolly left over junk")

    for secret_name in secret_names:
        print(f"deleting secret {secret_name}...")
        core_v1.delete_namespaced_secret(namespace=NAMESPACE, name=secret_name)



if __name__ == "__main__":
    main()
