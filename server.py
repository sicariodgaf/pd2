import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import psycopg2


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.conn = self.__connect_db()
        super().__init__(*args, **kwargs)

    def __connect_db(self):
        return psycopg2.connect(
            dbname='mydatabase',
            user='postgres',
            password='admin',
            host='localhost'
        )

    def do_GET(self):
        if self.path == '/tasks':
            self.__get_all_tasks()
        elif self.path.startswith('/tasks/'):
            task_id = self.path.split('/')[-1]
            self.__get_task_by_id(task_id)

    def do_POST(self):
        if self.path == '/tasks':
            self.__add_task()

    def do_PUT(self):
        if self.path == '/tasks':
            self.__update_task_status()

    def do_DELETE(self):
        if self.path == '/tasks':
            self.__delete_task()

    def __get_all_tasks(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tasks;")
            tasks = cursor.fetchall()
            self.__send_response(200, json.dumps(tasks))

    def __get_task_by_id(self, task_id):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tasks WHERE id = %s;", (task_id,))
            task = cursor.fetchone()
            if task:
                self.__send_response(200, json.dumps(task))
            else:
                self.__send_response(404, json.dumps({"error": "Task not found"}))

    def __add_task(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body)

        with self.conn.cursor() as cursor:
            cursor.execute("INSERT INTO tasks (title, completed) VALUES (%s, %s) RETURNING id;",
                           (data['title'], data.get('completed', '0')))
            task_id = cursor.fetchone()[0]
            self.conn.commit()
            self.__send_response(201, json.dumps({"id": task_id}))

    def __update_task_status(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body)

        with self.conn.cursor() as cursor:
            cursor.execute("UPDATE tasks SET completed = %s WHERE id = %s;",
                           (data['completed'], data['id']))
            self.conn.commit()
            self.__send_response(200, json.dumps({"message": "Task updated"}))

    def __delete_task(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body)

        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM tasks WHERE id = %s;", (data['id'],))
            self.conn.commit()
            self.__send_response(200, json.dumps({"message": "Task deleted"}))

    def __send_response(self, status_code, message):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
