from django.http import JsonResponse
from core.database import db
from core.utils.logger import get_logger

logger = get_logger()


class APIKeyMiddleware:
    """
    Middleware to validate the presence and validity of the X-API-KEY header
    by checking the existence of the corresponding webshop in the database.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info(f"Processing request path: {request.path}")

        # Define paths that require API key validation
        protected_paths = [
            '/webshops/',
            '/users/',
            '/events/',
            '/items/',
            '/recommender/'
        ]

        # Define paths that should be excluded from API key validation
        public_paths = ['/webshops/register/']

        # Skip validation for public paths
        if any(request.path.startswith(path) for path in public_paths):
            return self.get_response(request)

        # Validate API key for protected paths
        if any(request.path.startswith(path) for path in protected_paths):
            print(request.headers.get('X-API-KEY'))
            api_key = request.headers.get('X-API-KEY')
            if not api_key:
                return JsonResponse(
                    {"detail": "API key required."},
                    status=401
                )

            # Check if the API key corresponds to a valid webshop
            webshop = db.webshops.find_one({"id": api_key})
            if not webshop:
                return JsonResponse(
                    {"detail": "Invalid API key."},
                    status=401
                )

            # Attach the webshop object to the request for views to use
            request.webshop = webshop

        return self.get_response(request)
