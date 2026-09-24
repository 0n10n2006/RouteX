import { useEffect, useState } from "react";
import axios from "axios";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Users } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "/api";

export default function AdminDashboard({ user }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await axios.get(`${API_URL}/admin/users`);
        setUsers(res.data.users);
      } catch (err) {
        console.error("Failed to load users:", err);
      } finally {
        setLoading(false);
      }
    };
    if (user?.role === "admin") {
      fetchUsers();
    }
  }, [user]);

  if (user?.role !== "admin") {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        Admin access required.
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center space-x-3">
        <Users className="w-8 h-8 text-primary" />
        <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-card/50 backdrop-blur border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Users</CardTitle>
            <Users className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{users.length}</div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-card/50 backdrop-blur border-border/50">
        <CardHeader>
          <CardTitle>User Directory</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-sm text-muted-foreground">Loading users...</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead>Joined</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((u) => (
                  <TableRow key={u.firebase_uid}>
                    <TableCell className="font-medium">{u.email}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded-full text-xs ${u.role === 'admin' ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'}`}>
                        {u.role}
                      </span>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(u.last_login).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(u.created_at).toLocaleDateString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
