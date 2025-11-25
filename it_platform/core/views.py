from rest_framework import viewsets, permissions, status, filters, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, BasePermission, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Count, Sum, F
from .models import (
    Course, CustomUser, Module, Lesson, Enrollment,
    Category, InstructorApplication, Comment, Note, Assignment, Submission
)
from .serializers import (
    CourseDetailSerializer, CourseListSerializer, UserSerializer,
    ModuleSerializer, LessonSerializer, CategorySerializer,
    InstructorApplicationSerializer, CommentSerializer,
    ChangePasswordSerializer, NoteSerializer, AssignmentSerializer, SubmissionSerializer
)
from .tasks import process_video_upload


# --- 权限控制 ---
class IsInstructorOrAdmin(BasePermission):
    """仅允许讲师或管理员操作"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in [CustomUser.ROLE_INSTRUCTOR, CustomUser.ROLE_ADMIN]


# --- 1. 课程视图 ---
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('-created_at')
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'instructor__username']

    def get_queryset(self):
        # 预加载关联数据
        queryset = Course.objects.all().order_by('-created_at').select_related(
            'instructor', 'category'
        ).prefetch_related('likes', 'enrollments')

        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        if self.action == 'popular':
            queryset = queryset.annotate(view_count_annotated=F('view_count')).order_by('-view_count_annotated')
        if self.action == 'top_liked':
            queryset = queryset.annotate(like_count_annotated=Count('likes')).order_by('-like_count_annotated')

        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'popular', 'newest', 'top_liked', 'record_view']:
            return [permissions.AllowAny()]
        return [IsInstructorOrAdmin()]

    def get_serializer_class(self):
        if self.action in ['list', 'popular', 'newest', 'top_liked']:
            return CourseListSerializer
        return CourseDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        if request.user.role not in [CustomUser.ROLE_INSTRUCTOR, CustomUser.ROLE_ADMIN]:
            return Response({"detail": "权限不足"}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def popular(self, request):
        popular_courses = Course.objects.order_by('-view_count')[:3]
        serializer = self.get_serializer(popular_courses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def newest(self, request):
        newest_courses = Course.objects.order_by('-created_at')[:3]
        serializer = self.get_serializer(newest_courses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def top_liked(self, request):
        top_liked = Course.objects.annotate(like_count=Count('likes')).order_by('-like_count')[:3]
        serializer = self.get_serializer(top_liked, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def record_view(self, request, pk=None):
        try:
            Course.objects.filter(pk=pk).update(view_count=F('view_count') + 1)
            return Response({'status': 'view recorded'}, status=status.HTTP_200_OK)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)


# --- 2. 分类视图 ---
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.annotate(total_likes=Count('courses__likes')).order_by('-total_likes')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


# --- 3. 章节视图 ---
class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticatedOrReadOnly()]
        return [IsInstructorOrAdmin()]


# --- 4. 课时视图 ---
class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsInstructorOrAdmin()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        lesson = serializer.save(
            lesson_type=Lesson.LESSON_TEXT,
            content="视频正在处理中..."
        )
        if lesson.video_mp4_file:
            process_video_upload.delay(lesson.id, lesson.video_mp4_file.path)


# --- 5. 讲师申请视图 ---
class InstructorApplicationViewSet(viewsets.ModelViewSet):
    queryset = InstructorApplication.objects.all().order_by('-created_at')
    serializer_class = InstructorApplicationSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        if self.request.user.is_staff:
            return InstructorApplication.objects.all().order_by('-created_at')
        return InstructorApplication.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('status')
        if new_status == InstructorApplication.STATUS_APPROVED:
            instance.user.role = CustomUser.ROLE_INSTRUCTOR
            instance.user.save()
        return super().update(request, *args, **kwargs)


# --- 6. 讲师课程列表 ---
class InstructorCourseListView(ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [IsInstructorOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Course.objects.all().order_by('-created_at')
        return Course.objects.filter(instructor=user).order_by('-created_at')


# --- 7. 用户个人信息视图 ---
class UserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user


# --- 8. 修改密码视图 ---
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["旧密码不正确"]}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.data.get("new_password"))
            user.save()
            return Response({"detail": "密码修改成功"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- 9. 评论视图 ---
class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['content', 'user__username', 'lesson__title']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Comment.objects.all().select_related('user', 'lesson').order_by('-created_at')

        queryset = Comment.objects.select_related(
            'user', 'reply_to_user'
        ).prefetch_related(
            'replies__user', 'replies__reply_to_user'
        ).filter(parent__isnull=True).order_by('-created_at')

        lesson_id = self.request.query_params.get('lesson_id')
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        return queryset

    def perform_create(self, serializer):
        parent = serializer.validated_data.get('parent')
        reply_to_user = serializer.validated_data.get('reply_to_user')

        if parent:
            if parent.parent_id is not None:
                parent = parent.parent
            if not reply_to_user:
                reply_to_user = parent.user

        serializer.save(user=self.request.user, parent=parent, reply_to_user=reply_to_user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        instance = Comment.objects.get(pk=response.data['id'])
        return Response(CommentSerializer(instance, context={'request': request}).data, status=status.HTTP_201_CREATED)


# --- 10. 点赞/收藏 ---
class ToggleLikeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
            user = request.user
            if user in course.likes.all():
                course.likes.remove(user)
                liked = False
            else:
                course.likes.add(user)
                liked = True
            return Response({"liked": liked, "like_count": course.likes.count()})
        except Course.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ToggleFavoriteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
            user = request.user
            if course in user.favorited_courses.all():
                user.favorited_courses.remove(course)
                favorited = False
            else:
                user.favorited_courses.add(course)
                favorited = True
            return Response({
                "favorited": favorited,
                "favorites_list": list(user.favorited_courses.values_list('id', flat=True))
            })
        except Course.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class FavoriteCourseListView(ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.favorited_courses.all().order_by('-created_at').prefetch_related('likes')


# --- 11. 注册 ---
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        role = request.data.get('role', CustomUser.ROLE_STUDENT)

        if not username or not password:
            return Response({'detail': '用户名和密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        if CustomUser.objects.filter(username=username).exists():
            return Response({'detail': '用户名已存在'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.create_user(username=username, password=password, role=role)
            return Response({'detail': '注册成功'}, status=status.HTTP_201_CREATED)
        except Exception:
            return Response({'detail': '注册失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- 12. 用户管理视图 (管理员) ---
class UserManagementViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'nickname']


# --- 13. 笔记视图 ---
class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Note.objects.filter(user=self.request.user).order_by('-created_at')
        lesson_id = self.request.query_params.get('lesson_id')
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# --- 14. 作业管理视图 (新增) ---
class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [IsInstructorOrAdmin]

    def get_queryset(self):
        return Assignment.objects.filter(course__instructor=self.request.user).annotate(
            submission_count=Count('submissions')
        ).order_by('-created_at')


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in [CustomUser.ROLE_INSTRUCTOR, CustomUser.ROLE_ADMIN]:
            return Submission.objects.filter(assignment__course__instructor=user).order_by('-submitted_at')
        return Submission.objects.filter(student=user).order_by('-submitted_at')

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)


# --- 15. 讲师数据看板接口 (新增) ---
class InstructorAnalyticsView(APIView):
    permission_classes = [IsInstructorOrAdmin]

    def get(self, request):
        user = request.user
        courses = Course.objects.filter(instructor=user)

        total_students = Enrollment.objects.filter(course__in=courses).values('student').distinct().count()
        total_views = courses.aggregate(Sum('view_count'))['view_count__sum'] or 0
        total_likes_real = 0
        for c in courses:
            total_likes_real += c.likes.count()

        course_performance = courses.annotate(
            likes_num=Count('likes'),
            students_num=Count('enrollments')
        ).values('title', 'view_count', 'likes_num', 'students_num').order_by('-view_count')[:5]

        return Response({
            "total_students": total_students,
            "total_views": total_views,
            "total_likes": total_likes_real,
            "course_data": list(course_performance)
        })


# --- 16. 答疑控制台接口 (新增) ---
class InstructorQAView(ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsInstructorOrAdmin]

    def get_queryset(self):
        return Comment.objects.filter(
            lesson__module__course__instructor=self.request.user
        ).exclude(user=self.request.user).order_by('-created_at')