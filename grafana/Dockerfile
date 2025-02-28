FROM grafana/grafana:9.5.1

# Copy provisioning files
COPY provisioning /etc/grafana/provisioning

# Create dashboards directory
RUN mkdir -p /var/lib/grafana/dashboards

# Copy dashboards
COPY dashboards /var/lib/grafana/dashboards

# Set environment variables
ENV GF_SECURITY_ADMIN_PASSWORD=admin
ENV GF_USERS_ALLOW_SIGN_UP=false
ENV GF_INSTALL_PLUGINS=grafana-piechart-panel

# Expose Grafana port
EXPOSE 3000 