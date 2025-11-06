# Salt & Light Backend API

A comprehensive Django REST API for the Salt & Light Christian blogging platform, featuring AI-powered content moderation, user management, and community features.

## 🚀 Features

### Core Functionality
- **User Management**: Custom user model with profile pictures, verification status, and premium subscriptions
- **Content Creation**: Rich post creation with tags, scripture references, and AI moderation
- **Community Features**: Comments, reactions, and prayer requests
- **File Management**: Secure file uploads with AI content moderation
- **Payment Processing**: Donation and subscription management with Stripe integration
- **AI Moderation**: Google Gemini-powered content moderation for posts, comments, and files

### Technical Features
- **RESTful API**: Comprehensive API with Swagger documentation
- **JWT Authentication**: Secure token-based authentication
- **AI Integration**: Google Gemini for content moderation
- **File Uploads**: Secure file handling with size limits and type validation
- **Media Storage**: Supabase-backed image storage for post media
- **Database**: PostgreSQL with optimized queries
- **CORS Support**: Cross-origin resource sharing for frontend integration

## 🛠️ Technology Stack

- **Framework**: Django 4.2.25
- **API**: Django REST Framework 3.14.0
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: PostgreSQL (psycopg2-binary)
- **AI**: Google Generative AI (Gemini)
- **File Handling**: Pillow for image processing
- **Documentation**: drf-yasg (Swagger/OpenAPI)
- **CORS**: django-cors-headers

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Google Gemini API key
- Supabase project with a public storage bucket (use a Service Role key server-side)
- Stripe account (for payments)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd dayLight.build/backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the backend directory:
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=postgresql://username:password@localhost:5432/saltandlight
GEMINI_API_KEY=your-google-gemini-api-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_SECRET_KEY=your-stripe-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-supabase-service-role-or-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key # optional but recommended for server-side uploads
SUPABASE_POST_IMAGE_BUCKET=post-image-storage
```

### 5. Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`

### Key Endpoints

#### Authentication
- `POST /accounts/login/` - User login
- `POST /accounts/register/` - User registration
- `POST /accounts/logout/` - User logout
- `POST /accounts/password/reset/` - Password reset

#### Posts
- `GET /posts/` - List all posts
- `POST /posts/` - Create new post
- `GET /posts/{id}/` - Get specific post
- `PUT /posts/{id}/` - Update post
- `DELETE /posts/{id}/` - Delete post

#### Comments
- `GET /comments/` - List comments
- `POST /comments/` - Create comment
- `GET /comments/{id}/` - Get specific comment

#### Prayer Requests
- `GET /prayer_requests/` - List prayer requests
- `POST /prayer_requests/` - Create prayer request
- `POST /prayer_requests/{id}/pray/` - Add prayer count

#### Files
- `POST /files/` - Upload file
- `GET /files/{id}/` - Get file details

#### Media Uploads
- `POST /api/upload-image/` - Upload a post image to Supabase storage (authenticated)

## 🏗️ Project Structure

```
backend/
├── salt_and_light/          # Main Django project
│   ├── settings/           # Environment-specific settings
│   ├── urls.py            # Main URL configuration
│   └── wsgi.py            # WSGI configuration
├── users/                  # User management app
├── posts/                  # Post management with AI moderation
├── comments/              # Comment system
├── prayer_requests/       # Prayer request functionality
├── files/                 # File upload management
├── payments/              # Payment processing
├── core/                  # Core utilities
├── uploads/               # File storage
└── requirements.txt       # Python dependencies
```

## 🤖 AI Moderation

The platform uses Google Gemini AI for content moderation:

### Features
- **Automatic Moderation**: All posts are automatically moderated before publication
- **Content Analysis**: Detects inappropriate content, hate speech, and spam
- **Feedback System**: Provides detailed feedback on flagged content
- **Multi-language Support**: Works with various languages

### Configuration
Set your `GEMINI_API_KEY` in the environment variables to enable AI moderation.

## 💳 Payment Integration

### Features
- **Donations**: One-time donations with M-Pesa and Stripe support
- **Subscriptions**: Recurring subscription management
- **Multi-currency**: Support for KES (Kenya Shillings) and USD
- **Transaction Tracking**: Complete payment history

### Supported Payment Methods
- M-Pesa (Kenya)
- Stripe (International)

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **CORS Protection**: Configurable cross-origin resource sharing
- **Rate Limiting**: Built-in rate limiting for API endpoints
- **File Validation**: Secure file upload with type and size validation
- **Content Moderation**: AI-powered content filtering

## 🧪 Testing

Run the test suite:
```bash
python manage.py test
```

## 🚀 Deployment

### Production Settings
1. Set `DEBUG=False` in production
2. Configure production database
3. Set up static file serving
4. Configure email settings
5. Set up SSL certificates

### Environment Variables for Production
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=your-production-database-url
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

## 📊 Database Models

### Key Models
- **User**: Extended Django user with profile features
- **Post**: Blog posts with AI moderation
- **Comment**: Post comments with reactions
- **PrayerRequest**: Community prayer requests
- **File**: Uploaded files with moderation
- **Donation**: Payment transactions
- **Subscription**: User subscriptions

## 🔧 Configuration

### Settings Structure
- `base.py`: Common settings
- `dev.py`: Development settings
- `prod.py`: Production settings
- `local.py`: Local development overrides

### Key Settings
- **Database**: PostgreSQL configuration
- **Authentication**: JWT settings
- **File Storage**: Upload configuration
- **AI Integration**: Gemini API settings
- **CORS**: Cross-origin settings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the API documentation

## 🔄 API Versioning

The API uses versioning through URL patterns. Current version: `v1`

## 📈 Performance

- **Database Optimization**: Efficient queries with proper indexing
- **Caching**: Built-in Django caching support
- **File Compression**: Optimized file handling
- **Rate Limiting**: Prevents API abuse

## 🔍 Monitoring

- **Logging**: Comprehensive logging configuration
- **Error Tracking**: Django error handling
- **Performance Metrics**: Built-in Django monitoring

---

**Built with ❤️ for the Christian community**
