import json
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.text import slugify


# --- 1. 用户模型 ---
class CustomUser(AbstractUser):
    ROLE_STUDENT = 'student'
    ROLE_INSTRUCTOR = 'instructor'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_STUDENT, '学生'),
        (ROLE_INSTRUCTOR, '讲师'),
        (ROLE_ADMIN, '管理员'),
    ]

    role = models.CharField(
        verbose_name="用户角色",
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT
    )
    bio = models.TextField(verbose_name="个人简介", blank=True)
    nickname = models.CharField(verbose_name="昵称", max_length=30, blank=True)
    avatar = models.ImageField(verbose_name="头像", upload_to='avatars/', null=True, blank=True)

    favorited_courses = models.ManyToManyField(
        'Course',
        blank=True,
        related_name='favorited_by',
        verbose_name="收藏的课程"
    )

    def __str__(self):
        return self.nickname if self.nickname else self.username


# --- 2. 课程分类 ---
class Category(models.Model):
    name = models.CharField(verbose_name="分类名称", max_length=100, unique=True)
    slug = models.SlugField(
        max_length=100, unique=True, blank=True, allow_unicode=True,
        help_text="用于URL的短标签"
    )
    order = models.IntegerField(verbose_name="热门权重", default=0, help_text="数值越大，排序越靠前")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['-order']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# --- 3. 课程模型 ---
class Course(models.Model):
    title = models.CharField(verbose_name="课程标题", max_length=255, db_index=True)
    description = models.TextField(verbose_name="课程描述")
    cover_image = models.ImageField(
        verbose_name="课程封面图",
        upload_to='course_covers/',
        null=True, blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='courses',
        verbose_name="课程分类",
        db_index=True
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses_taught',
        verbose_name="授课讲师",
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='liked_courses',
        verbose_name="点赞用户"
    )
    view_count = models.PositiveIntegerField(
        verbose_name="观看次数",
        default=0,
        db_index=True
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['instructor', '-created_at']),
            models.Index(fields=['-view_count']),
        ]

    def __str__(self):
        return self.title


# --- 4. 章节 ---
class Module(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE,
        related_name='modules', verbose_name="所属课程", db_index=True
    )
    title = models.CharField(verbose_name="章节标题", max_length=255)
    order = models.PositiveIntegerField(verbose_name="章节顺序", default=0, db_index=True)

    class Meta:
        ordering = ['order']
        indexes = [models.Index(fields=['course', 'order'])]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


# --- 5. 课时 ---
class Lesson(models.Model):
    LESSON_VIDEO = 'video'
    LESSON_TEXT = 'text'
    LESSON_TYPE_CHOICES = [
        (LESSON_VIDEO, '视频'),
        (LESSON_TEXT, '文本'),
    ]

    module = models.ForeignKey(
        Module, on_delete=models.CASCADE,
        related_name='lessons', verbose_name="所属章节", db_index=True
    )
    title = models.CharField(verbose_name="课时标题", max_length=255)
    lesson_type = models.CharField(
        verbose_name="课时类型", max_length=10,
        choices=LESSON_TYPE_CHOICES, default=LESSON_TEXT, db_index=True
    )
    video_mp4_file = models.FileField(
        verbose_name="上传的MP4原文件",
        upload_to='lesson_videos_mp4/',
        null=True, blank=True
    )
    video_m3u8_url = models.URLField(verbose_name="HLS视频URL", null=True, blank=True)
    content = models.TextField(verbose_name="文本内容", blank=True)
    order = models.PositiveIntegerField(verbose_name="课时顺序", default=0, db_index=True)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['module', 'order']),
            models.Index(fields=['lesson_type']),
        ]

    def __str__(self):
        return self.title


# --- 6. 注册 (购买) ---
class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='enrollments', verbose_name="学生", db_index=True
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE,
        related_name='enrollments', verbose_name="课程", db_index=True
    )
    enrolled_at = models.DateTimeField(verbose_name="注册时间", auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ('student', 'course')
        indexes = [
            models.Index(fields=['student', '-enrolled_at']),
            models.Index(fields=['course', '-enrolled_at']),
        ]

    def __str__(self):
        return f"{self.student.username} 注册了 {self.course.title}"


# --- 7. 学习进度 ---
class LessonProgress(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='progress', verbose_name="学生", db_index=True
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE,
        related_name='progress', verbose_name="课时", db_index=True
    )
    is_completed = models.BooleanField(verbose_name="是否完成", default=False, db_index=True)

    class Meta:
        unique_together = ('student', 'lesson')
        indexes = [
            models.Index(fields=['student', 'is_completed']),
            models.Index(fields=['lesson', 'is_completed']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"


# --- 8. 讲师申请 ---
class InstructorApplication(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待处理'),
        (STATUS_APPROVED, '已批准'),
        (STATUS_REJECTED, '已拒绝'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='application', verbose_name="申请人"
    )
    justification = models.TextField(verbose_name="申请理由")
    status = models.CharField(
        verbose_name="申请状态", max_length=10,
        choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    created_at = models.DateTimeField(verbose_name="申请时间", auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} 的申请 ({self.status})"


# --- 9. 评论 ---
class Comment(models.Model):
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE,
        related_name='comments', verbose_name="所属课时", db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='comments', verbose_name="评论用户", db_index=True
    )
    content = models.TextField(verbose_name="评论内容")
    created_at = models.DateTimeField(verbose_name="评论时间", auto_now_add=True, db_index=True)

    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE,
        related_name='replies', verbose_name="父评论"
    )
    reply_to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='replies_received', verbose_name="回复对象"
    )

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['lesson', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} 评论 {self.lesson.title}"


# --- 10. 学习笔记 ---
class Note(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notes', verbose_name="用户"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE,
        related_name='notes', verbose_name="所属课时"
    )
    content = models.TextField(verbose_name="笔记内容")
    video_timestamp = models.FloatField(verbose_name="视频时间戳(秒)", default=0.0)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'lesson']),
        ]

    def __str__(self):
        return f"{self.user.username} 的笔记 - {self.lesson.title}"


# --- 11. 作业系统 ---
class Assignment(models.Model):
    TYPE_REGULAR = 'regular'
    TYPE_CHOICE = 'choice'
    TYPE_CHOICES = [
        (TYPE_REGULAR, '图文/文件作业'),
        (TYPE_CHOICE, '选择题(多题)'),
    ]

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE,
        related_name='assignments', verbose_name="所属课程"
    )
    title = models.CharField(verbose_name="作业标题", max_length=255)
    description = models.TextField(verbose_name="作业要求(或题目描述)")

    assignment_type = models.CharField(
        verbose_name="作业类型",
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_REGULAR
    )

    quiz_data = models.TextField(verbose_name="题目数据(JSON)", blank=True, null=True)

    attachment = models.FileField(
        verbose_name="作业附件",
        upload_to='assignments/',
        null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Submission(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PASSED = 'passed'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待批改'),
        (STATUS_PASSED, '已通过'),
        (STATUS_REJECTED, '需修改'),
    ]

    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE,
        related_name='submissions', verbose_name="所属作业"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='submissions', verbose_name="提交学生"
    )

    content = models.TextField(verbose_name="作业内容")

    attachment = models.FileField(
        verbose_name="提交附件",
        upload_to='submissions/',
        null=True, blank=True
    )

    status = models.CharField(
        verbose_name="状态", max_length=10,
        choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    feedback = models.TextField(verbose_name="讲师评语", blank=True)
    grade = models.PositiveIntegerField(verbose_name="评分", null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"{self.student.username} 提交 {self.assignment.title}"


# --- 12. 站内信模型 ---
class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='sent_messages', verbose_name="发送者"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='received_messages', verbose_name="接收者"
    )
    content = models.TextField(verbose_name="私信内容")
    is_read = models.BooleanField(default=False, verbose_name="是否已读")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="发送时间")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.content[:20]}"


# --- 13. 好友关系模型 (新增) ---
class Friendship(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待处理'),
        (STATUS_ACCEPTED, '已接受'),
        (STATUS_REJECTED, '已拒绝'),
    ]

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='friendship_sent',
        on_delete=models.CASCADE, verbose_name="申请人"
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='friendship_received',
        on_delete=models.CASCADE, verbose_name="接收人"
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES,
        default=STATUS_PENDING, verbose_name="状态"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="申请时间")

    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"