import json
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import (
    CustomUser, Course, Module, Lesson, Enrollment,
    Category, InstructorApplication, Comment, Note, Assignment, Submission, Message, Friendship
)


# --- 1. 用户序列化 (普通用途) ---
class UserSerializer(serializers.ModelSerializer):
    enrollments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    favorited_courses = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'nickname', 'email', 'avatar', 'bio', 'role',
            'enrollments', 'favorited_courses', 'date_joined'
        ]
        read_only_fields = ['role', 'username', 'enrollments', 'favorited_courses', 'date_joined']

    def validate_bio(self, value):
        if value and len(value) > 1000:
            raise serializers.ValidationError("个人简介长度不能超过1000个字符")
        return value


# --- 2. 修改密码序列化 ---
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "两次输入的密码不一致"})
        return data


# --- 3. 分类序列化 ---
class CategorySerializer(serializers.ModelSerializer):
    total_likes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'total_likes']


# --- 课程详情中的作业简略序列化 (学生看) ---
class CourseAssignmentSerializer(serializers.ModelSerializer):
    my_submission = serializers.SerializerMethodField()
    quiz_questions = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'assignment_type', 'quiz_questions', 'created_at', 'my_submission',
                  'attachment']

    def get_quiz_questions(self, obj):
        if obj.assignment_type == Assignment.TYPE_CHOICE and obj.quiz_data:
            try:
                questions = json.loads(obj.quiz_data)
                safe_questions = []
                for q in questions:
                    safe_questions.append({
                        "question": q.get("question"),
                        "options": q.get("options")
                    })
                return safe_questions
            except:
                return []
        return None

    def get_my_submission(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            submission = obj.submissions.filter(student=request.user).first()
            if submission:
                return {
                    'id': submission.id,
                    'status': submission.status,
                    'grade': submission.grade,
                    'feedback': submission.feedback,
                    'content': submission.content,
                    'submitted_at': submission.submitted_at,
                    'attachment': submission.attachment.url if submission.attachment else None
                }
        return None


# --- 4. 课时序列化 ---
class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id', 'module', 'title', 'lesson_type',
            'content', 'video_mp4_file', 'video_m3u8_url', 'order'
        ]

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("课时标题不能为空")
        return value.strip()


# --- 5. 章节序列化 ---
class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'order', 'lessons']

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("章节标题不能为空")
        return value.strip()


# --- 6. 课程列表序列化 (List) ---
class CourseListSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    like_count = serializers.SerializerMethodField()
    view_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'created_at',
            'instructor', 'cover_image', 'category',
            'like_count', 'view_count'
        ]

    def get_like_count(self, obj):
        return getattr(obj, 'like_count', obj.likes.count())

    def get_view_count(self, obj):
        return getattr(obj, 'view_count', obj.view_count)


# --- 7. 课程详情序列化 (Detail) ---
class CourseDetailSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    instructor = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    assignments = CourseAssignmentSerializer(many=True, read_only=True)

    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    view_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'created_at',
            'instructor', 'modules', 'cover_image', 'category',
            'like_count', 'is_liked', 'is_favorited', 'view_count',
            'assignments'
        ]

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            return obj.likes.filter(pk=user.pk).exists()
        return False

    def get_is_favorited(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            return user.favorited_courses.filter(pk=obj.pk).exists()
        return False


# --- 8. 讲师申请序列化 ---
class InstructorApplicationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = InstructorApplication
        fields = ['id', 'user', 'justification', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']

    def validate_justification(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("申请理由不能为空")
        return value.strip()

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user.role != CustomUser.ROLE_STUDENT:
            raise serializers.ValidationError("只有学生才能申请成为讲师")
        if request and InstructorApplication.objects.filter(user=request.user).exists():
            raise serializers.ValidationError("你已经提交过申请，请勿重复提交")
        return data


# --- 9. 评论序列化 ---
class ReplySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    reply_to_user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'created_at', 'parent', 'reply_to_user']


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = ReplySerializer(many=True, read_only=True)
    reply_to_user = UserSerializer(read_only=True)

    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(), write_only=True, allow_null=True, required=False
    )
    reply_to_user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), write_only=True, allow_null=True, required=False, source='reply_to_user'
    )

    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'lesson', 'content', 'created_at',
            'parent', 'replies', 'reply_to_user', 'reply_to_user_id'
        ]
        read_only_fields = ['user', 'created_at', 'replies', 'reply_to_user']

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("评论内容不能为空")
        return value.strip()

    def validate(self, data):
        parent = data.get('parent')
        reply_to_user = data.get('reply_to_user')

        if parent:
            if parent.parent_id is not None:
                data['parent'] = parent.parent
            if not reply_to_user:
                data['reply_to_user'] = parent.user
        return data


# --- 10. 笔记序列化 ---
class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'user', 'lesson', 'content', 'video_timestamp', 'created_at']
        read_only_fields = ['user', 'created_at']


# --- 11. 作业相关序列化 ---
class SubmissionSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    course_title = serializers.CharField(source='assignment.course.title', read_only=True)
    assignment_type = serializers.CharField(source='assignment.assignment_type', read_only=True)

    class Meta:
        model = Submission
        fields = ['id', 'assignment', 'assignment_title', 'course_title', 'assignment_type', 'student', 'content',
                  'status', 'feedback',
                  'grade', 'submitted_at', 'attachment']
        read_only_fields = ['student', 'submitted_at']


class AssignmentSerializer(serializers.ModelSerializer):
    submission_count = serializers.IntegerField(read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = Assignment
        fields = ['id', 'course', 'course_title', 'title', 'description', 'assignment_type', 'quiz_data', 'created_at',
                  'submission_count', 'attachment']


# --- 12. 管理员用户管理序列化 ---
class AdminUserSerializer(serializers.ModelSerializer):
    """
    管理员专用：允许修改所有用户字段（包括 role, is_active 等）
    """

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'nickname', 'email', 'bio', 'role', 'is_active', 'date_joined']
        read_only_fields = ['date_joined']


# --- 13. 私信序列化 ---
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    receiver_username = serializers.CharField(write_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'receiver_username', 'content', 'is_read', 'created_at']
        read_only_fields = ['sender', 'receiver', 'is_read', 'created_at']

    def create(self, validated_data):
        receiver_username = validated_data.pop('receiver_username')
        try:
            receiver = CustomUser.objects.get(username=receiver_username)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"receiver_username": "用户不存在"})

        request = self.context.get('request')
        if request.user == receiver:
            raise serializers.ValidationError({"receiver_username": "不能给自己发送私信"})

        message = Message.objects.create(sender=request.user, receiver=receiver, **validated_data)
        return message


# --- 14. 好友关系序列化 (新增) ---
class FriendshipSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    to_username = serializers.CharField(write_only=True)

    class Meta:
        model = Friendship
        fields = ['id', 'from_user', 'to_user', 'to_username', 'status', 'created_at']
        read_only_fields = ['from_user', 'to_user', 'status', 'created_at']

    def create(self, validated_data):
        to_username = validated_data.pop('to_username')
        request = self.context.get('request')
        from_user = request.user

        try:
            to_user = CustomUser.objects.get(username=to_username)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"to_username": "用户不存在"})

        if from_user == to_user:
            raise serializers.ValidationError({"to_username": "不能添加自己为好友"})

        if Friendship.objects.filter(from_user=from_user, to_user=to_user).exists():
            raise serializers.ValidationError({"to_username": "已发送过申请，请勿重复发送"})

        reverse_rel = Friendship.objects.filter(from_user=to_user, to_user=from_user).first()
        if reverse_rel:
            if reverse_rel.status == Friendship.STATUS_ACCEPTED:
                raise serializers.ValidationError({"to_username": "你们已经是好友了"})
            elif reverse_rel.status == Friendship.STATUS_PENDING:
                raise serializers.ValidationError({"to_username": "对方已经向你发送了申请，请去处理"})

        return Friendship.objects.create(from_user=from_user, to_user=to_user, status=Friendship.STATUS_PENDING)