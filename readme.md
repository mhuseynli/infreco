# Documentation for Event-Driven Recommender System

## Overview
This document provides a comprehensive overview of the Event-Driven Recommender System developed for webshops. The system's core functionality includes the registration of webshops, capturing user interactions as events, processing these events via RabbitMQ for real-time data handling, and providing a recommender engine interface for personalized user recommendations.

### Key Components
1. **Webshop Registration and Management**: Webshops can register, update their information, and be deleted from the system.
2. **Event Handling**: Capturing user interaction events (clicks, views, etc.) from webshops.
3. **RabbitMQ Integration**: Utilizing RabbitMQ for queuing and processing events asynchronously.
4. **Recommender Engine Interface**: An abstract interface for integrating various recommender algorithms.
5. **Data Models**: MongoDB data models for webshops, users, items, and events.

## Installation and Setup
1. **MongoDB**: Ensure MongoDB is installed and running.
2. **RabbitMQ**: Install and configure RabbitMQ. Ensure the service is running.
3. **Python Environment**: The system is developed in Python. Ensure Python and necessary libraries (`pika`, `Django`, `djangorestframework`) are installed.

## Usage
### Webshop Registration
Webshops can register using the `/webshops/register/` endpoint. Required data includes email, webshop name, and password.

### Event Capturing
Webshops send user interaction events to `/events/` with the `X-API-KEY` header for authentication. The event data should include user and item details along with the event type and timestamp.

### Event Processing with RabbitMQ
Events sent to the `/events/` endpoint are queued in RabbitMQ and processed asynchronously. The processing logic includes user and item data updates in MongoDB.

### Recommender Engine Interface
The abstract interface `RecommenderInterface` in `recommender_interface.py` allows integration of various recommendation algorithms. It includes methods for training, generating recommendations, and updating models.

## API Endpoints
- `POST /webshops/register/`: Register a new webshop.
- `GET /webshops/`: Retrieve webshop details (requires `X-API-KEY`).
- `PUT /webshops/`: Update webshop details (requires `X-API-KEY`).
- `DELETE /webshops/`: Delete a webshop and related data (requires `X-API-KEY`).
- `POST /events/`: Send user interaction events for processing.
- `POST /train/`: Initiate training of the recommender model (requires `X-API-KEY`).
- `GET /recommend/{user_id}/`: Get recommendations for a user (requires `X-API-KEY`).

## Data Models
### Webshop
- Email
- Name
- Password (hashed)

### User
- Webshop ID
- External ID
- Attributes

### Item
- Webshop ID
- External ID
- Attributes

### Event
- Webshop ID
- User ID
- Item ID
- Event Type
- Timestamp

## RabbitMQ Consumer
The `consume.py` script listens for new messages in the `webshop_events` queue and processes them by updating user and item information and storing the events in MongoDB.

## Recommendations
The `RecommendationView` handles requests for user recommendations. It utilizes the recommender algorithm defined in `MyRecommender`, which adheres to the `RecommenderInterface`.

## Security
- Webshop API key authentication.
- Passwords are stored in a hashed format.

## Future Enhancements
- Implementation of various recommender algorithms.
- Dashboard for webshops to manage their data and view analytics.
- Enhanced error handling and logging mechanisms.

---

This documentation serves as a guide for developers and users interacting with the Event-Driven Recommender System. Further details can be found in the codebase and additional documentation.