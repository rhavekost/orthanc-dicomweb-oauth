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
*/}}
{{- define "orthanc-oauth.databaseConnectionString" -}}
{{- if eq .Values.database.type "external" }}
{{- printf "host=%s port=%d dbname=%s sslmode=%s" .Values.database.external.host (.Values.database.external.port | int) .Values.database.external.database .Values.database.external.sslMode }}
{{- else }}
{{- printf "host=%s-postgresql port=5432 dbname=orthanc sslmode=disable" (include "orthanc-oauth.fullname" .) }}
{{- end }}
{{- end }}
