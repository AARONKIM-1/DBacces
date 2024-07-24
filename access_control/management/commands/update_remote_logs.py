import MySQLdb
from django.core.management.base import BaseCommand
from access_control.models import RemoteLog

class Command(BaseCommand):
    help = 'Fetch and update remote logs from MySQL general_log'

    def handle(self, *args, **kwargs):
        mysql_host = '127.0.0.1'
        mysql_user = 'root'
        mysql_password = '12345'
        mysql_db = 'mysql'

        self.update_remote_logs(mysql_host, mysql_user, mysql_password, mysql_db)

    def fetch_general_log(self, mysql_host, mysql_user, mysql_password, mysql_db):
        conn = MySQLdb.connect(
            host=mysql_host,
            user=mysql_user,
            passwd=mysql_password,
            db=mysql_db
        )
        cursor = conn.cursor()
        cursor.execute("SELECT event_time, user_host, command_type, argument FROM mysql.general_log")
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        return logs

    def update_remote_logs(self, mysql_host, mysql_user, mysql_password, mysql_db):
        logs = self.fetch_general_log(mysql_host, mysql_user, mysql_password, mysql_db)
        for log in logs:
            timestamp, user_host, command_type, argument = log
            RemoteLog.objects.get_or_create(
                timestamp=timestamp,
                user_host=user_host,
                command_type=command_type,
                argument=argument
            )
        self.stdout.write(self.style.SUCCESS('Successfully updated remote logs'))
