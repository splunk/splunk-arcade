splunk-arcade-mvc
=================

Configure the following environment variables (or configure them in `devspace.yaml`:

- `SPLUNK_ARCADE_OBSERVABILITY_ACCESS_TOKEN`
- `SPLUNK_ARCADE_OBSERVABILITY_REALM`
- `SPLUNK_ARCADE_DOMAIN`

For K3s a local registry can be used, configure the environment variable:

-  `SPLUNK_ARCADE_REGISTRY` to use `localhost:<port>/splunk-arcade`
  
To deploy:

- `devspace deploy`

To clean up/purge:

- `devspace purge`


Uninstalling a Helm chart does not automatically remove PVCs or other resources created by the portal. To clean them up manually, you can use the following commands (ensure you are configured to use the `splunk-arcade` namespace):

- `make clean-pvcs`
- `make clean-players`

In the future, we can set up a cron job to automatically prune these resources after a certain period.
