#!/bin/bash

# Define app names
APPS=("usuarios" "partidas" "chat_partida" "chat_global" "aspecto_carta")

# Print header
echo "====================================="
echo "🚀 Running Django Tests for All Apps"
echo "====================================="

# Loop through each app and run tests
for APP in "${APPS[@]}"; do
    echo ""
    echo "====================================="
    echo "🧪 Running Tests for: $APP"
    echo "====================================="
    
    python manage.py test $APP

    echo ""
    echo "✅ Finished Tests for: $APP"
    echo "====================================="
done

echo ""
echo "🎉 All Tests Completed!"

