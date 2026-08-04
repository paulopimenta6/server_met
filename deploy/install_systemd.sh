#!/bin/bash
# Install systemd services for Server MET v2.0
# Run with sudo: sudo ./install_systemd.sh

set -e

SERVICE_DIR="/etc/systemd/system"
PROJECT_DIR="/home/paulo/Documentos/meus_codigos/server_met"
DEPLOY_DIR="$PROJECT_DIR/deploy/systemd"

echo "📦 Instalando serviços systemd para Server MET v2.0"

# Copy service files
cp "$DEPLOY_DIR/server-met-api.service" "$SERVICE_DIR/"
cp "$DEPLOY_DIR/server-met-scheduler.service" "$SERVICE_DIR/"
cp "$DEPLOY_DIR/server-met-pipeline.service" "$SERVICE_DIR/"
cp "$DEPLOY_DIR/server-met-pipeline.timer" "$SERVICE_DIR/"

echo "✅ Arquivos de serviço copiados para $SERVICE_DIR"

# Reload systemd
systemctl daemon-reload
echo "✅ systemd reload completo"

# Enable services
systemctl enable server-met-api.service
systemctl enable server-met-scheduler.service
# Choose one: scheduler (APScheduler) OR timer (systemd cron)
# systemctl enable server-met-pipeline.timer

echo "✅ Serviços habilitados"
echo ""
echo "Para iniciar:"
echo "  sudo systemctl start server-met-api"
echo "  sudo systemctl start server-met-scheduler"
echo ""
echo "Para ver logs:"
echo "  journalctl -u server-met-api -f"
echo "  journalctl -u server-met-scheduler -f"
echo ""
echo "Para usar timer do systemd em vez do APScheduler:"
echo "  sudo systemctl enable --now server-met-pipeline.timer"
echo "  sudo systemctl disable --now server-met-scheduler"