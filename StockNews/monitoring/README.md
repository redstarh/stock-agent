# StockNews Monitoring Stack

This directory contains Prometheus and Grafana configurations for monitoring the StockNews backend API.

## Components

- **Prometheus** (port 9090) — Metrics collection and alerting
- **Grafana** (port 3000) — Visualization dashboards

## Quick Start

```bash
# Start all services including monitoring
docker-compose up -d

# Access Grafana dashboard
open http://localhost:3000
# Default login: admin / admin (change via GRAFANA_ADMIN_PASSWORD env var)

# Access Prometheus UI
open http://localhost:9090
```

## Directory Structure

```
monitoring/
├── prometheus/
│   ├── prometheus.yml        # Prometheus config
│   └── alert_rules.yml       # Alert rules
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/      # Auto-configured datasources
│   │   └── dashboards/       # Dashboard provisioning config
│   └── dashboards/
│       └── stocknews-overview.json  # Main dashboard
└── README.md
```

## Metrics Collected

The backend exposes Prometheus metrics at `http://localhost:8001/metrics` using `prometheus-fastapi-instrumentator`.

Standard metrics:
- `http_requests_total` — Request count by handler, method, status
- `http_request_duration_seconds` — Request latency histogram
- `http_requests_inprogress` — Current in-flight requests
- `process_resident_memory_bytes` — Process memory usage

## Alert Rules

| Alert | Threshold | Duration | Severity |
|-------|-----------|----------|----------|
| **HighErrorRate** | 5xx rate > 5% | 5 min | critical |
| **HighLatency** | P95 > 2s | 5 min | warning |
| **ServiceDown** | Target unreachable | 1 min | critical |
| **HighMemoryUsage** | Memory > 512MB | 5 min | warning |

## Grafana Dashboards

### StockNews Overview (UID: stocknews-overview)

Panels:
1. **Request Rate** — Requests/sec by endpoint
2. **Error Rate** — 5xx error percentage
3. **In-Progress Requests** — Current concurrent requests
4. **Error Rate Timeline** — 5xx trend over time
5. **Latency Percentiles** — P50/P95/P99 response times
6. **Top Endpoints by Latency** — Slowest endpoints table
7. **Status Code Distribution** — Response status breakdown

## Data Retention

- **Prometheus:** 15 days (configurable in docker-compose.yml)
- **Grafana:** Persistent via Docker volume

## Configuration

### Environment Variables

Add to `.env`:
```bash
# Grafana admin password (default: admin)
GRAFANA_ADMIN_PASSWORD=your-secure-password
```

### Prometheus Targets

Edit `prometheus/prometheus.yml` to add more scrape targets:
```yaml
scrape_configs:
  - job_name: "stocknews-backend"
    static_configs:
      - targets: ["backend:8001"]
```

### Alert Notification

To configure alert notifications (Slack, email, PagerDuty):
1. Add Alertmanager service to docker-compose.yml
2. Configure alertmanager.yml with notification channels
3. Update prometheus.yml to reference Alertmanager

## Troubleshooting

### Prometheus not scraping metrics
```bash
# Check backend /metrics endpoint is accessible
curl http://localhost:8001/metrics

# Check Prometheus targets status
open http://localhost:9090/targets
```

### Grafana dashboard not loading
```bash
# Check Grafana logs
docker-compose logs grafana

# Verify provisioning files are mounted
docker exec -it stocknews-grafana-1 ls -la /etc/grafana/provisioning
```

### No data in dashboard
- Ensure backend service is running and healthy
- Check Prometheus is successfully scraping (Status > Targets)
- Verify datasource is configured (Configuration > Data Sources)

## Production Recommendations

1. **Secure Grafana** — Change default admin password immediately
2. **Enable HTTPS** — Use reverse proxy (nginx/Traefik) with TLS
3. **Alert Routing** — Configure Alertmanager for critical alerts
4. **Increase Retention** — Adjust `--storage.tsdb.retention.time` for longer history
5. **Resource Limits** — Add memory/CPU limits in docker-compose.yml
6. **Backup Dashboards** — Export dashboards and store in version control
7. **External Storage** — Use remote storage for long-term metrics (Thanos, Cortex)
