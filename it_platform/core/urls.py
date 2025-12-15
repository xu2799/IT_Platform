from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import RegisterView, ChangePasswordView, UserSearchView

router = DefaultRouter()
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'modules', views.ModuleViewSet, basename='module')
router.register(r'lessons', views.LessonViewSet, basename='lesson')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'applications', views.InstructorApplicationViewSet, basename='application')
router.register(r'comments', views.CommentViewSet, basename='comment')
router.register(r'admin/users', views.UserManagementViewSet, basename='admin-users')
router.register(r'notes', views.NoteViewSet, basename='note')
router.register(r'assignments', views.AssignmentViewSet, basename='assignment')
router.register(r'submissions', views.SubmissionViewSet, basename='submission')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'friendships', views.FriendshipViewSet, basename='friendship')

urlpatterns = [
    path('', include(router.urls)),

    path('users/me/', views.UserView.as_view(), name='user-me'),
    path('users/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('users/search/', UserSearchView.as_view(), name='user-search'),

    path('instructor/courses/', views.InstructorCourseListView.as_view(), name='instructor-courses'),
    path('instructor/analytics/', views.InstructorAnalyticsView.as_view(), name='instructor-analytics'),
    path('instructor/qa/', views.InstructorQAView.as_view(), name='instructor-qa'),

    path('courses/<int:course_id>/like/', views.ToggleLikeView.as_view(), name='course-like-toggle'),
    path('courses/<int:course_id>/favorite/', views.ToggleFavoriteView.as_view(), name='course-favorite-toggle'),
    path('favorites/', views.FavoriteCourseListView.as_view(), name='course-favorite-list'),

    path('register/', RegisterView.as_view(), name='register'),
]