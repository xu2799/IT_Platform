import json
from rest_framework import viewsets, permissions, status, filters, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, BasePermission, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
from .models import (
    Course, CustomUser, Module, Lesson, Enrollment,
    Category, InstructorApplication, Comment, Note, Assignment, Submission, Message, Friendship,
    Banner, Announcement, VideoProgress, UserPoints, PointRecord, Badge, UserBadge
)
from .serializers import (
    CourseDetailSerializer, CourseListSerializer, UserSerializer,
    ModuleSerializer, LessonSerializer, CategorySerializer,
    InstructorApplicationSerializer, CommentSerializer,
    ChangePasswordSerializer, NoteSerializer, AssignmentSerializer, SubmissionSerializer,
    AdminUserSerializer, MessageSerializer, FriendshipSerializer,
    BannerSerializer, AnnouncementSerializer, VideoProgressSerializer,
    UserPointsSerializer, PointRecordSerializer, BadgeSerializer, UserBadgeSerializer
)
from .tasks import process_video_upload


# --- 权限控制 ---
class IsInstructorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in [CustomUser.ROLE_INSTRUCTOR, CustomUser.ROLE_ADMIN]


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == CustomUser.ROLE_ADMIN


class IsCourseOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.instructor == request.user or request.user.role == CustomUser.ROLE_ADMIN


# --- 1. 课程视图 ---
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('-created_at')
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'instructor__username']

    def get_queryset(self):
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

        if self.action == 'create':
            return [IsInstructorOrAdmin()]

        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsCourseOwner()]

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

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

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

    # 添加缓存 - 分类列表15分钟缓存
    def list(self, request, *args, **kwargs):
        from django.core.cache import cache
        cache_key = 'categories_list'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return Response(cached_data)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, 60 * 15)  # 15分钟
        return response


# --- 3. 章节视图 ---
class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.select_related('course').prefetch_related('lessons')
    serializer_class = ModuleSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticatedOrReadOnly()]
        return [IsInstructorOrAdmin()]


# --- 4. 课时视图 ---
class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.select_related('module__course')
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'bulk_delete']:
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

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"detail": "未选择任何课时"}, status=status.HTTP_400_BAD_REQUEST)
        lessons = Lesson.objects.filter(id__in=ids)
        deleted_count = 0
        for lesson in lessons:
            if request.user.role == CustomUser.ROLE_ADMIN or lesson.module.course.instructor == request.user:
                lesson.delete()
                deleted_count += 1
        return Response({"status": "success", "deleted": deleted_count})


# --- 5. 讲师申请视图 ---
class InstructorApplicationViewSet(viewsets.ModelViewSet):
    queryset = InstructorApplication.objects.all().order_by('-created_at')
    serializer_class = InstructorApplicationSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role == CustomUser.ROLE_ADMIN:
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
            return Course.objects.select_related('instructor', 'category').prefetch_related('likes').order_by('-created_at')
        return Course.objects.filter(instructor=user).select_related('instructor', 'category').prefetch_related('likes').order_by('-created_at')


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


# --- 9. 评论视图 (【核心修复】) ---
class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['content', 'user__username', 'lesson__title']

    def get_queryset(self):
        # 1. 确定基础查询集
        if self.request.user.is_authenticated and (
                self.request.user.is_staff or self.request.user.role == CustomUser.ROLE_ADMIN):
            # 管理员可以看到所有（用于审核管理）
            queryset = Comment.objects.all().select_related('user', 'lesson').order_by('-created_at')
        else:
            # 普通用户只返回“顶级评论”，子回复通过 parent 字段嵌套在序列化器中返回
            queryset = Comment.objects.select_related(
                'user', 'reply_to_user'
            ).prefetch_related(
                'replies__user', 'replies__reply_to_user'
            ).filter(parent__isnull=True).order_by('-created_at')

        # 2. 【关键】应用过滤：无论是否管理员，都必须响应 lesson_id 参数
        lesson_id = self.request.query_params.get('lesson_id')
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)

        # 3. 支持按课程ID筛选
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(lesson__module__course_id=course_id)

        # 4. 支持按分类筛选
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(lesson__module__course__category__slug=category_slug)

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
    permission_classes = [IsAdminRole]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'nickname']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'create']:
            return AdminUserSerializer
        return UserSerializer

    # 【新增】批量删除接口
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"detail": "未选择任何用户"}, status=status.HTTP_400_BAD_REQUEST)

        # 安全过滤：禁止删除自己
        users = CustomUser.objects.filter(id__in=ids).exclude(id=request.user.id)
        deleted_count, _ = users.delete()

        return Response({"status": "success", "deleted": deleted_count})


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


# --- 14. 作业管理视图 ---
class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [IsInstructorOrAdmin]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == CustomUser.ROLE_ADMIN:
            qs = Assignment.objects.annotate(submission_count=Count('submissions')).order_by('-created_at')
        else:
            qs = Assignment.objects.filter(course__instructor=user).annotate(
                submission_count=Count('submissions')).order_by('-created_at')

        course_id = self.request.query_params.get('course_id')
        if course_id:
            qs = qs.filter(course_id=course_id)
        
        # 支持按分类筛选
        category_slug = self.request.query_params.get('category')
        if category_slug:
            qs = qs.filter(course__category__slug=category_slug)
        
        return qs


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == CustomUser.ROLE_ADMIN:
            qs = Submission.objects.all().order_by('-submitted_at')
        elif user.role == CustomUser.ROLE_INSTRUCTOR:
            qs = Submission.objects.filter(assignment__course__instructor=user).order_by('-submitted_at')
        else:
            qs = Submission.objects.filter(student=user).order_by('-submitted_at')

        course_id = self.request.query_params.get('course_id')
        if course_id:
            qs = qs.filter(assignment__course_id=course_id)
        
        # 支持按分类筛选
        category_slug = self.request.query_params.get('category')
        if category_slug:
            qs = qs.filter(assignment__course__category__slug=category_slug)
        
        return qs

    def perform_create(self, serializer):
        assignment = serializer.validated_data.get('assignment')
        user_content_raw = serializer.validated_data.get('content', '')
        status_to_save = Submission.STATUS_PENDING
        grade_to_save = None
        feedback_to_save = ""

        if assignment.assignment_type == Assignment.TYPE_CHOICE and assignment.quiz_data:
            try:
                quiz_list = json.loads(assignment.quiz_data)
                user_answers = json.loads(user_content_raw)
                correct_count = 0
                total_count = len(quiz_list)
                if total_count > 0:
                    for idx, question in enumerate(quiz_list):
                        correct_key = question.get('answer', '').upper()
                        student_key = user_answers.get(str(idx), '').upper()
                        if correct_key and student_key == correct_key:
                            correct_count += 1
                    grade_to_save = int((correct_count / total_count) * 100)
                    status_to_save = Submission.STATUS_PASSED if grade_to_save >= 60 else Submission.STATUS_REJECTED
                    feedback_to_save = f"系统自动批改：共 {total_count} 题，答对 {correct_count} 题。"
                else:
                    feedback_to_save = "系统错误：题目数据为空"
            except Exception as e:
                print(f"Auto-grade error: {e}")
                feedback_to_save = "自动批改出错，请联系讲师人工审核。"

        serializer.save(
            student=self.request.user,
            status=status_to_save,
            grade=grade_to_save,
            feedback=feedback_to_save
        )


# --- 15. 讲师数据看板接口 ---
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


# --- 16. 答疑控制台接口 ---
class InstructorQAView(ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsInstructorOrAdmin]

    def get_queryset(self):
        return Comment.objects.filter(
            lesson__module__course__instructor=self.request.user
        ).exclude(user=self.request.user).order_by('-created_at')


# --- 17. 站内信视图 ---
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        receiver_username = request.data.get('receiver_username')
        sender = request.user
        try:
            receiver = CustomUser.objects.get(username=receiver_username)
        except CustomUser.DoesNotExist:
            return Response({"detail": "用户不存在"}, status=status.HTTP_400_BAD_REQUEST)

        is_friend = Friendship.objects.filter(
            (Q(from_user=sender, to_user=receiver) | Q(from_user=receiver, to_user=sender)),
            status=Friendship.STATUS_ACCEPTED
        ).exists()

        if not is_friend:
            return Response({"detail": "你们不是好友，无法发送消息"}, status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def conversations(self, request):
        user = request.user
        sent_ids = Message.objects.filter(sender=user).values_list('receiver', flat=True)
        received_ids = Message.objects.filter(receiver=user).values_list('sender', flat=True)
        contact_ids = set(list(sent_ids) + list(received_ids))
        contacts = CustomUser.objects.filter(id__in=contact_ids)
        serializer = UserSerializer(contacts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        target_id = request.query_params.get('target_id')
        if not target_id: return Response([])
        user = request.user
        msgs = Message.objects.filter(
            (Q(sender=user) & Q(receiver_id=target_id)) |
            (Q(sender_id=target_id) & Q(receiver=user))
        ).order_by('created_at')
        Message.objects.filter(sender_id=target_id, receiver=user, is_read=False).update(is_read=True)
        serializer = self.get_serializer(msgs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def inbox(self, request):
        msgs = Message.objects.filter(receiver=request.user).order_by('-created_at')
        page = self.paginate_queryset(msgs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(msgs, many=True).data)

    @action(detail=False, methods=['get'])
    def sent(self, request):
        msgs = Message.objects.filter(sender=request.user).order_by('-created_at')
        page = self.paginate_queryset(msgs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(msgs, many=True).data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        msg = self.get_object()
        if msg.receiver == request.user:
            msg.is_read = True
            msg.save()
            return Response({'status': 'marked as read'})
        return Response({'status': 'forbidden'}, status=403)


# --- 18. 用户搜索 ---
class UserSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([])

        users = CustomUser.objects.filter(
            Q(username__icontains=query) |
            Q(nickname__icontains=query) |
            Q(id__iexact=query)
        ).exclude(id=request.user.id)[:10]

        results = []
        my_friendships = Friendship.objects.filter(
            Q(from_user=request.user) | Q(to_user=request.user)
        )

        for u in users:
            status_str = 'none'
            rel = my_friendships.filter(
                (Q(from_user=request.user, to_user=u) | Q(from_user=u, to_user=request.user)),
                status=Friendship.STATUS_ACCEPTED
            ).first()

            if rel:
                status_str = 'friend'
            else:
                sent = my_friendships.filter(from_user=request.user, to_user=u,
                                             status=Friendship.STATUS_PENDING).exists()
                if sent:
                    status_str = 'sent'
                else:
                    received = my_friendships.filter(from_user=u, to_user=request.user,
                                                     status=Friendship.STATUS_PENDING).exists()
                    if received:
                        status_str = 'received'

            u_data = UserSerializer(u).data
            u_data['friendship_status'] = status_str
            results.append(u_data)

        return Response(results)


# --- 19. 好友管理视图 ---
class FriendshipViewSet(viewsets.ModelViewSet):
    serializer_class = FriendshipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Friendship.objects.filter(
            Q(from_user=user) | Q(to_user=user)
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset().filter(status=Friendship.STATUS_ACCEPTED))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def friends(self, request):
        user = request.user
        friendships = Friendship.objects.filter(
            (Q(from_user=user) | Q(to_user=user)),
            status=Friendship.STATUS_ACCEPTED
        )
        friend_users = []
        for f in friendships:
            if f.from_user == user:
                friend_users.append(f.to_user)
            else:
                friend_users.append(f.from_user)
        serializer = UserSerializer(friend_users, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_requests(self, request):
        requests = Friendship.objects.filter(
            to_user=request.user,
            status=Friendship.STATUS_PENDING
        ).order_by('-created_at')
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        friendship = self.get_object()
        if friendship.to_user != request.user:
            return Response({"detail": "无权操作"}, status=status.HTTP_403_FORBIDDEN)
        friendship.status = Friendship.STATUS_ACCEPTED
        friendship.save()
        return Response({"status": "accepted"})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        friendship = self.get_object()
        if friendship.to_user != request.user:
            return Response({"detail": "无权操作"}, status=status.HTTP_403_FORBIDDEN)
        friendship.status = Friendship.STATUS_REJECTED
        friendship.save()
        return Response({"status": "rejected"})


# --- 20. 轮播图管理 ---
class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'active']:
            return [permissions.AllowAny()]
        return [IsAdminRole()]

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def active(self, request):
        """获取所有启用的轮播图"""
        banners = Banner.objects.filter(is_active=True)
        serializer = self.get_serializer(banners, many=True)
        return Response(serializer.data)


# --- 21. 公告管理 ---
class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'active']:
            return [permissions.AllowAny()]
        return [IsAdminRole()]

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def active(self, request):
        """获取所有启用的公告"""
        announcements = Announcement.objects.filter(is_active=True)[:5]
        serializer = self.get_serializer(announcements, many=True)
        return Response(serializer.data)


# --- 22. 视频播放进度 ---
class VideoProgressViewSet(viewsets.ModelViewSet):
    serializer_class = VideoProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return VideoProgress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # 更新或创建进度
        lesson = serializer.validated_data.get('lesson')
        progress, created = VideoProgress.objects.update_or_create(
            user=self.request.user,
            lesson=lesson,
            defaults={
                'last_position': serializer.validated_data.get('last_position', 0),
                'duration': serializer.validated_data.get('duration', 0)
            }
        )
        return progress

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        progress = self.perform_create(serializer)
        return Response(VideoProgressSerializer(progress).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def get_progress(self, request):
        """获取指定课时的播放进度"""
        lesson_id = request.query_params.get('lesson_id')
        if not lesson_id:
            return Response({"last_position": 0, "duration": 0})
        try:
            progress = VideoProgress.objects.get(user=request.user, lesson_id=lesson_id)
            return Response({
                "last_position": progress.last_position,
                "duration": progress.duration
            })
        except VideoProgress.DoesNotExist:
            return Response({"last_position": 0, "duration": 0})


# --- 23. 用户积分系统 ---
class PointsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def my_points(self, request):
        """获取当前用户的积分信息"""
        points, created = UserPoints.objects.get_or_create(user=request.user)
        badges = UserBadge.objects.filter(user=request.user).select_related('badge')
        return Response({
            "total_points": points.total_points,
            "level": points.level,
            "continuous_days": points.continuous_days,
            "badges": UserBadgeSerializer(badges, many=True).data
        })

    @action(detail=False, methods=['get'])
    def records(self, request):
        """获取积分变化记录"""
        records = PointRecord.objects.filter(user=request.user)[:50]
        return Response(PointRecordSerializer(records, many=True).data)

    @action(detail=False, methods=['post'])
    def add_points(self, request):
        """添加积分(内部调用)"""
        action_type = request.data.get('action')
        if action_type not in ['watch', 'comment', 'submit', 'login']:
            return Response({"detail": "无效的积分类型"}, status=400)

        # 积分规则
        points_map = {
            'watch': 5,
            'comment': 3,
            'submit': 10,
            'login': 2
        }
        points = points_map.get(action_type, 0)

        # 更新用户积分
        user_points, _ = UserPoints.objects.get_or_create(user=request.user)
        user_points.total_points += points
        user_points.level = 1 + user_points.total_points // 100  # 每100分升一级
        
        # 更新连续学习天数
        today = timezone.now().date()
        if user_points.last_active_date:
            if user_points.last_active_date == today - timezone.timedelta(days=1):
                user_points.continuous_days += 1
            elif user_points.last_active_date != today:
                user_points.continuous_days = 1
        else:
            user_points.continuous_days = 1
        user_points.last_active_date = today
        user_points.save()

        # 记录积分变化
        PointRecord.objects.create(
            user=request.user,
            action=action_type,
            points=points,
            description=f"获得{points}积分"
        )

        # 检查并解锁勋章
        self._check_badges(request.user, user_points)

        return Response({
            "points_added": points,
            "total_points": user_points.total_points,
            "level": user_points.level
        })

    def _check_badges(self, user, user_points):
        """检查并解锁勋章"""
        badges = Badge.objects.all()
        for badge in badges:
            # 跳过已获得的勋章
            if UserBadge.objects.filter(user=user, badge=badge).exists():
                continue
            
            # 检查条件
            unlocked = False
            if badge.condition_type == 'points' and user_points.total_points >= badge.condition_value:
                unlocked = True
            elif badge.condition_type == 'continuous_days' and user_points.continuous_days >= badge.condition_value:
                unlocked = True
            elif badge.condition_type == 'level' and user_points.level >= badge.condition_value:
                unlocked = True

            if unlocked:
                UserBadge.objects.create(user=user, badge=badge)


# --- 24. 勋章管理 ---
class BadgeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    permission_classes = [permissions.AllowAny]