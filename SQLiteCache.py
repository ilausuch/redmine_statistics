from progress import *
import sqlite3

FIELDS_ISSUE = [{"name": "id", "type": "INTEGER"},
                {"name": "project.id", "type": "INTEGER"},
                {"name": "project.name", "type": "TEXT"},
                {"name": "type.id", "type": "INTEGER"},
                {"name": "type.name", "type": "TEXT"},
                {"name": "status.id", "type": "INTEGER"},
                {"name": "status.name", "type": "TEXT"},
                {"name": "priority.id", "type": "INTEGER"},
                {"name": "priority.name", "type": "TEXT"},
                {"name": "author.id", "type": "INTEGER"},
                {"name": "author.name", "type": "TEXT"},
                {"name": "assigned_to.id", "type": "INTEGER"},
                {"name": "assigned_to.name", "type": "TEXT"},
                {"name": "subject", "type": "TEXT"},
                {"name": "start_date", "type": "INTEGER"},
                {"name": "due_date", "type": "INTEGER"},
                {"name": "estimated_hours", "type": "INTEGER"},
                {"name": "created_on", "type": "INTEGER"},
                {"name": "updated_on", "type": "INTEGER"},
                {"name": "closed_on", "type": "INTEGER"}]

FIELDS_STATE = [{"name": "journal_id", "type": "INTEGER"},
                {"name": "project_id", "type": "INTEGER"},
                {"name": "issue_id", "type": "INTEGER"},
                {"name": "user.id", "type": "INTEGER"},
                {"name": "user.name", "type": "TEXT"},
                {"name": "created_on", "type": "INTEGER"},
                {"name": "property", "type": "TEXT"},
                {"name": "name", "type": "TEXT"},
                {"name": "old_value", "type": "TEXT"},
                {"name": "new_value", "type": "TEXT"}]

class SQLiteCache:
    def __init__(self, file, providder_adapter, drop_tables=False):
        self.file = file
        self.connected = False
        self.provider_adapter = providder_adapter
        self.drop_tables = drop_tables

    def setup(self):
        if not self.connected:
            self.con = sqlite3.connect(self.file)
            if self.drop_tables:
                self.exec("DROP TABLE IF EXISTS issue")
                self.exec("DROP TABLE IF EXISTS state")

            self.create_table("issue", FIELDS_ISSUE, ["id", "project.id"])
            self.create_table("state", FIELDS_STATE)

    def store_issue(self, issue, include_states=True, auto_commit=True):
        self.store("issue", FIELDS_ISSUE, issue.plain_values)
        if include_states:
            for state in issue.state_changes:
                self.store_state(state, False)

        if auto_commit:
            self.commit()

    def store_state(self, state, auto_commit=True):
        self.store("state", FIELDS_STATE, state.plain_values)
        if auto_commit:
            self.commit()

    def restore_issue(self, issue_id, project_id, include_states=True):
        res = self.exec(
            f"SELECT * FROM issue WHERE id={issue_id} AND \"project.id\"={project_id}")
        data = res.fetchone()
        return self.issue_from_data(data, include_states)

    def restore_states_from_issue(self, issue_id, project_id):
        res = self.exec(
            f"SELECT * FROM state WHERE \"project_id\"={project_id} AND \"issue_id\"={issue_id}")
        arr = res.fetchall()
        res = []
        for data in arr:
            res.append(State(self.row_to_data("state", data, FIELDS_STATE)))
        return res

    def restore_all_issues(self, include_states=True):
        res = self.exec(f"SELECT * FROM issue")
        data = res.fetchall()

        res = []
        for issue_data in data:
            issue = self.issue_from_data(issue_data, include_states)
            res.append(issue)

        return Issues(res)

    def issue_from_data(self, data, include_states=True):
        issue = Issue(self.row_to_data("issue", data, FIELDS_ISSUE))
        if include_states:
            issue.state_changes = self.restore_states_from_issue(
                issue.id(), issue.project_id())
        return issue

    def row_to_data(self, table, row, fields):
        plain = {}
        count = 0
        for field in fields:
            value = row[count]
            self.provider_adapter.from_database(table, field, value, plain)
            count = count + 1

        return plain_to_tree(plain)

    def create_table(self, table, fields, unique=None):
        arr_fields = []
        for field in fields:
            str_field = f"\"{field['name']}\" {field['type']}"
            if "extras" in field:
                str_field = f"{str_field} {field['extras']}"
            arr_fields.append(str_field)

        if unique is not None:
            unique_fix = []
            for v in unique:
                unique_fix.append(f"\"{v}\"")

            arr_fields.append(f"UNIQUE({','.join(unique_fix)})")

        try:
            self.exec(f"CREATE TABLE {table}({','.join(arr_fields)})")
        except sqlite3.OperationalError as e:
            if str(e) != f"table {table} already exists":
                raise e
        except Exception as e:
            raise e

    def exec(self, str, data=None):
        cur = self.con.cursor()
        if data is not None:
            cur.execute(str, data)
        else:
            cur.execute(str)

        return cur

    def store(self, table, fields, plain_values, auto_commit = True):
        plain = []

        for field in fields:
            plain.append(
                self.provider_adapter.to_database(table, field, plain_values))

        self.insert(table, plain)

        if auto_commit:
            self.commit()

    def insert(self, table, data):
        questionMarks = ['?'] * len(data)
        self.exec(
            f"INSERT INTO {table} VALUES({','.join(questionMarks)})", data)

    def commit(self):
        self.con.commit()