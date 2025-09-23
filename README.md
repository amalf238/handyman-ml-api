# Handyman ML API

AI-powered worker recommendation system for home services. This API uses machine learning to match user queries with the most suitable handyman workers based on service type, location, and requirements.

## Features

- **AI Service Classification**: Uses neural networks to understand service requirements
- **Location Detection**: Semantic location matching for Sri Lankan cities
- **Worker Scoring**: AI-powered ranking based on service match, distance, and quality
- **REST API**: Simple HTTP endpoints for integration
- **Real-time Processing**: Fast response times with pre-trained models

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/handyman-ml-api.git
   cd handyman-ml-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add your dataset**
   - Place `handyman_database_3000.json` in the `data/` folder

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Test the API**
   ```bash
   curl -X POST http://localhost:5000/api/search-workers \
     -H "Content-Type: application/json" \
     -d '{"query": "washing machine repair in colombo"}'
   ```

### Railway Deployment

1. **Create Railway account** at [railway.app](https://railway.app)

2. **Connect your GitHub repository**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `handyman-ml-api` repository

3. **Configure environment** (if needed)
   - Set `PORT` (Railway sets this automatically)
   - Set `DEBUG=false` for production

4. **Deploy**
   - Railway will automatically build and deploy your API
   - You'll get a URL like: `https://your-app.railway.app`

## API Endpoints

### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "ml_system_ready": true
}
```

### Search Workers
```http
POST /api/search-workers
```

Request Body:
```json
{
  "query": "washing machine repair in colombo",
  "max_results": 5
}
```

Response:
```json
{
  "success": true,
  "query": "washing machine repair in colombo",
  "total_results": 5,
  "workers": [
    {
      "id": "HM_1234",
      "name": "John Silva",
      "service_type": "Appliance Repair",
      "rating": 4.8,
      "experience_years": 5,
      "location": {
        "city": "Colombo",
        "latitude": 6.9271,
        "longitude": 79.8612
      },
      "pricing": {
        "daily_wage": 15000,
        "half_day_rate": 9000
      },
      "contact": {
        "phone": "+94771234567",
        "whatsapp_available": true
      },
      "ai_score": 95.2,
      "distance_km": 2.1,
      "service_confidence": 94.6
    }
  ]
}
```

### Analyze Image Description
```http
POST /api/analyze-image-description
```

Request Body:
```json
{
  "description": "The washing machine is leaking water",
  "location": "colombo",
  "max_results": 3
}
```

## Project Structure

```
handyman-ml-api/
├── data/
│   └── handyman_database_3000.json    # Worker dataset
├── src/
│   ├── __init__.py
│   ├── api_server.py                  # Flask API server
│   ├── ml_model.py                    # ML model implementation
│   └── utils.py                       # Utility functions
├── models/
│   └── trained_models/                # Saved model files
├── requirements.txt                   # Python dependencies
├── Dockerfile                         # Docker configuration
├── railway.json                       # Railway deployment config
├── run.py                            # Application entry point
└── README.md                         # This file
```

## Technology Stack

- **Python 3.9+**: Core runtime
- **Flask**: Web framework
- **Sentence Transformers**: Text embedding
- **Scikit-learn**: Machine learning
- **Pandas/NumPy**: Data processing
- **GeoPy**: Geographic calculations

## Machine Learning Pipeline

1. **Text Processing**: Convert user queries to semantic embeddings
2. **Service Classification**: Neural network predicts service type
3. **Location Extraction**: Semantic similarity matching for locations
4. **Worker Filtering**: Filter database by predicted service types
5. **Scoring Algorithm**: Combine service confidence, distance, and quality
6. **Ranking**: Sort and return top recommendations

## Deployment Options

### Railway (Recommended)
- **Cost**: ~$5-10/month for basic usage
- **Features**: Auto-scaling, SSL, custom domains
- **Setup**: Connect GitHub repo, automatic deploys

### Render
- **Cost**: Free tier available, ~$7/month for production
- **Features**: Auto-scaling, SSL, PostgreSQL add-on
- **Setup**: Similar to Railway

### Heroku
- **Cost**: ~$7/month (no free tier)
- **Features**: Add-ons ecosystem
- **Setup**: Git-based deployment

## Cost Estimation

### Railway Pricing:
- **Starter**: $5/month - Good for development
- **Pro**: $20/month - Production ready
- **Usage-based**: ~$0.000463 per GB-hour

### Expected Monthly Costs:
- **Light usage** (< 1000 requests/day): $5-10
- **Medium usage** (< 10k requests/day): $15-25
- **Heavy usage** (> 100k requests/day): $50-100

## Flutter Integration

Update your Flutter app's `ai_chat_service.dart`:

```dart
// Replace with your deployed URL
static const String _mlApiBaseUrl = 'https://your-app.railway.app';

// Use the getWorkerRecommendations method
final workers = await aiChatService.getWorkerRecommendations(
  query: imageDescription,
  maxResults: 5,
);
```

## Environment Variables

```bash
PORT=5000                    # Server port (set by Railway)
DEBUG=false                  # Debug mode
PYTHONPATH=/app/src         # Python module path
```

## Error Handling

The API returns standardized error responses:

```json
{
  "success": false,
  "error": "Error message here",
  "workers": [],
  "total_results": 0
}
```

## Performance

- **Response Time**: < 500ms for typical queries
- **Throughput**: ~100 requests/second on basic plan
- **Model Size**: ~200MB (includes sentence transformer)
- **Memory Usage**: ~1GB RAM

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -m 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

## License

MIT License - see LICENSE file for details

## Support

- Create an issue on GitHub for bugs
- Check the health endpoint: `/health`
- Monitor logs in Railway dashboard