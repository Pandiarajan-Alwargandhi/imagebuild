{{/*
Expand the name of the chart.
*/}}
{{- define "transact.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "transact.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 59 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 59 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 59 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}


{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "transact.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Selector labels
*/}}
{{- define "app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "transact.name" . }}{{ "-app" }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "web.selectorLabels" -}}
app.kubernetes.io/name: {{ include "transact.name" . }}{{ "-web" }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "transact.name" . }}{{ "-api" }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "iso.selectorLabels" -}}
app.kubernetes.io/name: {{ include "transact.name" . }}{{ "-iso" }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "logstash.selectorLabels" -}}
app.kubernetes.io/name: {{ include "transact.name" . }}{{ "-logstash" }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "app.image"}}
{{- if .Values.image.registry }}
{{- .Values.image.registry | trimSuffix "/" }}{{ "/" }}
{{- end }}
{{- .Values.image.app.repository }}{{ ":" }}
{{- if .Values.appVersion }}
{{- .Values.appVersion }}{{ "." }}
{{- end }}
{{- .Values.image.app.tag }}
{{- end }}

{{- define "web.image"}}
{{- if .Values.image.registry }}
{{- .Values.image.registry | trimSuffix "/" }}{{ "/" }}
{{- end }}
{{- .Values.image.web.repository }}{{ ":" }}
{{- if .Values.appVersion }}
{{- .Values.appVersion }}{{ "." }}
{{- end }}
{{- .Values.image.web.tag }}
{{- end }}

{{- define "iso.image"}}
{{- if .Values.image.registry }}
{{- .Values.image.registry | trimSuffix "/" }}{{ "/" }}
{{- end }}
{{- .Values.image.iso.repository }}{{ ":" }}
{{- default .Values.appVersion }}{{ "." }}
{{- .Values.image.iso.tag }}
{{- end }}

{{- define "api.image"}}
{{- if .Values.image.registry }}
{{- .Values.image.registry | trimSuffix "/" }}{{ "/" }}
{{- end }}
{{- .Values.image.api.repository }}{{ ":" }}
{{- if .Values.appVersion }}
{{- .Values.appVersion }}{{ "." }}
{{- end }}
{{- .Values.image.api.tag }}
{{- end }}

{{- define "logs.image"}}
{{- if .Values.image.registry }}
{{- .Values.image.registry | trimSuffix "/" }}{{ "/" }}
{{- end }}
{{- .Values.image.logstash.repository }}{{ ":" }}
{{- .Values.image.logstash.tag }}
{{- end }}

{{/*
Database connection string based on DB Type
*/}}
{{- define "database.connectionstring" }}
{{- if eq .Values.database.type "AzureSQL" }}
{{- "jdbc:sqlserver://" }}
{{- .Values.database.host }}{{ ":" }}{{ .Values.database.port | default 1433 }}{{ ";" }}
{{- "databaseName=" }}{{ .Values.database.database | default "transact" -}}{{ ";" }}
{{- "integratedSecurity=false" }}
{{- end }}
{{- if eq .Values.database.type "NuoDB" }}
{{- "jdbc:com.nuodb://" }}
{{- .Values.database.host }}{{ ":" }}{{ .Values.database.port | default 48004 }}{{ "/" }}
{{- .Values.database.database | default "transact" -}}{{ "?" }}
{{- "SCHEMA=USER" }}
{{- end }}
{{- if eq .Values.database.type "PostgreSQL" }}
{{- "jdbc:postgresql://" }}
{{- .Values.database.host }}{{ ":" }}{{ .Values.database.port | default 5432 }}{{ "/" }}
{{- .Values.database.database | default "transact" -}}{{ "?" }}
{{- "idle_in_transaction_session_timeout=2000&tcpKeepAlive=true&cleanupSavepoints=true" }}
{{- end }}
{{- if eq .Values.database.type "PostgreSQLawsWrapper" }}
{{- "jdbc:aws-wrapper:postgresql://" }}
{{- .Values.database.host }}{{ ":" }}{{ .Values.database.port | default 5432 }}{{ "/" }}
{{- .Values.database.database | default "transact" -}}{{ "?" }}
{{- "wrapperPlugins=iam&user=" }}{{ .Values.database.user }}{{ "&idle_in_transaction_session_timeout=2000&tcpKeepAlive=true&cleanupSavepoints=true" }}
{{- end }}
{{- if eq .Values.database.type "Yugabyte" }}
{{- "jdbc:yugabyte://" }}
{{- .Values.database.host }}{{ ":" }}{{ .Values.database.port | default 5432 }}{{ "/" }}
{{- .Values.database.database | default "transact" -}}{{ .Values.database.options }}
{{- end }}
{{- if eq .Values.database.type "Oracle" }}
{{- "jdbc:oracle://" }}
{{- .Values.database.host }}{{ ":" }}{{ .Values.database.port | default 1521 }}{{ "/" }}
{{- .Values.database.database | default "transact" -}}{{ ";" }}
{{- end }}
{{- if eq .Values.database.type "H2" }}
{{- "jdbc:h2://" }}
{{- .Values.database.host }}{{ ":" }}{{ .Values.database.port | default 5432 }}{{ "/" }}
{{- .Values.database.database | default "transact" -}}{{ ";" }}
{{- "DB_CLOSE_ON_EXIT=FALSE;MODE=Oracle;TRACE_LEVEL_FILE=0;TRACE_LEVEL_SYSTEM_OUT=0;FILE_LOCK=NO;IFEXISTS=TRUE;CACHE_SIZE=8192;LOCK_TIMEOUT=60000" }}
{{- end }}
{{- end }}


{{/*
Active MQ connection string
*/}}
{{- define "mq.connectionstring" }}{{ .Values.mq.connectionstring }}{{- end }}

{{/*
App service account name
*/}}
{{- define "serviceaccount.app.name" -}}
{{- if .Values.serviceAccount.app -}}
{{ .Values.serviceAccount.app }}
{{- else -}}
{{ template "transact.fullname" . }}{{ "-app-sa" }}
{{- end -}}
{{- end -}}

{{/*
Web service account name
*/}}
{{- define "serviceaccount.web.name" -}}
{{- if .Values.serviceAccount.web -}}
{{ .Values.serviceAccount.web }}  
{{- else -}}
{{ template "transact.fullname" . }}{{ "-web-sa" }}
{{- end -}}
{{- end -}}

{{/*
API service account name
*/}}
{{- define "serviceaccount.api.name" -}}
{{- if .Values.serviceAccount.api -}}
{{ .Values.serviceAccount.api }}  
{{- else -}}
{{ template "transact.fullname" . }}{{ "-api-sa" }}
{{- end -}}
{{- end -}}

{{/*
JAVA_OPTS for APP
*/}}
{{- define "java.opts.app" }}
{{- if eq .Values.database.type "AzureSQL" }}
{{- "-Dresource.server.options.tenant.jdbc.url.1='" }}
{{- "jdbc:sqlserver://" }}
{{- .Values.database.host }}{{ ":" }}{{ .Values.database.port | default 1433 }}{{ ";" }}
{{- "databaseName=" }}{{ .Values.database.database | default "transact" -}}{{ ";" }}
{{- "integratedSecurity=false'" }}
{{- "-Dresource.server.options.tenant.jdbc.username.1=" | indent 1 }}
{{- .Values.database.user }}
{{- "-Dresource.server.options.tenant.jdbc.password.1=" | indent 1 }}
{{- .Values.database.encryptedPassword }}
{{- end }}
{{- if eq .Values.database.type "PostgreSQL" }}
{{- "-Dresource.server.options.tenant.jdbc.url.1=" }}"{{- "jdbc:postgresql://" }}
{{- .Values.database.host }}{{ ":" }}{{ .Values.database.port | default 5432 }}{{ "/" }}
{{- .Values.database.database | default "transact" -}}{{ .Values.database.options }}"
{{- "-Dresource.server.options.tenant.jdbc.username.1=" | indent 1 }}
{{- .Values.database.user }}
{{- "-Dresource.server.options.tenant.jdbc.password.1=" | indent 1 }}
{{- .Values.database.encryptedPassword }}
{{- end }}
{{- if eq .Values.database.type "PostgreSQLawsWrapper" }}
{{- "-Dresource.server.options.tenant.jdbc.url.1=" }}"{{- "jdbc:aws-wrapper:postgresql://" }}
{{- .Values.database.host }}{{ ":" }}{{ .Values.database.port | default 5432 }}{{ "/" }}
{{- .Values.database.database | default "transact" -}}{{ "?" }}
{{- "wrapperPlugins=iam&user=" }}{{ .Values.database.user }}{{- "&idle_in_transaction_session_timeout=2000&tcpKeepAlive=true&cleanupSavepoints=true" }}"
{{- end }}
{{- if .Values.redis.enabled }} 
{{- "-Dtemn.cache.host="| indent 1 }}
{{- .Values.redis.host }}
{{- "-Dtemn.cache.port=6379"| indent 1 }}
{{- "-Dtemn.cache.provider=REDIS"| indent 1 }}
{{- "-Dtemn.cache.password="| indent 1 }}
{{- .Values.redis.keys }}
{{- end }}
{{- if eq .Values.environment "aks" }}
{{- "-Dmda.registry.url=https://"| indent 1 }}
{{- .Values.config.name }}{{"genericconfigapp.azurewebsites.net/api/v2.0.0/system/configurationGroups/{}/configuration/{}"}}
{{- "-Dtemn.msf.stream.kafka.bootstrap.servers="| indent 1 }}
{{- .Values.config.name }}{{"coreeventhub.servicebus.windows.net:9093"}}
{{- end }}
{{- if or (eq .Values.environment "roks" ) (eq .Values.environment "iks") }}
{{- "-Dtemn.msf.stream.kafka.bootstrap.servers="| indent 1 }}
{{- .Values.eventstream.server_config }}
{{- end }}
{{- "-Dbrowser.options.fullExternalCommandAccess=\"Y\""| indent 1 }}
{{- "-Dclass.outbox.dao=com.temenos.inboxoutbox.data.sql.OutboxDaoImpl"| indent 1 }}
{{- "-Doutboxid.jms.queue.name=java:/queue/tafj-outboxIdQueue"| indent 1 }}
{{- "-Doutboxid.jms.connection.factory=java:/JmsXA"| indent 1 }}
{{- "-Dtemn.msf.stream.vendor.outbox=kafka"| indent 1 }}
{{- "-Dtemn.msf.ingest.is.cloud.event=false"| indent 1 }}
{{- "-Dtemn.msf.stream.kafka.sasl.enabled=true"| indent 1 }}
{{- "-Dtemn.outbox.events.delivery.direct=true"| indent 1 }}
{{/*
{{- "-Dtemn.msf.metering.TRANSACT.scheduler.host=https://"| indent 1 }}
{{- .Values.domainname }}{{ "/irf-provider-container/" }}
*/}}
{{- "-XX:+UseParallelGC -XX:MaxRAMPercentage=75.0"| indent 1 }}
{{- if .Values.uxp.debugLogs }}
{{- "-DedgeSystemDebug=Y" | indent 1 }}
{{- "-DedgeSystemDebugFolder=$BRP_HOME/logs" | indent 1 }}
{{- end }}
{{- end }}

{{/*
JAVA_OPTS for API POD
*/}}
{{- define "java.opts.api" }}
{{- "-XX:+UseParallelGC -XX:MaxRAMPercentage=75.0" }}
{{- if eq .Values.environment "aks" }}
{{- " -Dmda.registry.url=https://"| indent 1 }}
{{- .Values.config.name }}{{"genericconfigapp.azurewebsites.net/api/v2.0.0/system/configurationGroups/{}/configuration/{}"}}
{{- end }}
{{- end }}
{{/*
JAVA_OPTS for WEB POD
*/}}
{{- define "java.opts.web" }}
{{- "-XX:+UseParallelGC -XX:MaxRAMPercentage=75.0" }}
{{- "-Dauthfilter.options.browserSessionUidCheckEnabled=\"N\""| indent 1 }}
{{- "-Dbrowser.options.fullExternalCommandAccess=\"Y\""| indent 1 }}
{{- if .Values.uxp.debugLogs }}
{{- "-DedgeSystemDebug=Y" | indent 1 }}
{{- "-DedgeSystemDebugFolder=$LOG_HOME/logs" | indent 1 }}
{{- end }}
{{- end }}
