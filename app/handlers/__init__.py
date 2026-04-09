from app.handlers.admin import router as admin_router
from app.handlers.inline import router as inline_router
from app.handlers.movie_upload import router as upload_router
from app.handlers.user import router as user_router

all_routers = [admin_router, upload_router, user_router, inline_router]
