from django.db import models
from django.contrib.auth.models import User
from django.db import connections, OperationalError
import base64
from db_access_control import settings
from cryptography.fernet import Fernet


key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode())
fernet = Fernet(key)

class Database(models.Model):
    DB_TYPE_CHOICES = [
        ('sqlite3', 'SQLite3'),
        ('postgresql', 'PostgreSQL'),
        ('mysql', 'MySQL'),
        ('oracle', 'Oracle'),
    ]

    STATUS_CHOICES = [
        ('Connected', 'Connected'),
        ('Disconnected', 'Disconnected'),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name='DB이름')
    # description = models.CharField(max_length=100, unique=True, verbose_name='DB설명')
    db_type = models.CharField(max_length=10, choices=DB_TYPE_CHOICES,verbose_name='DB 타입')
    user = models.CharField(max_length=100,verbose_name='DB계정명')
    password = models.CharField(max_length=100,verbose_name='DB비밀번호')
    host = models.CharField(max_length=100, default='localhost')
    port = models.CharField(max_length=5, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Disconnected')

    def set_password(self, raw_password):
        f = Fernet(key)
        self.password = f.encrypt(raw_password.encode()).decode()

    def get_decrypted_password(self):
        try:
            return fernet.decrypt(self.password.encode()).decode()
        except Exception as e:
            return "비밀번호를 복호화할 수 없습니다."
        
    def check_password(self, raw_password):
        f = Fernet(key)
        try:
            decrypted_password = f.decrypt(self.password.encode()).decode()
            return decrypted_password == raw_password
        except:
            return False

    def save(self, *args, **kwargs):
        if self.pk is None:
            # Encrypt the password before saving the model
            self.set_password(self.password)
        super().save(*args, **kwargs)

    def check_connection(self):
        try:
            with connections[self.name].cursor() as cursor:
                cursor.execute("SELECT 1")
            self.status = 'Connected'
        except OperationalError:
            self.status = 'Disconnected'
        self.save(update_fields=['status'])

    def save(self, *args, **kwargs):
        self.update_database_settings()
        super().save(*args, **kwargs)

    def update_database_settings(self):
        db_engine_map = {
            'sqlite3': 'django.db.backends.sqlite3',
            'postgresql': 'django.db.backends.postgresql',
            'mysql': 'django.db.backends.mysql',
            'oracle': 'django.db.backends.oracle',
        }

        if self.db_type in db_engine_map:
            settings.DATABASES[self.name] = {
                'ENGINE': db_engine_map[self.db_type],
                'NAME': self.name,
                'USER': self.user,
                'PASSWORD': self.password,
                'HOST': self.host,
                'PORT': self.port,
                'ATOMIC_REQUESTS': True,
                'AUTOCOMMIT': True,
                'OPTIONS': {},
                'TIME_ZONE': settings.TIME_ZONE,
                'CONN_HEALTH_CHECKS': True,
                'CONN_MAX_AGE': 0,
            }
    def __str__(self):
        return self.name
class PermissionGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    can_select_all = models.BooleanField(default=False)
    can_select_specific_columns = models.BooleanField(default=False)
    can_insert_all = models.BooleanField(default=False)
    can_insert_specific_columns = models.BooleanField(default=False)
    can_update_all = models.BooleanField(default=False)
    can_update_specific_columns = models.BooleanField(default=False)
    can_delete_all = models.BooleanField(default=False)
    can_delete_specific_rows = models.BooleanField(default=False)
    can_create_table = models.BooleanField(default=False)
    can_alter_table = models.BooleanField(default=False)
    can_drop_table = models.BooleanField(default=False)
    can_create_index = models.BooleanField(default=False)
    can_drop_index = models.BooleanField(default=False)
    can_execute_procedure = models.BooleanField(default=False)
    can_execute_function = models.BooleanField(default=False)
    query_examples = models.TextField(blank=True, null=True) 

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = '권한 그룹'
        verbose_name_plural = '권한 그룹'    

class Permission(models.Model):
    database = models.ForeignKey(Database, on_delete=models.CASCADE)
    users = models.ManyToManyField(User)
    groups = models.ManyToManyField(PermissionGroup)


class UserBehavior(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    username = models.CharField(max_length=150, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f"{self.username if self.username else 'Unknown user'} - {self.action} at {self.timestamp} from {self.ip_address}"
    class Meta:
        verbose_name = '로그인 관련 로그'
        verbose_name_plural = '로그인 관련 로그'    

class AllowedIP(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField(unique=True)

    def __str__(self):
        return self.ip_address
    class Meta:
        verbose_name = '허용 IP'
        verbose_name_plural = '허용 IP'    

class Query(models.Model):
    QUERY_TYPES = [
        ('SELECT', 'SELECT'),
        ('INSERT', 'INSERT'),
        ('UPDATE', 'UPDATE'),
        ('DELETE', 'DELETE'),
        ('DDL', 'DDL'),
        ('ENCRYPT', 'ENCRYPT'),
        ('DECRYPT', 'DECRYPT'),
    ]

    database = models.ForeignKey(Database, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query_text = models.TextField()
    query_type = models.CharField(max_length=8, choices=QUERY_TYPES)
    success = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    result = models.TextField(null=True, blank=True)
    is_committed = models.BooleanField(default=False)
    executed_at = models.DateTimeField(auto_now_add=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # 쿼리 유형을 자동으로 설정
        lower_query = self.query_text.strip().lower()
        if 'decrypt' in lower_query:
            self.query_type = 'DECRYPT'
        elif 'select' in lower_query:
            self.query_type = 'SELECT'
        elif 'insert' in lower_query:
            self.query_type = 'INSERT'
        elif 'update' in lower_query:
            self.query_type = 'UPDATE'
        elif 'delete' in lower_query:
            self.query_type = 'DELETE'
        elif 'encrypt' in lower_query:
            self.query_type = 'ENCRYPT'

        else:
            self.query_type = 'DDL'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = '쿼리 수행 로그'
        verbose_name_plural = '쿼리 수행 로그'    


class DatabaseObject(models.Model):
    name = models.CharField(max_length=255)
    object_type = models.CharField(max_length=50)  # Table, View, Procedure, Function, Trigger
    description = models.TextField(blank=True, null=True)


class RemoteLog(models.Model):
    timestamp = models.DateTimeField()
    user_host = models.CharField(max_length=255)
    command_type = models.CharField(max_length=50)
    argument = models.TextField()

    def __str__(self):
        return f"{self.timestamp} - {self.user_host} - {self.command_type}"
