#!/bin/bash

# Admissions Genie - Installation and Testing Script
# This script sets up the environment and runs the application locally

echo "🏥 Admissions Genie - Installation & Testing Script"
echo "===================================================="
echo ""

# Check Python version
echo "1️⃣  Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.9+"
    exit 1
fi
echo "✅ Python 3 found"
echo ""

# Create virtual environment
echo "2️⃣  Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "3️⃣  Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "4️⃣  Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check for Tesseract OCR
echo "5️⃣  Checking for Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract OCR found"
    tesseract --version | head -n 1
else
    echo "⚠️  Tesseract OCR not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install tesseract
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt-get update && sudo apt-get install -y tesseract-ocr
    else
        echo "❌ Please install Tesseract manually for your OS"
        echo "   macOS: brew install tesseract"
        echo "   Ubuntu: sudo apt-get install tesseract-ocr"
        exit 1
    fi
fi
echo ""

# Create .env file if it doesn't exist
echo "6️⃣  Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ .env file created from .env.example"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and add your Azure OpenAI credentials:"
    echo "   - AZURE_OPENAI_API_KEY"
    echo "   - AZURE_OPENAI_ENDPOINT"
    echo "   - AZURE_OPENAI_DEPLOYMENT_NAME"
    echo ""
    read -p "Press Enter after you've updated the .env file..."
else
    echo "✅ .env file already exists"
fi
echo ""

# Initialize database
echo "7️⃣  Initializing database..."
python3 -c "from config.database import init_db; init_db()"
echo "✅ Database initialized"
echo ""

# Seed database with sample data
echo "8️⃣  Seeding database with sample data..."
python3 seed_database.py
echo "✅ Database seeded"
echo ""

# Create necessary directories
echo "9️⃣  Creating necessary directories..."
mkdir -p logs
mkdir -p data/uploads
touch data/uploads/.gitkeep
echo "✅ Directories created"
echo ""

echo "🎉 Installation complete!"
echo ""
echo "======================================================"
echo "📋 Next Steps:"
echo "======================================================"
echo ""
echo "1. Make sure you've added your Azure OpenAI credentials to .env"
echo ""
echo "2. Start the application:"
echo "   python3 app.py"
echo ""
echo "3. Open your browser to:"
echo "   http://localhost:5000"
echo ""
echo "4. Login with:"
echo "   Admin: admin@admissionsgenie.com / admin123"
echo "   User:  user@admissionsgenie.com / user123"
echo ""
echo "======================================================"
echo ""

# Ask if user wants to start the app now
read -p "Would you like to start the application now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting Admissions Genie..."
    echo ""
    python3 app.py
fi
