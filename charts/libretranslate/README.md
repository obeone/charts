# libretranslate

![Version: 1.0.2](https://img.shields.io/badge/Version-1.0.2-informational?style=flat-square) ![AppVersion: v1.6.5](https://img.shields.io/badge/AppVersion-v1.6.5-informational?style=flat-square)

Free and Open Source Machine Translation API. Self-hosted, offline capable and easy to setup.

**Homepage:** <https://github.com/LibreTranslate/LibreTranslate>

## Requirements

Kubernetes: `>=1.16.0-0`

| Repository | Name | Version |
|------------|------|---------|
| https://bjw-s.github.io/helm-charts | common | 3.7.1 |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| additionalVolumeMounts | list | `[]` | Define additional volumeMounts if needed |
| additionalVolumes | list | `[]` | Define additional volumes if needed |
| affinity | object | `{}` | Affinity rules to control pod assignment based on node labels |
| controllers.main.containers.main.env.LT_API_KEYS | string | `"1"` | Set to "1" to enable API key usage for authentication |
| controllers.main.containers.main.env.LT_UPDATE_MODELS | string | `"1"` | Set to "1" to update language models on startup |
| controllers.main.containers.main.image.pullPolicy | string | `"Always"` | Image pull policy (Always, IfNotPresent, Never) |
| controllers.main.containers.main.image.repository | string | `"libretranslate/libretranslate"` | Image repository to pull |
| controllers.main.containers.main.image.tag | string | `"v1.6.5"` | Image tag to pull (use vX.X.X-cuda for GPU builds) |
| controllers.main.containers.main.probes.liveness.custom | bool | `true` |  |
| controllers.main.containers.main.probes.liveness.enabled | bool | `true` |  |
| controllers.main.containers.main.probes.liveness.spec.httpGet.path | string | `"/"` |  |
| controllers.main.containers.main.probes.liveness.spec.httpGet.port | string | `"http"` |  |
| controllers.main.containers.main.probes.readiness.custom | bool | `true` |  |
| controllers.main.containers.main.probes.readiness.enabled | bool | `true` |  |
| controllers.main.containers.main.probes.readiness.spec.httpGet.path | string | `"/"` |  |
| controllers.main.containers.main.probes.readiness.spec.httpGet.port | string | `"http"` |  |
| controllers.main.containers.main.resources.limits | object | `{"cpu":"500m","memory":"512Mi"}` | Resource limits for the main container |
| controllers.main.containers.main.resources.requests | object | `{"cpu":"100m","memory":"128Mi"}` | Resource requests for the main container |
| controllers.main.strategy | string | `"Recreate"` |  |
| global | object | `{"gpuEnabled":false}` | Global parameters for the chart Used to configure GPU support and other global settings |
| global.gpuEnabled | bool | `false` | Enable GPU-specific settings (like CUDA paths and GPU resources) |
| ingress | object | `{"main":{"enabled":false,"hosts":[{"host":"chart-example.local","paths":[{"path":"/","pathType":"Prefix","service":{"identifier":"main","port":"http"}}]}],"tls":[{"hosts":["chart-example.local"],"secretName":"tls-chart-example-local"}]}}` | Ingress configuration for external access to the service |
| ingress.main.enabled | bool | `false` | Enable or disable ingress |
| ingress.main.tls[0].secretName | string | `"tls-chart-example-local"` | Secret containing TLS certificate for the ingress |
| nodeSelector | object | `{}` | Node selector for pod assignment |
| persistence | object | `{"api-keys":{"accessMode":"ReadWriteOnce","annotations":{},"enabled":false,"globalMounts":[{"path":"/app/db"}],"size":"10Mi"},"cache":{"cpuPath":"/home/libretranslate/.local/cache","enabled":true,"gpuPath":"/root/.cache/libretranslate","type":"emptyDir"},"db":{"accessMode":"ReadWriteOnce","annotations":{},"cpuPath":"/home/libretranslate/.local/db","enabled":false,"gpuPath":"/root/.local/db","size":"1Gi"},"files-translate":{"enabled":true,"path":"/tmp/libretranslate-files-translate","type":"emptyDir"},"share":{"accessMode":"ReadWriteOnce","annotations":{},"cpuPath":"/home/libretranslate/.local/share","enabled":true,"gpuPath":"/root/.local/share","size":"20Gi"}}` | Persistence volumes configuration for different data types Paths are statically defined here. Template logic must occur in templates. |
| persistence.api-keys.enabled | bool | `false` | Enable persistence for API keys database |
| persistence.cache.enabled | bool | `true` | Enable temporary cache storage |
| persistence.db.enabled | bool | `false` | Enable database storage for application data |
| persistence.files-translate.enabled | bool | `true` | Temporary storage for uploaded translation files |
| persistence.share.enabled | bool | `true` | Enable persistent shared storage for translation models and shared assets |
| service | object | `{"main":{"controller":"main","ports":{"http":{"port":80,"protocol":"TCP","targetPort":5000}}}}` | Service configuration to expose the application internally in the cluster |
| service.main.ports.http.port | int | `80` | External service port |
| service.main.ports.http.protocol | string | `"TCP"` | Protocol to use (TCP/UDP) |
| service.main.ports.http.targetPort | int | `5000` | Internal container target port |
| tolerations | list | `[]` | Tolerations for pod assignment to specific nodes |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
