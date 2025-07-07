#!/bin/bash

echo "Starting deployment with environment variables..."

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file with your environment variables"
    exit 1
fi

# Generate unique deploy ID for session management
deploy_id=$(date +"%Y%m%d-%H%M%S")
echo "Generated deploy ID: $deploy_id"

# Читаем переменные из .env файла и формируем строку для --set-env-vars
env_vars="DEPLOY_ID=$deploy_id"

while IFS='=' read -r key value; do
    # Пропускаем комментарии и пустые строки
    if [[ ! $key =~ ^# ]] && [[ -n $key ]]; then
        # Убираем кавычки если есть
        value=$(echo $value | sed 's/^"//;s/"$//;s/^'"'"'//;s/'"'"'$//')
        env_vars="$env_vars,$key=$value"
        echo "Added env var: $key"
    fi
done < .env

echo "Deploying to Cloud Run with environment variables..."
echo "Environment variables: $env_vars"

# Deploy to Cloud Run
gcloud run deploy auraflora-bot \
    --source . \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --set-env-vars "$env_vars"

if [ $? -eq 0 ]; then
    echo "Deploy completed successfully!"
    echo "Deploy ID: $deploy_id"
    echo "Service URL: https://auraflora-bot-75152239022-as.a.run.app"
else
    echo "Deploy failed!"
    exit 1
fi 