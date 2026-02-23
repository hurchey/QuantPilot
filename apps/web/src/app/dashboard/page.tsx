"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

type TaskStatus = "todo" | "in_progress" | "done";
type TaskPriority = "low" | "medium" | "high";

type Me = {
  email: string;
  workspace_id: number;
  workspace_name: string;
};

type Task = {
  id: number;
  title: string;
  status: TaskStatus;
  priority: TaskPriority;
};

type TaskStats = {
  total: number;
  todo: number;
  in_progress: number;
  done: number;
};

export default function DashboardPage() {
  const router = useRouter();

  const [me, setMe] = useState<Me | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [stats, setStats] = useState<TaskStats | null>(null);

  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskPriority, setNewTaskPriority] = useState<TaskPriority>("medium");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const sortedTasks = useMemo(() => {
    const priorityWeight: Record<TaskPriority, number> = {
      high: 3,
      medium: 2,
      low: 1,
    };

    return [...tasks].sort((a, b) => {
      if (a.status !== b.status) {
        const statusOrder: Record<TaskStatus, number> = {
          todo: 0,
          in_progress: 1,
          done: 2,
        };
        return statusOrder[a.status] - statusOrder[b.status];
      }
      return priorityWeight[b.priority] - priorityWeight[a.priority];
    });
  }, [tasks]);

  async function loadAll() {
    setLoading(true);
    setError("");
    try {
      const [meData, taskData, statsData] = await Promise.all([
        apiFetch<Me>("/me"),
        apiFetch<{ tasks: Task[] }>("/tasks"),
        apiFetch<TaskStats>("/tasks/stats"),
      ]);

      setMe(meData);
      setTasks(taskData.tasks);
      setStats(statsData);
    } catch (err) {
      router.push("/login");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  async function addTask() {
    if (!newTaskTitle.trim()) return;

    setSaving(true);
    setError("");

    try {
      await apiFetch<Task>("/tasks", {
        method: "POST",
        body: JSON.stringify({
          title: newTaskTitle.trim(),
          priority: newTaskPriority,
        }),
      });
      setNewTaskTitle("");
      setNewTaskPriority("medium");
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
    } finally {
      setSaving(false);
    }
  }

  async function updateTaskStatus(taskId: number, status: TaskStatus) {
    setSaving(true);
    setError("");
    try {
      await apiFetch<Task>(`/tasks/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update task");
    } finally {
      setSaving(false);
    }
  }

  async function deleteTask(taskId: number) {
    setSaving(true);
    setError("");
    try {
      await apiFetch<{ message: string }>(`/tasks/${taskId}`, { method: "DELETE" });
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete task");
    } finally {
      setSaving(false);
    }
  }

  async function logout() {
    await apiFetch<{ message: string }>("/auth/logout", { method: "POST" });
    router.push("/login");
  }

  if (loading) {
    return (
      <main className="container">
        <div className="card">Loading dashboard...</div>
      </main>
    );
  }

  return (
    <main className="container">
      <div className="card" style={{ padding: 20 }}>
        <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1 className="title">{me?.workspace_name ?? "Workspace"}</h1>
            <p className="subtitle">{me?.email}</p>
          </div>

          <button className="button secondary" onClick={logout}>
            Logout
          </button>
        </div>
      </div>

      {stats && (
        <div className="stats-grid" style={{ marginTop: 12 }}>
          <StatCard label="Total" value={stats.total} />
          <StatCard label="Todo" value={stats.todo} />
          <StatCard label="In Progress" value={stats.in_progress} />
          <StatCard label="Done" value={stats.done} />
        </div>
      )}

      <div className="card" style={{ marginTop: 12 }}>
        <h2 style={{ margin: 0, fontSize: 18 }}>Create Task</h2>
        <div className="grid" style={{ marginTop: 12 }}>
          <input
            className="input"
            placeholder="Task title"
            value={newTaskTitle}
            onChange={(e) => setNewTaskTitle(e.target.value)}
          />

          <div className="row">
            <select
              className="select"
              value={newTaskPriority}
              onChange={(e) => setNewTaskPriority(e.target.value as TaskPriority)}
            >
              <option value="low">Low priority</option>
              <option value="medium">Medium priority</option>
              <option value="high">High priority</option>
            </select>

            <button className="button" onClick={addTask} disabled={saving}>
              Add Task
            </button>
          </div>
        </div>
      </div>

      {error ? (
        <div
          className="card"
          style={{ marginTop: 12, borderColor: "#fecaca", background: "#fef2f2", color: "#991b1b" }}
        >
          {error}
        </div>
      ) : null}

      <div className="grid" style={{ marginTop: 12 }}>
        {sortedTasks.length === 0 ? (
          <div className="card muted">No tasks yet. Add your first task above.</div>
        ) : (
          sortedTasks.map((task) => (
            <div key={task.id} className="card task-item">
              <div>
                <div style={{ fontWeight: 600 }}>{task.title}</div>
                <div className="badges">
                  <span className="badge">Status: {task.status}</span>
                  <span className="badge">Priority: {task.priority}</span>
                </div>
              </div>

              <div className="grid" style={{ minWidth: 180 }}>
                <select
                  className="select"
                  value={task.status}
                  onChange={(e) => updateTaskStatus(task.id, e.target.value as TaskStatus)}
                  disabled={saving}
                >
                  <option value="todo">todo</option>
                  <option value="in_progress">in_progress</option>
                  <option value="done">done</option>
                </select>

                <button
                  className="button danger"
                  onClick={() => deleteTask(task.id)}
                  disabled={saving}
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </main>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="card">
      <div className="muted" style={{ fontSize: 13 }}>{label}</div>
      <div style={{ fontWeight: 700, fontSize: 24, marginTop: 4 }}>{value}</div>
    </div>
  );
}