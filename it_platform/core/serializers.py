from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import (
    CustomUser, Course, Module, Lesson, Category,
    InstructorApplication, Comment
)


# --- 1. 用户序列化 ---
class UserSerializer(serializers.ModelSerializer):
    enrollments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    favorited_courses = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    # 【修复】: 允许头像字段写入 (移除 read_only=True，改为 required=False)
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'nickname', 'email', 'avatar', 'bio', 'role',
            'enrollments', 'favorited_courses'
        ]
        read_only_fields = ['role', 'username', 'enrollments', 'favorited_courses']

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

    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    view_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'created_at',
            'instructor', 'modules', 'cover_image', 'category',
            'like_count', 'is_liked', 'is_favorited', 'view_count'
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