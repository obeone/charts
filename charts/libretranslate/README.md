# libretranslate

![Version: 1.0.1](https://img.shields.io/badge/Version-1.0.1-informational?style=flat-square) ![AppVersion: v1.6.4](https://img.shields.io/badge/AppVersion-v1.6.4-informational?style=flat-square)

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
| controllers.main.containers.main.env.LT_API_KEYS | string | `"1"` | Set to "1" to enable API keys. |
| controllers.main.containers.main.env.LT_UPDATE_MODELS | string | `"1"` | Set to "1" to update models on startup. |
| controllers.main.containers.main.image.pullPolicy | string | `"Always"` | image pull policy |
| controllers.main.containers.main.image.repository | string | `"libretranslate/libretranslate"` | image repository |
| controllers.main.containers.main.image.tag | string | `"v1.6.4"` | image tag Use vX.X.X-cuda for GPU support. Use latest for CPU only. |
| controllers.main.strategy | string | `"Recreate"` |  |
| ingress.main | object | `{"enabled":false,"hosts":[{"host":"chart-example.local","paths":[{"path":"/","pathType":"Prefix","service":{"identifier":"main","port":"http"}}]}],"tls":[{"hosts":["chart-example.local"],"secretName":"tls-chart-example-local"}]}` | Enable and configure ingress settings for the chart under this key. |
| persistence | object | `{"api-keys":{"accessMode":"ReadWriteOnce","annotations":{},"enabled":false,"globalMounts":[{"path":"/app/db"}],"size":"10Mi"},"cache":{"enabled":true,"globalMounts":[{"path":"/home/libretranslate/.local/cache"}],"type":"emptyDir"},"db":{"accessMode":"ReadWriteOnce","annotations":{},"enabled":false,"globalMounts":[{"path":"/home/libretranslate/.local/db"}],"size":"1Gi"},"files-translate":{"enabled":true,"globalMounts":[{"path":"/tmp/libretranslate-files-translate"}],"type":"emptyDir"},"share":{"accessMode":"ReadWriteOnce","annotations":{},"enabled":true,"globalMounts":[{"path":"/home/libretranslate/.local/share"}],"size":"20Gi"}}` | Configure persistence settings for the chart under this key. |
| resources | object | `{}` | Configures resource requests and limits for the chart. |
| service | object | `{"main":{"controller":"main","ports":{"http":{"port":80,"protocol":"TCP","targetPort":5000}}}}` | Configures service settings for the chart. |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
