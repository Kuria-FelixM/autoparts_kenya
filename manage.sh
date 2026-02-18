#!/bin/bash

################################################################################
# AutoParts Kenya - Backend Production Management Script
# 
# Backend-Only Deployment on Digital Ocean Droplet
#
# Usage:
#   ./manage.sh start         - Start all backend services
#   ./manage.sh stop          - Stop all backend services
#   ./manage.sh logs          - View service logs
#   ./manage.sh backup        - Create database backup
#   ./manage.sh restore FILE  - Restore database backup
#   ./manage.sh status        - Check service status
#   ./manage.sh restart SVC   - Restart specific service
#   ./manage.sh health        - Check system health
################################################################################

set -e

COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="./backups"
LOG_DIR="./logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Utility functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

ensure_dirs() {
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
}

# Commands
start_services() {
    print_info "Starting AutoParts Kenya Backend..."
    ensure_dirs
    docker-compose -f "$COMPOSE_FILE" build
    docker-compose -f "$COMPOSE_FILE" up -d
    print_success "Backend services started"
    sleep 5
    health_check
}

stop_services() {
    print_info "Stopping AutoParts Kenya Backend..."
    docker-compose -f "$COMPOSE_FILE" down
    print_success "Backend services stopped"
}

view_logs() {
    SERVICE="${1:-web}"
    docker-compose -f "$COMPOSE_FILE" logs -f "$SERVICE"
}

backup_database() {
    print_info "Creating database backup..."
    ensure_dirs
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/autoparts_backup_$TIMESTAMP.sql.gz"
    
    docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump \
        -U "${DB_USER}" "${DB_NAME}" | gzip > "$BACKUP_FILE"
    
    print_success "Backup created: $BACKUP_FILE"
    
    # Keep only last 7 days of backups
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
    print_info "Cleaned up old backups (> 7 days)"
}

restore_database() {
    BACKUP_FILE="$1"
    
    if [ -z "$BACKUP_FILE" ]; then
        print_error "Usage: ./manage.sh restore <backup_file>"
        ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null || print_info "No backups found"
        exit 1
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    print_info "Restoring database from: $BACKUP_FILE"
    print_error "⚠ This will overwrite the current database. Continue? (yes/no)"
    read -r CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        print_info "Restore cancelled"
        exit 0
    fi
    
    gunzip < "$BACKUP_FILE" | docker-compose -f "$COMPOSE_FILE" exec -T db psql \
        -U "${DB_USER}" "${DB_NAME}"
    
    print_success "Database restored"
}

check_status() {
    print_info "Backend Service Status:"
    docker-compose -f "$COMPOSE_FILE" ps
}

restart_service() {
    SERVICE="$1"
    
    if [ -z "$SERVICE" ]; then
        print_error "Usage: ./manage.sh restart <service_name>"
        print_info "Available services: web, celery, celery_beat, db, redis"
        exit 1
    fi
    
    print_info "Restarting $SERVICE..."
    docker-compose -f "$COMPOSE_FILE" restart "$SERVICE"
    print_success "$SERVICE restarted"
}

health_check() {
    print_info "Checking backend health..."
    
    # Check backend API
    if curl -sf http://127.0.0.1:8000/api/v1/health/ > /dev/null; then
        print_success "Backend API: Running"
    else
        print_error "Backend API: Not responding"
    fi
    
    # Check database
    if docker-compose -f "$COMPOSE_FILE" exec -T db pg_isready -U postgres > /dev/null 2>&1; then
        print_success "Database: Running"
    else
        print_error "Database: Not responding"
    fi
    
    # Check Redis
    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis: Running"
    else
        print_error "Redis: Not responding"
    fi
    
    # Docker stats
    print_info "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.CPUPerc}}" | \
        grep -E "autoparts|CONTAINER"
}

print_usage() {
    cat << EOF
AutoParts Kenya - Backend Production Management Script

USAGE:
    ./manage.sh <command> [options]

COMMANDS:
    start              Start all backend services
    stop               Stop all backend services
    logs [SERVICE]     View service logs (default: web)
    backup             Create database backup
    restore FILE       Restore database from backup
    status             Show service status
    restart SERVICE    Restart specific service
    health             Check system health
    help               Show this help message

EXAMPLES:
    # Start all backend services
    ./manage.sh start
    
    # View backend API logs
    ./manage.sh logs web
    
    # View Celery worker logs
    ./manage.sh logs celery
    
    # Create backup
    ./manage.sh backup
    
    # Restore from backup
    ./manage.sh restore ./backups/autoparts_backup_20240115_120000.sql.gz
    
    # Check health
    ./manage.sh health
    
    # Restart a service
    ./manage.sh restart celery

AVAILABLE SERVICES:
    - web          Django REST API
    - celery       Async Task Worker
    - celery_beat  Scheduled Tasks
    - db           PostgreSQL Database
    - redis        Redis Cache

BACKEND ONLY DEPLOYMENT NOTES:
    - Frontend is deployed separately (not included)
    - API runs on http://127.0.0.1:8000
    - Nginx routes /api to backend
    - Database at http://127.0.0.1:5432
    - Redis at http://127.0.0.1:6379

For more information, see DEPLOYMENT.md

EOF
}

# Main script
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    logs)
        view_logs "$2"
        ;;
    backup)
        backup_database
        ;;
    restore)
        restore_database "$2"
        ;;
    status)
        check_status
        ;;
    restart)
        restart_service "$2"
        ;;
    health)
        health_check
        ;;
    help|--help|-h|"")
        print_usage
        ;;
    *)
        print_error "Unknown command: $1"
        print_usage
        exit 1
        ;;
esac
