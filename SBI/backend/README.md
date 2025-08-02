# Flask Backend for Data Processing

This is a sample Flask backend that processes data from the React frontend.

## Setup Instructions

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the Flask server:**
   ```bash
   python app.py
   ```

3. **The server will start on:**
   - URL: http://localhost:5000
   - Debug mode: Enabled

## API Endpoints

### POST /api/process
Processes data from the frontend form.

**Request Body:**
```json
{
  "field1": "value1",
  "field2": "value2", 
  "field3": "value3",
  "field4": "value4"
}
```

**Response:**
```json
{
  "success": true,
  "result": "Processed result string",
  "raw_data": { ... }
}
```

### GET /api/health
Health check endpoint to verify the server is running.

### GET /
Returns API information and available endpoints.

## Customization

Replace the sample processing logic in the `/api/process` endpoint with your actual business logic:

1. **Data validation** - Add your specific validation rules
2. **Processing logic** - Implement your data processing algorithms
3. **Response format** - Customize the output format as needed
4. **Error handling** - Add specific error handling for your use case

## CORS

CORS is enabled for all routes to allow the React frontend to communicate with this backend.

## Development

- The server runs in debug mode for development
- Changes to the code will automatically restart the server
- Error messages are detailed for debugging

## Production Deployment

For production deployment:
1. Set `debug=False` in `app.run()`
2. Use a production WSGI server like Gunicorn
3. Configure environment variables
4. Set up proper logging
5. Add authentication if needed