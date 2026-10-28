{{- define "sentinelflow.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "sentinelflow.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "sentinelflow.labels" -}}
app.kubernetes.io/name: {{ include "sentinelflow.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}

{{- define "sentinelflow.selector" -}}
app.kubernetes.io/name: {{ include "sentinelflow.name" .root }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "sentinelflow.image" -}}
{{- printf "%s:%s" .Values.image.repository (default .Chart.AppVersion .Values.image.tag) -}}
{{- end -}}

{{/* Environment shared by every container: config map plus the existing secret. */}}
{{- define "sentinelflow.envFrom" -}}
- configMapRef:
    name: {{ include "sentinelflow.fullname" . }}
- secretRef:
    name: {{ .Values.existingSecret }}
{{- end -}}
