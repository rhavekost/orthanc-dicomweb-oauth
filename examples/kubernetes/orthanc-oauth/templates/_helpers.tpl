{{/*
Expand the name of the chart.
*/}}
{{- define "orthanc-oauth.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "orthanc-oauth.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "orthanc-oauth.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "orthanc-oauth.labels" -}}
helm.sh/chart: {{ include "orthanc-oauth.chart" . }}
{{ include "orthanc-oauth.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "orthanc-oauth.selectorLabels" -}}
app.kubernetes.io/name: {{ include "orthanc-oauth.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "orthanc-oauth.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "orthanc-oauth.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Database connection string for Orthanc
Note: Username and password are passed via environment variables for security
*/}}
{{- define "orthanc-oauth.databaseConnectionString" -}}
{{- if eq .Values.database.type "external" }}
{{- $host := required "database.external.host is required when database.type is 'external'" .Values.database.external.host }}
{{- $port := required "database.external.port is required when database.type is 'external'" .Values.database.external.port }}
{{- $dbname := required "database.external.database is required when database.type is 'external'" .Values.database.external.database }}
{{- $sslMode := required "database.external.sslMode is required when database.type is 'external'" .Values.database.external.sslMode }}
{{- printf "host=%s port=%d dbname=%s sslmode=%s" $host ($port | int) $dbname $sslMode }}
{{- else if eq .Values.database.type "in-cluster" }}
{{- $host := printf "%s-postgresql" (include "orthanc-oauth.fullname" .) }}
{{- $port := .Values.database.inCluster.port | default 5432 | int }}
{{- $dbname := .Values.database.inCluster.database | default "orthanc" }}
{{- $sslMode := .Values.database.inCluster.sslMode | default "disable" }}
{{- printf "host=%s port=%d dbname=%s sslmode=%s" $host $port $dbname $sslMode }}
{{- else }}
{{- fail "database.type must be either 'external' or 'in-cluster'" }}
{{- end }}
{{- end }}
