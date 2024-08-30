# Temenos Transact - Rancher Helm Chart


This Helm chart deploys Temenos Transact on SUSE Rancher Kubernetes Environment (RKE). 


## Changelog

| Version   | Date      | Changelog                                                                                                                                                                                                                                                         |
|-----------|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.0.0     | 20/01/24  | Initial release                                                                                                                                                                                                                                    


## Rancher Helm Configuration

The following table lists the configurable parameters of the values-azure.yaml file and the default values.

| Parameter                | Description             | Default        |
| ------------------------ | ----------------------- | -------------- |
| `nameOverride` | (Optional) Override default chart name | `""` |
| `fullnameOverride` | (Optional) Override full default chart name | `""` |
| `deployFI.enabled` | Deploy Temenos Financial Inclusion | `false` |
| `deployATM.enabled` | Deploy Temenos ATM Framework | `false` |
| `appReplicaCount` | Transact app pod replicas | `1` |
| `webReplicaCount` | Transact web pod replicas | `1` |
| `apiReplicaCount` | Transact API pod replicas | `1` |
| `edgeProp` | Configuration modes for UXP Browser. Accepted values: SystemTestProperties, ProductionProperties | `"SystemTestProperties"` |
| `appVersion` | (Optional) Transact version to be used in all image tags in the format {.Values.image.app.repository}:{.Values.image.app.version.}.{.Values.image.app.tag} | `""` |
| `domainname` | Environment domain name used for AGIC | `""` |
| `environment` | Deployment environment. Accepted values: rke,aks, eks - for Rancher Kubernetes,Azure Kubernetes Service and AWS | `rke` |
| `serviceAccount.app` | Transact app service account. If value is blank, the service account will be created. To use an existing service account, set the name here. | `""` |
| `serviceAccount.web` | Transact web service account. If value is blank, the service account will be created. To use an existing service account, set the name here. | `""` |
| `serviceAccount.api` | Transact API service account. If value is blank, the service account will be created. To use an existing service account, set the name here. | `""` |
| `image.pullPolicy` | Pull policy for images. | `"IfNotPresent"` |
| `image.pullSecret` | (Optional) Image pull secret. | `""` |
| `image.app.repository` | App image repository. | `"transact-app"` |
| `image.app.tag` | App image tag. | `""` |
| `image.web.repository` | Web image repository. | `"transact-web"` |
| `image.web.tag` | Web image tag. | `""` |
| `image.api.repository` | API image repository. | `"transact-api"` |
| `image.api.tag` | API image tag. | `""` |
| `tafjee.OLTP_ACTIVE` | Online transaction processing active. true dictates that this Transact instance will serve the frontend applications. false will make it a Transact batch pod. | `"true"` |
| `tafjee.SERVICE_ACTIVE` | Run the Transact pod as a batch service. | `"false"` |
| `apiIp` | (Optional) Set the API load balancer IP address. | `""` |
| `config.name` | Resource prefix | `""` |
| `component.name` | Specifies the Temenos component. Accepted values: transact, lending. Setting this will apply custom network policies with a default deny-all posture. | `"transact"` |
| `database.type` | Database Type: AzureSQL, PostgreSQL, PostgreSQLawsWrapper, Yugabyte or Oracle | `""` |
| `database.user` | Databse username | `""` |
| `database.password` | Databse password - not required if using the PostgreSQLawsWrapper database option. | `""` |
| `database.host` | Database hostname. | `""` |
| `database.encryptedPassword` | Encrypted database password value generated using the EncryptionUtility JAR found in the UXPB Tools package. Required if UXP is deployed and the PostgreSQLawsWrapper database type is not being used. | `""` |
| `database.port` | Database port number | `null` |
| `database.database` | Database schema name | `""` |
| `mq.connectionstring` | ActiveMQ connection string | `""` |
| `mq.user` | ActiveMQ user | `""` |
| `mq.password` | ActiveMQ password | `""` |
| `app.user` | Transact username for UXP artefact connectivity | `""` |
| `app.password` | Transact user password for UXP artefact connectivity | `""` |
| `service.port` | WildFly HTTP port | `8080` |
| `service.httpsPort` | WildFly HTTPS port | `8443` |
| `requests.app.cpu` |  | `"1.5"` |
| `requests.app.memory` |  | `"7G"` |
| `requests.web.cpu` |  | `"1"` |
| `requests.web.memory` |  | `"6G"` |
| `requests.api.cpu` |  | `"1.5"` |
| `requests.api.memory` |  | `"6G"` |
| `limits.app.cpu` |  | `"1.5"` |
| `limits.app.memory` |  | `"7G"` |
| `limits.web.cpu` |  | `"1"` |
| `limits.web.memory` |  | `"6G"` |
| `limits.api.cpu` |  | `"2"` |
| `limits.api.memory` |  | `"12G"` |
| `ingress.enabled` | Deploy ingress to expose Transact services externally from the cluster | `true` |
| `ingress.controller` | Ingress controller to expose the Transact services. Accepted values: awsalbcontroller, nginx or agic | `"awsalbcontroller"` |
| `ingress.usePrivateIp` |  | `true` |
| `ingress.annotations` | Additional custom annotations for the ingress/ingress controller. | `{}` |
| `ingress.paths` |  | `[{"path": "/BrowserWeb*", "service": "-svc"}, {"path": "/TAFJ*", "service": "-app-svc"}, {"path": "/Browser*", "service": "-svc"}, {"path": "/irf*", "service": "-lb"}, {"path": "/infinity*", "service": "-lb"}, {"path": "/axis2*", "service": "-app-svc"}, {"path": "/TAFJCobMonitor*", "service": "-app-svc"}]` |
| `autoscaling.enabled` | Enable autoscaling for the Transact pods using the Horizontal Pod Autoscaler | `true` |
| `autoscaling.minReplicas` | Minimum number of Transact pods if autoscaling is enabled | `1` |
| `autoscaling.maxReplicas` | Maximum number of Transact pods if autoscaling is enabled | `5` |
| `autoscaling.targetCPUUtilizationPercentage` | Pod CPU utilisation value at which more replicas will be created to distribute load. | `75` |
| `share.names` |  | `""` |
| `mount.path` |  | `"/shares/"` |
| `eventstream.jaas_config` |  | `""` |
| `eventstream.server_config` |  | `""` |
| `jboss.MDB_POOL_MAX` | Maximum MDB pool size. | `"6"` |
| `jboss.DB_POOL_MIN` | Minimum database pool size | `"10"` |
| `jboss.DB_POOL_MAX` | Maximum database pool size | `"100"` |
| `jboss.MAX_POOL_SIZE` | JMS Connection factory pool size | `"200"` |
| `jboss.JBOSS_PWD` | Password for application server console admin user | `""` |
| `jboss.console.exposed` | Expose the application server console port in the app | `true` |
| `uxp.debugLogs` | Enable UXP debug logs | `false` |
| `ssl.enabled` | Use SSL for the Transact deployments. | `false` |
| `ssl.filename` | SSL certificate file name present in the ssl directory within this chart. | `""` |
| `ssl.password` | SSL certificate password | `""` |
| `ssl.rootCertName` | SSL certificate root certificate name | `""` |
| `redis.enabled` | Use Redis for the TAFJ cache. | `false` |
| `redis.host` | Redis hostname | `""` |
| `redis.keys` | Redis password | `""` |
| `keycloak.api.enabled` | Enable Keycloak for the API deployment | `false` |
| `keycloak.enabled` | Enable Keycloak for Transact web and app | `false` |
| `keycloak.pkencoded` | Base64 encoded Keycloak Transact realm public key | `""` |
| `keycloak.clientsecret` |  | `""` |
| `keycloak.redirecturi` |  | `""` |
| `keycloak.issuer` | Keycloak Transact realm URL | `""` |
| `keycloak.clientid` | ID of UXP Browser client in KeyCloak | `""` |
| `keycloak.principalclaim` | Name of Transact sign-on-name user attribute in Keycloak | `""` |
| `keycloak.tokenendpoint` | Keycloak transact realm token end point URL | `""` |
| `keycloak.pkcertencoded` |  | `""` |
| `keycloak.authzendpoint` | Keycloak Transact realm authorization end point URL | `""` |
| `keycloak.logoutendpoint` |  | `""` |
| `keycloak.pkjwksuri` |  | `""` |