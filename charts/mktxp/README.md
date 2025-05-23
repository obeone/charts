# mktxp

![Version: 1.1.7](https://img.shields.io/badge/Version-1.1.7-informational?style=flat-square) ![AppVersion: latest](https://img.shields.io/badge/AppVersion-latest-informational?style=flat-square)

Mikrotik (RouterOS) exporter for Prometheus metics

**Homepage:** <https://github.com/akpw/mktxp>

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| obeone | <obeone@obeone.org> |  |

## Source Code

* <https://github.com/akpw/mktxp>
* <https://github.com/obeone/charts>

## Requirements

Kubernetes: `>=1.16.0-0`

| Repository | Name | Version |
|------------|------|---------|
| https://library-charts.k8s-at-home.com | common | 4.5.2 |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| configmap.config.data."_mktxp.conf" | string | `"[MKTXP]\n  port = 49090\n  socket_timeout = 2\n\n  initial_delay_on_failure = 120\n  max_delay_on_failure = 900\n  delay_inc_div = 5\n\n  bandwidth = True               # Turns metrics bandwidth metrics collection on / off\n  bandwidth_test_interval = 3600   # Interval for colllecting bandwidth metrics\n  minimal_collect_interval = 5    # Minimal metric collection interval\n\n  verbose_mode = True            # Set it on for troubleshooting\n\n  fetch_routers_in_parallel = False   # Set to True if you want to fetch multiple routers parallel\n  max_worker_threads = 5              # Max number of worker threads that can fetch routers (parallel fetch only)\n  max_scrape_duration = 10            # Max duration of individual routers' metrics collection (parallel fetch only)\n  total_max_scrape_duration = 30      # Max overall duration of all metrics collection (parallel fetch only)\n"` |  |
| configmap.config.data."mktxp.conf" | string | `"## Copyright (c) 2020 Arseniy Kuznetsov\n##\n## This program is free software; you can redistribute it and/or\n## modify it under the terms of the GNU General Public License\n## as published by the Free Software Foundation; either version 2\n## of the License, or (at your option) any later version.\n##\n## This program is distributed in the hope that it will be useful,\n## but WITHOUT ANY WARRANTY; without even the implied warranty of\n## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n## GNU General Public License for more details.\n\n\n[Sample-Router]\n    enabled = False         # turns metrics collection for this RouterOS device on / off\n\n    hostname = localhost    # RouterOS IP address\n    port = 8728             # RouterOS IP Port\n\n    username = username     # RouterOS user, needs to have 'read' and 'api' permissions\n    password = password\n\n    use_ssl = False                 # enables connection via API-SSL servis\n    no_ssl_certificate = False      # enables API_SSL connect without router SSL certificate\n    ssl_certificate_verify = False  # turns SSL certificate verification on / off\n\n    installed_packages = True       # Installed packages\n    dhcp = True                     # DHCP general metrics\n    dhcp_lease = True               # DHCP lease metrics\n\n    connections = True              # IP connections metrics\n    connection_stats = False        # Open IP connections metrics\n\n    pool = True                     # Pool metrics\n    interface = True                # Interfaces traffic metrics\n\n    firewall = True                 # IPv4 Firewall rules traffic metrics\n    ipv6_firewall = False           # IPv6 Firewall rules traffic metrics\n    ipv6_neighbor = False           # Reachable IPv6 Neighbors\n\n    poe = True                      # POE metrics\n    monitor = True                  # Interface monitor metrics\n    netwatch = True                 # Netwatch metrics\n    public_ip = True                # Public IP metrics\n    route = True                    # Routes metrics\n    wireless = True                 # WLAN general metrics\n    wireless_clients = True         # WLAN clients metrics\n    capsman = True                  # CAPsMAN general metrics\n    capsman_clients = True          # CAPsMAN clients metrics\n\n    user = True                     # Active Users metrics\n    queue = True                    # Queues metrics\n\n    remote_dhcp_entry = None        # An MKTXP entry for remote DHCP info resolution (capsman/wireless)\n\n    use_comments_over_names = True  # when available, forces using comments over the interfaces names\n\n    check_for_updates = False       # check for available ROS updates\n"` |  |
| configmap.config.enabled | bool | `true` |  |
| env | object | See below | environment variables. See more environment variables in the [cyberchef documentation](https://cyberchef.org/docs). |
| env.TZ | string | `"UTC"` | Set the container timezone |
| image.pullPolicy | string | `"Always"` | image pull policy |
| image.repository | string | `"ghcr.io/akpw/mktxp"` | image repository |
| image.tag | string | chart.appVersion | image tag |
| ingress.main.enabled | bool | `false` |  |
| metrics | object | `{"enabled":true,"serviceMonitor":{"interval":"30s","labels":{},"scrapeTimeout":"20s"}}` | ServiceMonitor to tell to prometheus to scrape metrics |
| persistence | object | See values.yaml | Configure persistence settings for the chart under this key. (none required for this chart) |
| service | object | See values.yaml | Configures service settings for the chart. |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
